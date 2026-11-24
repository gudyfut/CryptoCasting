import tempfile
import unittest
from pathlib import Path
import numpy as np
import torch
from experimentos.lstm_diaria.modelo import LSTMDiaria
from experimentos.lstm_diaria.treinamento import ajustar, inferir


class ContratosLSTM(unittest.TestCase):
    def test_formato_transposicao_e_sem_transporte_de_estado(self):
        torch.manual_seed(1)
        rede = LSTMDiaria().eval()
        x = torch.randn(4, 6, 14)
        with torch.inference_mode():
            previsto = rede(x)
            sequencia, _ = rede.recorrente(x.transpose(1, 2).contiguous())
            esperado = rede.saida(sequencia[:, -1, :]).squeeze(-1)
            self.assertTrue(torch.equal(previsto, esperado))
            self.assertEqual(tuple(previsto.shape), (4,))
            self.assertTrue(torch.equal(previsto, rede(x)))
        with self.assertRaises(ValueError):
            rede(torch.randn(4, 14, 6))

    def test_repeticao_e_selecao_em_validacao(self):
        rng = np.random.default_rng(4)
        treino = dict(x=rng.normal(size=(15, 6, 14)).astype('float32'),
                      y=rng.normal(size=15).astype('float32') * .01)
        val = dict(x=rng.normal(size=(8, 6, 14)).astype('float32'),
                   y=rng.normal(size=8).astype('float32') * .01)
        cfg = dict(epocas=2, taxa=.001, weight_decay=.001, lote=8,
                   scheduler_passo=100, scheduler_gamma=.5, epsilon_raiz=1e-8,
                   limite_segundos_por_ajuste=120)
        with tempfile.TemporaryDirectory() as temp:
            a = ajustar(treino, val, cfg, 42, Path(temp)/'a', {'tipo':'sintetico'}, dispositivo='cpu')
            b = ajustar(treino, val, cfg, 42, Path(temp)/'b', {'tipo':'sintetico'}, dispositivo='cpu')
            self.assertEqual(a['epoca_escolhida'], b['epoca_escolhida'])
            with np.load(Path(temp)/'a'/'validacao.npz') as p, np.load(Path(temp)/'b'/'validacao.npz') as q:
                np.testing.assert_array_equal(p['previsoes'], q['previsoes'])


if __name__ == '__main__':
    unittest.main()
