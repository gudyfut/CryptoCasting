"""Ciclo novo: taxa inicial; referências encerradas são apenas lidas."""
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

REG = RAIZ/'registros/taxa_diaria'
CFG = RAIZ/'configuracoes/taxa_diaria_001.json'


def fontes():
    pacotes = ['infraestrutura', 'entradas_modelo', 'modelos', 'treinamento', 'avaliacao',
               'simulacao_operacoes', 'qualificacao', 'estudo_ohlcv', 'experimento_cryptomamba',
               'experimentos/taxa_diaria', 'experimentos/sem_penalizacao_diaria',
               'experimentos/alvo_retorno_diario', 'experimentos/cryptomamba_reproducivel']
    arquivos = [p for nome in pacotes for p in (RAIZ/'codigo'/nome).rglob('*.py')]
    arquivos += list((RAIZ/'testes/taxa_diaria').glob('*.py'))
    arquivos += [CFG, RAIZ/'docs/protocolo_taxa_diaria.md',
                 RAIZ/'codigo/experimentos/taxa_diaria/iniciar.ps1']
    return {p.relative_to(RAIZ).as_posix():sha256(p) for p in sorted(set(arquivos))}


def referencia():
    ptr = ler_json(RAIZ/'registros/sem_penalizacao_diaria/execucao.json')
    assert ptr['id'] == '8a0aeee4d78503b7f50d'
    p = RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json') == ptr['congelamento_sha256']
    assert ler_json(p/'processo.json')['ativo'] is False
    fecho = ler_json(RAIZ/'registros/sem_penalizacao_diaria/fechamento.json')
    assert sha256(RAIZ/fecho['arquivo']) == fecho['sha256']
    conferir_arquivos(p, ler_json(p/'fechamento.json')['arquivos'])
    f = ler_json(p/'congelamento.json')
    conferir_arquivos(p/'fontes', f['fontes'])
    return ptr, p, f


