"""Fixtures declaradamente sintéticas; não lê resultados nem executa ajustes."""
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json
from entradas_modelo.pipeline import construir


def conjunto(canais=None):
    n = 31 * 24
    i = np.arange(n)
    p = 100 * np.exp(.0001 * i + .01 * np.sin(i / 11))
    t = pd.date_range('2021-01-01T00:00Z', periods=n, freq='h')
    candles = pd.DataFrame({'inicio_utc': t, 'fim_utc': t + pd.Timedelta(hours=1),
                           'open': p * .999, 'high': p * 1.01, 'low': p * .99,
                           'close': p, 'volume': 1 + i % 20, 'completo': True})
    c = ler_json(RAIZ / 'configuracoes/entradas_ohlcv24_001.json')
    c['divisao'] = {'treino': ['2021-01-01T00:00Z', '2021-01-15T00:00Z'],
                   'validacao': ['2021-01-15T00:00Z', '2021-01-22T00:00Z'],
                   'teste': ['2021-01-22T00:00Z', '2021-02-01T00:00Z']}
    if canais is not None:
        c['canais'] = canais
    return construir(candles, c, 60)
