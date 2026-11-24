import unittest
from copy import deepcopy
import numpy as np
from experimentos.historico_treino.contrato import calendario, grade, configuracao
from experimentos.historico_treino.qualificacao import conferir_par
from entradas_modelo.operacional_futuros import preparar, montar_canais


class Historico(unittest.TestCase):
    def test_unica_diferenca_calendario_e_grade(self):
        c=configuracao()
        for r in c['recortes']:
            b=calendario(r,'movel12');a=calendario(r,'acumulado')
            self.assertNotEqual(a['treino'][0],b['treino'][0])
            b['treino'][0]=a['treino'][0]
            self.assertEqual(a,b);self.assertEqual(r,a)
        g=grade(c)
        self.assertEqual(sum(not j['controle'] for j in g),18)
        self.assertEqual(sum(j['controle'] for j in g),2)
        self.assertTrue(g[1]['controle'] and g[3]['controle'])
        self.assertEqual(len({j['id'] for j in g}),20)

    def test_pareamento_rejeita_origens_diferentes(self):
        from types import SimpleNamespace
        def d(ids):
            return SimpleNamespace(canais=('x',),contexto=168,alvo=np.zeros((20,2)),
               indices={'treino':np.array(ids),'validacao':np.array([10]),'calibracao':np.array([11]),'comparacao':np.array([12])})
        a,b=d(range(9)),d(range(4,9));conferir_par(a,b)
        b.indices['comparacao']=np.array([13])
        with self.assertRaises(AssertionError):conferir_par(a,b)

    def test_contrato_real_receita_fixa(self):
        c=configuracao()
        self.assertEqual(c['receita']['familia_alvo'],'payoff')
        self.assertEqual(c['receita']['contexto_horas'],168)
        self.assertEqual(c['seeds'],[42,17,2026])
        self.assertEqual(c['carteiras_previstas'],456)


if __name__=='__main__': unittest.main()
