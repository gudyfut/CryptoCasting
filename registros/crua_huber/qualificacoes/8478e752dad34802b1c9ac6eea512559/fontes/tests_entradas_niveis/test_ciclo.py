import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json
from entradas_modelo.pipeline import construir
from experimentos.entradas_niveis.dados import representar, ConsumoNiveis, VARIANTES
from experimentos.entradas_niveis.estatisticas import contraste


def mercado_sintetico():
    n=31*24;i=np.arange(n);p=100000*np.exp(.0001*i+.01*np.sin(i/11))
    t=pd.date_range('2021-01-01',periods=n,freq='h',tz='UTC')
    q=pd.DataFrame({'inicio_utc':t,'fim_utc':t+pd.Timedelta(hours=1),
        'open':p*.999,'high':p*1.01,'low':p*.99,'close':p,'volume':1000+i%20,'completo':True})
    c=ler_json(RAIZ/'configuracoes/entradas_ohlcv24_001.json')
    c['divisao']={'treino':['2021-01-01T00:00Z','2021-01-15T00:00Z'],
        'validacao':['2021-01-15T00:00Z','2021-01-22T00:00Z'],
        'teste':['2021-01-22T00:00Z','2021-02-01T00:00Z']}
    return q,construir(q,c,60)


def sinteticos():
    q,a=mercado_sintetico()
    return {v:ConsumoNiveis(representar(q,a,v),'sintetico_'+v) for v in VARIANTES}


class Entradas(unittest.TestCase):
    def test_crua_preserva_unidades_e_mascara_e_alvo(self):
        q,a=mercado_sintetico();z=representar(q,a,'crua')
        mask=np.isfinite(a.matriz).all(axis=1)
        np.testing.assert_array_equal(z.matriz[mask],q.loc[mask,['open','high','low','close','volume']].to_numpy(np.float32))
        self.assertEqual(z.escalas['media_entrada'],[0.]*5)
        self.assertEqual(z.escalas['escala_entrada'],[1.]*5)
        for k in ('media_alvo','escala_alvo'):self.assertEqual(z.escalas[k],a.escalas[k])
        self.assertEqual(z.contrato['normalizacao'],'identidade_entrada_alvo_zscore_treino')
        for parte in a.partes:pd.testing.assert_frame_equal(z.partes[parte],a.partes[parte])
        x=ConsumoNiveis(z,'sintetico');self.assertEqual(x._conjunto.contrato,z.contrato)
        pedido=x.solicitar('treino',[0]);self.assertNotIn('alvo',pedido.origens)
        np.testing.assert_array_equal(x.lote_neural(pedido).entradas,z.janelas(pedido.origens.indice_candle.to_numpy()))

    def test_padronizacao_refeita_com_horas_unicas_treino(self):
        q,a=mercado_sintetico();z=representar(q,a,'niveis_padronizados')
        usados=np.zeros(len(q),bool)
        for i in a.partes['treino'].indice_candle:usados[i-167:i+1]=True
        raw=q[['open','high','low','close','volume']].to_numpy()
        np.testing.assert_array_equal(np.array(z.escalas['media_entrada']),raw[usados].mean(axis=0))
        np.testing.assert_array_equal(np.array(z.escalas['escala_entrada']),raw[usados].std(axis=0))
        np.testing.assert_allclose(z.matriz[usados].mean(axis=0),0,atol=1e-6)
        self.assertNotEqual(z.escalas['media_entrada'],[0.]*5)

    def test_futuro_nao_altera_escalas_ou_janelas_anteriores(self):
        q,a=mercado_sintetico();qq=q.copy();fut=qq.inicio_utc>=pd.Timestamp('2021-01-22T00:00Z')
        qq.loc[fut,['open','high','low','close','volume']]*=10
        for v in VARIANTES:
            z=representar(q,a,v);b=representar(qq,a,v)
            self.assertEqual(z.escalas,b.escalas)
            np.testing.assert_array_equal(z.matriz[~fut],b.matriz[~fut])

    def test_alvo_observado_nao_entra_na_representacao(self):
        q,a=mercado_sintetico();aa=copy.deepcopy(a)
        aa.origens['alvo']=999.;aa.origens['preco_destino']=1.
        # As escalas do alvo não são recalculadas a partir de teste/operação.
        for parte in ('teste','operacional'):
            aa.partes[parte]['alvo']=999.;aa.partes[parte]['preco_destino']=1.
        for v in VARIANTES:
            np.testing.assert_array_equal(representar(q,a,v).matriz,representar(q,aa,v).matriz)

    def test_grade_orcamento_e_controles_precedem_outras_seeds(self):
        from experimentos.entradas_niveis.ciclo import configuracao,grade
        c=configuracao();g=grade(c)
        self.assertEqual(len(g),66);self.assertEqual(sum(i['controle'] for i in g),2)
        self.assertEqual([(i['seed'],i['controle']) for i in g[:4]],[(42,False),(42,False),(42,True),(42,True)])
        self.assertEqual({i['variante'] for i in g},set(VARIANTES))
        self.assertEqual(len({(i['bloco'],i['variante'],i['seed']) for i in g if not i['controle']}),64)

    def test_mesmo_alvo_perda_arquitetura_e_receita(self):
        from experimentos.entradas_niveis.ciclo import configuracao,receita
        c=configuracao();a=receita(c,'B1','crua','p');b=receita(c,'B1','niveis_padronizados','p')
        diferentes={k for k in a if a[k]!=b[k]}
        self.assertEqual(diferentes,{'variante','normalizacao'})
        self.assertEqual(a['perda'],{'nome':'MSELoss','alvo':'padronizado_treino'})
        self.assertEqual(a['treino']['taxa_aprendizado'],.0002)

    def test_bootstrap_peso_igual_blocos_e_tres_contrastes(self):
        b={}
        for nome,n,dif in [('B1',48,-1.),('B2',24,3.)]:
            b[nome]={'origens':pd.date_range('2024-01-01',periods=n,freq='h',tz='UTC'),
                'atual':np.ones((8,n))*4,'crua':np.ones((8,n))*(4+dif)}
        r=contraste(b,'crua','atual',replicas=30,dias=(2,))
        self.assertEqual(r['diferenca_mse'],1.)
        np.testing.assert_allclose(r['intervalos']['2']['ic_bonferroni_98_333'],[1.,1.])
        self.assertEqual(r['decisao'],'piora')
        for v in b.values():v['crua']=v['atual'].copy()
        self.assertEqual(contraste(b,'crua','atual',replicas=30,dias=(2,))['decisao'],'inconclusivo')
        b['B1']['crua']=b['B1']['crua'][:7]
        with self.assertRaises(ValueError):contraste(b,'crua','atual',replicas=30,dias=(2,))

    def test_consumidor_rejeita_identidade_de_entrada_falsa(self):
        q,a=mercado_sintetico();z=representar(q,a,'crua');z.escalas['escala_entrada'][0]=2.
        with self.assertRaises(AssertionError):ConsumoNiveis(z,'invalido')

    def test_calendario_operacional_independe_de_futuro(self):
        from experimentos.huber_blocos.publicacao import janela_operacional
        q,a=mercado_sintetico();d=a.partes['operacional'].copy();d['previsao']=0.
        antes=janela_operacional(d,'2021-02-01T00:00Z');d['alvo']=999.;d['preco_destino']=np.nan
        pd.testing.assert_frame_equal(antes,janela_operacional(d,'2021-02-01T00:00Z'))


if __name__=='__main__':unittest.main()
