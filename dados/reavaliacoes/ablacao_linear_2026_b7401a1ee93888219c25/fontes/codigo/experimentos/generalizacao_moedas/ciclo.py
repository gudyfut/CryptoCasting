"""Transferência da receita, sem transferir pesos, sem procurar novas configurações."""
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
from .contratos import SIMBOLOS, configurar, preparar as entradas, reconciliar_diario_minuto

REG = RAIZ/'registros/generalizacao_moedas'
CFG = RAIZ/'configuracoes/generalizacao_moedas_001.json'


def referencia():
    ptr = ler_json(RAIZ/'registros/padronizacao_diaria/execucao.json')
    assert ptr['id'] == 'f3f8772670f244779ad7'
    p = RAIZ/ptr['pasta']; assert sha256(p/'congelamento.json') == ptr['congelamento_sha256']
    assert not ler_json(p/'processo.json')['ativo']
    return ptr, p, ler_json(p/'congelamento.json')


def fontes():
    _, _, ref = referencia(); saida = dict(ref['fontes'])
    for pacote in ('codigo/experimentos/generalizacao_moedas','testes/generalizacao_moedas'):
        for p in (RAIZ/pacote).glob('*'):
            if p.suffix in ('.py','.ps1'): saida[p.relative_to(RAIZ).as_posix()] = sha256(p)
    for nome in ('codigo/mercado_futuros/multimoeda.py','codigo/mercado_futuros/historico_operacional.py','codigo/simulacao_operacoes/envelopes_marcacao.py',
                 'codigo/experimentos/sem_penalizacao_diaria/observacao.py',
                 'configuracoes/generalizacao_moedas_001.json','docs/protocolo_generalizacao_moedas.md',
                 'docs/adr/0036-generalizacao-tres-moedas.md'):
        saida[nome] = sha256(RAIZ/nome)
    return saida


def preparar():
    from mercado_futuros.multimoeda import conferir as conferir_mercado
    assert not (REG/'execucao.json').exists(), 'Não substituir identidade existente'
    ptr_ref, p_ref, ref = referencia(); receita = ler_json(CFG)
    assert receita['referencia'] == ptr_ref['id'] and receita['simbolos'] == list(SIMBOLOS)
    qual_ptr = ler_json(REG/'qualificacao.json')
    assert sha256(RAIZ/qual_ptr['arquivo']) == qual_ptr['sha256']
    qual = ler_json(RAIZ/qual_ptr['arquivo']); assert qual['situacao'] == 'aprovado'
    conferir_arquivos(RAIZ, qual_ptr['fontes'])
    ultimo = ler_json(RAIZ/'registros/sem_penalizacao_diaria/execucao.json')
    up = RAIZ/ultimo['pasta']; uf = ler_json(up/'congelamento.json')
    assert sha256(up/'congelamento.json') == ultimo['congelamento_sha256']
    assert ler_json(up/'fechamento.json')['situacao'] == 'concluido_conferido'
    pres = dict(uf['preservacao']); pres.update(uf['fontes'])
    for a in up.rglob('*'):
        if a.is_file(): pres[a.relative_to(RAIZ).as_posix()] = sha256(a)
    conferir_arquivos(RAIZ, pres)
    conferir_arquivos(p_ref, ler_json(p_ref/'fechamento.json')['arquivos'])
    moedas = {}
    for simbolo in SIMBOLOS:
        ptr = ler_json(REG/'dados'/simbolo/'execucao.json'); m = conferir_mercado(ptr)
        p = RAIZ/ptr['pasta']; c = configurar(ref['configuracao'], simbolo, m['contrato'])
        d, escalas = entradas(pd.read_parquet(p/'diario.parquet'), c)
        moedas[simbolo] = {'mercado':ptr, 'configuracao':c, 'escalas':escalas,
            'reconciliacao':reconciliar_diario_minuto(p),
            'populacoes':{k:{'n':len(z['y']), 'primeira_origem_ms':int(z['origens_ms'][0]),
                              'ultima_origem_ms':int(z['origens_ms'][-1])} for k,z in d.items()}}
    f = {'utc':agora(), 'receita':receita, 'referencia':ptr_ref, 'moedas':moedas, 'fontes':fontes(),
         'qualificacao':qual_ptr, 'ambiente':qual['ambiente'], 'preservacao':pres,
         'autorizacao':{'treinar':True, 'origem':'Pesquisador autorizou organizar, coletar, configurar e iniciar ETH, BNB e XRP; confirmou versão padronizada pelo menor erro em 09/11/2026.',
                       'escopo':'9 ajustes principais + 3 controles, 1000 épocas, 210 carteiras. Sem busca, sem retreino BTC, sem ordens reais.'}}
    codigo = identidade(f)[:20]; p = RAIZ/'dados/experimentos'/f'generalizacao_moedas_{codigo}'
    p.mkdir(parents=True, exist_ok=False)
    for nome in f['fontes']:
        dest = p/'fontes'/nome; dest.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(RAIZ/nome, dest)
    for simbolo, m in moedas.items(): salvar_json(p/simbolo/'escalas.json', m['escalas'])
    salvar_json(p/'congelamento.json', f)
    ptr = {'id':codigo, 'pasta':p.relative_to(RAIZ).as_posix(), 'congelamento_sha256':sha256(p/'congelamento.json')}
    salvar_json(REG/'execucao.json', ptr); salvar_json(REG/'autorizacao.json', {'execucao':ptr, **f['autorizacao']})
    salvar_json(REG/'estado.json', {'utc':agora(), 'situacao':'preparado_autorizado', 'execucao':ptr,
                                  'ajustes_previstos':12, 'ajustes_concluidos':0, 'carteiras_previstas':210})
    print('PREPARADO', ptr, flush=True)


