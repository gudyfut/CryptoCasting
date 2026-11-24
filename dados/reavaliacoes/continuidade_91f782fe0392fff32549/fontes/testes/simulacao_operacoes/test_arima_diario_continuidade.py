import unittest
import numpy as np
from modelos.arima import ParametrosARIMA,prever_arima
from analises.etapas.continuidade_moedas.arima_diario import historico,conferir_direto


class ARIMADiario(unittest.TestCase):
    def dados(self):
        r=np.random.default_rng(12);return np.cumsum(r.normal(0,.01,100))+5.
    def test_um_passo_com_api_independente(self):
        v=self.dados();p=ParametrosARIMA('sintetico',(1,1,1),(.2,.1,1.),('ar.L1','ma.L1','sigma2'),5.,19)
        h=historico(v,[35,60,90],5.,19,'sintetico');conferir_direto(h,p,prever_arima(h,p))
    def test_futuro_nao_muda_origem(self):
        v=self.dados();p=ParametrosARIMA('sintetico',(1,1,0),(.2,1.),('ar.L1','sigma2'),5.,19)
        h=historico(v,[35],5.,19,'sintetico');a=prever_arima(h,p);v[36:]+=100
        np.testing.assert_array_equal(a,prever_arima(historico(v,[35],5.,19,'sintetico'),p))
    def test_random_walk_e_naive_exato(self):
        v=self.dados();p=ParametrosARIMA('sintetico',(0,1,0),(1.,),('sigma2',),5.,19)
        np.testing.assert_array_equal(prever_arima(historico(v,[35,90],5.,19,'sintetico'),p),[0.,0.])
