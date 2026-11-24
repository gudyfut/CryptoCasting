"""Treino exclusivamente sintético; verificação de gradientes, recarga e isolamento."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import torch
from tests_modelos.apoio import conjunto
from modelos.consumo import ConsumoModelos
from modelos.neurais import criar_rede
from infraestrutura.artefatos import RAIZ, ler_json
from treinamento.configuracao import carregar
from treinamento.neural import ajustar
from treinamento.otimizacao import atualizar_lote, criar_otimizador, fixar_seed
from treinamento import checkpoints


class Neurais(unittest.TestCase):
    def test_microbatch_resto_equivale_lote(self):
        # Sete amostras, microbatch de três: o último pedaço não pode ter peso excessivo.
        a = torch.nn.Sequential(torch.nn.Linear(2,1), torch.nn.Flatten(0)).double()
        b = torch.nn.Sequential(torch.nn.Linear(2,1), torch.nn.Flatten(0)).double()
        b.load_state_dict(a.state_dict())
        x = torch.arange(14, dtype=torch.float64).reshape(7,2)/14
        y = torch.linspace(0,1,7,dtype=torch.float64)
        for rede, micro in ((a,3),(b,7)):
            atualizar_lote(rede, torch.optim.SGD(rede.parameters(), lr=.01), x,y,micro,1.)
        for x,y in zip(a.parameters(), b.parameters()):
            torch.testing.assert_close(x,y,rtol=1e-12,atol=1e-12)

    def test_grupos_mamba_preservam_isencoes(self):
        c = ConsumoModelos(conjunto(), 'sintetico')
        rede = criar_rede('mamba', c.especificacao)
        _, recibo = criar_otimizador(rede, carregar()['treino'])
        isentos = {n for g in recibo if g['weight_decay'] == 0 for n in g['nomes']}
        self.assertEqual(isentos, {n for n,p in rede.named_parameters() if getattr(p,'_no_weight_decay',False)})
        self.assertEqual(len(isentos), 4)

    def test_ajuste_nao_acessa_teste_recarga_e_contrato(self):
        consumo = ConsumoModelos(conjunto(), 'sintetico')
        original = consumo.solicitar
        def restrito(parte, *args, **kwargs):
            self.assertIn(parte, ('treino', 'validacao'))
            return original(parte, *args, **kwargs)
        cfg = dict(carregar()['treino'], epocas=2, paciencia=2)
        for nome in ('mamba', 'lstm'):
            with self.subTest(nome=nome), tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp)
                fixar_seed(42)
                inicial = criar_rede(nome, consumo.especificacao)
                pesos = {k:v.clone() for k,v in inicial.state_dict().items()}
                with patch.object(consumo, 'solicitar', side_effect=restrito):
                    rede, r = ajustar(consumo,nome,42,cfg,None,p,{'teste':'sintetico'})
                self.assertTrue(any(not torch.equal(pesos[k],v) for k,v in rede.state_dict().items()))
                with self.assertRaises(ValueError):
                    checkpoints.carregar(p, rede, {'teste':'outro'})
                selecao = ler_json(p/'selecao.json')
                checkpoint = p/selecao['arquivo']
                with checkpoint.open('ab') as f:
                    f.write(b'corrupcao')
                with self.assertRaises(ValueError):
                    checkpoints.carregar(p, rede, {'teste':'sintetico'})