def preparar():
    from entradas_modelo.padronizacao_diaria import preparar_com_escalas
    from .contratos import conferir_configuracao
    if (REG/'execucao.json').exists():
        raise RuntimeError('Identidade já preparada; não sobrescrever.')
    ptr_ant, ant, f_ant = referencia()
    c = ler_json(CFG); conferir_configuracao(c, f_ant['configuracao'])
    q = ler_json(REG/'qualificacao.json')
    assert sha256(RAIZ/q['arquivo']) == q['sha256']
    conferir_arquivos(RAIZ, q['fontes'])
    qual = ler_json(RAIZ/q['arquivo']); assert qual['situacao'] == 'aprovado'
    auth = ler_json(REG/'autorizacao.json'); assert auth['treinar']
    if qual['cache_validacao_aprovado']:
        assert ler_json(REG/'eficiencia_comunicada.json')['cache_validacao'] is True
    for nome in ('diario','mercado_minuto'):
        r = f_ant[nome]; base = RAIZ/r['pasta']
        assert sha256(base/'manifesto.json') == r['manifesto_sha256']
        conferir_arquivos(base, ler_json(base/'manifesto.json')['arquivos'])
    diario = pd.read_parquet(RAIZ/f_ant['diario']['pasta']/'diario.parquet')
    dados, escalas = preparar_com_escalas(diario, c)
    anteriores, _ = preparar_com_escalas(diario, f_ant['configuracao'])
    for fase,z in dados.items():
        for campo in z: np.testing.assert_array_equal(z[campo], anteriores[fase][campo])
    assert escalas == f_ant['escalas']
    populacoes = {k:{'n':len(v['y']), 'primeira_origem_ms':int(v['origens_ms'][0]),
                    'ultima_origem_ms':int(v['origens_ms'][-1])} for k,v in dados.items()}
    assert populacoes == f_ant['populacoes']
    custos = ler_json(RAIZ/'registros/custos_vigentes/vigente.json')
    assert custos['id'] == '9f7598f109962adc3d76'
    cp = RAIZ/custos['pasta']
    assert sha256(cp/'publicacao_manifesto.json') == custos['manifesto_sha256']
    conferir_arquivos(cp, ler_json(cp/'publicacao_manifesto.json')['arquivos'])
    pres = {p.relative_to(RAIZ).as_posix():sha256(p) for p in ant.rglob('*') if p.is_file()}
    pres.update({(cp/n).relative_to(RAIZ).as_posix():h for n,h in ler_json(cp/'publicacao_manifesto.json')['arquivos'].items()})
    for n in ('registros/sem_penalizacao_diaria/execucao.json','registros/sem_penalizacao_diaria/fechamento.json',
              'registros/custos_vigentes/vigente.json','registros/taxa_diaria/autorizacao.json'):
        pres[n] = sha256(RAIZ/n)
    f = {'utc':agora(), 'configuracao':c, 'fontes':fontes(), 'qualificacao':q,
         'ambiente':qual['ambiente'], 'cache_validacao':qual['cache_validacao_aprovado'],
         'diario':f_ant['diario'], 'mercado_minuto':f_ant['mercado_minuto'],
         'preservacao':pres, 'antecessora':ptr_ant, 'custos_vigentes':custos,
         'slippage_avaliacao':.0001, 'populacoes':populacoes, 'escalas':escalas,
         'autorizacao':auth, 'contratos_reais':{'mesmos_dados_escalas_alvos':True,'unica_mudanca_taxa':True},
         'limites':'Referência herdada; 2024/2025 retrospectivos; comparação financeira comum a 1bp provisório.'}
    codigo = identidade(f)[:20]; p = RAIZ/'dados/experimentos'/f'taxa_diaria_{codigo}'
    p.mkdir(parents=True, exist_ok=False)
    for n in f['fontes']:
        d = p/'fontes'/n; d.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(RAIZ/n,d)
    salvar_json(p/'escalas.json', escalas); salvar_json(p/'congelamento.json', f)
    ptr = {'id':codigo, 'pasta':p.relative_to(RAIZ).as_posix(), 'congelamento_sha256':sha256(p/'congelamento.json')}
    salvar_json(REG/'execucao.json', ptr)
    salvar_json(REG/'estado.json', {'utc':agora(),'situacao':'preparado_autorizado','execucao':ptr,
                                  'ajustes_previstos':4,'ajustes_concluidos':0,'carteiras_previstas':70})
    print(ptr, flush=True)


def conferir():
    ptr = ler_json(REG/'execucao.json'); p = RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json') == ptr['congelamento_sha256']
    f = ler_json(p/'congelamento.json'); assert ler_json(p/'escalas.json') == f['escalas']
    conferir_arquivos(RAIZ,f['preservacao']); conferir_arquivos(RAIZ,f['fontes'])
    conferir_arquivos(p/'fontes', f['fontes'])
    for k in ('diario','mercado_minuto'):
        r=f[k]; base=RAIZ/r['pasta']; assert sha256(base/'manifesto.json')==r['manifesto_sha256']
        conferir_arquivos(base,ler_json(base/'manifesto.json')['arquivos'])
    print('INTEGRIDADE_APROVADA', len(f['preservacao']), len(f['fontes']), flush=True)


def integridade():
    nativo = RAIZ/'.venv/Scripts/python.exe'
    if os.name == 'posix' and nativo.exists():
        r=subprocess.run([str(nativo),'-B','-m','experimentos.taxa_diaria','conferir'],cwd=RAIZ,capture_output=True,text=True)
        if r.returncode: raise RuntimeError(r.stdout+r.stderr)
        print(r.stdout,flush=True)
    else: conferir()