def conferir():
    from mercado_futuros.multimoeda import conferir as conferir_mercado
    ptr = ler_json(REG/'execucao.json'); p = RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json') == ptr['congelamento_sha256']
    f = ler_json(p/'congelamento.json')
    conferir_arquivos(RAIZ, f['preservacao']); conferir_arquivos(RAIZ, f['fontes']); conferir_arquivos(p/'fontes', f['fontes'])
    for s, m in f['moedas'].items():
        conferir_mercado(m['mercado']); assert ler_json(p/s/'escalas.json') == m['escalas']
    print('INTEGRIDADE_APROVADA', len(f['preservacao']), len(f['fontes']), flush=True)


def integridade_nativa():
    if os.name == 'posix':
        comando = [str(RAIZ/'.venv/Scripts/python.exe'), '-B', '-X', 'utf8', '-m', 'experimentos.generalizacao_moedas', 'conferir']
        r = subprocess.run(comando, cwd=RAIZ, capture_output=True, text=True)
        if r.returncode: raise RuntimeError(r.stdout+r.stderr)
        print(r.stdout, flush=True)
    else: conferir()


def executar():
    import fcntl
    import torch
    from experimentos.alvo_retorno_diario.treinamento import ajustar
    from experimentos.padronizacao_diaria.qualificacao import ambiente
    from .avaliacao import executar as avaliar
    with (REG/'execucao.lock').open('a+b') as lock, (RAIZ/'registros/operacional_futuros/gpu.lock').open('a+b') as gpu:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB); fcntl.flock(gpu, fcntl.LOCK_EX|fcntl.LOCK_NB)
        ocupacao = subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'], text=True)
        assert not ocupacao.strip(), 'GPU ocupada'
        ptr = ler_json(REG/'execucao.json'); p = RAIZ/ptr['pasta']; f = ler_json(p/'congelamento.json')
        assert not (p/'inicio.json').exists(), 'Já iniciada: não retomar ou repetir automaticamente'
        auth = ler_json(REG/'autorizacao.json'); assert auth['execucao'] == ptr and auth['treinar']
        integridade_nativa(); assert ambiente() == f['ambiente'], 'Ambiente mudou após qualificação'
        proc = {'pid':os.getpid(), 'host':socket.gethostname(), 'boot':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                'utc':agora(), 'ativo':True}
        salvar_json(p/'inicio.json', proc); salvar_json(p/'processo.json', proc); jobs=[]; carteiras=0
        def estado(situacao, **extras):
            r = {'utc':agora(), 'situacao':situacao, 'execucao':ptr, 'ajustes_previstos':12,
                 'ajustes_concluidos':sum(j['situacao']=='concluido' for j in jobs), 'carteiras_previstas':210,
                 'carteiras_concluidas':carteiras, 'processo':proc, **extras}
            salvar_json(p/'progresso.json', r); salvar_json(REG/'estado.json', r); print(r, flush=True)
        try:
            for simbolo in SIMBOLOS:
                m=f['moedas'][simbolo]; c=m['configuracao']; base=p/simbolo
                d, escalas = entradas(pd.read_parquet(RAIZ/m['mercado']['pasta']/'diario.parquet'), c)
                assert escalas == m['escalas']
                for nome, seed, controle in [('seed_42',42,False),('controle_42',42,True),('seed_17',17,False),('seed_2026',2026,False)]:
                    conferir_arquivos(RAIZ, f['fontes'])
                    job={'simbolo':simbolo,'id':nome,'seed':seed,'controle':controle,'situacao':'iniciado'}
                    jobs.append(job); salvar_json(p/'ajustes.json',jobs); estado('treinando',simbolo=simbolo,job_atual=nome)
                    ajustar(d,c,seed,base/'ajustes'/nome,{'execucao':ptr['id'],'simbolo':simbolo,'job':nome,'escalas_sha256':sha256(base/'escalas.json')})
                    job['situacao']='concluido';salvar_json(p/'ajustes.json',jobs)
                    if controle:
                        a=np.load(base/'ajustes/seed_42/validacao.npz')['previsoes'];b=np.load(base/'ajustes/controle_42/validacao.npz')['previsoes']
                        np.testing.assert_array_equal(a,b)
                        assert ler_json(base/'ajustes/seed_42/selecao.json')['epoca']==ler_json(base/'ajustes/controle_42/selecao.json')['epoca']
                        salvar_json(base/'controle.json',{'utc':agora(),'aprovado':True,'max_abs_retorno':0.,'fora_das_medias':True})
                assert ler_json(base/'controle.json')['aprovado']
                from experimentos.alvo_retorno_diario.treinamento import carregar_rede
                from experimentos.sem_penalizacao_diaria.observacao import observar
                for seed in c['seeds']:
                    a=base/'ajustes'/f'seed_{seed}';rede=carregar_rede(a,c)
                    observar(rede,d['treino']['x'],base/'observacoes'/f'seed_{seed}.json',ler_json(a/'selecao.json')['epoca'])
                    del rede;torch.cuda.empty_cache()
                estado('avaliando',simbolo=simbolo); avaliar(base,c,d,m['mercado']);carteiras+=70
                salvar_json(base/'fechamento.json',{'utc':agora(),'situacao':'concluido_conferido','principais':3,'controles':1,'carteiras':70,
                    'arquivos':{a.relative_to(base).as_posix():sha256(a) for a in base.rglob('*') if a.is_file() and a.name not in ('progresso.json','fechamento.json')}})
                estado('moeda_concluida',simbolo=simbolo)
            integridade_nativa()
            salvar_json(p/'preservacao_depois.json',{'utc':agora(),'aprovado':True,'arquivos_anteriores':len(f['preservacao'])})
            salvar_json(p/'resumo.json',{'utc':agora(),'referencia_btc':f['referencia'], 'moedas':{s:ler_json(p/s/'publicacao/resumo.json') for s in SIMBOLOS},
                'limite':'Médias por moeda e ensemble separados; não somar carteiras. Receita escolhida retrospectivamente em BTC, não confirmação intocada.'})
            proc.update(ativo=False,encerramento_utc=agora());salvar_json(p/'processo.json',proc)
            salvar_json(p/'fechamento.json',{'utc':agora(),'situacao':'concluido_conferido','principais':9,'controles':3,'carteiras':210,
                'arquivos':{a.relative_to(p).as_posix():sha256(a) for a in p.rglob('*') if a.is_file() and a.name not in ('progresso.json','processo.json') and a != p/'fechamento.json'}})
            salvar_json(REG/'fechamento.json',{'arquivo':(p/'fechamento.json').relative_to(RAIZ).as_posix(),'sha256':sha256(p/'fechamento.json')})
            estado('concluido_conferido')
        except BaseException:
            proc.update(ativo=False,encerramento_utc=agora());salvar_json(p/'processo.json',proc)
            salvar_json(p/'incidente.json',{'utc':agora(),'erro':traceback.format_exc()});estado('interrompido');raise
