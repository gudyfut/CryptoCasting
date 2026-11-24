import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.parse import parse_qs,urlparse
import zipfile
import numpy as np
import pandas as pd
from mercado_binance import Periodo
from mercado_binance.validacao import normalizar,conferir_checksum,ler_zip
from mercado_binance.candles import agregar
from mercado_binance.api import consultar
from mercado_binance.transporte import ClienteHTTP


def linhas(inicio='2025-01-01T00:00:00Z',n=120,unidade='ms'):
    d=60_000 if unidade=='ms' else 60_000_000
    a=int(pd.Timestamp(inicio).timestamp()//60)*d
    p=100*np.exp(np.arange(n)*.00001+np.sin(np.arange(n)/100)*.001)
    return [[a+i*d,float(v),float(v*1.01),float(v*.99),float(v*1.001),2.,a+(i+1)*d-1,200.,3,1.,100.,0] for i,v in enumerate(p)]


class Mercado(unittest.TestCase):
    def setUp(self):
        self.periodo=Periodo('2025-01-01T00:00:00Z','2025-01-01T02:00:00Z')

    def test_unidades_ms_us_mesma_grade(self):
        a,_=normalizar(linhas(),self.periodo,'ms');b,_=normalizar(linhas(unidade='us'),self.periodo,'us')
        pd.testing.assert_frame_equal(a,b,check_exact=True)
        with self.assertRaises(ValueError):normalizar(linhas(unidade='us'),self.periodo,'ms')

    def test_tempo_naive_ou_periodo_invertido_rejeitado(self):
        for a,b in [('2025-01-01','2025-01-02'),('2025-01-02T00:00Z','2025-01-01T00:00Z'),('2025-01-01T00:00:01Z','2025-01-02T00:00Z')]:
            with self.assertRaises(ValueError):Periodo(a,b)

    def test_fuso_converte_utc(self):
        p=Periodo('2024-12-31T21:00:00-03:00','2024-12-31T23:00:00-03:00')
        self.assertEqual(p,self.periodo)

    def test_lacuna_interrupcao_e_volume_zero_diferentes(self):
        r=linhas();r[3][5]=0;r[4][6]-=1000;r.pop(8)
        q,res=normalizar(r,self.periodo,'ms')
        self.assertEqual(res['interrompidos'],1);self.assertEqual(res['ausentes_na_fonte'],1)
        self.assertTrue(q.loc[3,'completo']);self.assertEqual(q.loc[3,'volume'],0)
        self.assertTrue(q.loc[4,'observado']);self.assertFalse(q.loc[4,'completo'])
        self.assertFalse(q.loc[8,'observado']);self.assertTrue(np.isnan(q.loc[8,'close']))
        self.assertFalse(agregar(q,60).loc[0,'completo'])

    def test_agregacao_ohlcv_e_disponibilidade(self):
        q,_=normalizar(linhas(),self.periodo,'ms');a=agregar(q,60)
        self.assertEqual(len(a),2);self.assertEqual(a.loc[0,'open'],q.loc[0,'open'])
        self.assertEqual(a.loc[0,'close'],q.loc[59,'close']);self.assertEqual(a.loc[0,'volume'],120)
        self.assertEqual(a.loc[0,'high'],q.loc[:59,'high'].max())
        self.assertEqual(a.loc[0,'fim_utc'],pd.Timestamp('2025-01-01T01:00:00Z'))
        self.assertFalse({'alvo','retorno','causal'}&set(a.columns))

    def test_agregacao_15m_sintetica_e_borda_rejeitada(self):
        q,_=normalizar(linhas(),self.periodo,'ms');self.assertEqual(len(agregar(q,15)),8)
        with self.assertRaises(ValueError):agregar(q.iloc[1:].copy(),60)

    def test_duplicata_desordem_e_fora_do_periodo_rejeitadas(self):
        for caso in (linhas()+[linhas()[0]],linhas()[::-1],linhas(n=121)):
            with self.assertRaises(ValueError):normalizar(caso,self.periodo,'ms')

    def test_campos_invalidos_rejeitados(self):
        for coluna,valor in [(1,0),(2,1),(5,-1),(8,1.5),(4,float('inf')),(6,0)]:
            r=linhas();r[0][coluna]=valor
            with self.subTest(coluna=coluna):
                with self.assertRaises(ValueError):normalizar(r,self.periodo,'ms')
        with self.assertRaises(ValueError):normalizar([[1,2]],self.periodo,'ms')

    def test_resposta_vazia_preserva_calendario_ausente(self):
        q,r=normalizar([],self.periodo,'ms')
        self.assertEqual(len(q),120);self.assertEqual(r['indisponiveis'],120)
        self.assertFalse(q.completo.any())

    def test_checksum_nome_conteudo_e_zip(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'BTCUSDT-1m-2025-01.zip';c=Path(str(p)+'.CHECKSUM')
            with zipfile.ZipFile(p,'w') as z:z.writestr(p.with_suffix('.csv').name,pd.DataFrame(linhas()).to_csv(index=False,header=False))
            h=hashlib.sha256(p.read_bytes()).hexdigest();c.write_text(h+'  '+p.name)
            self.assertEqual(conferir_checksum(p,c),h);self.assertEqual(ler_zip(p).shape,(120,12))
            c.write_text(h+'  outro.zip')
            with self.assertRaises(ValueError):conferir_checksum(p,c)
            c.write_text('0'*64+'  '+p.name)
            with self.assertRaises(ValueError):conferir_checksum(p,c)


class Resposta(io.BytesIO):
    status=200
    headers={'X-MBX-USED-WEIGHT-1M':'2'}


class Rede(unittest.TestCase):
    def test_429_respeita_retry_after(self):
        chamadas=[];esperas=[]
        def abrir(req,timeout):
            chamadas.append(req.full_url)
            if len(chamadas)==1:raise HTTPError(req.full_url,429,'limite',{'Retry-After':'2'},io.BytesIO(b'limite'))
            return Resposta(b'{}')
        with tempfile.TemporaryDirectory() as d:
            c=ClienteHTTP(Path(d),abrir=abrir,esperar=esperas.append)
            self.assertEqual(c.obter('https://data-api.binance.vision/api/v3/time')[0],b'{}')
            self.assertIn(2.,esperas);self.assertEqual(len(chamadas),2)

    def test_bloqueio_e_espera_longa_nao_insistem(self):
        for status in (403,418,451,429):
            chamadas=[]
            def abrir(req,timeout):
                chamadas.append(req.full_url)
                raise HTTPError(req.full_url,status,'bloqueio',{'Retry-After':'1000'},io.BytesIO(b'erro'))
            with tempfile.TemporaryDirectory() as d:
                c=ClienteHTTP(Path(d),abrir=abrir,esperar=lambda _:None)
                with self.assertRaises((HTTPError,RuntimeError)):c.obter('https://data-api.binance.vision/api/v3/time')
                self.assertEqual(len(chamadas),1)

    def test_cliente_nao_acessa_conta_ou_ordens(self):
        with tempfile.TemporaryDirectory() as d:
            c=ClienteHTTP(Path(d))
            for url in ('https://data-api.binance.vision/api/v3/order','https://example.com/data','http://data-api.binance.vision/api/v3/time'):
                with self.assertRaises(ValueError):c.obter(url)

    def test_paginacao_curta_com_lacuna_continua(self):
        r=linhas(n=5);r.pop(2);requisicoes=[]
        class Cliente:
            def obter(self,url):
                if url.endswith('/time'):dados={'serverTime':int(pd.Timestamp('2026-01-01T00:00Z').timestamp()*1000)}
                else:
                    args=parse_qs(urlparse(url).query);requisicoes.append(args)
                    dados=[x for x in r if x[0]>=int(args['startTime'][0])][:1]
                corpo=json.dumps(dados).encode();return corpo,{'sha256':hashlib.sha256(corpo).hexdigest()}
        with tempfile.TemporaryDirectory() as d:
            q,s=consultar(Cliente(),'BTCUSDT',Periodo('2025-01-01T00:00Z','2025-01-01T00:05Z'),Path(d),limite=2)
            self.assertEqual(s['completos'],4);self.assertEqual(s['ausentes_na_fonte'],1)
            self.assertEqual(len(requisicoes),4)
            self.assertEqual(int(requisicoes[0]['endTime'][0]),r[-1][0]+59999)
            self.assertTrue(all(a['timeZone']==['0'] for a in requisicoes))

    def test_api_rejeita_candle_aberto_sem_pedir_klines(self):
        class Cliente:
            def obter(self,url):
                assert url.endswith('/time')
                return json.dumps({'serverTime':1735689600000}).encode(),{}
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):consultar(Cliente(),'BTCUSDT',Periodo('2025-01-01T00:00Z','2025-01-01T00:05Z'),Path(d))

    def test_api_pagina_repetida_rejeitada(self):
        r=linhas(n=2)
        class Cliente:
            def obter(self,url):
                dados={'serverTime':1767225600000} if url.endswith('/time') else r
                corpo=json.dumps(dados).encode();return corpo,{'sha256':hashlib.sha256(corpo).hexdigest()}
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):consultar(Cliente(),'BTCUSDT',Periodo('2025-01-01T00:00Z','2025-01-01T00:05Z'),Path(d),limite=2)


if __name__=='__main__':unittest.main()
