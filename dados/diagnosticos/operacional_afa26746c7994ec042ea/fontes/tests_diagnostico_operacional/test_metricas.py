import unittest
import ast
from pathlib import Path
import numpy as np
import pandas as pd
from analises.diagnostico_operacional.metricas import direcao, quintis_c, correlacao, indices_blocos, decompor_operacao, bootstrap


class TestDiagnostico(unittest.TestCase):
    def test_direcao_precisao_recall_e_abstencao(self):
        r=direcao(np.array([1,1,-1,-1,0]),np.array([1,-1,-1,-1,1]))
        self.assertEqual(r['precisao_alta'],.5); self.assertEqual(r['precisao_queda'],1)
        self.assertEqual(r['recall_alta'],.5); self.assertEqual(r['recall_queda'],2/3)
        self.assertEqual(r['acuracia'],.75); self.assertEqual(r['cobertura_direcao'],.8)

    def test_constante_e_lado_ausente(self):
        r=direcao(np.ones(5),np.array([-1,1,1,-1,1]))
        self.assertIsNone(r['precisao_queda']); self.assertEqual(r['balanced_accuracy'],.5)
        self.assertIsNone(correlacao(np.ones(5),np.arange(5)))

    def test_quintis_so_c_empates(self):
        q,e=quintis_c(np.arange(10),np.array([-5,50]),[.2,.4,.6,.8])
        np.testing.assert_array_equal(q,[1,5]); np.testing.assert_allclose(e,[1.8,3.6,5.4,7.2])
        q,_=quintis_c(np.ones(10),np.ones(4),[.2,.4,.6,.8]); np.testing.assert_array_equal(q,np.ones(4))

    def test_bloco_temporal_nao_circular(self):
        a=indices_blocos(100,14,np.random.default_rng(5)); self.assertEqual(len(a),100)
        self.assertTrue(np.all(a<100)); self.assertTrue(np.all(a>=0))
        self.assertTrue(np.all(np.diff(a[:14])==1))

    def test_contabilidade(self):
        o={'quantidade':2,'pnl_bruto_por_btc':10,'comissao_por_btc':3,'funding_por_btc':-1,'pnl_liquido':12}
        self.assertEqual(decompor_operacao(o)['liquido'],12)
        o['pnl_liquido']=13
        with self.assertRaises(ValueError): decompor_operacao(o)

    def test_bootstrap_constante_e_zeros(self):
        rows=[]
        for seed in [17,42,2026]:
            for dia in range(30): rows.append({'seed':seed,'dia':dia,'recorte':'D1','score':1.,'quintil_c':5,
                'retorno_terminal':.1,'lado':1,'payoff_escolhido':.02,'payoff_lado_treino':.02,
                'acerto_maioria_treino':True,'erro2':0.,'erro2_media':0.})
        r=bootstrap(pd.DataFrame(rows),{'seed':1,'dias':[7,14],'repeticoes':30})
        for x in r:
            if x['metrica']=='payoff_score_positivo': np.testing.assert_allclose(x['ic95'],[.02,.02])
            if x['metrica']=='delta_mse_media_treino': self.assertEqual(x['ic95'],[0.,0.])

    def test_unidades(self):
        self.assertAlmostEqual(np.expm1(np.log(102/100)),.02)
        self.assertNotAlmostEqual(.02*100,np.log(102/100)*100,places=3)

    def test_sem_treinador_ou_simulador(self):
        for p in Path('analises/diagnostico_operacional').glob('*.py'):
            tree=ast.parse(p.read_text(encoding='utf-8'))
            for n in ast.walk(tree):
                if isinstance(n,ast.ImportFrom):
                    self.assertFalse(any(x in (n.module or '') for x in ['treinamento','modelos','motor','avaliar','worker']))

if __name__ == '__main__': unittest.main()
