import unittest
import numpy as np
import torch
from mamba_ssm import Mamba
from infraestrutura.artefatos import RAIZ,ler_json
from treinamento.otimizacao import fixar_seed
from experimentos.ablacao_linear_diaria.contratos import receita
from experimentos.ablacao_linear_diaria.modelo import construir,coeficientes_afins


class Modelo(unittest.TestCase):
    def test_inicializacao_rng_remocao_e_gradientes(self):
        c=ler_json(RAIZ/'configuracoes/ablacao_linear_diaria_001.json')
        for seed in c['seeds']:
            fixar_seed(seed);a=construir(receita(c,'A'))
            cpu,gpu=torch.get_rng_state().clone(),torch.cuda.get_rng_state().clone()
            fixar_seed(seed);l=construir(receita(c,'L'))
            self.assertTrue(torch.equal(cpu,torch.get_rng_state()))
            self.assertTrue(torch.equal(gpu,torch.cuda.get_rng_state()))
            self.assertEqual(sum(p.numel() for p in a.parameters()),136952)
            self.assertEqual(sum(p.numel() for p in l.parameters()),824)
            self.assertEqual(sum(isinstance(m,Mamba) for m in l.modules()),0)
            self.assertEqual(sum(isinstance(m,torch.nn.LayerNorm) for m in l.modules()),0)
            self.assertEqual(set(l.state_dict()),{k for k in a.state_dict() if '.op.' not in k and '.norm.' not in k})
            for k,p in l.state_dict().items():self.assertTrue(torch.equal(p,a.state_dict()[k]),k)
            hooks=[m.register_forward_hook(lambda m,a,o:torch.zeros_like(o)) for m in a.modules() if isinstance(m,Mamba)]
            try:
                for tamanho in (1,6,32):
                    x=torch.randn(tamanho,6,14,device='cuda');y=torch.randn(tamanho,device='cuda')*.01
                    a.zero_grad(set_to_none=True);l.zero_grad(set_to_none=True)
                    pa,pl=a(x),l(x)
                    self.assertEqual(pl.shape,(tamanho,));self.assertTrue(torch.equal(pa,pl))
                    torch.sqrt(((pa-y)**2).mean()+1e-8).backward()
                    torch.sqrt(((pl-y)**2).mean()+1e-8).backward()
                    for k,p in l.named_parameters():
                        self.assertTrue(torch.isfinite(p.grad).all())
                        self.assertTrue(torch.equal(p.grad,dict(a.named_parameters())[k].grad),k)
                    coef,inter=coeficientes_afins(l)
                    afim=np.einsum('nct,ct->n',x.cpu().numpy().astype(float),coef)+inter
                    np.testing.assert_allclose(pl.detach().cpu().numpy(),afim,atol=2e-6,rtol=1e-5)
                with self.assertRaises(ValueError):l(x.transpose(1,2).contiguous())
            finally:
                for h in hooks:h.remove()
            del a,l;torch.cuda.empty_cache()


if __name__=='__main__':unittest.main()
