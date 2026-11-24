"""Agregação de mercado somente. Não cria retorno, alvo, contexto ou scaler."""
import numpy as np
import pandas as pd
from .contratos import VALORES, conferir_candles


def agregar(minutos, intervalo):
    conferir_candles(minutos,1)
    if not isinstance(intervalo,int) or isinstance(intervalo,bool) or intervalo<=0 or 1440%intervalo:
        raise ValueError('Intervalo suportado: divisor inteiro positivo de um dia UTC.')
    a = pd.Timestamp(minutos['inicio_utc'].iloc[0])
    if a.value % pd.Timedelta(minutes=intervalo).value or len(minutos)%intervalo:
        raise ValueError('Período precisa conter candles inteiros; não cortar bordas silenciosamente.')
    v = minutos[VALORES].to_numpy(np.float64).reshape(-1,intervalo,len(VALORES))
    completos = minutos['completo'].to_numpy().reshape(-1,intervalo).all(axis=1)
    y = np.column_stack([v[:,0,0],v[:,:,1].max(axis=1),v[:,:,2].min(axis=1),v[:,-1,3],
                         *[v[:,:,j].sum(axis=1) for j in range(4,len(VALORES))]])
    y[~completos] = np.nan
    q = pd.DataFrame(y,columns=VALORES)
    q['inicio_utc'] = minutos['inicio_utc'].iloc[::intervalo].reset_index(drop=True)
    q['fim_utc'] = q['inicio_utc']+pd.Timedelta(minutes=intervalo)
    q['completo'] = completos
    q['minutos_completos'] = minutos['completo'].to_numpy().reshape(-1,intervalo).sum(axis=1)
    conferir_candles(q,intervalo)
    return q
