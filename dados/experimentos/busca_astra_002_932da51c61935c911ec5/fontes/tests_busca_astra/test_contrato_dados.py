import unittest
from copy import deepcopy
import numpy as np
import pandas as pd
from experimentos.busca_astra.contrato import REFERENCIA, validar_receita, chave_receita, elegivel
from experimentos.busca_astra.dados import Dados, representar, INICIO_COMUM

def candles():
    t=pd.date_range('2022-10-01',periods=24*180,freq='h',tz='UTC')
    rng=np.random.default_rng(3);c=100*np.exp(np.cumsum(rng.normal(0,.005,len(t))))
    return pd.DataFrame(dict(fim_utc=t,open=c*.999,high=c*1.01,low=c*.99,close=c,
                             volume=rng.lognormal(3,.3,len(t)),completo=True))

class ContratoDados(unittest.TestCase):
    def test_receita_rejeita_codigo_e_valor(self):
        with self.assertRaises(ValueError): validar_receita(dict(REFERENCIA, codigo='import os'))
        with self.assertRaises(ValueError): validar_receita(dict(REFERENCIA, contexto=336))
        with self.assertRaises(ValueError): validar_receita(dict(REFERENCIA, estado=True))
        self.assertEqual(chave_receita(dict(REFERENCIA, ganho_saida=1)),chave_receita(REFERENCIA))

    def test_origens_comuns_purga_e_alvo(self):
        q=candles();a=Dados(q,REFERENCIA,'D1')
        b=Dados(q,dict(REFERENCIA,contexto=24,indicadores=True),'D1')
        for p in a.indices:
            np.testing.assert_array_equal(a.indices[p],b.indices[p])
        self.assertGreaterEqual(a.indices['treino'].min(),INICIO_COMUM)
        self.assertTrue((a.tabela.iloc[a.indices['treino']].destino_utc<pd.Timestamp('2023-01-01',tz='UTC')).all())
        i=a.indices['validacao'][0]
        self.assertAlmostEqual(a.y[i],np.log(q.close.iloc[i+24]/q.close.iloc[i]))

    def test_futuro_nao_muda_entrada_ou_escalas(self):
        q=candles();r=dict(REFERENCIA,indicadores=True)
        a=Dados(q,r,'D1');alterado=q.copy()
        i=a.indices['validacao'][100]
        alterado.loc[i+1:,['open','high','low','close','volume']]*=3
        b=Dados(alterado,r,'D1')
        np.testing.assert_array_equal(a.janelas([i]),b.janelas([i]))
        np.testing.assert_array_equal(a.mu,b.mu)
        self.assertEqual(a.ym,b.ym)

    def test_escala_uniao_de_horas_e_indicadores(self):
        d=Dados(candles(),dict(REFERENCIA,indicadores=True,contexto=72),'D1')
        usados=np.unique(np.concatenate([np.arange(i-71,i+1) for i in d.indices['treino']]))
        np.testing.assert_allclose(d.mu,d.raw[usados].mean(0),rtol=1e-13)
        self.assertTrue(np.isfinite(d.janelas(d.indices['treino'])).all())

    def test_todas_representacoes_dimensao(self):
        for rep in ['relativa','crua','niveis','log_niveis','janela_relativa']:
            for indicador in [False,True]:
                d=Dados(candles(),dict(REFERENCIA,representacao=rep,indicadores=indicador),'D1')
                x=d.janelas(d.indices['validacao'][:2])
                self.assertEqual(x.shape,(2,168,10 if indicador else 5))
                self.assertEqual(x.dtype,np.float32)

    def test_lacunas_preservam_populacao_comum(self):
        q=candles();q.loc[500,['open','high','low','close','volume']]=np.nan
        a=Dados(q,REFERENCIA,'D1')
        b=Dados(q,dict(REFERENCIA,indicadores=True,contexto=24),'D1')
        for p in a.indices:np.testing.assert_array_equal(a.indices[p],b.indices[p])
        self.assertFalse(np.isin(np.arange(500,836),a.indices['treino']).any())

    def test_selecao_nao_promove_por_um_recorte(self):
        def rs(v):return [{'validacao':{'mse':x,'mse_naive':1.}} for x in v]
        ref=rs([1.]*6)
        self.assertFalse(elegivel(rs([.5]*3+[1.1]*3),ref))
        self.assertTrue(elegivel(rs([.99]*6),ref))
        self.assertFalse(elegivel(rs([1.]*6),ref))

if __name__=='__main__':unittest.main()
