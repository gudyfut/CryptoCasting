from dataclasses import replace
import unittest
from unittest.mock import patch
import numpy as np
from modelos.arima import ParametrosARIMA, criar_sistema, prever_arima
from modelos.contratos import HistoricoARIMA


class Arima(unittest.TestCase):
    def setUp(self):
        self.v = np.log(100.) + np.sin(np.arange(100) / 5) * .01
        self.v[45] = np.nan
        self.h = HistoricoARIMA('sintetico', self.v, np.array([50, 67, 90]), 24, float(self.v[0]), 30)

    def parametros(self, ordem):
        nomes = criar_sistema(self.v, ordem).param_names
        valores = tuple(.1 if nome != 'sigma2' else 1. for nome in nomes)
        return ParametrosARIMA('sintetico', ordem, valores, tuple(nomes), float(self.v[0]), 30)

    def test_nove_ordens_vs_forecast_prefixo_sem_fit(self):
        from statsmodels.tsa.arima.model import ARIMA
        with patch.object(ARIMA, 'fit', side_effect=AssertionError('Treinamento proibido')):
            for ordem in ((p, 1, q) for p in range(3) for q in range(3)):
                params = self.parametros(ordem); previsto = prever_arima(self.h, params)
                referencias = []
                for i in self.h.indices_origens:
                    r = criar_sistema((self.v[:i + 1] - self.h.base_log_preco) * 100, ordem).filter(params.valores)
                    referencias.append(float(np.asarray(r.get_forecast(24).predicted_mean)[-1]) / 100 + self.h.base_log_preco - self.v[i])
                np.testing.assert_allclose(previsto, referencias, rtol=1e-10, atol=1e-12)

    def test_causalidade_e_horizonte_nao_confundido_com_um_passo(self):
        p = self.parametros((1, 1, 0)); a = prever_arima(self.h, p)
        alterado = self.v.copy(); alterado[51:] += 100
        b = prever_arima(replace(self.h, log_precos=alterado), p)
        self.assertEqual(a[0], b[0])
        um = prever_arima(replace(self.h, horizonte_passos=1), p)
        self.assertGreater(float(np.max(np.abs(a - um))), 1e-8)

    def test_random_walk_exatamente_naive(self):
        np.testing.assert_array_equal(prever_arima(self.h, self.parametros((0, 1, 0))), np.zeros(3))

    def test_rejeita_parametros_futuros_ordem_e_contrato(self):
        p = self.parametros((1, 1, 0))
        for novo in (replace(p, indice_fim_ajuste=31), replace(p, identidade='outro'),
                     replace(p, base_log_preco=99.), replace(p, nomes=('errado', 'sigma2')),
                     replace(p, valores=(.1, -1.)), replace(p, valores=(1.5, 1.))):
            with self.assertRaises(ValueError): prever_arima(self.h, novo)
        for ordem in ((1, 0, 0), (3, 1, 0)):
            with self.assertRaises(ValueError): criar_sistema(self.v, ordem)


if __name__ == '__main__': unittest.main()
