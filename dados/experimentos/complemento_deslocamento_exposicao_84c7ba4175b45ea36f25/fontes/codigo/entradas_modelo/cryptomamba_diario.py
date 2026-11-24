"""Contrato diário fiel ao DataTransform público; sem treino ou backtest."""
import numpy as np
import pandas as pd


def preparar(diario,configuracao):
    c=configuracao
    if c['contexto_dias']!=14 or c['normalizar'] or c['canais']!=['Timestamp','Open','High','Low','Close','Volume']:
        raise ValueError('Receita pública mudou; requer nova identidade.')
    saida={}
    for fase,(inicio,fim) in c['periodos'].items():
        ini=int(pd.Timestamp(inicio,tz='UTC').timestamp()*1000);end=int(pd.Timestamp(fim,tz='UTC').timestamp()*1000)
        q=diario[(diario.open_time>=ini)&(diario.open_time<end)].copy()
        np.testing.assert_array_equal(q.open_time,np.arange(ini,end,86400000))
        # A fonte pública exclui a última janela possível. Preservado explicitamente.
        n=len(q)-15
        if n<=0:raise ValueError('Partição insuficiente.')
        valores=np.column_stack([q.open_time.to_numpy()/1000,q[['open','high','low','close']].to_numpy(),q.volume.to_numpy()/c['volume_divisor']]).astype('float32')
        x=np.stack([valores[i:i+14].T for i in range(n)])
        ids=np.arange(14,14+n)
        saida[fase]={'x':x,'y':q.close.to_numpy(dtype=np.float64)[ids],
            'origens_ms':q.open_time.to_numpy(dtype=np.int64)[ids],
            'ultimo_close':q.close.to_numpy(dtype=np.float64)[ids-1],
            'fim_alvo_ms':q.close_time.to_numpy(dtype=np.int64)[ids]}
        assert x.shape==(n,6,14) and np.isfinite(x).all()
        assert (saida[fase]['fim_alvo_ms']<end).all()
    return saida
