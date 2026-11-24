"""Identidade, herança, locks e execução da ablação dos ramos Mamba."""
import io
import os
import shutil
import socket
import subprocess
import sys
import traceback
from pathlib import Path
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, identidade, conferir_arquivos

REG=RAIZ/'registros/ablacao_linear_diaria'
CFG=RAIZ/'configuracoes/ablacao_linear_diaria_001.json'


def fontes():
    pacotes=['infraestrutura','entradas_modelo','modelos','treinamento','avaliacao',
             'simulacao_operacoes','qualificacao','estudo_ohlcv','experimento_cryptomamba',
             'experimentos/ablacao_linear_diaria','experimentos/penalizacao_seletiva_diaria','experimentos/eixo_temporal_diario','experimentos/sem_penalizacao_diaria',
             'experimentos/alvo_retorno_diario','experimentos/cryptomamba_reproducivel',
             'experimentos/taxa_diaria','experimentos/generalizacao_moedas']
    arquivos=[p for nome in pacotes for p in (RAIZ/'codigo'/nome).rglob('*.py')]
    arquivos+=list((RAIZ/'testes/ablacao_linear_diaria').glob('*.py'))
    arquivos+=list((RAIZ/'testes/eixo_temporal_diario').glob('*.py'))
    for suite in ('penalizacao_seletiva_diaria','padronizacao_diaria','alvo_retorno_diario'):
        arquivos+=list((RAIZ/'testes'/suite).glob('*.py'))
    arquivos+=[RAIZ/'testes/simulacao_operacoes/test_continuidade_diaria.py']
    arquivos+=[RAIZ/'testes/simulacao_operacoes/test_auditoria_grade_continuidade.py',CFG,
               RAIZ/'docs/protocolo_ablacao_linear_diaria.md',
               RAIZ/'codigo/experimentos/ablacao_linear_diaria/iniciar.ps1']
    return {p.relative_to(RAIZ).as_posix():sha256(p) for p in sorted(set(arquivos))}


def preparar():
    import hashlib
    from entradas_modelo.padronizacao_diaria import preparar_com_escalas
    if (REG/'execucao.json').exists():raise RuntimeError('Identidade já preparada; sem sobrescrita.')
    q=ler_json(REG/'qualificacao.json')
    assert sha256(RAIZ/q['arquivo'])==q['sha256'];conferir_arquivos(RAIZ,q['fontes'])
    qual=ler_json(RAIZ/q['arquivo']);assert qual['situacao']=='aprovado'
    assert sha256(RAIZ/qual['referencias_arquivo'])==qual['referencias_sha256']
    heranca=ler_json(RAIZ/qual['referencias_arquivo']);conferir_arquivos(RAIZ,heranca['preservacao'])
    c=ler_json(CFG);auth=ler_json(REG/'autorizacao.json');assert auth['treinar']
    diario=heranca['referencias']['A']['diario'];mercado=heranca['referencias']['A']['mercado_minuto']
    d,escalas=preparar_com_escalas(pd.read_parquet(RAIZ/diario['pasta']/'diario.parquet'),c)
    assert escalas==qual['escalas'] and {k:len(v['y']) for k,v in d.items()}==qual['populacoes']
    for fase,z in d.items():
        with np.load(RAIZ/heranca['dados_preparados'][fase],allow_pickle=False) as original:
            assert set(z)==set(original.files)
            for k in z:np.testing.assert_array_equal(z[k],original[k])
    preparados={}
    for fase,z in d.items():
        memoria=io.BytesIO();np.savez_compressed(memoria,**z);preparados[fase]=memoria.getvalue()
    f={'utc':agora(),'configuracao':c,'fontes':fontes(),'qualificacao':q,'ambiente':qual['ambiente'],
       'autorizacao':auth,'referencias':heranca['referencias'],'preservacao':heranca['preservacao'],
       'continuidade':heranca['continuidade'],'diario':diario,'mercado_minuto':mercado,
       'escalas':escalas,'populacoes':qual['populacoes'],
       'dados_preparados':{f'dados/{k}.npz':hashlib.sha256(v).hexdigest() for k,v in preparados.items()},
       'heranca':['A'],'ajustes_novos':3,'controles_novos':2,'epocas_novas_previstas':1000,
       'limites':'Ablação retrospectiva BTC: remoção dos ramos antes de treinar; projeções iniciais pareadas. A prefixo200 herdada; sem2026.'}
    codigo=identidade(f)[:20];p=RAIZ/'dados/experimentos'/f'ablacao_linear_diaria_{codigo}'
    p.mkdir(parents=True,exist_ok=False);(p/'dados').mkdir()
    for k,v in preparados.items():(p/'dados'/f'{k}.npz').write_bytes(v)
    for nome in f['fontes']:
        dest=p/'fontes'/nome;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(RAIZ/nome,dest)
    salvar_json(p/'escalas.json',escalas);salvar_json(p/'heranca.json',heranca)
    salvar_json(p/'congelamento.json',f)
    modelos={}
    for variante in ('A',):
        for seed in c['seeds']:
            prova=heranca['referencias'][variante]['provas'][str(seed)]
            modelos[f'{variante}_{seed}']={'pasta':prova['pasta'],'herdado':True,'epoca':prova['epoca'],
                                          'checkpoint_sha256':prova['checkpoint']['sha256'],'limite_selecao':200}
    salvar_json(p/'modelos.json',modelos)
    ptr={'id':codigo,'pasta':p.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(p/'congelamento.json')}
    salvar_json(REG/'execucao.json',ptr)
    salvar_json(REG/'estado.json',{'utc':agora(),'situacao':'preparado_autorizado','execucao':ptr,
        'principais_herdados':3,'ajustes_novos_previstos':5,'ajustes_novos_concluidos':0,'carteiras_previstas':60})
    print('PREPARADO',ptr,flush=True)


