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

REG=RAIZ/'registros/sem_penalizacao_diaria'
CFG=RAIZ/'configuracoes/sem_penalizacao_diaria_001.json'


def anterior():
    ptr=ler_json(RAIZ/'registros/padronizacao_diaria/execucao.json')
    assert ptr['id']=='f3f8772670f244779ad7'
    p=RAIZ/ptr['pasta'];assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    proc=ler_json(p/'processo.json');assert proc['ativo'] is False
    if os.name=='posix' and Path(f"/proc/{proc['pid']}/cmdline").exists():
        comando=Path(f"/proc/{proc['pid']}/cmdline").read_bytes()
        if b'padronizacao_diaria' in comando:raise RuntimeError('Processo anterior ainda vivo.')
    return ptr,p,ler_json(p/'congelamento.json')


def fontes():
    _,_,f=anterior();r=dict(f['fontes'])
    for pacote in ('experimentos/sem_penalizacao_diaria','tests_sem_penalizacao_diaria'):
        for p in (RAIZ/pacote).rglob('*.py'):r[p.relative_to(RAIZ).as_posix()]=sha256(p)
    for n in ('configuracoes/sem_penalizacao_diaria_001.json','docs/protocolo_sem_penalizacao_diaria.md',
              'docs/adr/0035-sem-penalizacao-diaria.md','entradas_modelo/padronizacao_diaria.py','experimentos/sem_penalizacao_diaria/iniciar.ps1'):
        r[n]=sha256(RAIZ/n)
    return r


def preparar():
    from entradas_modelo.padronizacao_diaria import preparar_com_escalas
    if (REG/'execucao.json').exists():raise RuntimeError('Identidade já preparada; não substituir.')
    ptr_ant,p_ant,f_ant=anterior();c=ler_json(CFG);q=ler_json(REG/'qualificacao.json')
    assert sha256(RAIZ/q['arquivo'])==q['sha256']
    conferir_arquivos(RAIZ,q['fontes'])
    assert q['testes_adicionais_aprovados'] is True
    qual=ler_json(RAIZ/q['arquivo']);assert qual['situacao']=='aprovado'
    from .contratos import conferir_configuracao
    conferir_configuracao(c,f_ant['configuracao'])
    fecho=ler_json(RAIZ/'registros/padronizacao_diaria/fechamento.json')
    assert sha256(RAIZ/fecho['arquivo'])==fecho['sha256']
    conferir_arquivos(p_ant,ler_json(p_ant/'fechamento.json')['arquivos'])
    conferir_arquivos(RAIZ,f_ant['fontes']);conferir_arquivos(p_ant/'fontes',f_ant['fontes'])
    pres=dict(f_ant['preservacao']);pres.update(f_ant['fontes'])
    for a in p_ant.rglob('*'):
        if a.is_file():pres[a.relative_to(RAIZ).as_posix()]=sha256(a)
    for n in ('estado.json','execucao.json','autorizacao.json'):
        a=RAIZ/'registros/padronizacao_diaria'/n;pres[a.relative_to(RAIZ).as_posix()]=sha256(a)
    conferir_arquivos(RAIZ,pres)
    for nome in ('diario','mercado_minuto'):
        r=f_ant[nome];base=RAIZ/r['pasta'];assert sha256(base/'manifesto.json')==r['manifesto_sha256']
        conferir_arquivos(base,ler_json(base/'manifesto.json')['arquivos'])
    diario=pd.read_parquet(RAIZ/f_ant['diario']['pasta']/'diario.parquet')
    dados,escalas=preparar_com_escalas(diario,c)
    from entradas_modelo.padronizacao_diaria import preparar as entradas_referencia
    referencia=entradas_referencia(diario,f_ant['configuracao'])
    for fase,z in dados.items():
        for campo in ('y','preco_alvo','origens_ms','fim_alvo_ms','ultimo_close'):
            np.testing.assert_array_equal(z[campo],referencia[fase][campo])
        assert z['x'].shape==referencia[fase]['x'].shape and z['x'].dtype==np.float32
        assert np.isfinite(z['x']).all()
        np.testing.assert_array_equal(z['x'],referencia[fase]['x'])
    assert escalas==f_ant['escalas']
    assert escalas['ultimo_candle_ms']<dados['validacao']['origens_ms'][0]
    populacoes={k:{'n':len(v['y']),'primeira_origem_ms':int(v['origens_ms'][0]),'ultima_origem_ms':int(v['origens_ms'][-1])} for k,v in dados.items()}
    assert populacoes==f_ant['populacoes']
    f={'utc':agora(),'configuracao':c,'fontes':fontes(),'qualificacao':q,'ambiente':qual['ambiente'],
       'diario':f_ant['diario'],'mercado_minuto':f_ant['mercado_minuto'],'preservacao':pres,
       'antecessora':ptr_ant,'reaproveitamento':'Referência padronizada herdada por hash; única mudança científica é weight_decay 0.001 para 0.0.',
       'populacoes':populacoes,'escalas':escalas,'contratos_reais':{'dimensoes_populacoes_alvos_identicos':True,'entradas_escalas_exatas':True,'unica_mudanca_weight_decay_zero':True},'autorizacao':{'treinar':True,
       'origem':'Pesquisador autorizou em08/11/2026 testar weight_decay zero, manter todo o restante igual, mesmas três seeds e controle; organizar/documentar separadamente, conferir e iniciar treinamentos e testes.',
       'escopo':'Ablação de weight_decay do Adam:3seeds+controle42;1000épocas cada;70carteiras;sem busca, sem retreinar referência, sem ordens reais.'}}
    codigo=identidade(f)[:20];p=RAIZ/'dados/experimentos'/f'sem_penalizacao_diaria_{codigo}';p.mkdir(parents=True,exist_ok=False)
    for n in f['fontes']:
        dest=p/'fontes'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(RAIZ/n,dest)
    salvar_json(p/'escalas.json',escalas)
    salvar_json(p/'congelamento.json',f)
    ptr={'id':codigo,'pasta':p.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(p/'congelamento.json')}
    salvar_json(REG/'execucao.json',ptr);salvar_json(REG/'autorizacao.json',{'execucao':ptr,**f['autorizacao']})
    salvar_json(REG/'estado.json',{'utc':agora(),'situacao':'preparado_autorizado','execucao':ptr,'ajustes_previstos':4,'principais':3,'carteiras_previstas':70})
    print(ptr,flush=True)


