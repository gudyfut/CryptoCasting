import copy,math,unittest
import numpy as np
import pandas as pd
from infraestrutura.artefatos import ler_json,RAIZ
from simulacao_operacoes.previsoes import diarias,COLUNAS
from simulacao_operacoes.politicas import direcao
from simulacao_operacoes.futuros.mercado import Mercado
from simulacao_operacoes.futuros.simulador import simular
from simulacao_operacoes.futuros.auditoria import conferir
from simulacao_operacoes.futuros.contabilidade import LimiteMargem
from mercado_futuros.pipeline import validar_candles

def exemplo(fim=100.,sinal=.01,eventos=None):
    t=pd.Timestamp('2024-01-02',tz='UTC');ts=int(t.timestamp()*1000);n=1443
    tempos=np.arange(ts-60000,ts-60000+n*60000,60000)
    preco=np.r_[100.,100.,np.linspace(100.,fim,n-2)]
    q=pd.DataFrame({'open_time':tempos,'open':preco,'high':preco,'low':preco,'close':preco,'count':1,'volume':1.,'close_time':tempos+59999})
    funding=pd.DataFrame(eventos or [],columns=['fundingTime','fundingRate','markPrice'])
    m=Mercado(q,q.copy(),funding)
    p=pd.DataFrame([[1,t,t+pd.Timedelta(hours=24),100.,sinal]],columns=COLUNAS)
    cfg=ler_json(RAIZ/'configuracoes/futuros_001.json')
    return p,m,cfg

