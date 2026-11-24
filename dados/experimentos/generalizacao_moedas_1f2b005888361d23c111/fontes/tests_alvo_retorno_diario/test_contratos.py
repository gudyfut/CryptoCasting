import unittest
import copy
import numpy as np
from infraestrutura.artefatos import RAIZ,ler_json
from tests_cryptomamba_diario.test_contratos import Contratos as ContratosHerdados, dados_artificiais
from tests_cryptomamba_reproducivel.test_isolamento import Contratos as IsolamentoHerdado
from entradas_modelo.cryptomamba_diario import preparar as precos
from experimentos.alvo_retorno_diario.entradas import preparar,preco_equivalente,publicar_previsoes
from experimentos.alvo_retorno_diario.metricas import metricas_retorno,avaliar_precos
from experimentos.alvo_retorno_diario.contratos import conferir_configuracao
from simulacao_operacoes.diaria_24h import decidir


class AlvoRetorno(unittest.TestCase):
    def setUp(self):self.c=ler_json(RAIZ/'configuracoes/alvo_retorno_diario_001.json')
    def test_receita_restante_identica(self):
        ref=ler_json(RAIZ/'configuracoes/cryptomamba_reproducivel_001.json')
        self.assertTrue(conferir_configuracao(self.c,ref))
        novo=copy.deepcopy(self.c);novo['treinamento']['taxa']=.001
        with self.assertRaises(AssertionError):conferir_configuracao(novo,ref)
    def test_entradas_populacoes_e_alvo(self):
        df=dados_artificiais();a=precos(df,self.c);b=preparar(df,self.c)
        for fase in a:
            for k in ('x','origens_ms','fim_alvo_ms','ultimo_close'):np.testing.assert_array_equal(a[fase][k],b[fase][k])
            np.testing.assert_array_equal(a[fase]['y'],b[fase]['preco_alvo'])
            np.testing.assert_array_equal(b[fase]['y'],a[fase]['y']/a[fase]['ultimo_close']-1)
    def test_unidade_e_sinal(self):
        v=preco_equivalente(np.array([.02,-.02,0.,-1.2]),np.full(4,100.))
        np.testing.assert_allclose(v,[102,98,100,-20])
        self.assertEqual([decidir(x,100,.002) for x in v],[1,-1,0,0])
        with self.assertRaises(ValueError):preco_equivalente(np.array([.02]),np.ones(3))
    def test_metricas_naive_e_unidades(self):
        y=np.array([.02,-.02]);m=metricas_retorno(y,np.zeros(2))
        self.assertAlmostEqual(m['rmse_retorno'],.02);self.assertEqual(m['habilidade_mse_retorno_naive'],0)
        p=avaliar_precos(np.array([102,98]),np.array([100,100]),np.array([100,100]))
        self.assertAlmostEqual(p['rmse_usdt'],2);self.assertAlmostEqual(p['mse_retorno'],.0004)
    def test_peso_relativo_do_erro(self):
        # Mesmo erro percentual em preços distintos deve contribuir igualmente no novo alvo.
        m=avaliar_precos(np.array([100,1000]),np.array([101,1010]),np.array([100,1000]))
        self.assertAlmostEqual(m['mse_retorno'],.0001)
    def test_sem_vazamento(self):
        df=dados_artificiais();a=preparar(df,self.c);df.loc[14:,'close']*=2;b=preparar(df,self.c)
        np.testing.assert_array_equal(a['treino']['x'][0],b['treino']['x'][0])
        self.assertNotEqual(a['treino']['y'][0],b['treino']['y'][0])
    def test_publicacao_separa_preco_de_retorno(self):
        z=preparar(dados_artificiais(),self.c)['validacao'];ret=np.full(len(z['y']),.02)
        a=publicar_previsoes(z,ret)
        np.testing.assert_array_equal(a['previsoes_retorno'],ret)
        np.testing.assert_array_equal(a['y'],z['preco_alvo'])
        np.testing.assert_array_equal(a['alvo_retorno'],z['y'])
        np.testing.assert_array_equal(a['previsoes'],z['ultimo_close']*1.02)
        alterado=dict(z,preco_alvo=z['preco_alvo']*100,y=z['y']*100)
        np.testing.assert_array_equal(a['previsoes'],publicar_previsoes(alterado,ret)['previsoes'])


if __name__=='__main__':unittest.main()
