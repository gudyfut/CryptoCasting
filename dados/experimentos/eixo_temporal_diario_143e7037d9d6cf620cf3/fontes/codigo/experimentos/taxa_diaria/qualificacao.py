"""Qualificação e cronometragem sintéticas; nenhuma seleção em mercado."""
import json
import os
import subprocess
import sys
import time
import traceback
import numpy as np
import torch
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256
from entradas_modelo.padronizacao_diaria import preparar
from qualificacao.dados_sinteticos import dados_artificiais
from experimentos.cryptomamba_reproducivel.qualificacao import ambiente
from experimentos.sem_penalizacao_diaria.qualificacao import sondar
from .treinamento import construir_ajustador


def historia(p):
    return [{k:v for k,v in json.loads(l).items() if k != 'segundos'}
            for l in (p/'epocas.jsonl').read_text().splitlines()]


def iguais(a, b):
    assert historia(a) == historia(b), 'Trajetória alterada.'
    assert ler_json(a/'selecao.json')['epoca'] == ler_json(b/'selecao.json')['epoca']
    np.testing.assert_array_equal(np.load(a/'validacao.npz')['previsoes'],
                                  np.load(b/'validacao.npz')['previsoes'])
    assert {p.name for p in (a/'checkpoints').glob('*.pt')} == {p.name for p in (b/'checkpoints').glob('*.pt')}
    for p in (a/'checkpoints').glob('*.pt'):
        x = torch.load(p, weights_only=True)['pesos']
        y = torch.load(b/'checkpoints'/p.name, weights_only=True)['pesos']
        assert all(torch.equal(x[k], y[k]) for k in x), p.name


def executar():
    import fcntl
    from .ciclo import REG, fontes
    with (RAIZ/'registros/operacional_futuros/gpu.lock').open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ocupado = subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'], text=True)
        if ocupado.strip(): raise RuntimeError('GPU ocupada.')
        destino = REG/'qualificacoes'/agora().replace(':','').replace('+','_')
        destino.mkdir(parents=True, exist_ok=False)
        try:
            c = ler_json(RAIZ/'configuracoes/taxa_diaria_001.json')
            testes = subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','testes/taxa_diaria','-t','.','-v'],
                                    cwd=RAIZ, capture_output=True, text=True)
            (destino/'tests.log').write_text(testes.stdout+testes.stderr, encoding='utf-8')
            assert testes.returncode == 0
            sondas = sondar(c)
            df = dados_artificiais(); df['volume'] = 120000+np.arange(len(df))*5
            dados = preparar(df, c)
            dados = {f:{k:v[:192] for k,v in z.items()} for f,z in dados.items() if f != 'teste'}
            class Proibido(dict):
                def __getitem__(self, chave): raise AssertionError('Teste acessado no treino.')
            dados['teste'] = Proibido()
            duracoes = {}
            # ABBA reduz viés simples de aquecimento; todos os pesos devem coincidir.
            for nome, usar_cache in [('base_1',False),('cache_1',True),('cache_2',True),('base_2',False)]:
                inicio = time.monotonic()
                construir_ajustador(usar_cache)(dados,c,42,destino/nome,{'tipo':'artificial'},epocas=50)
                torch.cuda.synchronize(); duracoes[nome] = time.monotonic()-inicio
            iguais(destino/'base_1', destino/'base_2')
            equivalencia_cache = True
            try:
                iguais(destino/'base_1', destino/'cache_1'); iguais(destino/'cache_1', destino/'cache_2')
            except AssertionError:
                equivalencia_cache = False
                (destino/'cache_rejeitado.txt').write_text(traceback.format_exc(),encoding='utf-8')
            base = np.mean([duracoes['base_1'],duracoes['base_2']])
            cache = np.mean([duracoes['cache_1'],duracoes['cache_2']])
            ganho = 1-cache/base
            # Escolha técnica pré-fixada: pelo menos5% e igualdade exata.
            usar = bool(equivalencia_cache and ganho >= .05)
            r = {'utc':agora(),'situacao':'aprovado','ambiente':ambiente(),'sondas':sondas,
                 'historico_pesos_previsoes_base_exatos':True,'teste_inacessivel':True,
                 'benchmark':{'ordem':'ABBA','epocas':50,'exemplos':192,'duracoes':duracoes,
                              'ganho_fracao':float(ganho),'cache_exatamente_equivalente':equivalencia_cache},
                 'cache_validacao_aprovado':usar,'novos_treinamentos_mercado':0,
                 'limite':'Estimativa sintética; controle de mercado ainda obrigatório; CUDA/receita não alterados.'}
            salvar_json(destino/'qualificacao.json',r)
            salvar_json(REG/'qualificacao.json',{'arquivo':(destino/'qualificacao.json').relative_to(RAIZ).as_posix(),
                                               'sha256':sha256(destino/'qualificacao.json'),'fontes':fontes()})
            print(json.dumps(r,ensure_ascii=False),flush=True)
        except BaseException:
            salvar_json(destino/'incidente.json',{'utc':agora(),'erro':traceback.format_exc()})
            raise
