import copy
import unittest
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json
from simulacao_operacoes.previsoes import COLUNAS
from simulacao_operacoes.futuros.mercado import Mercado
from simulacao_operacoes.futuros.contabilidade import LimiteMargem
from simulacao_operacoes.smart.politica import fracao,ordem_planejada
from simulacao_operacoes.smart.conta import Conta
from simulacao_operacoes.smart.simulador import simular
from simulacao_operacoes.smart.auditoria import conferir


def exemplo(sinais=(.01,.01,.01),ultimo=110.,funding=None):
    t=pd.Timestamp('2024-01-01T00:00:00Z');inicio=int(t.timestamp()*1000)
    n=len(sinais)*1440+3;tempos=inicio-60000+np.arange(n)*60000;precos=np.linspace(100.,ultimo,n)
    q=pd.DataFrame({'open_time':tempos,'open':precos,'high':precos,'low':precos,'close':precos,'count':1})
    eventos=pd.DataFrame(funding or [],columns=['fundingTime','fundingRate','markPrice'])
    m=Mercado(q,q.copy(),eventos)
    p=pd.DataFrame([[i,t+pd.Timedelta(days=i),t+pd.Timedelta(days=i+1),100.,s] for i,s in enumerate(sinais)],columns=COLUNAS)
    c=ler_json(RAIZ/'configuracoes/smart_mercados_001.json')
    return p,m,c


