import unittest
import numpy as np
from simulador import simular
from auditoria import conferir


class Continuidade(unittest.TestCase):
    def base(self,n=3):
        x=np.full((n*1440+2,4),100.)
        m={'tempo':np.arange(len(x),dtype=np.int64)*60000,'negocio':x,'marca':x.copy(),
            'funding_tempo':np.array([60000,1441*60000,2881*60000]),'funding_taxa':np.array([.001]*3),'funding_preco':np.array([100.]*3)}
        c=dict(capital_inicial=10000.,fracao_nocional=.95,latencia_minutos=1,comissao_por_lado=0.,slippage_por_lado=0.,tick_preco=.01,passo_quantidade=.001,nocional_minimo=1.,buffer_prudencial=.025,filtro_retorno_absoluto=.002)
        return m,c,np.arange(n,dtype=np.int64)*86400000
    def rodar(self,m,c,t,prev,modo,agenda=None):
        r,v=simular(t,np.array(prev),np.full(len(t),100.),m,c,modo,agenda=agenda)
        conferir(r,v,m,c,modo,t,np.array(prev),np.full(len(t),100.),None,agenda)
        return r,v
    def test_continuidade_sem_fees_sem_funding(self):
        m,c,t=self.base();m['funding_taxa']*=0
        a,_=self.rodar(m,c,t,[101]*3,'diaria');b,_=self.rodar(m,c,t,[101]*3,'liquida')
        self.assertEqual(a['metricas']['ordens'],6);self.assertEqual(b['metricas']['ordens'],2);self.assertEqual(b['metricas']['capital_final'],10000)
    def test_zerar_ao_sinal_caixa(self):
        m,c,t=self.base();r,_=self.rodar(m,c,t,[101,100,100],'liquida')
        self.assertEqual(r['metricas']['dias_posicionado'],1);self.assertEqual(r['ordens'][-1]['tempo_ms'],86460000)
    def test_inversao_nao_financia_venda(self):
        m,c,t=self.base();m['funding_taxa']*=0;r,_=self.rodar(m,c,t,[101,99,99],'liquida')
        self.assertEqual(r['metricas']['capital_final'],10000);self.assertEqual(r['metricas']['dias_vendido'],2)
    def test_funding_em_fronteira_sem_duplicacao(self):
        m,c,t=self.base();r,_=self.rodar(m,c,t,[101,101,101],'liquida')
        self.assertEqual(len(r['funding']),3);self.assertEqual(len({e['tempo_ms'] for e in r['funding']}),3)
    def test_agenda_isola_custo(self):
        m,c,t=self.base();c['comissao_por_lado']=.0005;c['slippage_por_lado']=.0001
        a,_=self.rodar(m,c,t,[101]*3,'diaria');agenda=[d['alvo_lotes'] for d in a['dias']]
        b,_=self.rodar(m,c,t,[101]*3,'agenda',agenda)
        self.assertLess(b['metricas']['comissoes'],a['metricas']['comissoes'])
        self.assertEqual(a['metricas']['pnl_movimento_contrato'],b['metricas']['pnl_movimento_contrato'])
        self.assertEqual(a['metricas']['funding'],b['metricas']['funding'])
        ganho=b['metricas']['capital_final']-a['metricas']['capital_final']
        poupado=a['metricas']['comissoes']+a['metricas']['custo_slippage_ticks']-b['metricas']['comissoes']-b['metricas']['custo_slippage_ticks']
        self.assertAlmostEqual(ganho,poupado,places=7)
    def test_limite_sinal_nao_acessa_futuro(self):
        m,c,t=self.base();m['funding_taxa']*=0
        r,_=self.rodar(m,c,t,[101]*3,'liquida');m['negocio'][-1]*=2;m['marca'][-1]*=2
        s,_=self.rodar(m,c,t,[101]*3,'liquida')
        self.assertEqual([(d['lado_sinal'],d['alvo_lotes']) for d in r['dias']],[(d['lado_sinal'],d['alvo_lotes']) for d in s['dias']])
        self.assertNotEqual(r['metricas']['capital_final'],s['metricas']['capital_final'])
    def test_sem_sinal_sem_ordens(self):
        m,c,t=self.base();r,_=self.rodar(m,c,t,[100]*3,'liquida')
        self.assertEqual(r['metricas']['ordens'],0);self.assertEqual(r['metricas']['capital_final'],10000)
    def test_marcacao_nao_contrato_para_risco(self):
        m,c,t=self.base();m['funding_taxa']*=0;m['marca'][100,2]=90
        r,_=self.rodar(m,c,t,[101]*3,'liquida');self.assertGreater(r['metricas']['drawdown_maximo'],.09)
    def test_reproducao_por_quantidades_e_equity(self):
        m,c,t=self.base();m['funding_taxa']*=0;m['negocio'][1441:,0]=105.;m['negocio'][1441:,1:]=105.;m['marca'][1441:]=105.
        for modo in ['diaria','liquida']:self.rodar(m,c,t,[101]*3,modo)


if __name__=='__main__':unittest.main(verbosity=2)
