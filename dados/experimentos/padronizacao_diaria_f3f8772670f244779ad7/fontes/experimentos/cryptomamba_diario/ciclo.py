"""Preparação, identidade e fila exclusiva. Encerrados não são reexecutados."""
import os
import sys
import shutil
import socket
import subprocess
import traceback
from pathlib import Path
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256,identidade,conferir_arquivos

REG=RAIZ/'registros/cryptomamba_diario'
CFG=RAIZ/'configuracoes/cryptomamba_diario_001.json'


def fontes():
    dirs=['experimentos/cryptomamba_diario','tests_cryptomamba_diario','infraestrutura','modelos','treinamento','entradas_modelo','mercado_futuros']
    r={p.relative_to(RAIZ).as_posix():sha256(p) for d in dirs for p in (RAIZ/d).rglob('*.py')}
    nomes=['experimento_cryptomamba/modelo.py','simulacao_operacoes/diaria_24h.py','configuracoes/cryptomamba_diario_001.json',
           'docs/protocolo_cryptomamba_diario.md','docs/adr/0031-cryptomamba-diario-futuros.md']
    for n in nomes:r[n]=sha256(RAIZ/n)
    externo=RAIZ/'registros/cryptomamba/fontes_externas'/ler_json(CFG)['codigo_publico_commit']
    for p in externo.rglob('*'):
        if p.is_file() and p.suffix!='.pyc':r[p.relative_to(RAIZ).as_posix()]=sha256(p)
    for p in (RAIZ/ler_json(CFG)['auditoria_volume']).glob('*.json'):
        r[p.relative_to(RAIZ).as_posix()]=sha256(p)
    return r


def qualificar():
    import fcntl
    from .qualificacao import executar
    REG.mkdir(parents=True,exist_ok=True)
    with (RAIZ/'registros/operacional_futuros/gpu.lock').open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        consulta=subprocess.run(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],capture_output=True,text=True,check=True)
        if consulta.stdout.strip():raise RuntimeError('GPU ocupada.')
        p=REG/'qualificacoes'/agora().replace(':','').replace('+','_')
        try:
            executar(p)
            salvar_json(REG/'qualificacao.json',{'arquivo':(p/'qualificacao.json').relative_to(RAIZ).as_posix(),'sha256':sha256(p/'qualificacao.json'),
                                              'fontes':fontes()})
        except BaseException:
            salvar_json(p/'incidente.json',{'utc':agora(),'erro':traceback.format_exc()});raise


def preservacao():
    ptr=ler_json(RAIZ/'registros/historico_treino/execucao.json');p=RAIZ/ptr['pasta'];f=ler_json(p/'congelamento.json')
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    r=dict(f['preservacao']);r.update(f['fontes'])
    fecho=ler_json(p/'fechamento.json')
    for n,h in fecho['arquivos'].items():r[(p/n).relative_to(RAIZ).as_posix()]=h
    r[(p/'fechamento.json').relative_to(RAIZ).as_posix()]=sha256(p/'fechamento.json')
    r[(p/'congelamento.json').relative_to(RAIZ).as_posix()]=sha256(p/'congelamento.json')
    return r


