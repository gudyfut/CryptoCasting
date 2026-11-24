import unittest
from avaliacao.metricas_operacionais import avaliar_patrimonio, resumo_pareado

ANO = 365*86400


class Metricas(unittest.TestCase):
    def test_exemplo_calmar_e_capital_efetivo(self):
        # 100→200→120→220: retorno120%, drawdown40%, Calmar3.
        m = avaliar_patrimonio([100,200,120,220], [0,ANO/3,2*ANO/3,ANO])
        self.assertAlmostEqual(m['retorno_liquido'], 1.2)
        self.assertAlmostEqual(m['drawdown_maximo'], .4)
        self.assertAlmostEqual(m['calmar'], 3.)

    def test_pico_nao_substitui_resultado(self):
        m = avaliar_patrimonio([100,200,80], [0,ANO/2,ANO])
        self.assertAlmostEqual(m['retorno_liquido'], -.2)
        self.assertAlmostEqual(m['drawdown_maximo'], .6)
        self.assertLess(m['crescimento_log_diario'], 0)

    def test_crescimento_igual_nao_significa_drawdown_igual(self):
        a = avaliar_patrimonio([100,200,120,130], [0,ANO/3,2*ANO/3,ANO])
        b = avaliar_patrimonio([100,110,105,130], [0,ANO/3,2*ANO/3,ANO])
        self.assertEqual(a['crescimento_log_diario'], b['crescimento_log_diario'])
        self.assertLess(a['calmar'], b['calmar'])

    def test_caixa_e_insolvencia_sem_score_infinito(self):
        self.assertIsNone(avaliar_patrimonio([100,100], [0,ANO])['calmar'])
        m = avaliar_patrimonio([100,0,10], [0,ANO/2,ANO])
        self.assertTrue(m['insolvente'])
        self.assertIsNone(m['calmar'])
        self.assertIsNone(m['crescimento_log_diario'])

    def test_nao_ocultar_seed_indefinida_ou_faltante(self):
        a = avaliar_patrimonio([100,90,130], [0,ANO/2,ANO])
        b = avaliar_patrimonio([100,100,100], [0,ANO/2,ANO])
        rows = [{'recorte':'D1','seed':s,'metricas':m} for s,m in [(42,a),(17,b)]]
        q = resumo_pareado(rows,['D1'],[42,17])
        self.assertIsNone(q['score_calmar'])
        self.assertAlmostEqual(q['medias']['retorno_liquido'],.15)
        with self.assertRaises(ValueError):
            resumo_pareado(rows[:1],['D1'],[42,17])
        with self.assertRaises(ValueError):
            resumo_pareado(rows+[rows[0]],['D1'],[42,17])

    def test_tempos_invalidos(self):
        with self.assertRaises(ValueError):
            avaliar_patrimonio([100,110,120], [0,10,9])

    def test_tempo_abaixo_do_pico_sem_inventar_queda(self):
        self.assertEqual(avaliar_patrimonio([100,110,120], [0,86400,172800])['tempo_maximo_abaixo_pico_dias'],0)
        q = avaliar_patrimonio([100,110,105,110], [0,86400,172800,259200])
        self.assertEqual(q['tempo_maximo_abaixo_pico_dias'],2)
        self.assertFalse(q['drawdown_final_aberto'])


if __name__ == '__main__':
    unittest.main()
