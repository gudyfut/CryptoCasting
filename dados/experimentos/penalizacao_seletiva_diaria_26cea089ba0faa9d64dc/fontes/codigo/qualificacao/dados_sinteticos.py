"""Dados artificiais: nenhuma leitura de mercado ou treinamento."""
import numpy as np
import pandas as pd


def dados_artificiais():
    t=np.arange(1577836800000,1767225600000,86400000,dtype=np.int64)
    p=20000+np.arange(len(t))*4+100*np.sin(np.arange(len(t))/4)
    return pd.DataFrame({'open_time':t,'close_time':t+86399999,'open':p,'high':p+100,'low':p-100,'close':p+20,'volume':np.full(len(t),120000.)})

