import unittest
import numpy as np
from experimentos.historico_treino.avaliacao import bootstrap_pareado, retornos_diarios


class Avaliacao(unittest.TestCase):
    def test_bootstrap_delta_constante_e_seeds_pareadas(self):
        p=[(np.full((3,40),2.),np.full((3,40),4.)) for _ in range(3)]
        r=bootstrap_pareado(p,14,20)
        self.assertEqual(r['ic95'],[.5,.5])

    def test_diario_caixa_e_mark_close_nao_extremos(self):
        from types import SimpleNamespace
        m=SimpleNamespace(indice=lambda t:t//60000,marca=np.tile([100,500,1,110.],(2880,1)))
        t={'entrada_ms':60000,'saida_ms':86460000,'caixa_antes':10000.,'caixa_depois':10019.89,
           'quantidade':1.,'preco_entrada':100.,'lado':1,'eventos_funding':[]}
        r={'operacoes':[t],'metricas':{'capital_final':10019.89}}
        diarios=retornos_diarios(r,m,0,2*86400000)
        self.assertAlmostEqual(diarios[0],np.log(10009.95/10000))
        self.assertAlmostEqual(diarios.sum(),np.log(10019.89/10000))
        self.assertEqual(len(diarios),2)


if __name__=='__main__':unittest.main()
