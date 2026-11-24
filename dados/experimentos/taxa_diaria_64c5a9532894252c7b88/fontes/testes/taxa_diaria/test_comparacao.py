import unittest
import numpy as np
from experimentos.taxa_diaria.comparacao import intervalos


class Contrastes(unittest.TestCase):
    def test_pareamento_nulo_e_sinal_constante(self):
        z=np.zeros((3,30)); a=intervalos(z,z,replicas=40)
        for r in a.values():
            self.assertEqual(r['delta_mse_retorno_ic95'],[0.,0.])
        b=intervalos(z+.002,z-.001,replicas=40)
        for r in b.values():
            np.testing.assert_allclose(r['delta_mse_retorno_ic95'],[.002,.002])
            np.testing.assert_allclose(r['delta_crescimento_log_ic95'],[-.001,-.001])

    def test_rejeita_populacoes_diferentes_e_nao_finitas(self):
        with self.assertRaises(ValueError): intervalos(np.zeros((3,30)),np.zeros((3,29)))
        with self.assertRaises(ValueError): intervalos(np.full((3,30),np.nan),np.zeros((3,30)))
