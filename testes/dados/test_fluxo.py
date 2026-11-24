"""Integração com arquivos sintéticos; nunca consulta rede ou inicia modelos."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import numpy as np
import pandas as pd
from infraestrutura.artefatos import abrir_artefato,sha256,ler_json,tentativa,fontes
from mercado_binance import Periodo,importar_arquivos,agregar_mercado,baixar_arquivos,coletar_api
from entradas_modelo import preparar_entradas,carregar_conjunto
from .test_mercado import linhas
from .test_entradas import configuracao


class Fluxo(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.raiz=Path(self.tmp.name)
        self.periodo=Periodo('2021-01-01T00:00Z','2021-02-01T00:00Z')

    def arquivo(self,invalido=False):
        p=self.raiz/'brutos/BTCUSDT/BTCUSDT-1m-2021-01.zip';p.parent.mkdir(parents=True)
        q=pd.DataFrame(linhas('2021-01-01T00:00Z',self.periodo.minutos))
        if invalido:q.iloc[0,2]=1
        with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr(p.with_suffix('.csv').name,q.to_csv(index=False,header=False))
        Path(str(p)+'.CHECKSUM').write_text(sha256(p)+'  '+p.name)
        return p

    def test_fluxo_completo_reuso_e_integridade_ancestral(self):
        p=self.arquivo()
        with contextlib.redirect_stdout(io.StringIO()):
            mercado=importar_arquivos(self.raiz/'brutos',['BTCUSDT'],self.periodo,self.raiz/'mercado')
        candles=agregar_mercado(mercado,60,self.raiz/'candles')
        entradas=preparar_entradas(candles,configuracao(),self.raiz/'entradas')
        conjunto=carregar_conjunto(entradas)
        self.assertEqual(conjunto.matriz.shape,(744,5))
        self.assertEqual(conjunto.janelas(conjunto.partes['teste'].indice_candle.values[:2]).shape,(2,168,5))
        antes=sha256(entradas/'manifesto.json')
        self.assertEqual(entradas,preparar_entradas(candles,configuracao(),self.raiz/'entradas'))
        self.assertEqual(antes,sha256(entradas/'manifesto.json'))
        p.write_bytes(p.read_bytes()+b'alterado')
        with self.assertRaisesRegex(ValueError,'Fonte original'):carregar_conjunto(entradas)

    def test_erro_nao_publica_e_preserva_tentativa(self):
        self.arquivo(invalido=True)
        with self.assertRaisesRegex(ValueError,'OHLC'):
            importar_arquivos(self.raiz/'brutos',['BTCUSDT'],self.periodo,self.raiz/'mercado')
        self.assertEqual([p.name for p in (self.raiz/'mercado').iterdir()],['tentativas'])
        falhas=list((self.raiz/'mercado').glob('tentativas/*/falha.json'))
        self.assertEqual(len(falhas),1);self.assertIn('OHLC',ler_json(falhas[0])['erro'])

    def test_alteracao_de_arquivo_publicado_rejeitada(self):
        assinatura={'fontes':fontes('infraestrutura'),'teste':'fixture'}
        with tentativa(self.raiz/'artefatos','teste',assinatura) as (p,existe):
            (p/'conteudo.txt').write_text('antes')
        p=next(x for x in (self.raiz/'artefatos').iterdir() if x.name!='tentativas')
        (p/'conteudo.txt').write_text('depois')
        with self.assertRaisesRegex(ValueError,'alterado'):abrir_artefato(p)

    def test_baixar_preserva_corpo_e_confere_checksum(self):
        p=self.arquivo();zip_bytes=p.read_bytes();checksum=Path(str(p)+'.CHECKSUM').read_bytes()
        with patch('mercado_binance.pipeline.ClienteHTTP') as cliente:
            cliente.return_value.obter.side_effect=lambda url:(checksum if url.endswith('.CHECKSUM') else zip_bytes,{})
            brutos=baixar_arquivos(['BTCUSDT'],self.periodo,self.raiz/'coletas')
        self.assertEqual(sha256(brutos/'BTCUSDT'/p.name),sha256(p))
        self.assertEqual(ler_json(brutos.parent/'conclusao.json')['status'],'baixado_checksum_conferido')

    def test_api_preserva_interrupcao_por_orcamento(self):
        import hashlib
        r=linhas(n=2)
        def obter(url):
            dados={'serverTime':1767225600000} if url.endswith('/time') else r
            b=json.dumps(dados).encode();return b,{'sha256':hashlib.sha256(b).hexdigest()}
        with patch('mercado_binance.pipeline.ClienteHTTP') as cliente:
            cliente.return_value.obter.side_effect=obter
            with self.assertRaisesRegex(RuntimeError,'Orçamento'):
                coletar_api('BTCUSDT',Periodo('2025-01-01T00:00Z','2025-01-01T00:05Z'),
                            self.raiz/'mercado',self.raiz/'coletas',limite=2,maximo_paginas=1)
        self.assertFalse((self.raiz/'mercado').exists())
        self.assertEqual(len(list((self.raiz/'coletas').glob('*/falha.json'))),1)
        self.assertEqual(len(list((self.raiz/'coletas').glob('*/respostas/pagina_*.json'))),1)


if __name__=='__main__':unittest.main()
