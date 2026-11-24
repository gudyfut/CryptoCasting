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

REG=RAIZ/'registros/alvo_retorno_diario'
CFG=RAIZ/'configuracoes/alvo_retorno_diario_001.json'


def anterior():
    ptr=ler_json(RAIZ/'registros/cryptomamba_reproducivel/execucao.json')
    assert ptr['id']=='ac8183e1ecfb91102b48'
    p=RAIZ/ptr['pasta'];assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    proc=ler_json(p/'processo.json');assert proc['ativo'] is False
    if os.name=='posix' and Path(f"/proc/{proc['pid']}/cmdline").exists():
        comando=Path(f"/proc/{proc['pid']}/cmdline").read_bytes()
        if b'cryptomamba_reproducivel' in comando:raise RuntimeError('Processo anterior ainda vivo.')
    return ptr,p,ler_json(p/'congelamento.json')


def fontes():
    _,_,f=anterior();r=dict(f['fontes'])
    for pacote in ('codigo/experimentos/alvo_retorno_diario','testes/alvo_retorno_diario'):
        for p in (RAIZ/pacote).rglob('*.py'):r[p.relative_to(RAIZ).as_posix()]=sha256(p)
    for n in ('configuracoes/alvo_retorno_diario_001.json','docs/protocolo_alvo_retorno_diario.md',
              'docs/adr/0033-alvo-retorno-diario.md'):
        r[n]=sha256(RAIZ/n)
    return r


def preparar():
    from .entradas import preparar as entradas
    if (REG/'execucao.json').exists():raise RuntimeError('Identidade já preparada; não substituir.')
    ptr_ant,p_ant,f_ant=anterior();c=ler_json(CFG);q=ler_json(REG/'qualificacao.json')
    assert sha256(RAIZ/q['arquivo'])==q['sha256']
    conferir_arquivos(RAIZ,q['fontes'])
    assert q['testes_adicionais_aprovados'] is True
    qual=ler_json(RAIZ/q['arquivo']);assert qual['situacao']=='aprovado'
    from .contratos import conferir_configuracao
    conferir_configuracao(c,f_ant['configuracao'])
    fecho=ler_json(RAIZ/'registros/cryptomamba_reproducivel/fechamento.json')
    assert sha256(RAIZ/fecho['arquivo'])==fecho['sha256']
    conferir_arquivos(p_ant,ler_json(p_ant/'fechamento.json')['arquivos'])
    conferir_arquivos(RAIZ,f_ant['fontes']);conferir_arquivos(p_ant/'fontes',f_ant['fontes'])
    pres=dict(f_ant['preservacao']);pres.update(f_ant['fontes'])
    for a in p_ant.rglob('*'):
        if a.is_file():pres[a.relative_to(RAIZ).as_posix()]=sha256(a)
    for n in ('estado.json','execucao.json','autorizacao.json'):
        a=RAIZ/'registros/cryptomamba_reproducivel'/n;pres[a.relative_to(RAIZ).as_posix()]=sha256(a)
    conferir_arquivos(RAIZ,pres)
    for nome in ('diario','mercado_minuto'):
        r=f_ant[nome];base=RAIZ/r['pasta'];assert sha256(base/'manifesto.json')==r['manifesto_sha256']
        conferir_arquivos(base,ler_json(base/'manifesto.json')['arquivos'])
    diario=pd.read_parquet(RAIZ/f_ant['diario']['pasta']/'diario.parquet')
    dados=entradas(diario,c)
    from entradas_modelo.cryptomamba_diario import preparar as entradas_preco
    referencia=entradas_preco(diario,f_ant['configuracao'])
    for fase,z in dados.items():
        for campo in ('x','origens_ms','fim_alvo_ms','ultimo_close'):
            np.testing.assert_array_equal(z[campo],referencia[fase][campo])
        np.testing.assert_array_equal(z['preco_alvo'],referencia[fase]['y'])
        np.testing.assert_array_equal(z['y'],referencia[fase]['y']/referencia[fase]['ultimo_close']-1)
    populacoes={k:{'n':len(v['y']),'primeira_origem_ms':int(v['origens_ms'][0]),'ultima_origem_ms':int(v['origens_ms'][-1])} for k,v in dados.items()}
    assert populacoes==f_ant['populacoes']
    f={'utc':agora(),'configuracao':c,'fontes':fontes(),'qualificacao':q,'ambiente':qual['ambiente'],
       'diario':f_ant['diario'],'mercado_minuto':f_ant['mercado_minuto'],'preservacao':pres,
       'antecessora':ptr_ant,'reaproveitamento':'Dados, baselines e resultados de preço herdados por hash; novos pesos apenas para o alvo de retorno.',
       'populacoes':populacoes,'contratos_reais':{'entradas_e_populacoes_identicas':True,'retorno_recalculado':True},'autorizacao':{'treinar':True,
       'origem':'Pesquisador autorizou em06/11/2026 testar retorno diário em lugar de preço, manter o restante igual, organizar e iniciar treinos/testes.',
       'escopo':'Ablação do alvo:3seeds+controle42;1000épocas cada;70carteiras;receita restante idêntica;sem busca e sem ordens reais.'}}
    codigo=identidade(f)[:20];p=RAIZ/'dados/experimentos'/f'alvo_retorno_diario_{codigo}';p.mkdir(parents=True,exist_ok=False)
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
        r=subprocess.run([str(nativo),'-B','-X','utf8','-m','experimentos.alvo_retorno_diario','conferir-preservacao'],cwd=RAIZ,capture_output=True,text=True)
        if r.returncode:raise RuntimeError(r.stdout+r.stderr)
        print(r.stdout,flush=True)
    else:conferir_preservacao()


def executar():
    import fcntl
    import torch
    from .entradas import preparar as entradas
    from .treinamento import ajustar
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
        from experimentos.cryptomamba_reproducivel.qualificacao import ambiente
        assert ambiente()==f['ambiente'], 'Ambiente alterado após qualificação.'
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
                    np.testing.assert_array_equal(a,b)
                    from .entradas import preco_equivalente
                    u=d['validacao']['ultimo_close'];np.testing.assert_allclose(preco_equivalente(a,u),preco_equivalente(b,u),rtol=1e-5,atol=.01)
                    assert ler_json(p/'ajustes/seed_42/selecao.json')['epoca']==ler_json(p/'ajustes/controle_42/selecao.json')['epoca']
                    salvar_json(p/'controle.json',{'aprovado':True,'max_abs_retorno':float(abs(a-b).max()),'max_abs_usdt':float(abs(preco_equivalente(a,u)-preco_equivalente(b,u)).max()),'utc':agora(),'fora_das_medias':True})
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
