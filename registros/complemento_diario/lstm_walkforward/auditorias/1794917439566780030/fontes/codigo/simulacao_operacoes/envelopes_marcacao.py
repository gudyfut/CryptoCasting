"""Alinha extremos de risco; não preenche candles canônicos nem preço de execução."""
import numpy as np
import pandas as pd


def alinhar(tempos, marca, envelopes):
    assert marca.open_time.is_unique and marca.open_time.is_monotonic_increasing
    tabela=marca.set_index('open_time')[['open','high','low','close']].reindex(tempos)
    faltas=tabela.index[tabela.high.isna()].to_numpy(np.int64)
    assert sorted(faltas.tolist())==sorted(e['minuto_ausente'] for e in envelopes)
    for e in envelopes:
        t=e['minuto_ausente']
        assert e['inicio_envelope']<=t and t+59999<=e['fim_envelope']
        assert e['fim_envelope']-e['inicio_envelope']==299999 and 0<e['low']<=e['high']
        tabela.loc[t,['high','low']]=[e['high'],e['low']]
        # open/close continuam NaN: não há observação 1m desses campos.
    assert np.isfinite(tabela[['high','low']].to_numpy()).all()
    return tabela.to_numpy(float), faltas
