import unittest
import numpy as np
from simulador import simular


class Saidas(unittest.TestCase):
    def dados(self):
        x=np.full((1443,4),100.,dtype=float)
        return {'tempo':np.arange(1443,dtype=np.int64)*60000,'negocio':x,'marca':x.copy(),
            'funding_tempo':np.array([60000,480*60000,960*60000],dtype=np.int64),
            'funding_taxa':np.array([.001,.001,.001]),'funding_preco':np.array([100.,100.,100.])}
    def regras(self):
        return dict(capital_inicial=10000.,fracao_nocional=.95,latencia_minutos=1,
            comissao_por_lado=0.,slippage_por_lado=0.,tick_preco=.01,passo_quantidade=.001,
            nocional_minimo=1.,buffer_prudencial=0.,filtro_retorno_absoluto=.002)
    def rodar(self,m,politica='stop_take',lado=1,desempate='stop'):
        r,c=simular(np.array([0]),np.array([100*(1+.01*lado)]),np.array([100.]),m,self.regras(),.01,politica,desempate)
        return r,c
    def test_take_antes_stop(self):
        m=self.dados();m['negocio'][5,1]=101.2;m['negocio'][8,2]=98.
        o=self.rodar(m)[0]['operacoes'][0];self.assertEqual(o['motivo'],'take');self.assertEqual(o['referencia_saida'],101.)
    def test_stop_antes_take(self):
        m=self.dados();m['negocio'][5,2]=98.8;m['negocio'][8,1]=102.
        o=self.rodar(m)[0]['operacoes'][0];self.assertEqual(o['motivo'],'stop');self.assertEqual(o['referencia_saida'],99.)
    def test_duplo_toque_dois_limites(self):
        m=self.dados();m['negocio'][5]=[100.,102.,98.,100.]
        a=self.rodar(m)[0]['operacoes'][0];b=self.rodar(m,desempate='take')[0]['operacoes'][0]
        self.assertTrue(a['ambiguo']);self.assertEqual(a['motivo'],'stop');self.assertEqual(b['motivo'],'take')
    def test_abertura_resolve_duplo_toque(self):
        m=self.dados();m['negocio'][5]=[98.,102.,97.,100.]
        o=self.rodar(m,desempate='take')[0]['operacoes'][0]
        self.assertFalse(o['ambiguo']);self.assertEqual(o['motivo'],'stop');self.assertEqual(o['referencia_saida'],98.)
    def test_short_take_stop(self):
        m=self.dados();m['negocio'][5,2]=98.8
        self.assertEqual(self.rodar(m,lado=-1)[0]['operacoes'][0]['motivo'],'take')
        m=self.dados();m['negocio'][5,1]=101.2
        self.assertEqual(self.rodar(m,lado=-1)[0]['operacoes'][0]['motivo'],'stop')
    def test_somente_stop_preserva_ganho(self):
        m=self.dados();m['negocio'][5,1]=104.;m['negocio'][1441,0]=105.
        o=self.rodar(m,'stop')[0]['operacoes'][0]
        self.assertEqual(o['motivo'],'prazo');self.assertEqual(o['preco_saida'],105.)
    def test_funding_apos_saida_excluido(self):
        m=self.dados();m['negocio'][5,1]=102.
        o=self.rodar(m)[0]['operacoes'][0]
        self.assertEqual(len(o['eventos_funding']),1);self.assertAlmostEqual(o['funding'],-9.5)
    def test_funding_no_inicio_minuto_do_toque(self):
        m=self.dados();m['negocio'][480,1]=102.
        o=self.rodar(m)[0]['operacoes'][0];self.assertEqual(len(o['eventos_funding']),2)
    def test_prazo_ignora_extremos_e_limita_24h(self):
        m=self.dados();m['negocio'][5]=[100.,110.,90.,100.]
        o=self.rodar(m,'prazo')[0]['operacoes'][0]
        self.assertEqual(o['motivo'],'prazo');self.assertEqual(o['saida_ms']-o['entrada_ms'],86400000)
    def test_antes_da_entrada_e_apos_prazo_nao_interferem(self):
        m=self.dados();m['negocio'][0,2]=1.;m['negocio'][1442,2]=1.
        self.assertEqual(self.rodar(m)[0]['operacoes'][0]['motivo'],'prazo')
    def test_previsao_dentro_filtro_caixa(self):
        m=self.dados();r,c=simular(np.array([0]),np.array([100.1]),np.array([100.]),m,self.regras(),.01,'stop_take')
        self.assertEqual(r['metricas']['operacoes'],0);np.testing.assert_array_equal(c['saldos_diarios'],[10000,10000])
    def test_fonte_sinal_nao_muda_com_saida(self):
        m=self.dados();m['negocio'][5,1]=102.;m['negocio'][1441,0]=103.
        for politica in ('prazo','stop','stop_take'):
            o=self.rodar(m,politica)[0]['operacoes'][0]
            self.assertEqual(o['lado'],1);self.assertEqual(o['entrada_ms'],60000);self.assertEqual(o['quantidade'],95.)


if __name__=='__main__':unittest.main(verbosity=2)
