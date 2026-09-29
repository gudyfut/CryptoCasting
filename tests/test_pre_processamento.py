"""Verificações pequenas, sintéticas e sem executar a coleta ou o pipeline oficial."""

import unittest
import json
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import numpy as np
import pandas as pd

from pre_processamento.amostras import (
    construir_amostras,
    origens_da_tarefa_complementar,
    origens_da_tarefa_principal,
)
from pre_processamento.contrato import FEATURES_OHLCV, carregar_configuracao_processamento, candles_por_horizonte_24h
from pre_processamento.folds import FOLDS, ajustar_normalizador, montar_janela, separar_fold
from pre_processamento.origem import carregar_manifesto_aprovado
from pre_processamento.origem import ler_zip_aprovado
from camada_dados.armazenamento import sha256_arquivo
from camada_dados.configuracao import gerar_itens_coleta
from camada_dados.dominio import ItemColeta
from pre_processamento.relatorios import calcular_volatilidade_comum, resumir_lacunas_15m
from pre_processamento.transformacoes import agregar_candles, associar_indicadores, indicadores_diarios


def base_sintetica(dias=22):
    aberturas = pd.date_range("2021-01-01", periods=dias * 96, freq="15min", tz="UTC")
    precos = 100 + np.arange(len(aberturas)) / 1000
    return pd.DataFrame({
        "abertura_utc": aberturas,
        "fim_utc": aberturas + pd.Timedelta(minutes=15),
        "open": precos,
        "high": precos + 1,
        "low": precos - 1,
        "close": precos + 0.1,
        "volume": np.ones(len(aberturas)),
    })


