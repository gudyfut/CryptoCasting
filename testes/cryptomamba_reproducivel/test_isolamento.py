"""Contratos da correção; testes de gradiente e treino ficam na qualificação CUDA."""
import unittest
from infraestrutura.artefatos import RAIZ,ler_json


class Contratos(unittest.TestCase):
    def test_unica_mudanca_de_execucao(self):
        a=ler_json(RAIZ/'configuracoes/cryptomamba_diario_001.json')
        b=ler_json(RAIZ/'configuracoes/cryptomamba_reproducivel_001.json')
        ignorar={'ciclo','versao','execucao_numerica','antecessora'}
        self.assertEqual({k:v for k,v in a.items() if k not in ignorar},
                         {k:v for k,v in b.items() if k not in ignorar})

    def test_namespace_privado(self):
        import torch
        if not torch.cuda.is_available():self.skipTest('Verificação CUDA no executor WSL.')
        from mamba_ssm import Mamba
        from modelos.cryptomamba_diario import construir as original
        from experimentos.cryptomamba_reproducivel.modelo import construir
        antes=Mamba.forward.__globals__['selective_scan_fn']
        c=ler_json(RAIZ/'configuracoes/cryptomamba_reproducivel_001.json')
        a=original(c);b=construir(c)
        self.assertIs(Mamba.forward.__globals__['selective_scan_fn'],antes)
        self.assertTrue(all(m.use_fast_path for m in a.modules() if isinstance(m,Mamba)))
        self.assertTrue(all(not m.use_fast_path for m in b.modules() if isinstance(m,Mamba)))
        self.assertEqual(list(a.state_dict()),list(b.state_dict()))
        self.assertEqual(sum(p.numel() for p in a.parameters()),sum(p.numel() for p in b.parameters()))
        self.assertFalse(torch.is_deterministic_algorithms_warn_only_enabled())
        with self.assertRaises(ValueError):construir({})


if __name__=='__main__':unittest.main()
