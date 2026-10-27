import unittest
import numpy as np
import pandas as pd
from scripts.auditar_controles import construir_controle,retorno_entre_pontas


class ControleTest(unittest.TestCase):
    def test_saida_no_open_sem_olhar_close_posterior(self):
        m=np.full((120,6),100.);m[:,4:]=1
        m[-1,:4]=[200,10000,100,9999]
        inicio=pd.Timestamp('2023-01-01',tz='UTC');primeiro=int(inicio.timestamp()//60)
        r,q=construir_controle(m,primeiro,1,inicio,inicio+pd.Timedelta(hours=2))
        self.assertEqual(r['status'],'auditavel')
        self.assertAlmostEqual(r['retorno_liquido'],.994,places=3)
        self.assertEqual(q.pior_marca_observavel.iloc[-1],q.patrimonio.iloc[-1])
        self.assertFalse(q.exposto.iloc[-1])
        pontas=retorno_entre_pontas(m,primeiro,1,inicio+pd.Timedelta(hours=2))
        self.assertAlmostEqual(pontas['retorno_liquido'],r['retorno_liquido'])

    def test_lacuna_nao_vira_curva_continua(self):
        m=np.full((120,6),100.);m[:,4:]=1;m[60]=np.nan
        inicio=pd.Timestamp('2023-01-01',tz='UTC');primeiro=int(inicio.timestamp()//60)
        r,q=construir_controle(m,primeiro,1,inicio,inicio+pd.Timedelta(hours=2))
        self.assertEqual(r['status'],'nao_auditavel')
        self.assertIsNone(r['retorno_liquido'])
        self.assertTrue(np.isnan(q.patrimonio.iloc[60]))

    def test_pontas_observadas_nao_inventam_risco_no_meio(self):
        m=np.full((120,6),100.);m[:,4:]=1;m[60]=np.nan;m[-1,0]=200.
        inicio=pd.Timestamp('2023-01-01',tz='UTC');primeiro=int(inicio.timestamp()//60)
        original,q=construir_controle(m,primeiro,1,inicio,inicio+pd.Timedelta(hours=2))
        r=retorno_entre_pontas(m,primeiro,1,inicio+pd.Timedelta(hours=2))
        self.assertIsNone(original['retorno_liquido'])
        self.assertEqual(r['status'],'pontas_observadas')
        self.assertAlmostEqual(r['retorno_liquido'],.994,places=3)
        self.assertIsNone(r['drawdown_maximo'])
        self.assertTrue(np.isnan(q.patrimonio.iloc[60]))

    def test_ponta_ausente_ou_sem_negocio_nao_autoriza_retorno(self):
        inicio=pd.Timestamp('2023-01-01',tz='UTC');primeiro=int(inicio.timestamp()//60)
        for indice,coluna,valor in ((1,0,np.nan),(119,5,0),(119,0,np.nan)):
            m=np.full((120,6),100.);m[:,4:]=1;m[indice,coluna]=valor
            r=retorno_entre_pontas(m,primeiro,1,inicio+pd.Timedelta(hours=2))
            self.assertEqual(r['status'],'pontas_nao_observadas')
            self.assertIsNone(r['retorno_liquido'])


if __name__=='__main__':
    unittest.main()