class TesteProcessamento(unittest.TestCase):
    def test_manifesto_incompleto_bloqueia_processamento(self):
        raiz = Path(__file__).resolve().parents[1]
        configuracao = carregar_configuracao_processamento(raiz / "configuracoes" / "pre_processamento.json")
        with TemporaryDirectory() as diretorio:
            manifesto = Path(diretorio) / "manifesto.jsonl"
            manifesto.write_text("", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "incompleto"):
                carregar_manifesto_aprovado(replace(configuracao, caminho_manifesto_coleta=manifesto))

    def test_manifesto_aceita_somente_lacuna_isolada_com_checksum(self):
        raiz = Path(__file__).resolve().parents[1]
        configuracao = carregar_configuracao_processamento(raiz / "configuracoes" / "pre_processamento.json")
        registros = []
        for item in gerar_itens_coleta(configuracao.coleta):
            quantidade = int((item.fim - item.inicio).total_seconds() // 900)
            registros.append({
                "chave": item.chave, "par": item.par, "intervalo": item.intervalo,
                "competencia": item.competencia, "status": "valido", "zip_valido": True,
                "checksum_valido": True, "quantidade_esperada": quantidade,
                "quantidade_observada": quantidade, "lacunas": 0, "duplicatas": 0,
                "duplicatas_conflitantes": 0, "erros": "", "sha256": "a" * 64,
            })
        registros[0].update({
            "status": "invalido", "quantidade_observada": registros[0]["quantidade_esperada"] - 2,
            "lacunas": 2, "erros": "2 candle(s) ausente(s)",
        })
        with TemporaryDirectory() as diretorio:
            manifesto = Path(diretorio) / "manifesto.jsonl"
            configuracao = replace(configuracao, caminho_manifesto_coleta=manifesto)
            manifesto.write_text("\n".join(json.dumps(r) for r in registros), encoding="utf-8")
            carregados, _ = carregar_manifesto_aprovado(configuracao)
            self.assertEqual(len(carregados), 240)
            registros[0]["erros"] += " | 1 timestamp duplicado"
            manifesto.write_text("\n".join(json.dumps(r) for r in registros), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Falha além de lacunas"):
                carregar_manifesto_aprovado(configuracao)

    def test_leitor_preserva_lacuna_15m_auditada(self):
        raiz = Path(__file__).resolve().parents[1]
        configuracao = carregar_configuracao_processamento(raiz / "configuracoes" / "pre_processamento.json")
        with TemporaryDirectory() as diretorio:
            diretorio_base = Path(diretorio)
            caminho_relativo = Path("BTCUSDT") / "15m" / "BTCUSDT-15m-2021-01.zip"
            caminho = diretorio_base / caminho_relativo
            caminho.parent.mkdir(parents=True)
            csv = "".join(
                f"{int(instante.timestamp() * 1000)},100,101,99,100,1\n"
                for instante in pd.to_datetime(
                    ["2021-01-01 00:00Z", "2021-01-01 00:15Z", "2021-01-01 00:45Z"]
                )
            )
            with ZipFile(caminho, "w") as arquivo:
                arquivo.writestr(caminho.with_suffix(".csv").name, csv)
            inicio = pd.Timestamp("2021-01-01", tz="UTC")
            item = ItemColeta(
                "BTCUSDT", "15m", "2021-01", inicio.to_pydatetime(),
                (inicio + pd.Timedelta(hours=1)).to_pydatetime(), "", "", caminho_relativo,
            )
            configuracao = replace(
                configuracao, coleta=replace(configuracao.coleta, diretorio_dados=diretorio_base)
            )
            registro = {"sha256": sha256_arquivo(caminho), "quantidade_observada": 3,
                        "unidade_timestamp_origem": "milissegundos"}
            quadro = ler_zip_aprovado(configuracao, item, registro)
            self.assertEqual(len(quadro), 3)
            self.assertEqual(quadro["abertura_utc"].diff().iloc[-1], pd.Timedelta(minutes=30))
            lacunas = resumir_lacunas_15m(
                quadro, "BTCUSDT", inicio, inicio + pd.Timedelta(hours=1), 1,
            )
            self.assertEqual(int(lacunas.iloc[0]["candles_15m_ausentes"]), 1)
            self.assertEqual(lacunas.iloc[0]["abertura_inicio_utc"], inicio + pd.Timedelta(minutes=30))
            with self.assertRaisesRegex(ValueError, "divergem do manifesto"):
                resumir_lacunas_15m(quadro, "BTCUSDT", inicio, inicio + pd.Timedelta(hours=1), 0)

    def test_agregacao_utc_e_bloqueio_de_candle_incompleto(self):
        base = base_sintetica(2)
        hora = agregar_candles(base, "1h")
        self.assertEqual(len(hora), 48)
        self.assertEqual(hora.iloc[0]["open"], base.iloc[0]["open"])
        self.assertEqual(hora.iloc[0]["close"], base.iloc[3]["close"])
        self.assertEqual(hora.iloc[0]["volume"], 4)
        self.assertEqual(hora.iloc[0]["fim_utc"], pd.Timestamp("2021-01-01 01:00", tz="UTC"))
        sem_um = base.drop(index=1)
        self.assertEqual(len(agregar_candles(sem_um, "1h")), 47)

    def test_indicadores_causais_e_reinicio_apos_lacuna(self):
        base = base_sintetica(12)
        diario = agregar_candles(base, "1d")
        indicadores = indicadores_diarios(diario)
        intradia = associar_indicadores(base, indicadores)
        indice_primeiro = intradia.index[intradia["fim_utc"] == pd.Timestamp("2021-01-09", tz="UTC")][0]
        self.assertTrue(np.isfinite(intradia.loc[indice_primeiro, "volatilidade_7d"]))
        self.assertTrue(np.isnan(intradia.loc[indice_primeiro - 1, "volatilidade_7d"]))
        sem_dia = diario.drop(index=8).reset_index(drop=True)
        apos_lacuna = indicadores_diarios(sem_dia)
        self.assertTrue(apos_lacuna.iloc[-1]["volatilidade_7d"] != apos_lacuna.iloc[-1]["volatilidade_7d"])

    def test_grade_principal_contextos_rotulo_e_lacuna(self):
        base = base_sintetica(30)
        diario = agregar_candles(base, "1d")
        candles = associar_indicadores(base, indicadores_diarios(diario))
        origens = origens_da_tarefa_principal(candles, "15m")
        self.assertGreater(len(origens), 0)
        a7 = construir_amostras(candles, origens, "BTCUSDT", "15m", 7, 96, "24h")
        a14 = construir_amostras(candles, origens, "BTCUSDT", "15m", 14, 96, "24h")
        self.assertTrue(a7["origem_utc"].equals(a14["origem_utc"]))
        self.assertTrue((a7["classe_alta"] == 1).all())
        self.assertTrue((a7["indice_contexto_fim"] - a7["indice_contexto_inicio"] == 671).all())
        self.assertTrue((a7["alvo_fim_utc"] - a7["origem_utc"] == pd.Timedelta(days=1)).all())
        self.assertTrue((a7["origem_utc"].dt.hour == 0).all())
        com_lacuna = candles.drop(index=24 * 96 + 20).reset_index(drop=True)
        novas = origens_da_tarefa_principal(com_lacuna, "15m")
        self.assertLess(len(novas), len(origens))

    def test_mesmo_preco_e_rotulo_nas_quatro_resolucoes(self):
        base = base_sintetica(30)
        diarios = agregar_candles(base, "1d")
        indicadores = indicadores_diarios(diarios)
        candidatos = {}
        candles_por_granularidade = {}
        for granularidade in ("15m", "1h", "4h", "1d"):
            quadro = associar_indicadores(agregar_candles(base, granularidade), indicadores)
            candles_por_granularidade[granularidade] = quadro
            posicoes = origens_da_tarefa_principal(quadro, granularidade)
            candidatos[granularidade] = pd.DatetimeIndex(quadro.iloc[posicoes]["fim_utc"])
        grade = candidatos["15m"]
        for outros in list(candidatos.values())[1:]:
            grade = grade.intersection(outros)
        self.assertGreater(len(grade), 0)
        referencias = []
        for granularidade, quadro in candles_por_granularidade.items():
            posicoes = pd.Index(quadro["fim_utc"]).get_indexer(grade)
            tabela = construir_amostras(
                quadro, posicoes, "BTCUSDT", granularidade, 7,
                candles_por_horizonte_24h(granularidade), "24h",
            )
            referencias.append(tabela[["origem_utc", "alvo_fim_utc", "preco_origem", "preco_alvo", "classe_alta"]].reset_index(drop=True))
        for tabela in referencias[1:]:
            pd.testing.assert_frame_equal(tabela, referencias[0])

    def test_empate_fica_na_classe_zero(self):
        base = base_sintetica(20)
        base["close"] = 100.0
        diario = agregar_candles(base, "1d")
        candles = associar_indicadores(base, indicadores_diarios(diario))
        origens = origens_da_tarefa_complementar(candles, "15m")
        amostras = construir_amostras(candles, origens, "BTCUSDT", "15m", 7, 1, "proximo_candle")
        self.assertGreater(len(amostras), 0)
        self.assertTrue((amostras["classe_alta"] == 0).all())
        self.assertTrue(amostras["empate"].all())

    def test_purga_estrita_e_scaler_somente_candles_unicos(self):
        tempos = pd.to_datetime(["2022-09-29", "2022-09-30", "2022-10-01", "2022-12-31", "2023-01-01"], utc=True)
        amostras = pd.DataFrame({
            "origem_utc": tempos,
            "alvo_fim_utc": tempos + pd.Timedelta(days=1),
            "indice_contexto_inicio": [0, 1, 2, 3, 4],
            "indice_contexto_fim": [1, 2, 3, 4, 5],
        })
        blocos = separar_fold(amostras, FOLDS[0])
        self.assertEqual(blocos["treino"]["origem_utc"].tolist(), [tempos[0]])
        self.assertEqual(blocos["validacao"]["origem_utc"].tolist(), [tempos[2]])
        candles = base_sintetica(8).copy().reset_index(drop=True)
        candles.insert(0, "par", "BTCUSDT")
        candles.insert(1, "granularidade", "15m")
        treino = pd.DataFrame({"indice_contexto_inicio": [0, 1], "indice_contexto_fim": [2, 3]})
        normalizador, indices = ajustar_normalizador(candles, treino)
        self.assertEqual(indices.tolist(), [0, 1, 2, 3])
        self.assertAlmostEqual(normalizador.mean_[0], candles.iloc[:4]["open"].mean())
        amostra = pd.Series({
            "par": "BTCUSDT", "granularidade": "15m",
            "contexto_dias": 7, "horizonte_candles": 1,
            "indice_contexto_inicio": 0, "indice_contexto_fim": 671, "indice_alvo": 672,
            "contexto_inicio_utc": candles.iloc[0]["abertura_utc"],
            "origem_utc": candles.iloc[671]["fim_utc"],
            "alvo_fim_utc": candles.iloc[672]["fim_utc"],
        })
        self.assertEqual(montar_janela(candles, amostra, FEATURES_OHLCV, normalizador).shape, (672, 5))
        amostra["origem_utc"] += pd.Timedelta(minutes=15)
        with self.assertRaises(ValueError):
            montar_janela(candles, amostra, FEATURES_OHLCV, normalizador)
        amostra["origem_utc"] -= pd.Timedelta(minutes=15)
        amostra["par"] = "ETHUSDT"
        with self.assertRaises(ValueError):
            montar_janela(candles, amostra, FEATURES_OHLCV, normalizador)

    def test_volatilidade_usa_mesmos_dias(self):
        dias = pd.date_range("2021-01-02", periods=5, freq="1d", tz="UTC")
        diarios = {}
        for par in ("BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT"):
            quadro = pd.DataFrame({"fim_utc": dias, "close": [100, 101, 100, 103, 105]})
            if par == "BNBUSDT":
                quadro = quadro.drop(index=2)
            diarios[par] = quadro
        tabela, cobertura = calcular_volatilidade_comum(diarios)
        self.assertEqual(int(tabela.iloc[0]["dias_comuns"]), 2)
        self.assertEqual(len(cobertura), 4)

    def test_volatilidade_ano_do_candle_que_termina_em_janeiro(self):
        fins = pd.to_datetime(["2021-12-30", "2021-12-31", "2022-01-01", "2022-01-02"], utc=True)
        diarios = {
            par: pd.DataFrame({"fim_utc": fins, "close": [100, 101, 102, 103]})
            for par in ("BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT")
        }
        tabela, _ = calcular_volatilidade_comum(diarios)
        ano_2021 = tabela[(tabela["periodo"] == "2021") & (tabela["par"] == "BTCUSDT")]
        self.assertEqual(int(ano_2021.iloc[0]["dias_comuns"]), 2)


if __name__ == "__main__":
    unittest.main()
