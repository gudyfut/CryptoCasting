"""Receitas causais versionadas. Recebem somente campos de mercado, nunca alvos."""
import numpy as np
from mercado_binance.contratos import OHLCV

CANAIS = ['abertura_relativa','maxima_relativa','minima_relativa','fechamento_relativo','volume_transformado']


def _ohlcv_relativo(q):
    p=q[OHLCV].to_numpy(np.float64)
    anterior=np.r_[np.nan,p[:-1,3]]
    with np.errstate(divide='ignore',invalid='ignore'):
        x=np.column_stack([np.log(p[:,:4]/anterior[:,None]),np.log1p(p[:,4])])
    x[~np.isfinite(p).all(axis=1)]=np.nan
    return x


# Novas receitas precisam de nome/versionamento/testes, não de eval ou código no JSON.
RECEITAS = {'ohlcv_relativo_v1': _ohlcv_relativo}


def calcular_entradas(candles, receita, canais):
    if receita not in RECEITAS:
        raise ValueError('Receita não registrada; implementar e testar antes de usar.')
    if not canais or len(set(canais))!=len(canais) or any(k not in CANAIS for k in canais):
        raise ValueError('Canais vazios, duplicados ou desconhecidos.')
    # A restrição é também uma fronteira contra vazamento acidental de rótulos/metadados.
    x=RECEITAS[receita](candles[OHLCV].copy())
    return x[:,[CANAIS.index(k) for k in canais]]
