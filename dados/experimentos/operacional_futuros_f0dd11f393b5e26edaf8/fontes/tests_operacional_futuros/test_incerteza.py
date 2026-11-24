import unittest
import numpy as np
from avaliacao.incerteza_operacional import comprimir_dias,reconstruir,bootstrap_pareado
from avaliacao.metricas_operacionais import avaliar_patrimonio


class Incerteza(unittest.TestCase):
    def test_compressao_preserva_ordem_pico_vale(self):
        e=np.array([100,70,130,120,110,140,90,115.]);t=np.array([0,10,20,80000,86410,86420,86430,172800.])
        d=comprimir_dias(e,t);r=reconstruir(d);m=avaliar_patrimonio(e,t)
        self.assertAlmostEqual(r[0],m['retorno_liquido'])
        self.assertAlmostEqual(r[1],m['drawdown_maximo'])
        np.testing.assert_allclose(r[2],m['calmar'],rtol=1e-12)

    def test_pareado_identico_delta_zero(self):
        d=np.tile([1.001,1.01,.995,.015],(30,1));a={('D1',s):d.copy() for s in [17,42]}
        b=bootstrap_pareado(a,a,['D1'],[17,42],repeticoes=20)
        for v in b['ic95_delta_candidata_menos_referencia'].values(): self.assertEqual(v,[0.,0.])

    def test_nao_esconde_insolvencia(self):
        with self.assertRaises(ValueError): comprimir_dias([100,0],[0,86400])


if __name__=='__main__': unittest.main()
