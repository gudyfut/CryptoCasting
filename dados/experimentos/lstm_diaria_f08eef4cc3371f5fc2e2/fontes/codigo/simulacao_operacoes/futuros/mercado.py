import numpy as np

class Mercado:
    def __init__(self,negocio,marca,funding):
        np.testing.assert_array_equal(negocio.open_time,marca.open_time)
        t=negocio.open_time.to_numpy(np.int64)
        assert len(t)>1 and (np.diff(t)==60000).all()
        self.inicio=int(t[0]//60000);self.fim=self.inicio+len(t)
        self.negocio=negocio[['open','high','low','close','count']].to_numpy(float)
        self.marca=marca[['open','high','low','close']].to_numpy(float)
        assert np.isfinite(self.negocio).all() and np.isfinite(self.marca).all()
        assert (self.negocio[:,:4]>0).all() and (self.marca>0).all()
        self.funding=funding[['fundingTime','fundingRate','markPrice']].to_numpy(float)
        assert np.isfinite(self.funding).all() and (self.funding[:,2]>0).all()
        assert len(self.funding)==0 or (np.diff(self.funding[:,0])>0).all()
    def indice(self,minuto):
        i=int(minuto)-self.inicio
        if not 0<=i<len(self.negocio):raise ValueError('Mercado fora da cobertura.')
        return i
