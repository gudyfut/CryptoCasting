from dataclasses import replace
import io
import unittest
from unittest.mock import patch
import numpy as np
try:
    import torch
except ImportError:
    torch = None
from .apoio import conjunto
from modelos import ConsumoModelos
from modelos.contratos import LoteNeural
from modelos.neurais import criar_rede, inferir_normalizado, prever_neural, empacotar_pesos, restaurar_pesos
from infraestrutura.artefatos import RAIZ, ler_json


@unittest.skipUnless(torch is not None and torch.cuda.is_available(), 'Verificação neural exige CUDA oficial, sem fallback.')
class Neurais(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(42)
        torch.set_num_threads(2)
        self.c = ConsumoModelos(conjunto(), 'fixture-neural')
        self.p = self.c.solicitar('validacao', [0, 1, 2])
        self.lote = self.c.lote_neural(self.p)

    def test_paridade_exata_com_redes_preservadas(self):
        from estudo_ohlcv.redes import criar as criar_anterior
        config = ler_json(RAIZ / 'configuracoes/ohlcv24_001.json')
        for nome, n in [('mamba', 20257), ('lstm', 13473)]:
            rede = criar_rede(nome, self.c.especificacao)
            anterior = criar_anterior(nome, config).cuda().eval()
            anterior.load_state_dict(rede.state_dict(), strict=True)
            with torch.inference_mode():
                esperado = anterior(torch.as_tensor(self.lote.entradas, device='cuda')).cpu().numpy()
            np.testing.assert_array_equal(inferir_normalizado(rede, self.lote), esperado)
            self.assertEqual(sum(p.numel() for p in rede.parameters()), n)
            if nome == 'mamba':
                self.assertEqual(sum(p.numel() for p in rede.parameters() if getattr(p, '_no_weight_decay', False)), 2176)

    def test_forward_sem_alterar_pesos_ou_criar_gradientes(self):
        for nome in ('mamba', 'lstm'):
            rede = criar_rede(nome, self.c.especificacao)
            antes = {k: v.clone() for k, v in rede.state_dict().items()}
            with patch.object(torch.Tensor, 'backward', side_effect=AssertionError('backward proibido')):
                y = inferir_normalizado(rede, self.lote)
            self.assertEqual(y.shape, (3,))
            self.assertTrue(all(p.grad is None for p in rede.parameters()))
            for k, v in rede.state_dict().items(): self.assertTrue(torch.equal(v, antes[k]))

    def test_dimensoes_derivadas_e_lote_unitario(self):
        for canais in (['fechamento_relativo'], ['fechamento_relativo', 'volume_transformado']):
            c = ConsumoModelos(conjunto(canais), 'fixture-canais')
            p = c.solicitar('teste', [0])
            for nome in ('mamba', 'lstm'):
                rede = criar_rede(nome, c.especificacao)
                self.assertEqual(inferir_normalizado(rede, c.lote_neural(p)).shape, (1,))

    def test_rejeita_eixos_canais_dtype_nan_e_contrato_trocados(self):
        rede = criar_rede('mamba', self.c.especificacao)
        for x in (self.lote.entradas.transpose(0, 2, 1), self.lote.entradas[:, :-1],
                  self.lote.entradas.astype(np.float64), np.full_like(self.lote.entradas, np.nan)):
            with self.assertRaises(ValueError): inferir_normalizado(rede, LoteNeural(self.c.especificacao, x))
        esp = replace(self.c.especificacao, canais=tuple(reversed(self.c.especificacao.canais)))
        with self.assertRaises(ValueError): inferir_normalizado(rede, LoteNeural(esp, self.lote.entradas))
        rede.train()  # Apenas muda a flag; nenhuma passagem/atualização nesse modo.
        with self.assertRaises(ValueError): inferir_normalizado(rede, self.lote)

    def test_contexto_configuravel_sem_alterar_arquitetura(self):
        esp = replace(self.c.especificacao, identidade='fixture-contexto24', contexto=24)
        lote = LoteNeural(esp, self.lote.entradas[:, -24:, :].copy())
        for nome in ('mamba', 'lstm'):
            rede = criar_rede(nome, esp)
            self.assertEqual(inferir_normalizado(rede, lote).shape, (3,))

    def test_recarga_exata_e_decodificacao_uma_vez(self):
        for nome in ('mamba', 'lstm'):
            rede = criar_rede(nome, self.c.especificacao)
            z = inferir_normalizado(rede, self.lote)
            resultado = prever_neural(rede, self.c, self.p, tamanho_lote=3)
            np.testing.assert_array_equal(resultado.previsao, self.c.decodificar_saida_neural(self.p, z))
            pacote = empacotar_pesos(rede)
            memoria = io.BytesIO(); torch.save(pacote, memoria); memoria.seek(0)
            outro = criar_rede(nome, self.c.especificacao)
            restaurar_pesos(outro, torch.load(memoria, weights_only=True))
            np.testing.assert_array_equal(inferir_normalizado(outro, self.lote), z)
            pacote['especificacao']['identidade'] = 'outro'
            with self.assertRaises(ValueError): restaurar_pesos(outro, pacote)


if __name__ == '__main__': unittest.main()
