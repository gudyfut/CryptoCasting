from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from camada_dados.armazenamento import extrair_checksum, sha256_arquivo, validar_zip
from camada_dados.auditoria import auditar_zip, detectar_unidade_timestamp
from camada_dados.configuracao import _data_utc, carregar_configuracao, gerar_itens_coleta
from camada_dados.dominio import ItemColeta
from camada_dados.manifesto import RepositorioManifesto
from camada_dados.servico_coleta import ServicoColeta


RAIZ = Path(__file__).resolve().parents[1]
PASTA_TESTES = RAIZ / "tests" / "artefatos_locais"


class TesteConfiguracao(unittest.TestCase):
    def test_inventario_oficial_tem_240_itens(self) -> None:
        configuracao = carregar_configuracao(RAIZ / "configuracoes/coleta_oficial.json")
        itens = gerar_itens_coleta(configuracao)
        self.assertEqual(240, len(itens))
        self.assertEqual(("BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT"), configuracao.pares)
        self.assertEqual("BTCUSDT-15m-2021-01.zip", itens[0].caminho_relativo.name)
        self.assertEqual("BNBUSDT-15m-2021-01.zip", itens[120].caminho_relativo.name)
        self.assertEqual("XRPUSDT-15m-2025-12.zip", itens[-1].caminho_relativo.name)

    def test_url_e_deterministica(self) -> None:
        configuracao = carregar_configuracao(RAIZ / "configuracoes/coleta_oficial.json")
        primeiro = gerar_itens_coleta(configuracao)[0]
        self.assertEqual(
            "https://data.binance.vision/data/spot/monthly/klines/"
            "BTCUSDT/15m/BTCUSDT-15m-2021-01.zip",
            primeiro.url_dados,
        )

    def test_configuracao_recusa_data_sem_fuso_e_periodo_diferente(self) -> None:
        with self.assertRaisesRegex(ValueError, "fuso horário"):
            _data_utc("2021-01-01T00:00:00")
        configuracao = carregar_configuracao(RAIZ / "configuracoes/coleta_oficial.json")
        with self.assertRaisesRegex(ValueError, "período oficial"):
            replace(configuracao, fim=datetime(2025, 1, 1, tzinfo=timezone.utc)).validar()


class TesteIntegridade(unittest.TestCase):
    def test_timestamp_milissegundos_e_microssegundos(self) -> None:
        self.assertEqual("milissegundos", detectar_unidade_timestamp(1_735_689_600_000))
        self.assertEqual("microssegundos", detectar_unidade_timestamp(1_735_689_600_000_000))

    def test_hash_e_extracao_checksum(self) -> None:
        caminho = PASTA_TESTES / "arquivo.bin"
        try:
            caminho.write_bytes(b"CryptoCasting")
            resumo = sha256_arquivo(caminho)
            self.assertEqual(resumo, extrair_checksum(f"{resumo}  arquivo.bin"))
        finally:
            caminho.unlink(missing_ok=True)

    def test_auditoria_detecta_lacuna_e_ohlc_invalido(self) -> None:
        caminho = PASTA_TESTES / "BTCUSDT-15m-2025-01.zip"
        try:
            linhas = (
                "1735689600000000,100,110,90,105,1\n"
                "1735691400000000,100,90,95,105,1\n"
            )
            with zipfile.ZipFile(caminho, "w") as arquivo_zip:
                arquivo_zip.writestr("BTCUSDT-15m-2025-01.csv", linhas)
            validar_zip(caminho, "BTCUSDT-15m-2025-01.csv")
            item = ItemColeta(
                par="BTCUSDT",
                intervalo="15m",
                competencia="2025-01",
                inicio=datetime(2025, 1, 1, tzinfo=timezone.utc),
                fim=datetime(2025, 1, 1, 0, 45, tzinfo=timezone.utc),
                url_dados="",
                url_checksum="",
                caminho_relativo=Path(caminho.name),
            )
            resultado = auditar_zip(caminho, item)
            self.assertEqual("microssegundos", resultado.unidade_timestamp_origem)
            self.assertEqual(2, resultado.lacunas)
            self.assertTrue(any("OHLC inconsistente" in erro for erro in resultado.erros))
        finally:
            caminho.unlink(missing_ok=True)

    def test_auditoria_detecta_duplicata_conflitante(self) -> None:
        caminho = PASTA_TESTES / "BTCUSDT-15m-2021-01.zip"
        try:
            linhas = (
                "1609459200000,100,110,90,105,1\n"
                "1609459200000,100,111,90,106,1\n"
            )
            with zipfile.ZipFile(caminho, "w") as arquivo_zip:
                arquivo_zip.writestr("BTCUSDT-15m-2021-01.csv", linhas)
            item = ItemColeta(
                par="BTCUSDT",
                intervalo="15m",
                competencia="2021-01",
                inicio=datetime(2021, 1, 1, tzinfo=timezone.utc),
                fim=datetime(2021, 1, 1, 0, 15, tzinfo=timezone.utc),
                url_dados="",
                url_checksum="",
                caminho_relativo=Path(caminho.name),
            )
            resultado = auditar_zip(caminho, item)
            self.assertEqual(1, resultado.duplicatas)
            self.assertEqual(1, resultado.duplicatas_conflitantes)
        finally:
            caminho.unlink(missing_ok=True)