def conferir():
    ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    f=ler_json(p/'congelamento.json')
    assert ler_json(p/'escalas.json')==f['escalas']
    conferir_arquivos(RAIZ,f['fontes']);conferir_arquivos(p/'fontes',f['fontes'])
    conferir_arquivos(RAIZ,f['preservacao']);conferir_arquivos(p,f['dados_preparados'])
    for chave in ('diario','mercado_minuto'):
        r=f[chave];base=RAIZ/r['pasta']
        assert sha256(base/'manifesto.json')==r['manifesto_sha256']
        conferir_arquivos(base,ler_json(base/'manifesto.json')['arquivos'])
    print('INTEGRIDADE_APROVADA',len(f['preservacao']),len(f['fontes']),flush=True)


def integridade():
    nativo=RAIZ/'.venv/Scripts/python.exe'
    if os.name=='posix' and nativo.exists():
        r=subprocess.run([str(nativo),'-B','-m','experimentos.ablacao_linear_diaria','conferir'],cwd=RAIZ,capture_output=True,text=True)
        assert r.returncode==0,r.stdout+r.stderr
        print(r.stdout,flush=True)
    else:conferir()


def executar():
    import fcntl
    from treinamento.otimizacao import fixar_seed
    from experimentos.cryptomamba_reproducivel.qualificacao import ambiente
    from experimentos.taxa_diaria.qualificacao import iguais
    from .qualificacao import conferir_controle_A
    from .contratos import organizar,receita
    from .treinamento import ajustar
    from .avaliacao import executar as avaliar
    with (REG/'execucao.lock').open('a+b') as lock,(RAIZ/'registros/operacional_futuros/gpu.lock').open('a+b') as gpu:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gpu,fcntl.LOCK_EX|fcntl.LOCK_NB)
        ocupado=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True)
        if ocupado.strip():raise RuntimeError('GPU ocupada.')
        ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta']
        if (p/'inicio.json').exists():raise RuntimeError('Já iniciada; retomada requer diagnóstico e identidade preservada.')
        integridade();f=ler_json(p/'congelamento.json');c=f['configuracao']
        fixar_seed(42);assert ambiente()==f['ambiente']
        proc={'pid':os.getpid(),'host':socket.gethostname(),'boot':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
              'inicio_processo_ticks':Path('/proc/self/stat').read_text().split()[21],'utc':agora(),'ativo':True}
        salvar_json(p/'inicio.json',proc);salvar_json(p/'processo.json',proc)
        trabalhos=[];controles={};modelos=ler_json(p/'modelos.json')
        def estado(situacao,**extras):
            v={'utc':agora(),'situacao':situacao,'execucao':ptr,'principais_herdados':3,'ajustes_novos_previstos':5,
               'ajustes_novos_concluidos':sum(j['situacao']=='concluido' for j in trabalhos),
               'epocas_novas_previstas':1000,'carteiras_previstas':60,'controles':controles,'processo':proc,**extras}
            salvar_json(p/'progresso.json',v);salvar_json(REG/'estado.json',v);print('ESTADO',v,flush=True)
        try:
            dados={fase:dict(np.load(p/'dados'/f'{fase}.npz',allow_pickle=False)) for fase in ('treino','validacao')}
            ordem=[('A',42,True),('L',42,False),('L',42,True),('L',17,False),('L',2026,False)]
            for variante,seed,controle in ordem:
                if variante=='L':assert controles.get('A') is True
                if seed!=42:assert controles=={'A':True,'L':True}
                conferir_arquivos(RAIZ,f['fontes'])
                nome=f'{variante}_'+('controle_' if controle else '')+str(seed)
                cfg=receita(c,variante);adaptado=organizar(dados,cfg['eixo'])
                j={'id':nome,'variante':variante,'seed':seed,'controle':controle,'situacao':'iniciado'}
                trabalhos.append(j);salvar_json(p/'ajustes.json',trabalhos);estado('treinando',ajuste_atual=nome)
                ajustar(adaptado,cfg,seed,p/'ajustes'/nome,{'execucao':ptr['id'],'job':nome,
                    'variante':variante,'eixo':cfg['eixo'],'escalas_sha256':sha256(p/'escalas.json')})
                j['situacao']='concluido';salvar_json(p/'ajustes.json',trabalhos)
                if controle:
                    if variante=='A':conferir_controle_A(p/'ajustes'/nome,RAIZ/f['referencias']['A']['provas']['42']['pasta'])
                    else:iguais(p/'ajustes'/f'{variante}_42',p/'ajustes'/nome)
                    controles[variante]=True
                    salvar_json(p/'controles.json',{'utc':agora(),'aprovados':controles,
                        'historico_pesos_previsoes_exatos':True,'epocas_por_controle':200,'fora_das_medias':True})
                else:
                    sel=ler_json(p/'ajustes'/nome/'selecao.json')
                    modelos[nome]={'pasta':(p/'ajustes'/nome).relative_to(RAIZ).as_posix(),'herdado':False,
                                   'epoca':sel['epoca'],'checkpoint_sha256':sel['sha256'],'limite_selecao':200}
                    salvar_json(p/'modelos.json',modelos)
            assert len(modelos)==6 and controles=={'A':True,'L':True}
            estado('avaliando');dados['teste']=dict(np.load(p/'dados/teste.npz',allow_pickle=False))
            resultados=avaliar(p,c,dados,f,estado);integridade()
            salvar_json(p/'preservacao_depois.json',{'utc':agora(),'aprovado':True,'arquivos':len(f['preservacao'])})
            proc.update(ativo=False,encerramento_utc=agora());salvar_json(p/'processo.json',proc)
            situacao='concluido_conferido' if not resultados['falhas_prudenciais'] else 'concluido_com_falhas_operacionais'
            salvar_json(p/'fechamento.json',{'utc':agora(),'situacao':situacao,'principais_novos':3,'principais_herdados':3,
                'controles_novos':2,**resultados,'arquivos':{a.relative_to(p).as_posix():sha256(a) for a in p.rglob('*') if a.is_file() and a.name not in ('fechamento.json','progresso.json','processo.json')}})
            salvar_json(REG/'fechamento.json',{'arquivo':(p/'fechamento.json').relative_to(RAIZ).as_posix(),'sha256':sha256(p/'fechamento.json')})
            estado(situacao,**resultados)
        except BaseException:
            proc.update(ativo=False,encerramento_utc=agora());salvar_json(p/'processo.json',proc)
            salvar_json(p/'incidente.json',{'utc':agora(),'erro':traceback.format_exc()});estado('interrompido_preservado');raise
