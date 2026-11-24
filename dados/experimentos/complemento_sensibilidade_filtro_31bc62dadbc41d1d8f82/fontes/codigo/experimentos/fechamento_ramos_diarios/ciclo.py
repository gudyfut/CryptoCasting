"""Congelamento e sequência finita, com unidades segregadas por símbolo."""
import hashlib
import io
import os
import shutil
import socket
import subprocess
import traceback
from pathlib import Path
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, identidade, conferir_arquivos
from entradas_modelo.padronizacao_diaria import preparar_com_escalas
from .contratos import CFG, REG, FASES, configuracao_moeda, receita, ordem_trabalhos


def fontes():
    from experimentos.ablacao_linear_diaria.ciclo import fontes as fontes_anteriores
    f = fontes_anteriores()
    for prefixo in ('codigo/experimentos/fechamento_ramos_diarios', 'testes/fechamento_ramos_diarios'):
        for p in (RAIZ/prefixo).glob('*.py'): f[p.relative_to(RAIZ).as_posix()] = sha256(p)
    for nome in ('configuracoes/fechamento_ramos_diarios_001.json',
                 'docs/protocolo_fechamento_ramos_diarios.md',
                 'codigo/experimentos/fechamento_ramos_diarios/iniciar.ps1'):
        f[nome] = sha256(RAIZ/nome)
    return f


def preparar():
    assert not (REG/'execucao.json').exists(), 'Não sobrescrever identidade.'
    q = ler_json(REG/'qualificacao.json')
    assert sha256(RAIZ/q['arquivo']) == q['sha256']
    conferir_arquivos(RAIZ,q['fontes']); assert q['fontes'] == fontes()
    qual = ler_json(RAIZ/q['arquivo']); assert qual['situacao'] == 'aprovado'
    assert sha256(RAIZ/qual['referencias_arquivo']) == qual['referencias_sha256']
    refs = ler_json(RAIZ/qual['referencias_arquivo'])
    conferir_arquivos(RAIZ,refs['preservacao'])
    c = ler_json(CFG); auth = ler_json(REG/'autorizacao.json')
    assert auth['treinar'] and auth['max_ajustes_cientificos'] == 12
    preparados = {}
    for simbolo,info in refs['moedas'].items():
        cfg = configuracao_moeda(c,simbolo)
        dados,escalas = preparar_com_escalas(pd.read_parquet(RAIZ/info['diario']['pasta']/'diario.parquet'),cfg)
        assert escalas == info['escalas']
        assert {fase:len(z['y']) for fase,z in dados.items()} == qual['populacoes'][simbolo]
        for fase,z in dados.items():
            memoria=io.BytesIO();np.savez_compressed(memoria,**z)
            preparados[f'{simbolo}/dados/{fase}.npz'] = memoria.getvalue()
    f = dict(utc=agora(),configuracao=c,fontes=fontes(),qualificacao=q,ambiente=qual['ambiente'],
        autorizacao=auth,referencias=refs,ajustes=ordem_trabalhos(c),
        dados_preparados={k:hashlib.sha256(v).hexdigest() for k,v in preparados.items()},
        limite='BTC fatorial e A/L por ativo definidos antes dos ajustes; sem2026; conclusão pode ser negativa.')
    codigo=identidade(f)[:20];p=RAIZ/'dados/experimentos'/f'fechamento_ramos_diarios_{codigo}'
    p.mkdir(parents=True,exist_ok=False)
    for nome,b in preparados.items():
        destino=p/nome;destino.parent.mkdir(parents=True,exist_ok=True);destino.write_bytes(b)
    for nome in f['fontes']:
        destino=p/'fontes'/nome;destino.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(RAIZ/nome,destino)
    for simbolo,info in refs['moedas'].items():
        salvar_json(p/simbolo/'escalas.json',info['escalas'])
        salvar_json(p/simbolo/'configuracao.json',configuracao_moeda(c,simbolo))
        salvar_json(p/simbolo/'modelos.json',{k:dict(v,herdado=True) for k,v in info['modelos'].items()})
    salvar_json(p/'congelamento.json',f)
    ptr=dict(id=codigo,pasta=p.relative_to(RAIZ).as_posix(),congelamento_sha256=sha256(p/'congelamento.json'))
    salvar_json(REG/'execucao.json',ptr)
    salvar_json(REG/'estado.json',dict(utc=agora(),situacao='preparado_autorizado',execucao=ptr,
        ajustes_cientificos_previstos=12,controles_previstos=8,epocas_novas_previstas=4000,carteiras_previstas=288))
    print('PREPARADO',ptr,flush=True)


