"""Dados, sinais e matrizes definidos antes de resultados novos."""
from pathlib import Path
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json
from experimentos.walkforward_diario.dados import configuracao_bloco, preparar
from simulacao_operacoes.diaria_24h import decidir
from .comum import configuracao, pais, carregar_npz


def conferir_dados_reais():
    c, refs = configuracao(), pais()
    wf = ler_json(refs['walkforward'] / 'congelamento.json')
    base = ler_json(refs['fixa'] / 'BTCUSDT/configuracao.json')
    diario = pd.read_parquet(RAIZ / wf['referencias']['diario']['pasta'] / 'diario.parquet')
    resultado = {}
    for bloco in c['blocos']:
        b = bloco['id']
        cfg = configuracao_bloco(base, bloco, c['treino_inicio'])
        assert cfg == wf['configs_blocos'][b]
        dados, escalas = preparar(diario, cfg)
        assert escalas == wf['escalas'][b]
        for fase, z in dados.items():
            antigo = carregar_npz(refs['walkforward'] / b / 'dados' / f'{fase}.npz')
            assert set(z) == set(antigo)
            for k, v in z.items():
                np.testing.assert_array_equal(v, antigo[k], err_msg=f'{b}/{fase}/{k}')
        assert len(dados['teste']['y']) == bloco['n_teste']
        origem = dados['teste']['origens_ms'][0]
        alterado = diario.copy()
        alterado.loc[alterado.open_time >= origem, ['open', 'high', 'low', 'close', 'volume']] *= 1.2
        contraprova, escalas2 = preparar(alterado, cfg)
        assert escalas == escalas2
        np.testing.assert_array_equal(dados['teste']['x'][0], contraprova['teste']['x'][0])
        np.testing.assert_array_equal(dados['treino']['x'], contraprova['treino']['x'])
        np.testing.assert_array_equal(dados['validacao']['x'], contraprova['validacao']['x'])
        assert dados['teste']['y'][0] != contraprova['teste']['y'][0]
        resultado[b] = dict(populacoes={k: len(v['y']) for k, v in dados.items()},
                            escalas_exatas=True, janelas_exatas=True, perturbacao_futura=True)
    return resultado


def retirar_timestamp(z):
    copia = {k: v.copy() for k, v in z.items()}
    assert copia['x'].shape[1:] == (6, 14)
    copia['x'][:, 0, :] = 0
    for k in z:
        np.testing.assert_array_equal(z[k][:, 1:, :] if k == 'x' else z[k],
                                      copia[k][:, 1:, :] if k == 'x' else copia[k])
    return copia


def decisoes(precos, ultimo, filtro):
    return np.asarray([decidir(float(p), float(u), filtro) for p, u in zip(precos, ultimo)], dtype=np.int8)


def precos_decisoes(lados, ultimo, filtro):
    lados, ultimo = np.asarray(lados), np.asarray(ultimo)
    assert lados.shape == ultimo.shape and np.isin(lados, [-1, 0, 1]).all()
    # Sinais artificiais somente codificam lado. O motor dimensiona a posição
    # por patrimônio e mercado; a magnitude do score não altera a quantidade.
    margem = max(0.01, 2 * filtro)
    precos = ultimo * (1 + lados * margem)
    np.testing.assert_array_equal(decisoes(precos, ultimo, filtro), lados)
    return precos


def deslocamentos(n, c):
    candidatos = np.arange(c['minimo'], n - c['distancia_final'] + 1, dtype=np.int64)
    assert len(candidatos) >= c['quantidade']
    return np.random.default_rng(c['seed']).choice(candidatos, c['quantidade'], replace=False)


def grade_sensibilidade(c):
    populacoes = [(f'fixa_{ano}', m, v) for ano in (2025, 2026) for m in c['moedas'] for v in c['variantes']]
    populacoes += [(b['id'], 'BTCUSDT', v) for b in c['blocos'] for v in c['variantes']]
    return [dict(populacao=p, moeda=m, variante=v, filtro=filtro, custo=i, slippage=slip)
            for p, m, v in populacoes for filtro in c['filtros']
            for i, slip in enumerate(c['slippage_cenarios'], 1)]


def entradas_lstm():
    refs = pais()
    entradas = [refs['walkforward'] / 'congelamento.json', refs['lstm'] / 'congelamento.json']
    for b in configuracao()['blocos']:
        for fase in ('treino', 'validacao', 'teste'):
            entradas.append(refs['walkforward'] / b['id'] / 'dados' / f'{fase}.npz')
        for nome in [f'{v}_{s}' for v in ('A', 'L') for s in configuracao()['seeds']] + ['A_ensemble', 'L_ensemble', 'naive']:
            entradas.append(refs['walkforward'] / 'publicacao' / b['id'] / 'previsoes' / f'{nome}.npz')
    for fase in ('treino', 'validacao'):
        entradas.append(refs['fixa'] / 'BTCUSDT/dados' / f'{fase}.npz')
    ajuste = refs['lstm'] / 'BTCUSDT/ajustes/seed_42'
    entradas.extend(p for p in ajuste.rglob('*') if p.is_file())
    return entradas