class Futuros(unittest.TestCase):
    def test_long_lucra_alta(self):
        p,m,c=exemplo(110);r,t,q,f=simular(p,m,c,'sinal24','bilateral','ideal')
        self.assertAlmostEqual(r['capital_final'],10950);self.assertEqual(r['compradas'],1);conferir(r,t,f,m,c)
    def test_short_sem_btc_lucra_queda(self):
        p,m,c=exemplo(90,-.01);r,t,q,f=simular(p,m,c,'sinal24','bilateral','ideal')
        self.assertAlmostEqual(r['capital_final'],10950);self.assertEqual(r['vendidas'],1);self.assertLess(t[0]['quantidade_btc'],0);conferir(r,t,f,m,c)
    def test_comprada_nao_abre_short(self):
        p,m,c=exemplo(90,-.01);r,*_=simular(p,m,c,'sinal24','comprada','base');self.assertEqual(r['capital_final'],10000);self.assertEqual(r['operacoes'],0)
    def test_custos_flat_long_e_short(self):
        for sinal in [.01,-.01]:
            p,m,c=exemplo(100,sinal);r,t,q,f=simular(p,m,c,'sinal24','bilateral','base');self.assertLess(r['capital_final'],10000)
            self.assertAlmostEqual(r['capital_final'],10000-r['comissoes']-r['slippage']);conferir(r,t,f,m,c)
    def test_funding_sinais_e_fronteiras(self):
        ts=int(pd.Timestamp('2024-01-02',tz='UTC').timestamp()*1000);ini=ts+60000;fim=ini+86400000
        ev=[[ini,.9,100.],[ini+28800001,.01,100.],[fim,.02,100.],[fim+1,.9,100.]]
        for sinal,esperado in [(.01,-285.),(-.01,285.)]:
            p,m,c=exemplo(100,sinal,ev);r,t,q,f=simular(p,m,c,'sinal24','bilateral','ideal');self.assertAlmostEqual(r['funding_liquido'],esperado);self.assertEqual(len(f),2);conferir(r,t,f,m,c)
    def test_funding_negativo_inverte_fluxo(self):
        ts=int(pd.Timestamp('2024-01-02T08:00:00Z').timestamp()*1000)
        p,m,c=exemplo(100,-.01,[[ts,-.01,100.]]);r,*_=simular(p,m,c,'sinal24','bilateral','ideal');self.assertAlmostEqual(r['funding_liquido'],-95.)
    def test_naive_caixa(self):
        p,m,c=exemplo(110,0.);r,*_=simular(p,m,c,'sinal24','bilateral','base');self.assertEqual(r['capital_final'],10000)
    def test_filtro_simetrico_e_fixo(self):
        _,_,c=exemplo();self.assertEqual(direcao(.0001,'filtrada24','bilateral',c),0)
        self.assertEqual(direcao(-.01,'filtrada24','bilateral',c),-1)
    def test_quantidade_nao_depende_do_futuro(self):
        p,m,c=exemplo(110);a=simular(p,m,c,'sinal24','bilateral','ideal')[1][0]['quantidade_btc']
        p,m,c=exemplo(90);b=simular(p,m,c,'sinal24','bilateral','ideal')[1][0]['quantidade_btc'];self.assertEqual(a,b)
    def test_proibe_coluna_alvo(self):
        p,m,c=exemplo();p['alvo']=0.
        with self.assertRaises(ValueError):diarias(p)
    def test_mark_extremo_bloqueia(self):
        p,m,c=exemplo(100,-.01);m.marca=m.marca.copy();m.marca[100,1]=300.
        with self.assertRaises(LimiteMargem):simular(p,m,c,'sinal24','bilateral','ideal')
    def test_auditoria_detecta_corrupcao(self):
        p,m,c=exemplo(110);r,t,q,f=simular(p,m,c,'sinal24','bilateral','base');t[0]['saldo_depois']+=10
        with self.assertRaises(AssertionError):conferir(r,t,f,m,c)
    def test_gap_rejeitado(self):
        p,m,c=exemplo();ts=1704153600000
        q=pd.DataFrame({'open_time':[ts,ts+120000],'close_time':[ts+59999,ts+179999],'open':[1.,1.],'high':[1.,1.],'low':[1.,1.],'close':[1.,1.],'volume':[1.,1.],'count':[1,1]})
        with self.assertRaises(AssertionError):validar_candles(q,ts,ts+180000,True)
    def test_nao_admite_alavancagem_extra(self):
        p,m,c=exemplo();c['alavancagem_maxima']=5
        with self.assertRaises(ValueError):simular(p,m,c,'sinal24','bilateral','ideal')
    def test_duas_datas_capital_causal_funding_e_reversao(self):
        p,m,c=exemplo();t=p.origem_utc.iloc[0];ts=int(t.timestamp()*1000)
        n=2883;tempos=np.arange(ts-60000,ts-60000+n*60000,60000);precos=np.linspace(100.,110.,n)
        q=pd.DataFrame({'open_time':tempos,'open':precos,'high':precos,'low':precos,'close':precos,'count':1})
        f=pd.DataFrame([[ts+86400000,.001,105.],[ts+86400001,.002,105.]],columns=['fundingTime','fundingRate','markPrice'])
        m=Mercado(q,q.copy(),f);p=pd.concat([p,p.assign(origem_utc=t+pd.Timedelta(days=1),destino_utc=t+pd.Timedelta(days=2),previsao=-.01)],ignore_index=True)
        r,tr,cur,ev=simular(p,m,c,'sinal24','bilateral','base');conferir(r,tr,ev,m,c)
        self.assertEqual([x['lado'] for x in tr],[1,-1]);self.assertNotEqual(tr[1]['capital_conhecido_no_sinal'],tr[1]['saldo_antes'])
        tr[1]['capital_conhecido_no_sinal']+=1
        with self.assertRaises(AssertionError):conferir(r,tr,ev,m,c)
    def test_gap_abertura_recusa_sem_redimensionar_com_futuro(self):
        p,m,c=exemplo();m.negocio=m.negocio.copy();m.negocio[2,0]=120.
        r,tr,*_=simular(p,m,c,'sinal24','bilateral','base');self.assertEqual(r['recusas'],1);self.assertEqual(tr[0]['quantidade_btc'],0.)
    def test_latencia_diferente_bloqueada(self):
        p,m,c=exemplo();c['latencia_minutos']=2
        with self.assertRaises(ValueError):simular(p,m,c,'sinal24','bilateral','base')
    def test_grade_exata_sem_treino(self):
        from experimentos.futuros.ciclo import grade
        _,_,c=exemplo();g=grade(c)
        self.assertEqual(len(g),804);self.assertEqual(sum(x['seed'] is not None for x in g),768)
        self.assertEqual(sum(x['seed'] is None for x in g),36);self.assertEqual(c['novos_treinamentos'],0)
    def test_fuso_nao_utc_rejeitado(self):
        p,m,c=exemplo();p['origem_utc']=p.origem_utc.dt.tz_convert('America/Sao_Paulo')
        with self.assertRaises(ValueError):diarias(p)

if __name__=='__main__':unittest.main()