class Smart(unittest.TestCase):
    def rodar(self,p,m,c,braco='futuro',politica='smart',cenario='iguais',benchmark=None):
        r,o,e,cur,d=simular(p,m,c,politica,braco,cenario,benchmark);conferir(r,o,e,m,c);return r,o,e,cur,d

    def test_spot_futuro_identicos_sem_funding(self):
        p,m,c=exemplo((.02,-.005,.01,-.02))
        a=self.rodar(p,m,c,'spot');b=self.rodar(p,m,c,'futuro_sem_funding')
        for k in ['capital_final','comissoes','slippage','drawdown','exposicao_media']:self.assertAlmostEqual(a[0][k],b[0][k],places=8)
        np.testing.assert_allclose(a[3].patrimonio,b[3].patrimonio,rtol=0,atol=1e-8)

    def test_sinal_igual_nao_zera_e_reabre(self):
        p,m,c=exemplo((1.,1.,1.),100.)
        r,o,*_=self.rodar(p,m,c)
        self.assertEqual(r['ordens'],2)
        self.assertEqual(o[1]['delta_executado'],0.)
        self.assertEqual(o[2]['delta_executado'],0.)

    def test_neutro_mantem_posicao(self):
        p,m,c=exemplo((.02,0.,0.));r,o,*_=self.rodar(p,m,c)
        self.assertEqual(o[1]['delta_planejado'],0.)
        self.assertGreater(o[1]['depois']['quantidade'],0.)

    def test_filtro_ignora_pequeno_sem_liquidar(self):
        p,m,c=exemplo((.02,.0001,-.0001));r,o,*_=self.rodar(p,m,c,politica='smart_filtrada')
        self.assertEqual(o[1]['delta_executado'],0.);self.assertEqual(o[2]['delta_executado'],0.)

    def test_filtro_simetrico(self):
        _,_,c=exemplo();self.assertEqual(fracao(.001,'smart_filtrada',c),0.);self.assertEqual(fracao(-.001,'smart_filtrada',c),0.)
        self.assertGreater(fracao(.004,'smart_filtrada',c),0);self.assertLess(fracao(-.004,'smart_filtrada',c),0)

    def test_short_somente_no_bilateral(self):
        p,m,c=exemplo((-.02,-.02),90.)
        a=self.rodar(p,m,c,'spot');b=self.rodar(p,m,c,'futuro_bilateral')
        self.assertEqual(a[0]['ordens'],0);self.assertGreater(b[0]['capital_final'],10000)
        self.assertLess(b[1][0]['depois']['quantidade'],0)

    def test_funding_historico_e_contrafactual(self):
        ts=1704067200000
        p,m,c=exemplo((.02,.02),100.,[[ts+60000,.9,100.],[ts+8*3600000,.001,100.],[ts+24*3600000,.001,100.]])
        a=self.rodar(p,m,c,'futuro');b=self.rodar(p,m,c,'futuro_sem_funding')
        self.assertLess(a[0]['funding'],0);self.assertEqual(b[0]['funding'],0);self.assertEqual(len(a[2]),2)

    def test_vendido_recebe_funding_positivo(self):
        p,m,c=exemplo((-.02,),100.,[[1704096000000,.001,100.]])
        r,*_=self.rodar(p,m,c,'futuro_bilateral');self.assertGreater(r['funding'],0)

    def test_preco_futuro_nao_muda_ordem_inicial(self):
        p,m,c=exemplo(ultimo=110);a=self.rodar(p,m,c)[1][0]['delta_planejado']
        p,m,c=exemplo(ultimo=90);b=self.rodar(p,m,c)[1][0]['delta_planejado'];self.assertEqual(a,b)

    def test_reversao_realiza_apenas_parte_encerrada(self):
        a=Conta(10000.,True);a.negociar(2.,100.,0);self.assertEqual(a.saldo,10000.)
        a.negociar(-3.,110.,0);self.assertEqual(a.saldo,10020.);self.assertEqual(a.quantidade,-1.);self.assertEqual(a.preco_medio,110.)
        a.negociar(1.,90.,0);self.assertEqual(a.saldo,10040.)

    def test_conta_spot_nao_vende_sem_moeda(self):
        with self.assertRaises(ValueError):Conta(10000.,False).negociar(-1.,100.,0)

    def test_margem_bloqueia(self):
        p,m,c=exemplo((-.02,));m.marca=m.marca.copy();m.marca[10,1]=300.
        with self.assertRaises(LimiteMargem):simular(p,m,c,'smart','futuro_bilateral','iguais')

    def test_auditoria_rejeita_corrupcao(self):
        p,m,c=exemplo();r,o,e,_,_=self.rodar(p,m,c);o[0]['depois']['saldo']+=1
        with self.assertRaises(AssertionError):conferir(r,o,e,m,c)

    def test_caixa_e_comprar_manter(self):
        p,m,c=exemplo();r,*_=self.rodar(p,m,c,benchmark='caixa');self.assertEqual(r['capital_final'],10000.)
        r,*_=self.rodar(p,m,c,benchmark='comprar_manter');self.assertEqual(r['ordens'],2)

    def test_alvo_futuro_proibido(self):
        p,m,c=exemplo();p['alvo']=0
        with self.assertRaises(ValueError):simular(p,m,c,'smart','spot','iguais')

    def test_grade_fixa_sem_treino(self):
        from experimentos.smart_mercados.ciclo import grade
        _,_,c=exemplo();g=grade(c)
        self.assertEqual(len(g),1632);self.assertEqual(sum(x['seed'] is not None for x in g),1536)
        self.assertEqual(c['novos_treinamentos'],0)

    def test_funding_negativo_custa_para_vendido(self):
        p,m,c=exemplo((-.02,),100.,[[1704096000000,-.001,100.]])
        r,*_=self.rodar(p,m,c,'futuro_bilateral');self.assertLess(r['funding'],0)

    def test_gap_nao_redimensiona_ordem(self):
        p,m,c=exemplo((1.,),100.);m.negocio=m.negocio.copy();m.marca=m.marca.copy()
        m.negocio[2,:4]=120.;m.marca[2,:4]=120.
        for braco in ['spot','futuro']:
            r,o,*_=self.rodar(p,m,c,braco)
            self.assertEqual(o[0]['delta_planejado'],95.)
            self.assertEqual(o[0]['delta_executado'],0.)
            self.assertEqual(r['recusas'],1)

if __name__=='__main__':unittest.main()
