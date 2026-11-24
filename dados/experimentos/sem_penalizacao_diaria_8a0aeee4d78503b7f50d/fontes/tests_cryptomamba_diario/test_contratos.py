import copy
import unittest
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json
from entradas_modelo.cryptomamba_diario import preparar
from simulacao_operacoes.diaria_24h import simular,conferir,decidir,arredondar_preco


def config():return ler_json(RAIZ/'configuracoes/cryptomamba_diario_001.json')


def dados_artificiais():
    t=np.arange(1577836800000,1767225600000,86400000,dtype=np.int64)
    p=20000+np.arange(len(t))*4+100*np.sin(np.arange(len(t))/4)
    return pd.DataFrame({'open_time':t,'close_time':t+86399999,'open':p,'high':p+100,'low':p-100,'close':p+20,'volume':np.full(len(t),120000.)})


def mercado(preco=100.,funding=.0):
    t=np.arange(0,86460000+60000,60000,dtype=np.int64)
    p=np.full((len(t),4),preco)
    return {'tempo':t,'negocio':p.copy(),'marca':p.copy(),'funding_tempo':np.array([28800000,57600000,86400000]),
            'funding_taxa':np.full(3,funding),'funding_preco':np.full(3,preco)}


class Contratos(unittest.TestCase):
    def setUp(self):self.c=config()
    def test_contagem_eixos(self):
        d=preparar(dados_artificiais(),self.c)
        self.assertEqual({k:len(v['y']) for k,v in d.items()},{'treino':1446,'validacao':351,'teste':350})
        self.assertEqual(d['treino']['x'].shape,(1446,6,14))
    def test_representacao_publica(self):
        q=dados_artificiais();a=preparar(q,self.c)['treino']
        np.testing.assert_array_equal(a['x'][0,0],(q.open_time.to_numpy()[:14]/1000).astype('float32'))
        np.testing.assert_allclose(a['x'][0,5],q.volume.to_numpy()[:14]/1e9)
        np.testing.assert_array_equal(a['x'][0,4],q.close.to_numpy()[:14].astype('float32'))
        self.assertEqual(a['y'][0],q.close.iloc[14]);self.assertEqual(a['ultimo_close'][0],q.close.iloc[13])
    def test_futuro_nao_entra_na_janela(self):
        q=dados_artificiais();antes=preparar(q,self.c)['treino'];q.loc[14:,'close']*=2
        depois=preparar(q,self.c)['treino'];np.testing.assert_array_equal(antes['x'][0],depois['x'][0])
        self.assertNotEqual(antes['y'][0],depois['y'][0])
    def test_particoes_nao_compartilham_contextos(self):
        q=dados_artificiais();a=preparar(q,self.c)
        for f,(inicio,fim) in self.c['periodos'].items():
            ini=int(pd.Timestamp(inicio,tz='UTC').timestamp()*1000);end=int(pd.Timestamp(fim,tz='UTC').timestamp()*1000)
            self.assertEqual(a[f]['origens_ms'][0],ini+14*86400000)
            self.assertLess(a[f]['fim_alvo_ms'][-1],end)
    def test_lacuna_rejeitada(self):
        with self.assertRaises(AssertionError):preparar(dados_artificiais().drop(15),self.c)
    def test_naive_fica_caixa(self):
        r,v=simular([0],[100],[100],mercado(),self.c['operacoes'],self.c['cenarios']['base'])
        self.assertEqual(r['metricas']['operacoes'],0);self.assertEqual(r['metricas']['retorno_liquido'],0);conferir(r,v,self.c['operacoes'])
    def test_lado_custo_e_prazo(self):
        for sinal,lado in [(110,1),(90,-1)]:
            r,v=simular([0],[sinal],[100],mercado(),self.c['operacoes'],self.c['cenarios']['base'])
            o=r['operacoes'][0];self.assertEqual(o['lado'],lado);self.assertLess(o['pnl_liquido'],0)
            self.assertEqual(o['entrada_ms'],60000);self.assertEqual(o['saida_ms'],86460000);conferir(r,v,self.c['operacoes'])
    def test_funding_sinal(self):
        regras=copy.deepcopy(self.c['operacoes']);regras.update(comissao_por_lado=0.,slippage_por_lado=0.)
        for sinal,lado in [(110,1),(90,-1)]:
            r,v=simular([0],[sinal],[100],mercado(funding=.001),regras,self.c['cenarios']['base'])
            self.assertAlmostEqual(r['metricas']['funding'],-lado*95*100*.003);conferir(r,v,regras)
    def test_custos_estressados_nao_mudam_direcao(self):
        a,_=simular([0],[110],[100],mercado(),self.c['operacoes'],self.c['cenarios']['base'])
        b,_=simular([0],[110],[100],mercado(),self.c['operacoes'],self.c['cenarios']['slippage3'])
        self.assertEqual(a['operacoes'][0]['lado'],b['operacoes'][0]['lado'])
        self.assertLess(b['metricas']['capital_final'],a['metricas']['capital_final'])
    def test_drawdown_intradiario_nao_e_apenas_terminal(self):
        m=mercado();m['marca'][200,2]=90
        r,v=simular([0],[110],[100],m,self.c['operacoes'],self.c['cenarios']['base'])
        self.assertGreater(r['metricas']['drawdown_maximo'],.09);conferir(r,v,self.c['operacoes'])
    def test_buffer_nao_oculta_insolvencia(self):
        m=mercado();m['marca'][200,1]=250
        with self.assertRaisesRegex(ValueError,'prudencial'):simular([0],[90],[100],m,self.c['operacoes'],self.c['cenarios']['base'])
    def test_preco_invalido_nao_produz_short(self):
        self.assertEqual(decidir(-100,100,.002),0)
        with self.assertRaises(ValueError):decidir(float('nan'),100,.002)
    def test_arredondamento_adverso(self):
        self.assertGreaterEqual(arredondar_preco(100.025,1,.1),100.025)
        self.assertLessEqual(arredondar_preco(100.025,-1,.1),100.025)
    def test_ledger_detecta_adulteracao(self):
        r,v=simular([0],[110],[100],mercado(),self.c['operacoes'],self.c['cenarios']['base']);r['operacoes'][0]['pnl_liquido']+=1
        with self.assertRaises(AssertionError):conferir(r,v,self.c['operacoes'])


if __name__=='__main__':unittest.main()