def conferir_preservacao():
    ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta'];assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    f=ler_json(p/'congelamento.json');assert ler_json(p/'escalas.json')==f['escalas'];conferir_arquivos(RAIZ,f['preservacao']);conferir_arquivos(RAIZ,f['fontes']);conferir_arquivos(p/'fontes',f['fontes'])
    for k in ('diario','mercado_minuto'):
        r=f[k];base=RAIZ/r['pasta'];assert sha256(base/'manifesto.json')==r['manifesto_sha256']
        conferir_arquivos(base,ler_json(base/'manifesto.json')['arquivos'])
    print('INTEGRIDADE_APROVADA',len(f['preservacao']),len(f['fontes']),flush=True)


def integridade_rapida():
    # Hashing nativo Windows evita custo de milhares de acessos pequenos em /mnt/c.
    nativo=RAIZ/'.venv/Scripts/python.exe'
    if os.name=='posix' and nativo.exists():
        r=subprocess.run([str(nativo),'-B','-X','utf8','-m','experimentos.sem_penalizacao_diaria','conferir-preservacao'],cwd=RAIZ,capture_output=True,text=True)
        if r.returncode:raise RuntimeError(r.stdout+r.stderr)
        print(r.stdout,flush=True)
    else:conferir_preservacao()


def executar():
    import fcntl
    import torch
    from entradas_modelo.padronizacao_diaria import preparar_com_escalas
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
        d,escalas=preparar_com_escalas(pd.read_parquet(RAIZ/f['diario']['pasta']/'diario.parquet'),c)
        assert escalas==f['escalas']==ler_json(p/'escalas.json')
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
                ajustar(d,c,seed,p/'ajustes'/nome,{'execucao':ptr['id'],'job':nome,'escalas_sha256':sha256(p/'escalas.json')})
                j['situacao']='concluido';salvar_json(p/'ajustes.json',jobs)
                if controle:
                    a=np.load(p/'ajustes/seed_42/validacao.npz')['previsoes'];b=np.load(p/'ajustes/controle_42/validacao.npz')['previsoes']
                    np.testing.assert_array_equal(a,b)
                    from experimentos.alvo_retorno_diario.entradas import preco_equivalente
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
