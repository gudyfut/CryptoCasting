"""Retomada autorizada de XRP: preserva tentativa interrompida e executa receita congelada."""
import fcntl
import json
import os
import socket
import subprocess
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from infraestrutura.artefatos import RAIZ, agora, conferir_arquivos, ler_json, salvar_json, sha256
from experimentos.generalizacao_moedas.ciclo import integridade_nativa
from experimentos.generalizacao_moedas.contratos import preparar
from experimentos.generalizacao_moedas.avaliacao import executar as avaliar
from experimentos.alvo_retorno_diario.treinamento import ajustar, carregar_rede
from experimentos.padronizacao_diaria.qualificacao import ambiente
from experimentos.sem_penalizacao_diaria.observacao import observar

REG = RAIZ / 'registros/generalizacao_moedas'
ORIGINAL = RAIZ / 'dados/experimentos/generalizacao_moedas_1f2b005888361d23c111'
BASE = ORIGINAL / 'XRPUSDT/continuacao_001'
EVIDENCIA = REG / 'retomadas/20261110'


def verificar_publicadas():
    for simbolo in ('ETHUSDT', 'BNBUSDT'):
        base = ORIGINAL / simbolo
        fechamento = ler_json(base / 'fechamento.json')
        assert fechamento['situacao'] == 'concluido_conferido'
        assert fechamento['principais'] == 3 and fechamento['controles'] == 1 and fechamento['carteiras'] == 70
        assert ler_json(base / 'controle.json')['aprovado']
        conferir_arquivos(base, fechamento['arquivos'])


