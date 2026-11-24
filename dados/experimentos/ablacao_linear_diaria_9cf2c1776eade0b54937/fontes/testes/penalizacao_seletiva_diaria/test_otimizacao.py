import unittest
import torch
from torch import nn
from experimentos.penalizacao_seletiva_diaria.otimizacao import separar,gradientes


class Rede(nn.Module):
    def __init__(self):
        super().__init__();self.norm=nn.LayerNorm(3);self.linear=nn.Linear(3,2)
        self.ssm=nn.Module()
        self.ssm.A_log=nn.Parameter(torch.ones(2,3));self.ssm.A_log._no_weight_decay=True
        self.ssm.D=nn.Parameter(torch.ones(2));self.ssm.D._no_weight_decay=True
        self.vetor=nn.Parameter(torch.ones(4))


class Otimizacao(unittest.TestCase):
    def test_grupos_cobertura_e_excecoes(self):
        r=Rede();grupos,nomes=separar(r,'seletiva',.001)
        self.assertEqual(len(grupos),2)
        mapa={n['nome']:n['weight_decay'] for n in nomes}
        self.assertEqual(mapa,{'ssm.A_log':0,'ssm.D':0,'vetor':.001,'norm.weight':0,'norm.bias':0,'linear.weight':.001,'linear.bias':0})
        ids=[id(p) for g in grupos for p in g['params']]
        self.assertEqual(len(ids),len(set(ids)));self.assertEqual(set(ids),{id(p) for p in r.parameters()})
        uniforme,_=separar(r,'uniforme',.001)
        self.assertEqual([id(p) for p in uniforme[0]['params']],[id(p) for p in r.parameters()])

    def test_penalizacao_efetiva_no_passo_adam(self):
        r=Rede()
        with torch.no_grad():
            for p in r.parameters():p.fill_(1.)
        grupos,nomes=separar(r,'seletiva',.001);o=torch.optim.Adam(grupos,lr=.01)
        for p in r.parameters():p.grad=torch.zeros_like(p)
        g=gradientes(r,o);self.assertEqual(g['A_log']['norma_l2'],0);self.assertEqual(g['D']['norma_l2'],0)
        o.step();mapa={n['nome']:n['weight_decay'] for n in nomes}
        for n,p in r.named_parameters():
            if mapa[n]==0:self.assertTrue(torch.equal(p,torch.ones_like(p)),n)
            else:self.assertTrue(torch.all(p<1),n)

    def test_rejeita_politica_ambigua(self):
        with self.assertRaises(ValueError):separar(Rede(),'qualquer',.001)


if __name__=='__main__':unittest.main()