def preparar():
    from mercado_futuros.diario_cryptomamba import carregar
    from entradas_modelo.cryptomamba_diario import preparar as entradas
    if (REG/'execucao.json').exists():raise RuntimeError('Identidade já preparada; não substituir.')
    c=ler_json(CFG);q=ler_json(REG/'qualificacao.json');assert sha256(RAIZ/q['arquivo'])==q['sha256']
    assert ler_json(RAIZ/q['arquivo'])['situacao']=='aprovado';conferir_arquivos(RAIZ,q['fontes'])
    diario,df=carregar();d=entradas(df,c)
    minute=ler_json(RAIZ/'registros/mercado_futuros/execucao.json');mp=RAIZ/minute['pasta']
    assert sha256(mp/'manifesto.json')==minute['manifesto_sha256']
    conferir_arquivos(mp,ler_json(mp/'manifesto.json')['arquivos'])
    k=pd.read_parquet(mp/'klines.parquet');g=k.groupby(k.open_time//86400000*86400000).agg(open=('open','first'),high=('high','max'),low=('low','min'),close=('close','last'),volume=('volume','sum'))
    a=df.set_index('open_time').loc[g.index];cols=['open','high','low','close']
    np.testing.assert_allclose(a[cols],g[cols],atol=.11,rtol=0)
    divergentes=abs(a.volume-g.volume)>g.volume*1e-6+.001
    audit=ler_json(RAIZ/c['auditoria_volume']/'incidente.json')
    observados={int(ts):(float(a.loc[ts].volume),float(g.loc[ts].volume)) for ts in g.index[divergentes]}
    aprovados={x['origem_ms']:(x['volume_diario'],x['volume_soma_minutos']) for x in audit['ocorrencias']}
    if observados!=aprovados:raise ValueError('Nova divergência de volume; não aceitar sem investigação.')
    api=ler_json(RAIZ/c['auditoria_volume']/'comparacao_api_completa.json')
    assert api['n']==len(df) and all(all(v==0 for v in x['diferenca'][:4]) for x in api['divergencias'])
    pres=preservacao();conferir_arquivos(RAIZ,pres)
    f={'utc':agora(),'configuracao':c,'fontes':fontes(),'qualificacao':q,'diario':diario,'mercado_minuto':minute,
       'preservacao':pres,'autorizacao':{'treinar':True,'origem':'Solicitação explícita neste chat: copiar CryptoMamba adaptado à Binance/futuros24h, executar e depois avaliar alterações.',
       'escopo':'3seeds +1controle;1000épocas cada;70carteiras;sem busca, sem ordens reais.'},
       'populacoes':{k:{'n':len(v['y']),'primeira_origem_ms':int(v['origens_ms'][0]),'ultima_origem_ms':int(v['origens_ms'][-1])} for k,v in d.items()},
       'auditoria_diario_minuto':{'max_abs_preco':float(np.max(abs(a[cols].to_numpy()-g[cols].to_numpy()))),'dias':len(g),
         'volumes_divergentes':len(observados),'escolha':'Arquivos mensais diários fixados são a fonte primária; sem substituir volumes seletivamente pela API/minutos.',
         'api_precos_iguais_2192_dias':True,'api_volumes_divergentes':len(api['divergencias'])}}
    codigo=identidade(f)[:20];p=RAIZ/'dados/experimentos'/f'cryptomamba_diario_{codigo}';p.mkdir(parents=True,exist_ok=False)
    for n in f['fontes']:
        dest=p/'fontes'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(RAIZ/n,dest)
    salvar_json(p/'congelamento.json',f)
    ptr={'id':codigo,'pasta':p.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(p/'congelamento.json')}
    salvar_json(REG/'execucao.json',ptr);salvar_json(REG/'autorizacao.json',{'execucao':ptr,**f['autorizacao']})
    salvar_json(REG/'estado.json',{'utc':agora(),'situacao':'preparado_autorizado','execucao':ptr,'ajustes_previstos':4,'principais':3,'carteiras_previstas':70})
    print(ptr,flush=True)


def conferir_preservacao():
    ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta'];assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    f=ler_json(p/'congelamento.json');conferir_arquivos(RAIZ,f['preservacao']);conferir_arquivos(RAIZ,f['fontes']);conferir_arquivos(p/'fontes',f['fontes'])
    for k in ('diario','mercado_minuto'):
        r=f[k];base=RAIZ/r['pasta'];assert sha256(base/'manifesto.json')==r['manifesto_sha256']
        conferir_arquivos(base,ler_json(base/'manifesto.json')['arquivos'])
    print('INTEGRIDADE_APROVADA',len(f['preservacao']),len(f['fontes']),flush=True)


def integridade_rapida():
    # Hashing nativo Windows evita custo de milhares de acessos pequenos em /mnt/c.
    nativo=RAIZ/'.venv/Scripts/python.exe'
    if os.name=='posix' and nativo.exists():
        r=subprocess.run([str(nativo),'-B','-X','utf8','-m','experimentos.cryptomamba_diario','conferir-preservacao'],cwd=RAIZ,capture_output=True,text=True)
        if r.returncode:raise RuntimeError(r.stdout+r.stderr)
        print(r.stdout,flush=True)
    else:conferir_preservacao()


def executar():
    import fcntl
    import torch
    from entradas_modelo.cryptomamba_diario import preparar as entradas
    from treinamento.cryptomamba_diario import ajustar
    from .avaliacao import executar as avaliar
    with (REG/'execucao.lock').open('a+b') as lock,(RAIZ/'registros/operacional_futuros/gpu.lock').open('a+b') as gpu:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gpu,fcntl.LOCK_EX|fcntl.LOCK_NB)
        r=subprocess.run(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],capture_output=True,text=True,check=True)
        if r.stdout.strip():raise RuntimeError('GPU ocupada.')
        ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta']
        if (p/'inicio.json').exists():raise RuntimeError('Execução já iniciada; não retomar/repetir automaticamente.')
        f=ler_json(p/'congelamento.json');c=f['configuracao'];auth=ler_json(REG/'autorizacao.json')
        assert auth['execucao']==ptr and auth['treinar']
        integridade_rapida()
        d=entradas(pd.read_parquet(RAIZ/f['diario']['pasta']/'diario.parquet'),c)
        proc={'pid':os.getpid(),'host':socket.gethostname(),'boot':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'utc':agora(),'ativo':True}
        salvar_json(p/'inicio.json',proc);salvar_json(p/'processo.json',proc);jobs=[]
        def estado(situacao,**extras):
            v={'utc':agora(),'situacao':situacao,'execucao':ptr,'ajustes_previstos':4,'ajustes_concluidos':len([x for x in jobs if x['situacao']=='concluido']),
               'carteiras_previstas':70,'processo':proc,**extras}
            salvar_json(p/'progresso.json',v);salvar_json(REG/'estado.json',v);print(v,flush=True)
        try:
            ordem=[('seed_42',42,False),('controle_42',42,True),('seed_17',17,False),('seed_2026',2026,False)]
            for nome,seed,controle in ordem:
                conferir_arquivos(RAIZ,f['fontes'])
                j={'id':nome,'seed':seed,'controle':controle,'situacao':'iniciado'};jobs.append(j);salvar_json(p/'ajustes.json',jobs);estado('treinando',job_atual=nome)
                ajustar(d,c,seed,p/'ajustes'/nome,{'execucao':ptr['id'],'job':nome})
                j['situacao']='concluido';salvar_json(p/'ajustes.json',jobs)
                if controle:
                    a=np.load(p/'ajustes/seed_42/validacao.npz')['previsoes'];b=np.load(p/'ajustes/controle_42/validacao.npz')['previsoes']
                    np.testing.assert_allclose(a,b,rtol=1e-5,atol=.01)
                    assert ler_json(p/'ajustes/seed_42/selecao.json')['epoca']==ler_json(p/'ajustes/controle_42/selecao.json')['epoca']
                    salvar_json(p/'controle.json',{'aprovado':True,'max_abs_usdt':float(abs(a-b).max()),'utc':agora(),'fora_das_medias':True})
            estado('avaliando');avaliar(p,c,d,f['mercado_minuto']);integridade_rapida()
            salvar_json(p/'preservacao_depois.json',{'utc':agora(),'aprovado':True,'arquivos_anteriores':len(f['preservacao'])})
            proc.update(ativo=False,encerramento_utc=agora());salvar_json(p/'processo.json',proc)
            salvar_json(p/'fechamento.json',{'utc':agora(),'situacao':'concluido_conferido','principais':3,'controles':1,'carteiras':70,
              'arquivos':{a.relative_to(p).as_posix():sha256(a) for a in p.rglob('*') if a.is_file() and a.name not in ('progresso.json','processo.json','fechamento.json')}})
            salvar_json(REG/'fechamento.json',{'arquivo':(p/'fechamento.json').relative_to(RAIZ).as_posix(),'sha256':sha256(p/'fechamento.json')})
            estado('concluido_conferido',carteiras_concluidas=70,publicacao=(p/'publicacao').relative_to(RAIZ).as_posix())
        except BaseException:
            proc.update(ativo=False,encerramento_utc=agora());salvar_json(p/'processo.json',proc)
            salvar_json(p/'incidente.json',{'utc':agora(),'erro':traceback.format_exc()});estado('interrompido');raise
