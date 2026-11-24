import copy
import unittest
import numpy as np
from infraestrutura.artefatos import RAIZ, ler_json
from entradas_modelo.padronizacao_diaria import preparar_com_escalas
from qualificacao.dados_sinteticos import dados_artificiais
from experimentos.eixo_temporal_diario.contratos import organizar, receita, conferir_configuracao, selecionar_prefixo


class Contratos(unittest.TestCase):
    def setUp(self):
        self.c = ler_json(RAIZ/'configuracoes/eixo_temporal_diario_001.json')
        self.ant = ler_json(RAIZ/'configuracoes/padronizacao_diaria_001.json')

    def test_fatores_e_orcamento(self):
        self.assertTrue(conferir_configuracao(self.c, self.ant))
        for campo,valor in [('epocas',201),('taxa',.001),('lote',64),('scheduler_passo',50)]:
            c=copy.deepcopy(self.c);c['treinamento'][campo]=valor
            with self.assertRaises(AssertionError):conferir_configuracao(c,self.ant)
        self.assertEqual(receita(self.c,'D')['treinamento']['weight_decay'],0)

    def test_transformacao_alvo_causalidade(self):
        df=dados_artificiais();dados,escalas=preparar_com_escalas(df,self.c)
        antigo,ea=preparar_com_escalas(df,self.ant)
        self.assertEqual(escalas,ea)
        temporal=organizar(dados,'dias')
        for fase,z in dados.items():
            for k in z:np.testing.assert_array_equal(z[k],antigo[fase][k])
            np.testing.assert_array_equal(temporal[fase]['x'].transpose(0,2,1),z['x'])
            ids=np.searchsorted(df.open_time,z['origens_ms'])
            np.testing.assert_array_equal(z['y'],df.close.to_numpy()[ids]/df.close.to_numpy()[ids-1]-1)
            self.assertTrue(np.all(z['fim_alvo_ms']>z['origens_ms']))
        alterado=df.copy();alterado.loc[alterado.open_time>=1704067200000,'close']*=2
        novo,en=preparar_com_escalas(alterado,self.c)
        self.assertEqual(en,escalas)
        np.testing.assert_array_equal(novo['treino']['x'],dados['treino']['x'])
        origem=int(dados['validacao']['origens_ms'][20])
        alterado=df.copy();alterado.loc[alterado.open_time>=origem,['open','high','low','close','volume']]*=1.5
        novo,_=preparar_com_escalas(alterado,self.c)
        np.testing.assert_array_equal(novo['validacao']['x'][:21],dados['validacao']['x'][:21])

    def test_prefixo_e_empate(self):
        h=[{'epoca':i,'taxa':.01*.5**((i-1)//100),'rmse_global_validacao_retorno':1. if i in (5,7) else 2.} for i in range(1,201)]
        self.assertEqual(selecionar_prefixo(h)['epoca'],5)
        with self.assertRaises(AssertionError):selecionar_prefixo(h[:199])
        h[100]['taxa']=.01
        with self.assertRaises(AssertionError):selecionar_prefixo(h)


if __name__ == '__main__':unittest.main()
