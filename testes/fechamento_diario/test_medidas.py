import unittest
import numpy as np
from analises.etapas.fechamento_diario.medidas import medir, ridge


class Medidas(unittest.TestCase):
    def test_previsao_perfeita_e_constante(self):
        y=np.array([-.02,.01,.03,-.01])
        a=medir(y,y); self.assertEqual(a['mse'],0);self.assertEqual(a['balanced_accuracy'],1)
        b=medir(y,np.zeros(4));self.assertEqual(b['habilidade_naive'],0)
        self.assertIsNone(b['correlacao']);self.assertEqual(b['desvio_previsto'],0)
        self.assertAlmostEqual(sum(b['decomposicao_mse'].values()),b['mse'])

    def test_ridge_intercepto_e_sinal(self):
        x=np.arange(20,dtype=float)[:,None];y=.02*x[:,0]+.5
        (w,b),s=ridge(x[:15],y[:15],x[15:],y[15:])
        self.assertGreater(w[0],0); self.assertEqual(s['lambda'],.01)
        (w,b),s=ridge(x[:15],np.full(15,2.),x[15:],np.full(5,2.))
        np.testing.assert_array_equal(w,[0]);self.assertEqual(b,2.)

    def test_rejeita_nan_e_broadcast(self):
        with self.assertRaises(ValueError):medir([1,2],[1])
        with self.assertRaises(ValueError):medir([1,np.nan],[1,2])
