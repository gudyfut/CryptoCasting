import copy
import unittest
import numpy as np
from infraestrutura.artefatos import RAIZ,ler_json
from tests_alvo_retorno_diario.test_contratos import AlvoRetorno,ContratosHerdados,IsolamentoHerdado
from tests_cryptomamba_diario.test_contratos import dados_artificiais
from experimentos.alvo_retorno_diario.entradas import preparar as referencia
from entradas_modelo.padronizacao_diaria import preparar_com_escalas,candles_unicos,transformar,configurar_referencia
from experimentos.padronizacao_diaria.contratos import conferir_configuracao


class Padronizacao(unittest.TestCase):
    def setUp(self):
        self.c=ler_json(RAIZ/'configuracoes/padronizacao_diaria_001.json')
        self.df=dados_artificiais()
        self.df['volume']=120000+np.arange(len(self.df))*5

    def test_apenas_padronizacao(self):
        ref=ler_json(RAIZ/'configuracoes/alvo_retorno_diario_001.json')
        self.assertTrue(conferir_configuracao(self.c,ref))
        c=copy.deepcopy(self.c);c['treinamento']['taxa']/=10
        with self.assertRaises(AssertionError):conferir_configuracao(c,ref)

    def test_momentos_sem_peso_de_sobreposicao(self):
        dados,e=preparar_com_escalas(self.df,self.c)
        q=self.df[self.df.open_time<1704067200000].iloc[:-2]
        u=np.column_stack((q.open_time/1000,q[['open','high','low','close']].to_numpy(),q.volume/1e9)).astype('float32').astype('float64')
        np.testing.assert_allclose(e['media'],u.mean(axis=0),rtol=1e-14)
        np.testing.assert_allclose(e['escala'],u.std(axis=0),rtol=1e-14)
        z=candles_unicos(dados['treino']['x'])
        np.testing.assert_allclose(z.mean(axis=0),0,atol=1e-7)
        np.testing.assert_allclose(z.std(axis=0),1,atol=1e-7)
        self.assertEqual(e['candles_unicos'],1459)

    def test_populacoes_alvos_inversao(self):
        a=referencia(self.df,configurar_referencia(self.c));b,e=preparar_com_escalas(self.df,self.c)
        for fase in a:
            for k in a[fase]:
                if k!='x':np.testing.assert_array_equal(a[fase][k],b[fase][k])
            x=b[fase]['x'];self.assertEqual(x.dtype,np.float32);self.assertEqual(x.shape,a[fase]['x'].shape)
            recuperado=x.astype(float)*np.array(e['escala'])[None,:,None]+np.array(e['media'])[None,:,None]
            np.testing.assert_allclose(recuperado,a[fase]['x'],rtol=2e-7,atol=1e-6)

    def test_validacao_teste_nao_ajustam_escala(self):
        a,e=preparar_com_escalas(self.df,self.c)
        q=self.df.copy();q.loc[q.open_time>=1704067200000,['open','high','low','close','volume']]*=50
        b,f=preparar_com_escalas(q,self.c)
        self.assertEqual(e,f);np.testing.assert_array_equal(a['treino']['x'],b['treino']['x'])
        self.assertGreater(abs(b['teste']['x']).max(),10) # Sem clipping ou reajuste no teste.

    def test_alterar_futuro_nao_altera_janela_validacao(self):
        a,e=preparar_com_escalas(self.df,self.c);q=self.df.copy()
        q.loc[q.open_time>=a['validacao']['origens_ms'][0],['open','high','low','close','volume']]*=2
        b,f=preparar_com_escalas(q,self.c)
        self.assertEqual(e,f);np.testing.assert_array_equal(a['validacao']['x'][0],b['validacao']['x'][0])
        self.assertNotEqual(a['validacao']['y'][0],b['validacao']['y'][0])

    def test_canal_constante_e_nulos(self):
        a,e=preparar_com_escalas(dados_artificiais(),self.c)
        self.assertEqual(e['escala'][5],1);np.testing.assert_array_equal(a['treino']['x'][:,5],0)
        x=a['treino']['x'].copy();x[0,0,0]=np.nan
        with self.assertRaises(ValueError):transformar(x,e)


if __name__=='__main__':unittest.main()
