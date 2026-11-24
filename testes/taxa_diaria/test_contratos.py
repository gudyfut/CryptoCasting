import copy
import unittest
import numpy as np
from infraestrutura.artefatos import RAIZ, ler_json
from experimentos.taxa_diaria.contratos import conferir_configuracao
from entradas_modelo.padronizacao_diaria import preparar_com_escalas
from qualificacao.dados_sinteticos import dados_artificiais


class TaxaDiaria(unittest.TestCase):
    def setUp(self):
        self.a = ler_json(RAIZ/'configuracoes/taxa_diaria_001.json')
        self.b = ler_json(RAIZ/'configuracoes/sem_penalizacao_diaria_001.json')

    def test_fator_unico(self):
        self.assertTrue(conferir_configuracao(self.a, self.b))
        for campo, valor in [('weight_decay', .001), ('lote', 64), ('epocas', 500),
                             ('scheduler_gamma', .1), ('taxa', .0001)]:
            c = copy.deepcopy(self.a); c['treinamento'][campo] = valor
            with self.assertRaises(AssertionError): conferir_configuracao(c, self.b)
        c = copy.deepcopy(self.a); c['operacoes']['slippage_por_lado'] = .0001
        with self.assertRaises(AssertionError): conferir_configuracao(c, self.b)

    def test_dados_escalas_exatos(self):
        a, ea = preparar_com_escalas(dados_artificiais(), self.a)
        b, eb = preparar_com_escalas(dados_artificiais(), self.b)
        self.assertEqual(ea, eb)
        for fase in a:
            for campo in a[fase]: np.testing.assert_array_equal(a[fase][campo], b[fase][campo])


if __name__ == '__main__': unittest.main()
