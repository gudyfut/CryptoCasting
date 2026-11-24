import unittest
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from previsao24.dados import construir_horas,separar,ajustar_escalas
from previsao24.metricas import calcular
from previsao24.baselines import prever_arima,projecao_filtrada
from previsao24.configuracao import referencia,celulas

class DadosTeste(unittest.TestCase):
    def minutos(self,n=500):
        p=np.exp(np.arange(n*60)*0.000001)
        return np.column_stack([p,p,p,p,np.ones(len(p)),np.ones(len(p))])

    def test_alvo_exatamente_24h(self):
        q=construir_horas(self.minutos(),0)
        i=350
        self.assertAlmostEqual(q.loc[i,'alvo'],24*60*0.000001,places=12)
        self.assertEqual(q.loc[i,'destino_utc']-q.loc[i,'origem_utc'],pd.Timedelta(hours=24))
        self.assertFalse(q.loc[335,'causal'])
        self.assertTrue(q.loc[336,'causal'])

    def test_lacuna_no_percurso_nao_apaga_alvo_terminal(self):
        m=self.minutos()
        m[360*60+3]=np.nan
        q=construir_horas(m,0)
        self.assertTrue(q.loc[350,'observavel'])
        self.assertTrue(np.isnan(q.loc[360,'close']))
        self.assertFalse(q.loc[370,'causal'])

    def test_lacuna_no_destino_nao_remove_elegibilidade_causal(self):
        m=self.minutos()
        m[374*60+3]=np.nan
        q=construir_horas(m,0)
        self.assertTrue(q.loc[350,'causal'])
        self.assertFalse(q.loc[350,'observavel'])

    def test_features_invariantes_a_futuro(self):
        m=self.minutos()
        q=construir_horas(m,0)
        m[351*60:,:4]*=7
        alterado=construir_horas(m,0)
        np.testing.assert_array_equal(q.loc[:350,'retorno'],alterado.loc[:350,'retorno'])
        self.assertNotEqual(q.loc[350,'alvo'],alterado.loc[350,'alvo'])

    def test_purga_e_escalas(self):
        t=pd.date_range('2021-01-01','2023-04-01',freq='h',inclusive='left',tz='UTC')
        n=len(t)
        q=pd.DataFrame({'origem_utc':t,'destino_utc':t+pd.Timedelta(hours=24),'indice_hora':np.arange(n),
                        'retorno':np.sin(np.arange(n))*.01,'alvo':np.cos(np.arange(n))*.02,'causal':np.arange(n)>=336})
        mascara=q['causal'].to_numpy()
        b=separar(q,mascara,'DB1')
        self.assertLess(b['treino']['destino_utc'].max(),pd.Timestamp('2022-10-01',tz='UTC'))
        self.assertLess(b['validacao']['destino_utc'].max(),pd.Timestamp('2023-01-01',tz='UTC'))
        self.assertLess(b['teste']['destino_utc'].max(),pd.Timestamp('2023-04-01',tz='UTC'))
        _,s=ajustar_escalas(q,b['treino'])
        q.loc[q['origem_utc']>=pd.Timestamp('2022-10-01',tz='UTC'),'retorno']=1000
        _,s2=ajustar_escalas(q,b['treino'])
        self.assertEqual(s,s2)

class MetricasTeste(unittest.TestCase):
    def test_naive_e_perfeito(self):
        y=np.array([-.02,.01,.03])
        m=calcular(y,np.zeros(3))
        self.assertEqual(m['habilidade_mse'],0)
        self.assertEqual(m['acerto_balanceado_direcional'],0)
        self.assertEqual(calcular(y,y)['habilidade_mse'],1)
        self.assertEqual(calcular(y,y)['acerto_balanceado_direcional'],1)

    def test_zero_preservado_e_denominador_nulo(self):
        m=calcular([0,0],[0,0])
        self.assertIsNone(m['habilidade_mse'])
        self.assertIsNone(m['acerto_balanceado_direcional'])
        self.assertEqual(m['reais_zero'],2)

    def test_formato_invalido(self):
        with self.assertRaises(ValueError):
            calcular([1,2],[1])
        with self.assertRaises(ValueError):
            calcular([1,np.nan],[1,0])

class ArimaTeste(unittest.TestCase):
    def setUp(self):
        self.precos=4+np.cumsum(np.random.default_rng(7).normal(0,.01,180))

    def test_persistencia(self):
        p,_=prever_arima(self.precos,[0,1,0],[1.0],self.precos[0])
        np.testing.assert_array_equal(p,np.zeros(len(p)))

    def test_projecao_equivale_prefixo_oficial(self):
        for ordem,parametros in [((1,1,0),[.4,1.]),((0,1,1),[.3,1.]),((1,1,1),[.4,.3,1.])]:
            p,_=prever_arima(self.precos,ordem,parametros,self.precos[0])
            for i in (70,130,179):
                r=ARIMA((self.precos[:i+1]-self.precos[0])*100,order=ordem,trend='n').filter(parametros)
                esperado=np.asarray(r.get_forecast(24).predicted_mean)[-1]/100+self.precos[0]-self.precos[i]
                self.assertAlmostEqual(p[i],esperado,places=11)

    def test_filtro_nao_usa_futuro_e_preserva_grade_com_lacuna(self):
        original=self.precos.copy()
        original[90]=np.nan
        p,_=prever_arima(original,[1,1,1],[.4,.3,1.],original[0])
        alterado=original.copy()
        alterado[131:]+=2
        p2,_=prever_arima(alterado,[1,1,1],[.4,.3,1.],original[0])
        np.testing.assert_array_equal(p[:131],p2[:131])
        self.assertTrue(np.isnan(p[90]))
        self.assertTrue(np.isfinite(p[91]))

class GradeTeste(unittest.TestCase):
    def test_contagens(self):
        c=referencia()
        self.assertEqual(len(celulas(c,'desenvolvimento')),384)
        self.assertEqual(len(celulas(c,'avaliacao')),384)
        self.assertEqual(len(c['arima']['ordens']),9)
        self.assertEqual(c['contextos'],[24,72,168,336])

if __name__=='__main__':
    unittest.main()
