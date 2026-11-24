import copy
import math
import unittest
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json
from simulacao_operacoes.previsoes import COLUNAS
from simulacao_operacoes.futuros.mercado import Mercado
from simulacao_operacoes.futuros.contabilidade import LimiteMargem
from simulacao_operacoes.revisada.conta import Conta
from simulacao_operacoes.revisada.regras import quantizar,aumenta_risco,separar_ordem
from simulacao_operacoes.revisada.politica import ordem_planejada
from simulacao_operacoes.revisada.simulador import simular
from simulacao_operacoes.revisada.auditoria import conferir


def exemplo(sinais=(.01,.01,.01),ultimo=110.,funding=None):
    t=pd.Timestamp('2024-01-01T00:00:00Z');inicio=int(t.timestamp()*1000)
    n=len(sinais)*1440+3;tempos=inicio-60000+np.arange(n)*60000;precos=np.linspace(100.,ultimo,n)
    q=pd.DataFrame({'open_time':tempos,'open':precos,'high':precos,'low':precos,'close':precos,'count':1})
    eventos=pd.DataFrame(funding or [],columns=['fundingTime','fundingRate','markPrice'])
    m=Mercado(q,q.copy(),eventos)
    p=pd.DataFrame([[i,t+pd.Timedelta(days=i),t+pd.Timedelta(days=i+1),100.,s] for i,s in enumerate(sinais)],columns=COLUNAS)
    c=ler_json(RAIZ/'configuracoes/revisao_operacional_001.json')
    for f in c['filtros'].values():f['maximo_btc']=1000.
    return p,m,c


