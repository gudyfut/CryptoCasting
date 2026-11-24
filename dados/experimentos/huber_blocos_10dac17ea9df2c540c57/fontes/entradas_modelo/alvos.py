"""Alvo terminal separado das entradas; ausência futura não decide elegibilidade causal."""
import numpy as np
import pandas as pd


def retorno_terminal(candles, horizonte_minutos, intervalo_minutos):
    if (not isinstance(horizonte_minutos,int) or isinstance(horizonte_minutos,bool)
            or horizonte_minutos<=0 or horizonte_minutos%intervalo_minutos):
        raise ValueError('Horizonte deve ser múltiplo inteiro positivo do candle.')
    passos=horizonte_minutos//intervalo_minutos
    close=candles['close'].reset_index(drop=True)
    destino=close.shift(-passos)
    return pd.DataFrame({'indice_candle':np.arange(len(candles),dtype=np.int64),
                         'origem_utc':candles['fim_utc'].reset_index(drop=True),
                         'destino_utc':candles['fim_utc'].reset_index(drop=True)+pd.Timedelta(minutes=horizonte_minutos),
                         'close':close,'preco_destino':destino,'alvo':np.log(destino/close)})
