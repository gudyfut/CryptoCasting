import unittest
import numpy as np
import pandas as pd

from barreiras.dados import construir_horas
from barreiras.rotulagem import rotular
from barreiras.particoes import ajustar_escalas, separar
from barreiras.metricas import calcular


class RotulagemTest(unittest.TestCase):
    def base(self):
        a=np.full((150,6),100.0)
        a[:,4:]=1
        return a

    def executar(self,a,h=60):
        return rotular(a,np.array([1]),np.array([np.log(1.1)]),h)

    def test_toque_inferior_antes_recuperacao(self):
        a=self.base();a[3,2]=80;a[40,1]=120;a[-1,3]=120
        y,s,k,p,amb,m=self.executar(a)
        self.assertEqual((y[0],s[0],k[0]),(0,3,4))
        self.assertAlmostEqual(p[0],100/1.1)

    def test_duplo_toque_e_gap_abertura(self):
        a=self.base();a[2,1]=120;a[2,2]=80
        y,s,k,p,amb,m=self.executar(a)
        self.assertTrue(amb[0]);self.assertEqual(y[0],0)
        a[2,0]=120
        y,s,k,p,amb,m=self.executar(a)
        self.assertEqual((y[0],p[0],k[0]),(2,120,2));self.assertFalse(amb[0])

    def test_expiracao_tem_prioridade_e_retorno(self):
        a=self.base();a[61,0]=130
        y,s,k,p,amb,m=self.executar(a)
        self.assertEqual((y[0],s[0],p[0]),(1,61,130))

    def test_latencia_e_lacunas(self):
        a=self.base();a[0,1]=200
        self.assertEqual(self.executar(a)[0][0],1)
        a[10]=np.nan
        self.assertEqual(self.executar(a)[0][0],-1)
        a[2,1]=120
        self.assertEqual(self.executar(a)[0][0],2)

    def test_sem_negocio_na_entrada(self):
        a=self.base();a[1,5]=0
        self.assertEqual(self.executar(a)[-1][0],1)


class CausalidadeTest(unittest.TestCase):
    def dados(self):
        rng=np.random.default_rng(17)
        preco=np.exp(4.6+np.cumsum(rng.normal(0,.0001,60*400)))
        return np.column_stack([preco,preco*1.0001,preco*.9999,preco,np.ones(len(preco)),np.ones(len(preco))])

    def test_perturbar_futuro_nao_altera_entradas_ou_sigma(self):
        a=self.dados();b=a.copy();b[60*250:,:4]*=20
        qa=construir_horas(a,0);qb=construir_horas(b,0)
        pd.testing.assert_frame_equal(qa.iloc[:250],qb.iloc[:250])

    def test_lacuna_nao_interpolada(self):
        a=self.dados();a[60*50+4]=np.nan
        q=construir_horas(a,0)
        self.assertTrue(np.isnan(q.loc[50,'retorno']))
        self.assertFalse(q.loc[218,'elegivel_passado'])
        self.assertTrue(q.loc[219,'elegivel_passado'])

    def test_escalas_ignoraram_futuro(self):
        q=construir_horas(self.dados(),0)
        treino=q.iloc[180:220].copy();treino['distancia']=treino.sigma
        treino['expiracao_maxima_utc']=treino.origem_utc+pd.Timedelta(hours=168,minutes=1)
        _,a=ajustar_escalas(q,treino)
        outro=q.copy();outro.loc[220:,'retorno']=1000
        _,b=ajustar_escalas(outro,treino)
        self.assertEqual(a,b)

    def test_logloss_tres_classes(self):
        q=calcular([0,1,2],np.eye(3))
        self.assertEqual(q['log_loss'],0);self.assertEqual(q['balanced_accuracy'],1)
        self.assertIsNone(calcular([0],[[1,0,0]])['balanced_accuracy'])


if __name__=='__main__':
    unittest.main()
