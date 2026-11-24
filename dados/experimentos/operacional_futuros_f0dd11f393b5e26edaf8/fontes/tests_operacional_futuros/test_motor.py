import unittest
import numpy as np
from simulacao_operacoes.operacional.mercado import Mercado
from simulacao_operacoes.operacional.motor import (trajeto,preencher,Politica,simular,escores)
from simulacao_operacoes.operacional.auditoria import conferir


def mercado(n=5000):
    p=np.tile([100.,100.1,99.9,100.],(n,1))
    return Mercado(np.arange(n,dtype=np.int64)*60000,p,p.copy(),np.zeros(n),
        np.full(n,np.nan),np.zeros(n,bool),np.zeros(n,bool),np.zeros(n,np.int64),np.full(n,8.))


class Motor(unittest.TestCase):
    def test_custos_duas_pernas_e_sem_direcao_magica(self):
        m=mercado()
        for lado in (1,-1):
            t=trajeto(m,1,lado,.05,1.5)
            self.assertLess(t['payoff'],0)
            esperado=(lado*(t['preco_saida']-t['preco_entrada'])-.0005*(t['preco_entrada']+t['preco_saida']))/t['preco_entrada']
            self.assertAlmostEqual(t['payoff'],esperado)
            self.assertEqual(t['saida'],1441)

    def test_ambas_barreiras_stop_primeiro(self):
        m=mercado();m.negociacao[5]=[100,120,80,100]
        t=trajeto(m,1,1,.01,1.5)
        self.assertEqual(t['motivo'],'stop');self.assertTrue(t['dupla_barreira'])

    def test_gap_stop_adverso(self):
        m=mercado();m.negociacao[5]=[90,91,89,90]
        t=trajeto(m,1,1,.01,1.5)
        self.assertLessEqual(t['preco_saida'],90)

    def test_funding_ausente_e_ambiguo(self):
        m=mercado();m.funding_evento[5]=True;m.funding_taxa[5]=.01
        m.eventos=np.array([5]);m.marca[5]=[100,110,90,100]
        t=trajeto(m,1,1,.05,1.5)
        self.assertAlmostEqual(t['funding_por_btc'],-1.1)
        t=trajeto(m,1,-1,.05,1.5)
        self.assertAlmostEqual(t['funding_por_btc'],.9)
        m.negociacao[5]=[100,120,80,100]
        t=trajeto(m,1,-1,.05,1.5)
        self.assertEqual(t['funding_por_btc'],0)

    def test_publicacao_funding_causal(self):
        m=mercado();m.eventos=np.array([5]);m.funding_taxa[5]=.01
        m.funding_publicado[5]=360003
        self.assertEqual(m.estimativa_funding(360000),0)
        self.assertAlmostEqual(m.estimativa_funding(360003),.03)

    def test_sem_sinal_sem_operacao(self):
        m=mercado();o=np.arange(60,1200,60)*60000
        r=simular(m,o,np.zeros((len(o),1)),np.full(len(o),.1),'terminal',Politica(),0,5000*60000)
        self.assertEqual(r['metricas']['capital_final'],10000)
        self.assertEqual(r['metricas']['operacoes'],0)
        self.assertIsNone(r['metricas']['calmar'])

    def test_carteira_e_conferencia_independente(self):
        m=mercado();o=np.arange(60,3000,60)*60000
        r=simular(m,o,np.full((len(o),1),.1),np.full(len(o),.1),'terminal',Politica(),0,5000*60000)
        self.assertGreater(r['metricas']['operacoes'],0)
        self.assertLess(r['metricas']['capital_final'],10000)
        self.assertTrue(conferir(r,m,0,5000*60000)['conferido'])
        r['operacoes'][0]['pnl_liquido']+=1
        with self.assertRaises(ValueError): conferir(r,m,0,5000*60000)

    def test_futuro_nao_muda_sinal_ou_tamanho(self):
        m=mercado();o=np.array([60*60000]);p=np.array([[.1]])
        a=simular(m,o,p,np.array([.1]),'terminal',Politica(),0,5000*60000)
        m.negociacao[100:]=[105,106,104,105];m.marca[100:]=m.negociacao[100:]
        b=simular(m,o,p,np.array([.1]),'terminal',Politica(),0,5000*60000)
        for k in ['lado','quantidade','preco_entrada','entrada_ms']:
            self.assertEqual(a['operacoes'][0][k],b['operacoes'][0][k])

    def test_payoff_nao_desconta_custo_duas_vezes(self):
        np.testing.assert_array_equal(escores([.01,-.02],'payoff',.1,.001),[.01,-.02])
        np.testing.assert_array_equal(escores([.01],'terminal',0,.001),escores([.01],'terminal',0,.0005))

    def test_prudencial_preserva_perda(self):
        m=mercado();o=np.array([60*60000]);m.marca[80]=[100,3000,99,100]
        r=simular(m,o,np.array([[-.1]]),np.array([.1]),'terminal',Politica(),0,5000*60000)
        self.assertTrue(r['metricas']['saida_prudencial'])
        self.assertTrue(conferir(r,m,0,5000*60000)['conferido'])

    def test_passivo_retido_e_tendencia_inverte(self):
        m=mercado();o=np.arange(60,3000,60)*60000
        p=np.full((len(o),1),1.);p[20:]=-1
        kwargs=dict(m=m,origens=o,previsoes=p,sigmas=np.full(len(o),.1),familia='terminal',
            politica=Politica(),inicio_ms=0,fim_ms=5000*60000)
        a=simular(**kwargs,baseline='comprado')
        self.assertEqual(len(a['operacoes']),1)
        b=simular(**kwargs,baseline='tendencia')
        self.assertEqual(len(b['operacoes']),2)
        self.assertEqual(b['operacoes'][0]['saida_ms'],b['operacoes'][1]['entrada_ms'])
        self.assertTrue(conferir(b,m,0,5000*60000)['conferido'])


if __name__=='__main__': unittest.main()
