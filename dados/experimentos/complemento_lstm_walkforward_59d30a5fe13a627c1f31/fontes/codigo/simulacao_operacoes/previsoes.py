import numpy as np
import pandas as pd

COLUNAS=['indice_candle','origem_utc','destino_utc','close','previsao']

def diarias(q):
    if list(q.columns)!=COLUNAS:raise ValueError('Somente previsao e dados conhecidos; alvo/preco futuro sao proibidos.')
    t=pd.DatetimeIndex(q.origem_utc)
    if str(t.tz)!='UTC' or not t.is_monotonic_increasing or t.has_duplicates:raise ValueError('Origens UTC ordenadas/unicas obrigatorias.')
    if not np.isfinite(q[['close','previsao']]).all().all() or (q.close<=0).any():raise ValueError('Previsao/preco invalido.')
    if not ((pd.DatetimeIndex(q.destino_utc)-t)==pd.Timedelta(hours=24)).all():raise ValueError('Horizonte24h obrigatorio.')
    d=q.loc[(t.hour==0)&(t.minute==0)&(t.second==0)].copy().reset_index(drop=True)
    if not len(d):raise ValueError('Sem previsoes diarias.')
    td=pd.DatetimeIndex(d.origem_utc)
    if len(td)>1 and not (td[1:]-td[:-1]==pd.Timedelta(days=1)).all():raise ValueError('Calendario diario incompleto.')
    return d
