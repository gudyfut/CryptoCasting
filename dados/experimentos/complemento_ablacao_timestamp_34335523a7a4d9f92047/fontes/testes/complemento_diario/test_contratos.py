import unittest
import numpy as np
from experimentos.complemento_diario.comum import configuracao
from experimentos.complemento_diario.contratos import (
    retirar_timestamp, decisoes, precos_decisoes, deslocamentos, grade_sensibilidade)
from simulacao_operacoes.continuidade_diaria.simulador import simular
from simulacao_operacoes.continuidade_diaria.auditoria_grade import conferir


class ContratosComplemento(unittest.TestCase):
    def test_remocao_timestamp_preserva_todas_as_outras_informacoes(self):
        rng = np.random.default_rng(81)
        z = dict(x=rng.normal(size=(7, 6, 14)).astype('float32'),
                 y=rng.normal(size=7), origens_ms=np.arange(7, dtype=np.int64))
        copia = z['x'].copy()
        novo = retirar_timestamp(z)
        self.assertTrue(np.all(novo['x'][:, 0] == 0))
        np.testing.assert_array_equal(z['x'], copia)
        np.testing.assert_array_equal(novo['x'][:, 1:], copia[:, 1:])
        for nome in ('y', 'origens_ms'):
            np.testing.assert_array_equal(novo[nome], z[nome])

    def test_grade_completa_sem_escolher_modelo_moeda_periodo(self):
        g = grade_sensibilidade(configuracao())
        self.assertEqual(len(g), 324)
        self.assertEqual(len({tuple(x.values()) for x in g}), 324)
        self.assertEqual(sum(x['populacao'].startswith('fixa') for x in g), 216)

    def test_deslocamentos_preservam_composicao_e_mesma_agenda_por_n(self):
        c = configuracao()['deslocamentos']
        for n in (314, 350):
            k = deslocamentos(n, c)
            np.testing.assert_array_equal(k, deslocamentos(n, c))
            self.assertEqual(len(set(k)), 99)
            self.assertTrue(np.all((k >= 14) & (k <= n-14)))
            lados = np.resize(np.array([-1, -1, 0, 1, 1, 1]), n)
            for v in k:
                np.testing.assert_array_equal(np.sort(np.roll(lados, v)), np.sort(lados))
            self.assertTrue(np.all(np.roll(np.zeros(n), k[0]) == 0))

    def test_codificacao_zero_reproduz_ledger_curva_e_auditoria(self):
        n = 5
        negocios = np.full((n*1440+2, 4), 100.)
        negocios[1441:] = 102.
        negocios[4321:] = 98.
        mercado = dict(tempo=np.arange(len(negocios), dtype=np.int64)*60000,
                       negocio=negocios, marca=negocios.copy(),
                       funding_tempo=np.arange(n, dtype=np.int64)*86400000+60000,
                       funding_taxa=np.array([.001, -.001, .002, -.002, .001]),
                       funding_preco=np.full(n, 100.))
        regras = dict(capital_inicial=10000., fracao_nocional=.95, latencia_minutos=1,
                      comissao_por_lado=.0005, slippage_por_lado=.0001, tick_preco=.01,
                      passo_quantidade=.001, nocional_minimo=10., buffer_prudencial=.025,
                      filtro_retorno_absoluto=.002)
        t, ultimo = np.arange(n, dtype=np.int64)*86400000, np.full(n, 100.)
        original = np.array([100.4, 100.3, 100.1, 99.6, 99.4])
        lados = decisoes(original, ultimo, .002)
        sintetico = precos_decisoes(lados, ultimo, .002)
        a, ca = simular(t, original, ultimo, mercado, regras, 'liquida')
        b, cb = simular(t, sintetico, ultimo, mercado, regras, 'liquida')
        self.assertEqual(a, b)
        for k in ca:
            np.testing.assert_array_equal(ca[k], cb[k])
        conferir(b, cb, mercado, regras, 'liquida', t, sintetico, ultimo, None)
        # O auditor deve detectar uma alteração material no ledger.
        b['ordens'][0]['comissao'] += 1
        with self.assertRaises(AssertionError):
            conferir(b, cb, mercado, regras, 'liquida', t, sintetico, ultimo, None)


if __name__ == '__main__':
    unittest.main()