class TesteManifesto(unittest.TestCase):
    def test_salvar_mesma_chave_substitui_em_vez_de_duplicar(self) -> None:
        repositorio = RepositorioManifesto(PASTA_TESTES)
        try:
            base = {
                "chave": "BTCUSDT:15m:2021-01",
                "par": "BTCUSDT",
                "intervalo": "15m",
                "competencia": "2021-01",
                "status": "invalido",
                "erros": "teste",
                "avisos": "",
            }
            repositorio.salvar(base)
            repositorio.salvar({**base, "status": "valido", "erros": ""})
            linhas = repositorio.caminho_jsonl.read_text(encoding="utf-8").splitlines()
            self.assertEqual(1, len(linhas))
            self.assertEqual("valido", json.loads(linhas[0])["status"])
        finally:
            repositorio.caminho_jsonl.unlink(missing_ok=True)
            repositorio.caminho_csv.unlink(missing_ok=True)


class TesteRetomada(unittest.TestCase):
    def test_zip_corrompido_sem_checksum_e_baixado_novamente(self) -> None:
        class FonteLocal:
            def __init__(self) -> None:
                self.forcado = False

            def baixar(self, url: str, destino: Path, forcar: bool = False) -> bool:
                if url.endswith(".CHECKSUM"):
                    return False
                if not forcar:
                    return False
                self.forcado = True
                with zipfile.ZipFile(destino, "w") as arquivo_zip:
                    arquivo_zip.writestr(
                        "BNBUSDT-15m-2021-01.csv",
                        "1609459200000,10,11,9,10,1\n",
                    )
                return True

        with tempfile.TemporaryDirectory() as temporario:
            configuracao = carregar_configuracao(RAIZ / "configuracoes/coleta_oficial.json")
            configuracao = replace(configuracao, diretorio_dados=Path(temporario) / "binance_spot")
            item = gerar_itens_coleta(configuracao)[120]
            caminho = configuracao.diretorio_dados / item.caminho_relativo
            caminho.parent.mkdir(parents=True)
            caminho.write_bytes(b"ZIP incompleto")
            fonte = FonteLocal()
            registro = ServicoColeta(configuracao, fonte=fonte)._processar(item, False)
            self.assertTrue(fonte.forcado)
            self.assertTrue(registro["zip_valido"])
            self.assertIn("ZIP inválido foi baixado novamente", registro["avisos"])


if __name__ == "__main__":
    unittest.main()
