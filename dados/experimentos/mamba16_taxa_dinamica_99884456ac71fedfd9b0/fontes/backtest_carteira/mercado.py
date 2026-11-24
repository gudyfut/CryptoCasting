"""Leitura de minutos com propriedade explícita da matriz numérica (pandas3)."""
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ


def carregar(p,contrato):
    cfg=contrato['configuracao'];partes=[]
    for r in sorted(contrato['mercado_partes'],key=lambda d:d['periodo']['inicio']):
        partes.append(pd.read_parquet(RAIZ/cfg['mercado_pasta']/r['arquivo']))
    m=pd.concat(partes,ignore_index=True);t=pd.DatetimeIndex(m.inicio_utc)
    if t.tz is None or not (t[1:]-t[:-1]==pd.Timedelta(minutes=1)).all():raise ValueError('Grade temporal inválida.')
    # copy=True impede escrita na visão somente leitura que pandas3 pode retornar.
    x=m[['open','high','low','close','volume','negocios']].to_numpy(dtype=float,copy=True)
    x[~m.completo.to_numpy()]=np.nan
    return x,int(t[0].timestamp()//60)
