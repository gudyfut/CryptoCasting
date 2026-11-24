import copy
import unittest
import numpy as np
import pandas as pd
from estudo_ohlcv.dados import transformar, separar, padronizar
from estudo_ohlcv.avaliacao import conferir_previsoes, contraste_temporal, comprar_manter
from estudo_ohlcv.ciclo import configuracao, grade


def sinteticas(n=600):
    c = 100*np.exp(np.arange(n)*.0001 + .01*np.sin(np.arange(n)/13))
    return pd.DataFrame({'indice_hora': np.arange(n), 'origem_utc': pd.date_range('2021-01-01', periods=n, freq='h', tz='UTC'),
                         'open': c*.999, 'high': c*1.01, 'low': c*.99, 'close': c, 'volume': np.arange(n)%20})


class Contratos(unittest.TestCase):
    def test_formulas_unidades_e_alvo(self):
        entrada=sinteticas();entrada['causal']=False;entrada['observavel']=False
        h,x = transformar(entrada)
        self.assertNotIn('causal',h.columns)
        self.assertNotIn('observavel',h.columns)
        i=100
        np.testing.assert_allclose(x[i,:4], np.log(h.loc[i,['open','high','low','close']].to_numpy(float)/h.close[i-1]))
        self.assertEqual(x[i,4], 0.)
        self.assertAlmostEqual(np.expm1(h.alvo[i]), h.close[i+24]/h.close[i]-1)
        self.assertEqual(x.shape, (600,5))

    def test_invariancia_de_escala_precos(self):
        h=sinteticas()
        _,x=transformar(h)
        h[['open','high','low','close']] *= 1000
        _,z=transformar(h)
        np.testing.assert_allclose(x,z,rtol=1e-11,atol=1e-14,equal_nan=True)

    def test_perturbar_futuro_nao_altera_passado(self):
        h=sinteticas()
        _,x=transformar(h)
        h.loc[301:,['open','high','low','close','volume']] *= 3
        _,z=transformar(h)
        np.testing.assert_array_equal(x[:301],z[:301])

    def test_lacuna_invalida_contexto_sem_interpolacao(self):
        h=sinteticas()
        h.loc[200,['open','high','low','close','volume']]=np.nan
        h,x=transformar(h)
        c={'contexto':168,'divisao':{'treino':['2021-01-01','2021-01-26'],'teste':['2021-01-01','2021-01-26']}}
        b=separar(h,x,c)
        self.assertNotIn(368,b['treino'].indice_hora.values)
        self.assertIn(369,b['treino'].indice_hora.values)

    def test_futuro_ausente_nao_remove_decisao(self):
        h=sinteticas()
        h.loc[524,['open','high','low','close','volume']]=np.nan
        h,x=transformar(h)
        b=separar(h,x,{'contexto':168,'divisao':{'teste':['2021-01-01','2021-01-26']}})
        self.assertIn(500,b['operacional'].indice_hora.values)
        self.assertNotIn(500,b['teste'].indice_hora.values)

    def test_purga_exclui_destino_na_fronteira(self):
        h,x=transformar(sinteticas())
        b=separar(h,x,{'contexto':168,'divisao':{'treino':['2021-01-01','2021-01-20']}})
        self.assertTrue((b['treino'].destino_utc < pd.Timestamp('2021-01-20',tz='UTC')).all())
        self.assertNotIn(432,b['treino'].indice_hora.values)
        self.assertIn(431,b['treino'].indice_hora.values)

    def test_scalers_horas_unicas_e_apenas_treino(self):
        h,x=transformar(sinteticas())
        treino=h.iloc[168:300]
        _,e=padronizar(x,treino,168)
        np.testing.assert_allclose(e['media_entrada'],x[1:300].mean(axis=0))
        x[300:]*=100
        _,f=padronizar(x,treino,168)
        self.assertEqual(e,f)
        self.assertEqual(e['horas_unicas_ajuste'],299)

    def test_canal_constante_explicito(self):
        h,x=transformar(sinteticas())
        x[:,4]=7
        z,e=padronizar(x,h.iloc[168:300],168)
        self.assertTrue(e['canais_constantes'][4])
        self.assertEqual(e['escala_entrada'][4],1)
        self.assertTrue((z[:,4]==0).all())

    def test_rejeita_geometria_invalida_e_calendario_irregular(self):
        h=sinteticas()
        h.loc[20,'high']=1
        with self.assertRaises(ValueError): transformar(h)
        with self.assertRaises(ValueError): transformar(sinteticas().drop(20))

    def test_controles_e_seeds_sem_grade_oculta(self):
        g=grade(configuracao())
        self.assertEqual(len(g),10)
        self.assertEqual(sum(q.get('controle',False) for q in g),2)
        self.assertEqual(len({q['chave'] for q in g}),10)

    def test_auditoria_rejeita_previsoes_desalinhadas(self):
        h,_=transformar(sinteticas())
        q=h.iloc[200:250].copy()
        q['previsao']=0.
        conferir_previsoes(q,q)
        with self.assertRaises(AssertionError): conferir_previsoes(q.iloc[::-1],q)

    def test_bootstrap_diferenca_constante(self):
        t=pd.date_range('2025-01-01',periods=24*40,freq='h',tz='UTC')
        r=contraste_temporal(t,np.ones(len(t)),np.zeros(len(t)),{'dias':[7,14,28],'seed':42,'replicas':30,'principal':14})
        self.assertEqual(r['diferenca_mse_a_menos_b'],1)
        for intervalo in r['ic95'].values(): self.assertEqual(intervalo,[1.,1.])

    def test_comprar_manter_custo_e_ausencia(self):
        m=np.ones((5000,6))*100
        p={'capital':10000,'latencia_minutos':1,'taxa':.001,'slippage':.0005}
        inicio='2025-01-01';fim='2025-01-04';primeiro=int(pd.Timestamp(inicio,tz='UTC').timestamp()//60)
        r=comprar_manter(m,primeiro,inicio,fim,p)
        esperado=(1-.0005)*(1-.001)/((1+.0005)*(1+.001))-1
        self.assertAlmostEqual(r['retorno_liquido'],esperado)
        self.assertAlmostEqual(r['drawdown'],-esperado)
        m[10,3]=np.nan
        self.assertIsNone(comprar_manter(m,primeiro,inicio,fim,p)['drawdown'])
        m[1,0]=np.nan
        self.assertFalse(comprar_manter(m,primeiro,inicio,fim,p)['retorno_auditavel'])


if __name__=='__main__': unittest.main()
