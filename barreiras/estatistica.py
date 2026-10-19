"""Intervalos descritivos pareados que preservam blocos de tempo."""
import numpy as np
import pandas as pd

from .metricas import erros


def comparar(previsoes_a,previsoes_b):
    if not previsoes_a.origem_utc.equals(previsoes_b.origem_utc):
        raise ValueError('Comparação exige origens pareadas.')
    ya=previsoes_a.classe.to_numpy()
    if not np.array_equal(ya,previsoes_b.classe.to_numpy()):
        raise ValueError('Comparação exige rótulos idênticos.')
    da=erros(ya,previsoes_a[['p0','p1','p2']].to_numpy())[0]
    db=erros(ya,previsoes_b[['p0','p1','p2']].to_numpy())[0]
    diario=pd.DataFrame({'dia':previsoes_a.origem_utc.dt.floor('D'),'soma':da-db,'n':1}).groupby('dia').sum()
    diario=diario.reindex(pd.date_range(diario.index.min(),diario.index.max(),freq='D'),fill_value=0)
    resultados={'diferenca_log_loss':float((da-db).mean()),'n':len(da),'intervalos':{}}
    for bloco in (7,14,28):
        if len(diario)<bloco:
            resultados['intervalos'][str(bloco)]=None
            continue
        indices=indices_blocos(len(diario),bloco,deslocamento_fold(previsoes_a.origem_utc.iloc[0]))
        somas=diario['soma'].to_numpy()[indices].sum(axis=1)
        ns=diario['n'].to_numpy()[indices].sum(axis=1)
        amostras=somas[ns>0]/ns[ns>0]
        resultados['intervalos'][str(bloco)]=np.quantile(amostras,[.025,.975]).tolist()
    return resultados


def deslocamento_fold(data):
    data=pd.Timestamp(data)
    return data.year*4+(data.month-1)//3


def indices_blocos(n,bloco,deslocamento=0):
    rng=np.random.default_rng(20261018+deslocamento)
    comecos=rng.integers(0,n-bloco+1,size=(2000,int(np.ceil(n/bloco))))
    return (comecos[:,:,None]+np.arange(bloco)).reshape(2000,-1)[:,:n]


def incerteza_financeira(curva,capital=10000.):
    if not np.isfinite(curva.patrimonio).all():
        return {'status':'nao_auditavel','intervalos':None}
    diario=curva.assign(dia=pd.to_datetime(curva.minuto_utc,unit='m',utc=True).dt.floor('D')).groupby('dia').patrimonio.last()
    retornos=diario.to_numpy()/np.r_[capital,diario.to_numpy()[:-1]]-1
    intervalos={}
    for bloco in (7,14,28):
        if len(retornos)<bloco:
            intervalos[str(bloco)]=None
            continue
        r=retornos[indices_blocos(len(retornos),bloco,deslocamento_fold(diario.index[0]))]
        patrimonio=np.cumprod(1+r,axis=1)
        picos=np.maximum.accumulate(np.column_stack([np.ones(len(r)),patrimonio]),axis=1)[:,1:]
        intervalos[str(bloco)]={'retorno_liquido':np.quantile(patrimonio[:,-1]-1,[.025,.975]).tolist(),
             'drawdown_fechamento_diario':np.quantile((1-patrimonio/picos).max(axis=1),[.025,.975]).tolist()}
    return {'status':'calculado','dias':len(retornos),'intervalos':intervalos,
            'interpretacao':'Reamostragem de retornos diários observados; não recria sinais nem treina modelos.'}
