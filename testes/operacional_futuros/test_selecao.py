import unittest
from copy import deepcopy
from experimentos.operacional_futuros.receitas import iniciais,propor,validar
from experimentos.operacional_futuros.avaliar import pontuar_c,melhor,elegibilidade


def metrica(g=.001,calmar=1.,operacoes=25):
    return dict(insolvente=False,saida_prudencial=False,operacoes=operacoes,calmar=calmar,
        crescimento_log_diario=g,giro=5.,retorno_liquido=.1,drawdown_maximo=.1)


class Selecao(unittest.TestCase):
    def test_apenas_um_fator_sem_repetir(self):
        r=iniciais();n=propor('P0','representacao','relativa',r)
        self.assertEqual(n['familia_alvo'],'payoff')
        with self.assertRaises(ValueError): propor('P0','d_state',16,r)
        with self.assertRaises(ValueError): propor('R0','barreiras_payoff',[1.,2.],r)
        with self.assertRaises(ValueError): propor('R0','familia_alvo','payoff',r)

    def test_calmar_indefinido_nao_vira_infinito(self):
        self.assertIsNone(pontuar_c([metrica(calmar=None)]))
        self.assertIsNone(pontuar_c([metrica(operacoes=0)]))
        self.assertEqual(melhor({0:None,1:(1.,.01,-3.),2:(1.+1e-11,.02,-4.)}),2)

    def test_atividade_cinco_cenarios_e_cobertura(self):
        linhas=[dict(recorte=b,seed=s,cenario=c,metricas=metrica()) for b in ['D1','D2','D3']
                for s in [17,42,2026] for c in ['base','custo2x','custo3x','comprado','vendido']]
        self.assertTrue(elegibilidade(linhas,['D1','D2','D3'],[17,42,2026])['elegivel'])
        linhas[-1]['metricas']['operacoes']=0
        self.assertFalse(elegibilidade(linhas,['D1','D2','D3'],[17,42,2026])['elegivel'])
        with self.assertRaises(ValueError): elegibilidade(linhas[1:],['D1','D2','D3'],[17,42,2026])