def conferir():
    ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    f=ler_json(p/'congelamento.json')
    conferir_arquivos(RAIZ,f['fontes']);conferir_arquivos(p/'fontes',f['fontes'])
    conferir_arquivos(RAIZ,f['referencias']['preservacao']);conferir_arquivos(p,f['dados_preparados'])
    for simbolo,info in f['referencias']['moedas'].items():
        assert ler_json(p/simbolo/'escalas.json') == info['escalas']
        assert ler_json(p/simbolo/'configuracao.json') == configuracao_moeda(f['configuracao'],simbolo)
        for ref in (info['diario'],info['mercado_minuto']):
            base=RAIZ/ref['pasta'];assert sha256(base/'manifesto.json')==ref['manifesto_sha256']
            conferir_arquivos(base,ler_json(base/'manifesto.json')['arquivos'])
    print('INTEGRIDADE_APROVADA',len(f['referencias']['preservacao']),len(f['fontes']),flush=True)


def integridade():
    nativo=RAIZ/'.venv/Scripts/python.exe'
    if os.name=='posix' and nativo.exists():
        r=subprocess.run([str(nativo),'-B','-m','experimentos.fechamento_ramos_diarios','conferir'],cwd=RAIZ,capture_output=True,text=True)
        assert r.returncode==0,r.stdout+r.stderr
        print(r.stdout,flush=True)
    else:conferir()