def executar():
    with (REG / 'execucao.lock').open('a+b') as lock, (RAIZ / 'registros/operacional_futuros/gpu.lock').open('a+b') as gpu:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(gpu, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'], text=True).strip(), 'GPU ocupada'
        ptr = ler_json(REG / 'execucao.json')
        assert ptr['id'] == '1f2b005888361d23c111' and sha256(ORIGINAL / 'congelamento.json') == ptr['congelamento_sha256']
        preparo = ler_json(EVIDENCIA / 'preparo.json')
        assert sha256(Path(__file__)) == preparo['executor_sha256']
        conferir_arquivos(RAIZ, preparo['artefatos_preservados'])
        integridade_nativa()
        congelado = ler_json(ORIGINAL / 'congelamento.json')
        assert ambiente() == congelado['ambiente'], 'Ambiente divergente da qualificação'
        verificar_publicadas()
        assert not BASE.exists(), 'Continuação já iniciada; não duplicar'
        BASE.mkdir(parents=True)
        m = congelado['moedas']['XRPUSDT']; c = m['configuracao']
        d, escalas = preparar(pd.read_parquet(RAIZ / m['mercado']['pasta'] / 'diario.parquet'), c)
        assert escalas == m['escalas'] == ler_json(ORIGINAL / 'XRPUSDT/escalas.json')
        salvar_json(BASE / 'escalas.json', escalas)
        proc = {'pid': os.getpid(), 'host': socket.gethostname(), 'boot': Path('/proc/sys/kernel/random/boot_id').read_text().strip(), 'utc': agora(), 'ativo': True}
        salvar_json(EVIDENCIA / 'processo.json', proc)
        def estado(situacao, job=None, concluidos=0, carteiras=140):
            s = {'utc': agora(), 'situacao': situacao, 'execucao': ptr, 'continuacao': BASE.relative_to(RAIZ).as_posix(),
                 'ajustes_previstos': 12, 'ajustes_concluidos': 8 + concluidos, 'carteiras_previstas': 210,
                 'carteiras_concluidas': carteiras, 'simbolo': 'XRPUSDT', 'job_atual': job, 'processo': proc}
            salvar_json(EVIDENCIA / 'estado.json', s); salvar_json(REG / 'estado.json', s); print(s, flush=True)
        try:
            for i, (nome, seed, controle) in enumerate((('seed_42', 42, False), ('controle_42', 42, True), ('seed_17', 17, False), ('seed_2026', 2026, False))):
                conferir_arquivos(RAIZ, congelado['fontes'])
                estado('treinando', nome, i)
                vinculo = {'execucao': ptr['id'], 'simbolo': 'XRPUSDT', 'job': nome, 'escalas_sha256': sha256(BASE / 'escalas.json')}
                ajustar(d, c, seed, BASE / 'ajustes' / nome, vinculo)
                if nome == 'seed_42':
                    velho = ORIGINAL / 'XRPUSDT/ajustes/seed_42/epocas.jsonl'
                    novo = BASE / 'ajustes/seed_42/epocas.jsonl'
                    a = [json.loads(x) for x in velho.read_text().splitlines()]
                    b = [json.loads(x) for x in novo.read_text().splitlines()]
                    assert len(a) == 390 and len(b) == 1000
                    campos = ('epoca', 'perda_treino_rmse_lotes', 'rmse_global_validacao_retorno', 'taxa')
                    assert all(all(x[k] == y[k] for k in campos) for x, y in zip(a, b)), 'Trajetória de XRP divergente antes da interrupção'
                    salvar_json(EVIDENCIA / 'reproducao_parcial.json', {'utc': agora(), 'epocas': len(a), 'campos_exatos': list(campos), 'aprovado': True})
                if controle:
                    a = np.load(BASE / 'ajustes/seed_42/validacao.npz')['previsoes']
                    b = np.load(BASE / 'ajustes/controle_42/validacao.npz')['previsoes']
                    np.testing.assert_array_equal(a, b)
                    assert ler_json(BASE / 'ajustes/seed_42/selecao.json')['epoca'] == ler_json(BASE / 'ajustes/controle_42/selecao.json')['epoca']
                    salvar_json(BASE / 'controle.json', {'utc': agora(), 'aprovado': True, 'max_abs_retorno': 0., 'fora_das_medias': True})
            for seed in c['seeds']:
                pasta = BASE / 'ajustes' / f'seed_{seed}'
                rede = carregar_rede(pasta, c)
                observar(rede, d['treino']['x'], BASE / 'observacoes' / f'seed_{seed}.json', ler_json(pasta / 'selecao.json')['epoca'])
                del rede; torch.cuda.empty_cache()
            estado('avaliando', concluidos=4)
            avaliar(BASE, c, d, m['mercado'])
            verificar_publicadas(); conferir_arquivos(RAIZ, preparo['artefatos_preservados']); integridade_nativa()
            arquivos = {p.relative_to(BASE).as_posix(): sha256(p) for p in BASE.rglob('*') if p.is_file() and p.name != 'fechamento.json'}
            salvar_json(BASE / 'fechamento.json', {'utc': agora(), 'situacao': 'concluido_conferido', 'principais': 3, 'controles': 1, 'carteiras': 70, 'arquivos': arquivos})
            salvar_json(EVIDENCIA / 'fechamento.json', {'utc': agora(), 'conclusao_xrp': (BASE / 'fechamento.json').relative_to(RAIZ).as_posix(),
                        'sha256': sha256(BASE / 'fechamento.json'), 'eth_bnb_preservados': True, 'tentativa_interrompida_preservada': True,
                        'ajustes_principais': 9, 'controles': 3, 'carteiras': 210})
            proc.update(ativo=False, encerramento_utc=agora()); salvar_json(EVIDENCIA / 'processo.json', proc)
            estado('concluido_conferido_continuacao', concluidos=4, carteiras=210)
        except BaseException:
            proc.update(ativo=False, encerramento_utc=agora()); salvar_json(EVIDENCIA / 'processo.json', proc)
            salvar_json(EVIDENCIA / 'incidente_continuacao.json', {'utc': agora(), 'erro': traceback.format_exc()})
            estado('interrompido_continuacao'); raise


if __name__ == '__main__':
    executar()
