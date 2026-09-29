"""Checagens de alinhamento e métricas sem ajustar modelos nesta máquina."""

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from baseline_ar1.avaliacao import calcular_metricas
from baseline_ar1.execucao import executar_piloto
from baseline_ar1.modelo import ParametrosAR1, construir_pares_autorregressivos, prever_amostras
from run_baseline_desenvolvimento import resumir_resultados


class TesteBaselineAR1(unittest.TestCase):
    def setUp(self):
        aberturas = pd.date_range("2021-01-01", periods=5, freq="1d", tz="UTC")
        fechamentos = np.array([100.0, 102.0, 101.0, 103.0, 104.0])
        self.candles = pd.DataFrame({
            "par": "BTCUSDT", "granularidade": "1d",
            "abertura_utc": aberturas,
            "fim_utc": aberturas + pd.Timedelta(days=1),
            "close": fechamentos,
        })
        origens = [1, 2, 3]
        self.amostras = pd.DataFrame({
            "par": ["BTCUSDT"] * 3,
            "granularidade": ["1d"] * 3,
            "tarefa": ["24h"] * 3,
            "contexto_dias": [7] * 3,
            "horizonte_candles": [1] * 3,
            "indice_contexto_fim": origens,
            "indice_alvo": [2, 3, 4],
            "origem_utc": self.candles.iloc[origens]["fim_utc"].reset_index(drop=True),
            "alvo_fim_utc": self.candles.iloc[[2, 3, 4]]["fim_utc"].reset_index(drop=True),
            "preco_origem": fechamentos[origens],
            "preco_alvo": fechamentos[[2, 3, 4]],
            "retorno_futuro": np.log(fechamentos[[2, 3, 4]] / fechamentos[origens]),
            "classe_alta": [0, 1, 1],
            "empate": [False] * 3,
        })

    def test_pares_usam_apenas_retorno_observado_e_alvo_consecutivo(self):
        anteriores, seguintes = construir_pares_autorregressivos(self.candles, self.amostras)
        self.assertAlmostEqual(anteriores[0], np.log(102 / 100))
        self.assertAlmostEqual(seguintes[0], np.log(101 / 102))
        self.assertEqual(len(anteriores), 3)

    def test_previsao_com_coeficientes_congelados_e_metricas(self):
        parametros = ParametrosAR1(alfa=0.0, phi=-1.0, quantidade_pares=3)
        previsoes = prever_amostras(self.candles, self.amostras, parametros)
        self.assertEqual(previsoes["classe_prevista_ar1"].tolist(), [0, 1, 0])
        metricas = calcular_metricas(previsoes)
        self.assertAlmostEqual(metricas["balanced_accuracy"], 0.75)
        self.assertEqual(metricas["matriz_confusao_linhas_reais_colunas_previstas"], [[1, 0], [1, 1]])

    def test_lacuna_ou_par_errado_sao_rejeitados(self):
        diferentes = self.amostras.copy()
        diferentes.loc[0, "par"] = "ETHUSDT"
        with self.assertRaisesRegex(ValueError, "outro par"):
            construir_pares_autorregressivos(self.candles, diferentes)
        com_lacuna = self.candles.copy()
        com_lacuna.loc[2, "fim_utc"] += pd.Timedelta(days=1)
        with self.assertRaisesRegex(ValueError, "lacuna"):
            construir_pares_autorregressivos(com_lacuna, self.amostras)

    def test_piloto_impede_fold_final_antes_do_congelamento(self):
        with self.assertRaisesRegex(ValueError, "somente D1"):
            executar_piloto(Path("inexistente"), fold_nome="F1")

    def test_resumo_pesa_folds_igualmente_e_rejeita_finais(self):
        resultados = []
        for nome, ba, n in (("D1", 0.4, 80), ("D2", 0.6, 100)):
            resultados.append({
                "par": "BTCUSDT", "fold": nome, "tarefa": "principal",
                "pares_retorno_ajuste": 500, "caminho_resultado": "teste.json",
                "sha256_resultado": "a" * 64,
                "metricas": {"teste": {
                    "amostras": n, "balanced_accuracy": ba, "accuracy": ba,
                    "f1_macro": ba, "predicoes_alta": 1, "suporte_alta": 40,
                    "por_classe": {"1": {"recall": ba}},
                }},
            })
        resumo = resumir_resultados(resultados)
        self.assertAlmostEqual(resumo["resumo_por_par"]["BTCUSDT"]["ba_media_nao_ponderada"], 0.5)
        resultados[1]["fold"] = "F1"
        with self.assertRaisesRegex(ValueError, "somente a matriz principal"):
            resumir_resultados(resultados)


if __name__ == "__main__":
    unittest.main()
