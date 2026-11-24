"""Janelas causais usando escalas antigas, incluindo contexto anterior a2026."""
import numpy as np
from entradas_modelo.padronizacao_diaria import transformar

DIA = 86400000


def preparar(diario, origens, configuracao, escalas):
    assert configuracao['contexto_dias'] == 14 and configuracao['normalizar']
    assert configuracao['canais'] == ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
    t = diario.open_time.to_numpy(np.int64)
    assert np.all(np.diff(t) == DIA)
    ids = np.searchsorted(t, origens)
    np.testing.assert_array_equal(t[ids], origens)
    assert (ids >= 14).all()
    valores = np.column_stack([t / 1000, diario[['open', 'high', 'low', 'close']].to_numpy(),
                               diario.volume.to_numpy() / configuracao['volume_divisor']]).astype(np.float32)
    bruto = np.stack([valores[i-14:i].T for i in ids])
    x = transformar(bruto, escalas)
    assert x.shape == (len(origens), 6, 14) and x.dtype == np.float32
    assert np.isfinite(x).all()
    ultimo = diario.close.to_numpy(float)[ids-1]
    # Alvos separados de x; nunca usados na decisão ou no ajuste de escala.
    y = diario.close.to_numpy(float)[ids]
    return dict(x=x, origens_ms=np.asarray(origens, np.int64), ultimo_close=ultimo,
                y=y, alvo_retorno=y/ultimo-1, fim_alvo_ms=np.asarray(origens)+DIA-1)
