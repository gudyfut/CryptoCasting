import copy
import unittest
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json
from mercado_futuros.multimoeda import inicio_completo, regras_simbolo, validar_diario
from experimentos.generalizacao_moedas.contratos import configurar, preparar
from entradas_modelo.padronizacao_diaria import preparar_com_escalas
from tests_cryptomamba_diario.test_contratos import dados_artificiais, mercado
from simulacao_operacoes.diaria_24h import simular, conferir
from simulacao_operacoes.envelopes_marcacao import alinhar


class Generalizacao(unittest.TestCase):
    def setUp(self):
        self.ref=ler_json(RAIZ/'configuracoes/padronizacao_diaria_001.json')
        self.info=ler_json(RAIZ/'registros/generalizacao_moedas/preparacao/exchangeInfo.json')['symbols']

    def contrato(self, simbolo):
        i=next(x for x in self.info if x['symbol']==simbolo)
        return {'simbolo':simbolo,'inicio_diario_ms':inicio_completo(i['onboardDate']),'regras_simbolo':regras_simbolo(i)}

    def test_receita_cientifica_conservada(self):
        for s in ('ETHUSDT','BNBUSDT','XRPUSDT'):
            a=copy.deepcopy(self.ref);b=configurar(a,s,self.contrato(s))
            for x in (a,b):
                for k in ('ciclo','simbolo','antecessora','exposicao'):x.pop(k,None)
                x['periodos']['treino'][0]='inicio_variavel'
                for k in ('tick_preco','passo_quantidade','nocional_minimo','quantidade_minima','quantidade_maxima'):x['operacoes'].pop(k,None)
            self.assertEqual(a,b)

    def test_disponibilidade_e_contagem(self):
        esperado={'ETHUSDT':1446,'BNBUSDT':1405,'XRPUSDT':1440}
        for s,n in esperado.items():
            c=configurar(self.ref,s,self.contrato(s));q=dados_artificiais();q=q[q.open_time>=self.contrato(s)['inicio_diario_ms']]
            d,e=preparar(q,c);self.assertEqual(len(d['treino']['y']),n)
            self.assertEqual(e['candles_unicos'],n+13)
            self.assertEqual(d['validacao']['x'].shape,(351,6,14))
            self.assertEqual(d['teste']['x'].shape,(350,6,14))

    def test_primeiro_dia_parcial_excluido(self):
        self.assertEqual(inicio_completo(1578298800000),1578355200000)
        self.assertEqual(inicio_completo(1581321600000),1581379200000)

    def test_futuro_nao_muda_escala_ou_treino(self):
        c=configurar(self.ref,'ETHUSDT',self.contrato('ETHUSDT'));q=dados_artificiais()
        a,e=preparar(q,c);q.loc[q.open_time>=1704067200000,['open','high','low','close','volume']]*=4
        b,f=preparar(q,c);self.assertEqual(e,f);np.testing.assert_array_equal(a['treino']['x'],b['treino']['x'])

    def test_reuso_exato_preparacao_btc(self):
        q=dados_artificiais();a,e=preparar_com_escalas(q,self.ref);b,f=preparar(q,self.ref)
        self.assertEqual(e,f)
        for fase in a:
            for k in a[fase]:np.testing.assert_array_equal(a[fase][k],b[fase][k])

    def test_lacuna_rejeitada(self):
        with self.assertRaises(AssertionError):preparar(dados_artificiais().drop(30),self.ref)

    def test_simbolo_nao_autorizado_rejeitado(self):
        with self.assertRaises(AssertionError):configurar(self.ref,'SOLUSDT',{'simbolo':'SOLUSDT'})

    def test_lotes_ticks_e_custos_de_cada_moeda(self):
        for s,preco in [('ETHUSDT',2000.),('BNBUSDT',300.),('XRPUSDT',.5)]:
            c=configurar(self.ref,s,self.contrato(s));regras=c['operacoes']
            for fator in (1.01,.99):
                r,curva=simular([0],[preco*fator],[preco],mercado(preco),regras,c['cenarios']['base'])
                conferir(r,curva,regras);o=r['operacoes'][0]
                self.assertLess(o['pnl_liquido'],0)
                self.assertAlmostEqual(o['quantidade']/regras['passo_quantidade'],round(o['quantidade']/regras['passo_quantidade']),places=6)
                self.assertAlmostEqual(o['preco_entrada']/regras['tick_preco'],round(o['preco_entrada']/regras['tick_preco']),places=6)
                self.assertGreaterEqual(o['quantidade'],regras['quantidade_minima'])
                self.assertLessEqual(o['quantidade'],regras['quantidade_maxima'])

    def test_envelope_nao_inventa_open_close(self):
        t=np.arange(0,300000,60000);q=pd.DataFrame({'open_time':t,'open':100.,'high':101.,'low':99.,'close':100.})
        q=q.drop(2);e=[{'minuto_ausente':120000,'inicio_envelope':0,'fim_envelope':299999,'high':103.,'low':97.}]
        a,f=alinhar(t,q,e);self.assertTrue(np.isnan(a[2,[0,3]]).all());np.testing.assert_array_equal(a[2,[1,2]],[103.,97.])
        np.testing.assert_array_equal(f,[120000])
        with self.assertRaises(AssertionError):alinhar(t,q,[])

    def test_envelope_so_afeta_risco_nao_caixa(self):
        c=self.ref;m=mercado();r,v=simular([0],[101.],[100.],m,c['operacoes'],c['cenarios']['base'])
        m['marca'][3]=[np.nan,110.,90.,np.nan]
        novo,curva=simular([0],[101.],[100.],m,c['operacoes'],c['cenarios']['base'])
        self.assertEqual(r['operacoes'],novo['operacoes']);np.testing.assert_array_equal(v['saldos_diarios'],curva['saldos_diarios'])
        self.assertGreater(novo['metricas']['drawdown_maximo'],r['metricas']['drawdown_maximo']);conferir(novo,curva,c['operacoes'])


if __name__=='__main__':unittest.main()
