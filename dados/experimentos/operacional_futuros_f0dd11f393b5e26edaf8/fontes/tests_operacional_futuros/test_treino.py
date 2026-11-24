import unittest
import numpy as np
import torch
from treinamento.operacional_futuros import atualizar,metricas


class Treino(unittest.TestCase):
    def test_mse_elementos_e_acumulacao_duas_saidas(self):
        torch.manual_seed(42)
        a=torch.nn.Linear(3,2);b=torch.nn.Linear(3,2);b.load_state_dict(a.state_dict())
        x=torch.randn(7,3);y=torch.randn(7,2)
        oa=torch.optim.SGD(a.parameters(),lr=.01);ob=torch.optim.SGD(b.parameters(),lr=.01)
        v,_=atualizar(a,oa,x,y,'mse',microbatch=3)
        ob.zero_grad();p=b(x);loss=((p-y)**2).mean();loss.backward()
        torch.nn.utils.clip_grad_norm_(b.parameters(),1.);ob.step()
        self.assertAlmostEqual(v,float(loss.detach()),6)
        for pa,pb in zip(a.parameters(),b.parameters()):
            torch.testing.assert_close(pa,pb,atol=1e-7,rtol=1e-6)

    def test_huber_e_mse_nao_broadcast(self):
        a=torch.nn.Linear(3,2);o=torch.optim.SGD(a.parameters(),lr=.01)
        with self.assertRaises(ValueError): atualizar(a,o,torch.ones(2,3),torch.ones(2,1),'huber')
        with self.assertRaises(ValueError): metricas(np.zeros((2,2)),np.zeros((2,1)))

    def test_metricas_reais_por_canal(self):
        m=metricas([[1.,3.],[2.,4.]],[[0.,1.],[2.,4.]])
        self.assertEqual(m['mse'],1.25);self.assertEqual(m['mse_por_canal'],[.5,2.])


if __name__=='__main__': unittest.main()