def executar():
    import fcntl
    from entradas_modelo.padronizacao_diaria import preparar_com_escalas
    from experimentos.cryptomamba_reproducivel.qualificacao import ambiente
    from .treinamento import construir_ajustador
    from .qualificacao import iguais
    from .avaliacao import executar as avaliar
    with (REG/'execucao.lock').open('a+b') as lock, (RAIZ/'registros/operacional_futuros/gpu.lock').open('a+b') as gpu:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB); fcntl.flock(gpu,fcntl.LOCK_EX|fcntl.LOCK_NB)
        ocupado=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True)
        if ocupado.strip(): raise RuntimeError('GPU ocupada.')
        ptr=ler_json(REG/'execucao.json'); p=RAIZ/ptr['pasta']
        if (p/'inicio.json').exists(): raise RuntimeError('Já iniciada; retomada exige diagnóstico próprio.')
        integridade(); f=ler_json(p/'congelamento.json'); c=f['configuracao']
        assert f['autorizacao']['treinar'] and ambiente()==f['ambiente']
        d,escalas=preparar_com_escalas(pd.read_parquet(RAIZ/f['diario']['pasta']/'diario.parquet'),c)
        assert escalas==f['escalas']
        proc={'pid':os.getpid(),'host':socket.gethostname(), 'boot':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
              'inicio_processo_ticks':Path('/proc/self/stat').read_text().split()[21], 'utc':agora(),'ativo':True}
        salvar_json(p/'inicio.json',proc); salvar_json(p/'processo.json',proc); jobs=[]
        def estado(situacao,**extras):
            v={'utc':agora(),'situacao':situacao,'execucao':ptr,'ajustes_previstos':4,
               'ajustes_concluidos':sum(j['situacao']=='concluido' for j in jobs),'carteiras_previstas':70,'processo':proc,**extras}
            salvar_json(p/'progresso.json',v); salvar_json(REG/'estado.json',v); print(v,flush=True)
        try:
            treino={k:v for k,v in d.items() if k!='teste'}
            for nome,seed in [('seed_42',42),('controle_42',42),('seed_17',17),('seed_2026',2026)]:
                conferir_arquivos(RAIZ,f['fontes'])
                j={'id':nome,'seed':seed,'controle':nome.startswith('controle'),'situacao':'iniciado'}
                jobs.append(j); salvar_json(p/'ajustes.json',jobs); estado('treinando',job_atual=nome)
                construir_ajustador(f['cache_validacao'])(treino,c,seed,p/'ajustes'/nome,
                    {'execucao':ptr['id'],'job':nome,'escalas_sha256':sha256(p/'escalas.json')})
                j['situacao']='concluido'; salvar_json(p/'ajustes.json',jobs)
                if j['controle']:
                    iguais(p/'ajustes/seed_42',p/'ajustes/controle_42')
                    salvar_json(p/'controle.json',{'utc':agora(),'aprovado':True,'historico_pesos_previsoes_epoca_exatos':True,'fora_das_medias':True})
            assert ler_json(p/'controle.json')['aprovado']
            estado('avaliando'); avaliar(p,c,d,f['mercado_minuto']); integridade()
            salvar_json(p/'preservacao_depois.json',{'utc':agora(),'aprovado':True,'arquivos_anteriores':len(f['preservacao'])})
            proc.update(ativo=False,encerramento_utc=agora()); salvar_json(p/'processo.json',proc)
            salvar_json(p/'fechamento.json',{'utc':agora(),'situacao':'concluido_conferido','principais':3,'controles':1,'carteiras':70,
                'arquivos':{a.relative_to(p).as_posix():sha256(a) for a in p.rglob('*') if a.is_file() and a.name not in ('progresso.json','processo.json','fechamento.json')}})
            salvar_json(REG/'fechamento.json',{'arquivo':(p/'fechamento.json').relative_to(RAIZ).as_posix(),'sha256':sha256(p/'fechamento.json')})
            estado('concluido_conferido',carteiras_concluidas=70)
        except BaseException:
            proc.update(ativo=False,encerramento_utc=agora()); salvar_json(p/'processo.json',proc)
            salvar_json(p/'incidente.json',{'utc':agora(),'erro':traceback.format_exc()}); estado('interrompido'); raise
