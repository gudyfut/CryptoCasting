import unittest
import numpy as np
import pandas as pd
from entradas_modelo.operacional_futuros import preparar,montar_canais


class Entradas(unittest.TestCase):
    def setUp(self):
        n=24*150;t=pd.date_range('2021-01-01',periods=n,freq='h',tz='UTC').as_unit('ms').asi8
        c=100*np.exp(np.arange(n)*.0001+.01*np.sin(np.arange(n)/30))
        self.q=pd.DataFrame({'open_time':t,'close_time':t+3599999,'open':c,'high':c*1.01,'low':c*.99,'close':c,'volume':np.arange(n)%10})
        self.cal={'treino':['2021-01-01','2021-03-01'],'validacao':['2021-03-01','2021-04-01'],
                  'calibracao':['2021-04-01','2021-05-01'],'comparacao':['2021-05-01','2021-05-30']}
        self.r={'representacao':'relativa','contexto_horas':168,'familia_alvo':'terminal','momentum':True,'volatilidade':True,'volume_relativo':True}

    def test_futuro_nao_muda_canais_passados_ou_escalas(self):
        a=preparar(self.q,self.r,self.cal);q=self.q.copy();limite=24*90
        q.loc[limite:,['open','high','low','close']]*=2;q.loc[limite:,'volume']+=1000
        b=preparar(q,self.r,self.cal)
        self.assertEqual(a.escalas,b.escalas)
        np.testing.assert_array_equal(a.matriz[:limite],b.matriz[:limite])

    def test_contextos_mesmas_origens_e_purga(self):
        a=preparar(self.q,self.r,self.cal);b=preparar(self.q,dict(self.r,contexto_horas=24),self.cal)
        for k in a.indices:np.testing.assert_array_equal(a.indices[k],b.indices[k])
        self.assertLess(a.origens_ms[a.indices['treino'][-1]]+1442*60000,a.origens_ms[a.indices['validacao'][0]])
        ids=a.indices['comparacao'][:3];self.assertEqual(a.janelas(ids).shape,(3,168,12))

    def test_alvo_24h_e_decode(self):
        a=preparar(self.q,self.r,self.cal);i=500
        self.assertAlmostEqual(a.alvo[i,0],np.log(self.q.close.iloc[i+24]/self.q.close.iloc[i]))
        np.testing.assert_allclose(a.decodificar(a.alvo_normalizado([i])),a.alvo[[i]],rtol=1e-6)

    def test_crua_nao_padroniza_ohlcv(self):
        a=preparar(self.q,dict(self.r,representacao='crua'),self.cal)
        np.testing.assert_array_equal(a.matriz[500,:5],self.q[['open','high','low','close','volume']].iloc[500].to_numpy(dtype=np.float32))

    def test_payoff_dois_canais_sem_broadcast(self):
        y=np.column_stack([np.sin(np.arange(len(self.q))),np.cos(np.arange(len(self.q)))])
        a=preparar(self.q,dict(self.r,familia_alvo='payoff'),self.cal,y)
        self.assertEqual(a.alvo_normalizado([500]).shape,(1,2))
        with self.assertRaises(ValueError):preparar(self.q,dict(self.r,familia_alvo='payoff'),self.cal,y[:,0])

    def test_lacuna_nao_e_interpolada(self):
        with self.assertRaises(ValueError):montar_canais(self.q.drop(500),self.r)


if __name__=='__main__':unittest.main()
