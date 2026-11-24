from infraestrutura.caminhos import CODIGO
import copy
from pathlib import Path
import tempfile
import unittest
import ast
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json
from entradas_modelo.pipeline import construir
from entradas_modelo.receitas import calcular_entradas,CANAIS
from entradas_modelo.amostras import ajustar_escalas,aplicar_escalas


def candles():
    n=24*31;p=100*np.exp(np.arange(n)*.0001+.01*np.sin(np.arange(n)/13))
    a=pd.date_range('2021-01-01T00:00Z',periods=n,freq='h')
    return pd.DataFrame({'inicio_utc':a,'fim_utc':a+pd.Timedelta(hours=1),'open':p*.999,
                         'high':p*1.01,'low':p*.99,'close':p,'volume':np.arange(n)%20,'completo':True})


def configuracao():
    c=ler_json(RAIZ/'configuracoes/entradas_ohlcv24_001.json')
    c['divisao']={'treino':['2021-01-01T00:00Z','2021-01-15T00:00Z'],
                 'validacao':['2021-01-15T00:00Z','2021-01-22T00:00Z'],
                 'teste':['2021-01-22T00:00Z','2021-02-01T00:00Z']}
    return c


class Entradas(unittest.TestCase):
    def test_causalidade_e_separacao_de_alvo(self):
        q=candles();a=calcular_entradas(q,'ohlcv_relativo_v1',CANAIS)
        q['alvo']=np.arange(len(q))*999
        np.testing.assert_array_equal(a,calcular_entradas(q,'ohlcv_relativo_v1',CANAIS))
        q.loc[400:,['open','high','low','close','volume']]*=5
        b=calcular_entradas(q,'ohlcv_relativo_v1',CANAIS)
        np.testing.assert_array_equal(a[:400],b[:400])

    def test_futuro_nao_altera_scaler_de_treino(self):
        q=candles();a=construir(q,configuracao(),60)
        q.loc[400:,['open','high','low','close','volume']]*=3
        b=construir(q,configuracao(),60)
        self.assertEqual(a.escalas,b.escalas)

    def test_compatibilidade_exata_com_preparacao_preservada(self):
        from estudo_ohlcv.dados import preparar
        q=candles();c=configuracao();novo=construir(q,c,60)
        antigo=q.copy();antigo['origem_utc']=q.fim_utc;antigo['indice_hora']=np.arange(len(q))
        esperado=preparar(antigo,{'contexto':168,'divisao':{k:[v[:10] for v in t] for k,t in c['divisao'].items()}})
        h,x,b,e=novo.adaptar_ohlcv24()
        np.testing.assert_array_equal(x,esperado[1]);self.assertEqual(e,esperado[3])
        for parte in b:
            pd.testing.assert_frame_equal(b[parte],esperado[2][parte][b[parte].columns],check_exact=True)

    def test_canais_configuraveis_e_janela(self):
        c=configuracao();c['canais']=['fechamento_relativo','volume_transformado']
        a=construir(candles(),c,60)
        i=a.partes['treino'].indice_candle.to_numpy()[:3]
        self.assertEqual(a.janelas(i).shape,(3,168,2));self.assertEqual(a.dimensao_entrada,2)
        with self.assertRaises(ValueError):a.adaptar_ohlcv24()
        with self.assertRaises(ValueError):a.janelas([-1])
        with self.assertRaises(ValueError):a.janelas([1.5])

    def test_purga_e_inversao_alvo(self):
        a=construir(candles(),configuracao(),60)
        for nome,part in a.partes.items():
            if nome!='operacional':self.assertTrue((part.destino_utc<pd.Timestamp(configuracao()['divisao'][nome][1])).all())
        y=a.partes['treino'].alvo.to_numpy();z=(y-a.escalas['media_alvo'])/a.escalas['escala_alvo']
        np.testing.assert_allclose(a.inverter_alvo(z),y,rtol=1e-12,atol=1e-15)

    def test_futuro_ausente_nao_apaga_decisao(self):
        q=candles();q.loc[550,['open','high','low','close','volume']]=np.nan;q.loc[550,'completo']=False
        a=construir(q,configuracao(),60)
        self.assertIn(526,a.partes['operacional'].indice_candle.values)
        self.assertNotIn(526,a.partes['teste'].indice_candle.values)

    def test_rejeita_configuracao_ignorada_ou_sobreposta(self):
        for chave,valor in [('campo_ignorado',1),('receita','desconhecida'),('horizonte_minutos',25),('canais',['x'])]:
            c=configuracao();c[chave]=valor
            with self.assertRaises(ValueError):construir(candles(),c,60)
        c=configuracao();c['divisao']['validacao'][0]='2021-01-10T00:00Z'
        with self.assertRaises(ValueError):construir(candles(),c,60)

    def test_escala_zero_sem_divisao_por_zero(self):
        q=candles();q['volume']=0
        a=construir(q,configuracao(),60)
        self.assertTrue(a.escalas['canais_constantes'][-1]);self.assertTrue((a.matriz[:,-1]==0).all())

    def test_fronteiras_de_importacao(self):
        proibidos={'torch','previsao24','estudo_ohlcv','experimento_penalizacao','experimento_normalizacao','dataview'}
        for pacote in ('infraestrutura','mercado_binance','entradas_modelo'):
            for p in (CODIGO/pacote).glob('*.py'):
                arvore=ast.parse(p.read_text(encoding='utf-8'))
                for n in ast.walk(arvore):
                    nomes=[a.name for a in n.names] if isinstance(n,ast.Import) else [n.module or ''] if isinstance(n,ast.ImportFrom) else []
                    for nome in nomes:
                        self.assertNotIn(nome.split('.')[0],proibidos,f'{p}:{n.lineno}')
                        if pacote=='mercado_binance':self.assertNotEqual(nome.split('.')[0],'entradas_modelo')


if __name__=='__main__':unittest.main()
