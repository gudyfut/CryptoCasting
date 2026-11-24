import unittest
import numpy as np
from experimentos.eixo_temporal_diario.avaliacao import medir, ajustar_linear, prever_linear, intervalo, contrastar


class Avaliacao(unittest.TestCase):
    def test_metricas_direcao_naive(self):
        y=np.array([.1,-.1,.2,-.2]);p=np.array([.1,.1,.1,-.1])
        m=medir(y,p)
        self.assertAlmostEqual(m['mse_retorno'],.015)
        self.assertEqual(m['recall_alta'],1);self.assertEqual(m['recall_queda'],.5)
        self.assertEqual(m['acerto_balanceado'],.75)
        n=medir(y,np.zeros(4));self.assertIsNone(n['acerto_balanceado']);self.assertIsNone(n['acerto_sinal'])

    def test_linear_nao_acessa_teste(self):
        rng=np.random.default_rng(42);x=rng.normal(size=(130,6,14)).astype(np.float32)
        y=.02*x[:,0,0]-.01*x[:,1,1]+.003
        d={'treino':{'x':x[:100],'y':y[:100]},'validacao':{'x':x[100:],'y':y[100:]}}
        a=ajustar_linear(d,[.01,.1,1,10,100]);self.assertEqual(a,ajustar_linear(d,[.01,.1,1,10,100]))
        self.assertLess(np.mean((prever_linear(x[100:],a)-y[100:])**2),np.mean(y[100:]**2))

    def test_interacao_pareamento_intervalo(self):
        cfg={'bootstrap':{'seed':42,'replicas':100,'blocos':[7]},
             'contrastes':{'interacao':{'D':1,'C':-1,'B':-1,'A':1}}}
        m={k:np.full((3,35),v) for k,v in {'A':1,'B':2,'C':3,'D':6}.items()}
        r=contrastar(m,{},cfg,False)['interacao']['7']
        self.assertEqual(r['media'],2);self.assertEqual(r['ic95'],[2.,2.])
        self.assertFalse(intervalo(np.ones(35),7,cfg['bootstrap'],False)['reamostrar_seeds'])


if __name__=='__main__':unittest.main()