def executar():
    import fcntl
    from treinamento.otimizacao import fixar_seed
    from experimentos.cryptomamba_reproducivel.qualificacao import ambiente
    from experimentos.taxa_diaria.qualificacao import iguais
    from .qualificacao import conferir_reproducao
    from .treinamento import ajustar
    from .avaliacao import executar as avaliar
    with (REG/'execucao.lock').open('a+b') as lock,(RAIZ/'registros/operacional_futuros/gpu.lock').open('a+b') as gpu:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gpu,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip(),'GPU ocupada.'
        ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta']
        assert not (p/'inicio.json').exists(),'Já iniciada; investigar antes de retomar.'
        integridade();f=ler_json(p/'congelamento.json');c=f['configuracao']
        fixar_seed(42);assert ambiente()==f['ambiente']
        proc=dict(pid=os.getpid(),host=socket.gethostname(),boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            inicio_processo_ticks=Path('/proc/self/stat').read_text().split()[21],utc=agora(),ativo=True)
        salvar_json(p/'inicio.json',proc);salvar_json(p/'processo.json',proc)
        trabalhos=[];controles={};avaliacoes={}
        def estado(situacao,**extras):
            r=dict(utc=agora(),situacao=situacao,execucao=ptr,processo=proc,controles=controles,
                ajustes_novos_previstos=20,ajustes_novos_concluidos=sum(j['situacao']=='concluido' for j in trabalhos),
                ajustes_cientificos_previstos=12,controles_previstos=8,epocas_novas_previstas=4000,
                carteiras_previstas=288,avaliacoes=avaliacoes,**extras)
            salvar_json(p/'progresso.json',r);salvar_json(REG/'estado.json',r)
            print('ESTADO',situacao,extras,flush=True)
        try:
            for simbolo in c['moedas']:
                base=p/simbolo;cfg=configuracao_moeda(c,simbolo)
                dados={fase:dict(np.load(base/'dados'/f'{fase}.npz',allow_pickle=False)) for fase in ('treino','validacao')}
                modelos=ler_json(base/'modelos.json');controles[simbolo]={}
                referencia,nova=('B','L0') if simbolo=='BTCUSDT' else ('A','L')
                for trabalho in [j for j in f['ajustes'] if j['simbolo']==simbolo]:
                    v,seed,controle,nome=(trabalho[k] for k in ('variante','seed','controle','id'))
                    if v==nova:assert controles[simbolo].get(referencia) is True
                    if seed!=42:assert controles[simbolo]=={referencia:True,nova:True}
                    conferir_arquivos(RAIZ,f['fontes'])
                    j=dict(trabalho,situacao='iniciado');trabalhos.append(j)
                    salvar_json(p/'ajustes.json',trabalhos);estado('treinando',simbolo=simbolo,ajuste_atual=nome)
                    destino=base/'ajustes'/nome
                    ajustar(dados,receita(cfg,v),seed,destino,dict(execucao=ptr['id'],simbolo=simbolo,job=nome,
                        variante=v,eixo='canais',escalas_sha256=sha256(base/'escalas.json')))
                    if controle:
                        if v==referencia:conferir_reproducao(destino,RAIZ/modelos[f'{v}_{seed}']['pasta'])
                        else:iguais(base/'ajustes'/f'{v}_{seed}',destino)
                        controles[simbolo][v]=True;salvar_json(p/'controles.json',controles)
                    else:
                        s=ler_json(destino/'selecao.json')
                        modelos[f'{v}_{seed}']=dict(pasta=destino.relative_to(RAIZ).as_posix(),herdado=False,
                            epoca=s['epoca'],checkpoint=s)
                        salvar_json(base/'modelos.json',modelos)
                    j['situacao']='concluido';salvar_json(p/'ajustes.json',trabalhos)
                assert controles[simbolo]=={referencia:True,nova:True}
                dados['teste']=dict(np.load(base/'dados/teste.npz',allow_pickle=False))
                ff=dict(f['referencias']['moedas'][simbolo],continuidade=f['referencias']['continuidade'])
                estado('avaliando',simbolo=simbolo)
                avaliacoes[simbolo]=avaliar(base,cfg,dados,ff,lambda s,**kw:estado(s,simbolo=simbolo,**kw))
                salvar_json(base/'fechamento.json',dict(utc=agora(),situacao='concluido_conferido',
                    **avaliacoes[simbolo],arquivos={q.relative_to(base).as_posix():sha256(q) for q in base.rglob('*') if q.is_file()}))
            assert len(trabalhos)==20 and all(j['situacao']=='concluido' for j in trabalhos)
            assert sum(v['carteiras_concluidas']+v['falhas_prudenciais'] for v in avaliacoes.values())==288
            integridade();salvar_json(p/'preservacao_depois.json',dict(utc=agora(),aprovado=True,arquivos=len(f['referencias']['preservacao'])))
            proc.update(ativo=False,encerramento_utc=agora());salvar_json(p/'processo.json',proc)
            situacao='concluido_conferido' if not any(v['falhas_prudenciais'] for v in avaliacoes.values()) else 'concluido_com_falhas_operacionais'
            salvar_json(p/'fechamento.json',dict(utc=agora(),situacao=situacao,avaliacoes=avaliacoes,
                ajustes_cientificos=12,controles=8,herdados=18,
                arquivos={q.relative_to(p).as_posix():sha256(q) for q in p.rglob('*') if q.is_file() and q.name not in ('fechamento.json','progresso.json','processo.json')}))
            salvar_json(REG/'fechamento.json',dict(arquivo=(p/'fechamento.json').relative_to(RAIZ).as_posix(),sha256=sha256(p/'fechamento.json')))
            estado(situacao)
        except BaseException:
            proc.update(ativo=False,encerramento_utc=agora());salvar_json(p/'processo.json',proc)
            salvar_json(p/'incidente.json',dict(utc=agora(),erro=traceback.format_exc()))
            estado('interrompido_preservado');raise