class Execucao(unittest.TestCase):
    def rodar(self,p,m,c,braco='futuro',politica='smart',cenario='base',benchmark=None):
        r,o,e,cur,d=simular(p,m,c,politica,braco,cenario,benchmark)
        conferir(r,o,e,m,c,p)
        return r,o,e,cur,d

    def test_spot_comissao_recebida(self):
        a=Conta(1000.,False);a.negociar(1.,100.,.001)
        self.assertEqual(a.saldo,900.);self.assertEqual(a.quantidade,.999)
        a.negociar(-.999,100.,.001)
        self.assertAlmostEqual(a.saldo,999.8001)

    def test_colateral_nao_recebe_nocional_short(self):
        a=Conta(1000.,True);a.negociar(-2.,100.,0)
        self.assertEqual(a.saldo,1000.);a.negociar(1.,90.,0,True)
        self.assertEqual(a.saldo,1010.);self.assertEqual(a.preco_medio,100.)

    def test_reversao_contabil(self):
        a=Conta(1000.,True);a.negociar(2.,100.,0);a.negociar(-3.,110.,0)
        self.assertEqual(a.saldo,1020.);self.assertEqual(a.preco_medio,110.);self.assertEqual(a.quantidade,-1.)

    def test_reduce_only_nao_inverte(self):
        a=Conta(1000.,True,1.,100.)
        with self.assertRaises(ValueError):a.negociar(-2.,100.,0,True)
        with self.assertRaises(ValueError):a.negociar(1.,100.,0,True)

    def test_spot_nao_vende_sem_saldo(self):
        with self.assertRaises(ValueError):Conta(1000.,False).negociar(-1.,100.,0)

    def test_dados_invalidos(self):
        for preco,taxa in [(0,0),(100,-.01),(100,math.nan),(math.inf,0)]:
            with self.assertRaises(ValueError):Conta(1000.,True).negociar(1.,preco,taxa)

    def test_quantizacao_conservadora(self):
        self.assertEqual(quantizar(.000019,.00001),.00001)
        self.assertEqual(quantizar(-.0019,.001),-.001)
        with self.assertRaises(ValueError):quantizar(math.nan,.001)

    def test_reversao_menor_tambem_exige_margem(self):
        self.assertTrue(aumenta_risco(2.,-1.));self.assertFalse(aumenta_risco(2.,1.))
        self.assertEqual(separar_ordem(-3.,2.,True),[(-2.,True),(-1.,False)])

    def test_equivalencia_sem_custos_mesmos_filtros(self):
        p,m,c=exemplo((.02,-.005,.01,-.02));c['custos']['base']={k:0. for k in c['custos']['base']}
        c['filtros']['spot']=copy.deepcopy(c['filtros']['futuro'])
        for pol in c['politicas']:
            a=self.rodar(p,m,c,'spot',pol);b=self.rodar(p,m,c,'futuro',pol)
            self.assertAlmostEqual(a[0]['capital_final'],b[0]['capital_final'],places=7)

    def test_reducao_comum_e_abertura_separada(self):
        _,_,c=exemplo();a=ordem_planejada(-.002,'direcional',10000,100,50,False,c,True)
        b=ordem_planejada(-.002,'direcional',10000,100,50,True,c,True)
        self.assertEqual(a,-50.);self.assertEqual(separar_ordem(b,50,True)[0],(-50.,True))

    def test_filtro_nao_bloqueia_saida(self):
        p,m,c=exemplo((.02,-.0001,0),100.)
        r,o,*_=self.rodar(p,m,c,'futuro_bilateral','direcional_filtrada')
        dias=[x for x in o if x['motivo']=='decisao']
        self.assertEqual(dias[1]['depois']['quantidade'],0.)
        self.assertEqual(dias[2]['delta_executado'],0.)

    def test_sinal_neutro_mantem(self):
        p,m,c=exemplo((.02,0.,0.),100.);r,o,*_=self.rodar(p,m,c)
        self.assertGreater(o[1]['depois']['quantidade'],0.);self.assertEqual(o[1]['delta_planejado'],0.)

    def test_funding_antes_da_reversao(self):
        ts=1704067200000
        p,m,c=exemplo((.02,-.02),100.,[[ts+60000,.9,100.],[ts+86460000,.001,100.],[ts+90000000,.001,100.]])
        r,o,e,*_=self.rodar(p,m,c,'futuro_bilateral','direcional')
        self.assertEqual(len(e),2);self.assertGreater(e[0]['btc'],0.);self.assertLess(e[1]['btc'],0.)

    def test_funding_negativo_short_paga(self):
        p,m,c=exemplo((-.02,),100.,[[1704096000000,-.001,100.]])
        r,*_=self.rodar(p,m,c,'futuro_bilateral');self.assertLess(r['funding'],0)

    def test_futuro_pequeno_pode_fechar(self):
        p,m,c=exemplo((.02,-.02),100.);c['filtros']['futuro']['minimo']=10000
        # Ordem de abertura abaixo do mínimo é recusada, redução não é.
        r,o,*_=self.rodar(p,m,c);self.assertEqual(r['ordens'],0)
        p,m,c=exemplo((.02,-.00001),100.)
        r,o,*_=self.rodar(p,m,c)
        pequena=[x for x in o if x['reduce_only'] and 0<abs(x['delta_executado'])*x['preco_conhecido']<100]
        self.assertTrue(pequena)

    def test_residuo_spot_nao_vende_fracao_invalida(self):
        p,m,c=exemplo((.02,),100.)
        r,o,*_=self.rodar(p,m,c,'spot');self.assertGreaterEqual(r['btc_residual'],0.)
        self.assertLess(r['residuo_usdt'],10.)

    def test_gap_recusa_sem_redimensionar(self):
        for b in ['spot','futuro']:
            p,m,c=exemplo((1.,),100.);m.negocio=m.negocio.copy();m.marca=m.marca.copy()
            m.negocio[2,:4]=120.;m.marca[2,:4]=120.
            r,o,*_=self.rodar(p,m,c,b)
            self.assertEqual(o[0]['delta_planejado'],95.);self.assertEqual(o[0]['delta_executado'],0.)

    def test_reversao_com_gap_fecha_mas_nao_abre_sem_margem(self):
        p,m,c=exemplo((-1.,1.),100.);m.negocio=m.negocio.copy();m.marca=m.marca.copy()
        m.negocio[1442,:4]=150.;m.marca[1442,:4]=150.
        r,o,*_=self.rodar(p,m,c,'futuro_bilateral','direcional')
        segunda=[x for x in o if x['parte']==1]
        self.assertEqual(len(segunda),1);self.assertEqual(segunda[0]['status'],'recusada_exposicao_apos_gap')
        self.assertEqual(segunda[0]['antes']['quantidade'],0.)

    def test_lote_nao_perde_tick_por_float_ao_fechar(self):
        a=Conta(1000.,True);a.negociar(.123,100.,0);a.negociar(-.022,100.,0,True)
        self.assertEqual(quantizar(-a.quantidade,.001),-.101)

    def test_causalidade(self):
        p,m,c=exemplo(ultimo=90.);a=self.rodar(p,m,c)[1][0]['delta_decisao']
        p,m,c=exemplo(ultimo=110.);b=self.rodar(p,m,c)[1][0]['delta_decisao']
        self.assertEqual(a,b)

    def test_alvo_futuro_proibido(self):
        p,m,c=exemplo();p['alvo']=0
        with self.assertRaises(ValueError):simular(p,m,c,'smart','spot','base')

    def test_auditor_rejeita_corromper_plano_saldo_fee(self):
        p,m,c=exemplo();r,o,e,*_=self.rodar(p,m,c)
        for campo in ['delta_decisao','comissao']:
            copia=copy.deepcopy(o);copia[0][campo]+=1
            with self.assertRaises(AssertionError):conferir(r,copia,e,m,c,p)
        copia=copy.deepcopy(o);copia[0]['depois']['saldo']+=1
        with self.assertRaises(AssertionError):conferir(r,copia,e,m,c,p)

    def test_margem_intraminuto_bloqueia(self):
        p,m,c=exemplo((-.02,));m.marca=m.marca.copy();m.marca[10,1]=300.
        with self.assertRaises(LimiteMargem):simular(p,m,c,'smart','futuro_bilateral','base')

    def test_caixa_e_comprar_manter(self):
        p,m,c=exemplo();r,*_=self.rodar(p,m,c,benchmark='caixa');self.assertEqual(r['capital_final'],10000.)
        r,*_=self.rodar(p,m,c,benchmark='comprar_manter');self.assertEqual(r['ordens'],2)

    def test_sem_giro_diario_forcado(self):
        p,m,c=exemplo((1.,1.,1.),100.);r,*_=self.rodar(p,m,c);self.assertEqual(r['ordens'],2)

    def test_maior_slippage_custa_mais_no_roundtrip(self):
        p,m,c=exemplo((1.,),100.)
        a=self.rodar(p,m,c);b=self.rodar(p,m,c,cenario='estresse')
        self.assertLess(b[0]['capital_final'],a[0]['capital_final'])

    def test_grade_sem_treino(self):
        from experimentos.revisao_operacional.ciclo import grade
        _,_,c=exemplo();g=grade(c)
        self.assertEqual(len(g),1200);self.assertEqual(sum(x['seed'] is not None for x in g),1152)
        self.assertEqual(c['novos_treinamentos'],0)

if __name__=='__main__':unittest.main()
