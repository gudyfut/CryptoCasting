import ast
import math
import unittest
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json
from backtest_carteira.politicas import decisao
from backtest_carteira.simulador import simular,COLUNAS
from backtest_carteira.auditoria import conferir


def sintetico(retornos=(.003,.003),capital=10000.):
    c=ler_json(RAIZ/'configuracoes/backtest_carteira_001.json');c['capital']=capital
    t=pd.date_range('2025-01-01',periods=len(retornos),freq='D',tz='UTC')
    primeiro=int(t[0].timestamp()//60)-1;n=len(retornos)*1440+4
    m=np.ones((n,6));m[:,:4]=100.
    q=pd.DataFrame({'indice_candle':np.arange(len(t)),'origem_utc':t,'destino_utc':t+pd.Timedelta(days=1),'close':100.,'previsao':retornos})
    return c,q,m,primeiro


class Carteira(unittest.TestCase):
    def conferir_motor(self,c,q,m,a,politica='smart',cenario='base'):
        r,o,cur,d,s=simular(q,m,a,c,politica,cenario);conferir(q,m,a,c,politica,cenario,r,o,d);return r,o,cur,d,s

    def test_fracoes_equivalem_codigo_publico(self):
        caminho=RAIZ/'registros/cryptomamba/fontes_externas/fef42727861a9c3a32241283ab981ef21a49e291/utils/trade.py'
        arvore=ast.parse(caminho.read_text());funcoes=[n for n in arvore.body if isinstance(n,ast.FunctionDef) and n.name in ('buy_sell_smart','buy_sell_vanilla')];g={};exec(compile(ast.Module(body=funcoes,type_ignores=[]),str(caminho),'exec'),g)
        c,*_=sintetico()
        for r in (-100.,-.1,-.02,-.001,0.,.001,.02,.1,100.):
            for p,n in [('smart','buy_sell_smart'),('vanilla','buy_sell_vanilla')]:
                acao,f=decisao(p,r,c);caixa,btc=900.,2.
                if acao=='comprar':btc+=caixa*f/100;caixa*=1-f
                elif acao=='vender':caixa+=btc*f*100;btc*=1-f
                args={'risk':2} if p=='smart' else {'tr':.01}
                a,b=g[n](100.,100*math.exp(r),900.,2.,**args)
                self.assertAlmostEqual(a,caixa,places=8);self.assertAlmostEqual(b,btc,places=8)

    def test_fee_recebido_e_caixa_conservado(self):
        c,q,m,a=sintetico((.05,));r,o,*_=self.conferir_motor(c,q,m,a)
        compra=next(x for x in o if x['status']=='executada' and x['lado']=='comprar')
        self.assertEqual(compra['comissao_ativo'],'BTC');self.assertAlmostEqual(compra['btc_depois'],compra['quantidade_bruta']*.999)
        self.assertLess(r['capital_final'],10000.);self.assertGreater(r['comissoes_usdt'],0.)

    def test_reter_evitar_roundtrip_diario(self):
        c,q,m,a=sintetico((.05,.05,.05));smart=self.conferir_motor(c,q,m,a)[0];diaria=self.conferir_motor(c,q,m,a,'diaria24')[0]
        self.assertEqual(smart['ordens_executadas'],2);self.assertEqual(diaria['ordens_executadas'],6);self.assertGreater(smart['capital_final'],diaria['capital_final'])

    def test_smart_acumula_caixa_nao_peso_alvo(self):
        c,q,m,a=sintetico((math.log(1.01),)*3);r,o,*_=self.conferir_motor(c,q,m,a,cenario='ideal')
        compras=[x for x in o if x['status']=='executada' and x['lado']=='comprar'];self.assertEqual(len(compras),3)
        self.assertGreater(compras[-1]['btc_depois'],compras[0]['btc_depois']);self.assertLess(compras[-1]['caixa_depois'],compras[0]['caixa_depois'])

    def test_filtro_e_poeira_real(self):
        c,q,m,a=sintetico((.000001,),capital=100.);r,o,*_=self.conferir_motor(c,q,m,a)
        self.assertEqual(r['ordens_executadas'],0);self.assertGreater(r['ordens_recusadas_filtro'],0);self.assertEqual(r['capital_final'],100.)

    def test_risco_inclui_ultimo_preco_e_saida(self):
        c,q,m,a=sintetico((.05,));m[-3:,:4]=50.;r,*_=self.conferir_motor(c,q,m,a)
        self.assertGreater(r['drawdown_minuto_close'],.49);self.assertLess(r['capital_final'],5010.)

    def test_causalidade_e_proibir_coluna_futura(self):
        c,q,m,a=sintetico();r,o,cur,d,s=self.conferir_motor(c,q,m,a)
        z=m.copy();z[20:100,3]=120.;rr,oo,cu,di,ss=self.conferir_motor(c,q,z,a)
        self.assertEqual(s,ss);self.assertEqual(o[0],oo[0])
        q['alvo']=1000
        with self.assertRaises(ValueError):simular(q,m,a,c,'smart','base')

    def test_precos_ausentes_e_origens_deslocadas(self):
        c,q,m,a=sintetico();m[40,3]=np.nan
        with self.assertRaises(ValueError):simular(q,m,a,c,'smart','base')
        m[40,3]=100.;q.loc[0,'close']=101.
        with self.assertRaises(ValueError):simular(q,m,a,c,'smart','base')

    def test_compra_manter_e_caixa_controles(self):
        c,q,m,a=sintetico((0.,0.));r,*_=self.conferir_motor(c,q,m,a,'caixa');self.assertEqual(r['retorno_liquido'],0);self.assertEqual(r['drawdown_minuto_close'],0)
        r,*_=self.conferir_motor(c,q,m,a,'comprar_manter','ideal');self.assertEqual(r['capital_final'],10000.);self.assertEqual(r['ordens_executadas'],2)

    def test_auditor_detecta_fraude_no_saldo(self):
        c,q,m,a=sintetico();r,o,cur,d,s=simular(q,m,a,c,'smart','base');o[0]['caixa_depois']+=10
        with self.assertRaises(ValueError):conferir(q,m,a,c,'smart','base',r,o,d)
