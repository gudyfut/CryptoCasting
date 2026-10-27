import unittest
import numpy as np
import pandas as pd
from previsao24.financeiro import simular
from previsao24.configuracao import referencia

class FinanceiroTeste(unittest.TestCase):
    def setUp(self):
        self.inicio=int(pd.Timestamp('2023-01-01',tz='UTC').timestamp()//60)
        self.m=np.ones((5*1440,6))
        self.m[:,:4]=100
        self.q=pd.DataFrame({'origem_utc':pd.date_range('2023-01-01',periods=4,freq='D',tz='UTC'),'previsao':[.01]*4})
        self.p=referencia()['operacao']

    def test_custos_e_reentrada_sem_capital_duplicado(self):
        r,o,c=simular(self.q,self.m,self.inicio,'2023-01-06',self.p)
        fator=(1-self.p['slippage'])*(1-self.p['taxa'])/((1+self.p['slippage'])*(1+self.p['taxa']))
        self.assertAlmostEqual(r['capital_final'],10000*fator**4)
        self.assertEqual(len(o),4)
        self.assertLess(r['retorno_liquido'],0)

    def test_naive_fica_em_caixa(self):
        self.q['previsao']=0
        r,o,_=simular(self.q,self.m,self.inicio,'2023-01-06',self.p)
        self.assertEqual(r['capital_final'],10000)
        self.assertFalse(o)

    def test_futuro_ausente_nao_elimina_entrada(self):
        self.m[1441,0]=np.nan
        r,o,_=simular(self.q,self.m,self.inicio,'2023-01-06',self.p)
        self.assertEqual(len(o),4)
        self.assertIsNone(r['retorno_liquido'])
        self.assertEqual(o[0]['status'],'nao_auditavel')

    def test_percurso_ausente_preserva_pontas_mas_nao_drawdown(self):
        self.m[70]=np.nan
        r,o,_=simular(self.q,self.m,self.inicio,'2023-01-06',self.p)
        self.assertTrue(r['retorno_auditavel'])
        self.assertFalse(r['risco_auditavel'])
        self.assertIsNone(r['drawdown'])

    def test_custos_agravados_preservam_sinais(self):
        a,o,_=simular(self.q,self.m,self.inicio,'2023-01-06',self.p)
        b,o2,_=simular(self.q,self.m,self.inicio,'2023-01-06',self.p,agravado=True)
        self.assertEqual(len(o),len(o2))
        self.assertLess(b['capital_final'],a['capital_final'])

if __name__=='__main__':
    unittest.main()
