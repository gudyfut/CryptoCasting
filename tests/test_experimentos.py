"""Verificações rápidas com dados sintéticos; nenhum otimizador ou treino é executado."""

import copy
import json
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from experimentos.avaliacao import alinhar_previsoes, calcular_metricas, comparar_modelos, testar_pt
from experimentos.consolidacao import consolidar
from experimentos.auditoria import auditar_execucao, ARQUIVOS_PAREADOS
from experimentos.configuracao import RAIZ, validar_configuracao, gerar_celulas
from experimentos.dados import JanelasTemporais, preparar_entradas, validar_amostras
from experimentos.registro import gravar_json, inventariar, verificar_resultado, assinatura_codigo
from experimentos.planejamento import construir_plano, documento_matriz, exemplo_temporal
from pre_processamento.folds import FOLDS
from experimentos.treinamento import criar_modelo, quadro_previsoes
from pre_processamento.amostras import construir_amostras
from modelo.mamba_minimal import Mamba
from camada_dados.armazenamento import sha256_arquivo


def criar_execucao_sintetica(raiz, configuracao, fold="D1", n=4, corretas=True):
    """Somente artefatos temporários; checkpoints são marcadores, jamais carregados."""
    destino = raiz / fold
    destino.mkdir()
    configuracao = {**configuracao, "folds": [fold]}
    celula = gerar_celulas(configuracao)[0]
    fronteiras = next(f for f in FOLDS if f.nome == fold)
    avaliacoes = {}
    for bloco, inicio in (("validacao", fronteiras.fim_treino), ("teste", fronteiras.fim_validacao)):
        datas = pd.date_range(inicio, periods=n, tz="UTC")
        reais = np.tile([0, 1], n // 2)
        previstas = reais if corretas else 1 - reais
        quadro = pd.DataFrame({"par": "BTCUSDT", "granularidade": "1d", "tarefa": "24h", "contexto_dias": 7,
            "fold": fold, "bloco": bloco, "origem_utc": datas, "alvo_fim_utc": datas + pd.Timedelta(days=1),
            "classe_alta": reais, "classe_prevista": previstas, "empate": False, "retorno_futuro": (2 * reais - 1) * .01})
        previsoes = {}
        for nome in ("ar1", "lstm", "mamba"):
            previsoes[nome] = quadro.assign(modelo=nome)
            if nome == "ar1":
                previsoes[nome]["retorno_previsto_ar1"] = (2 * previstas - 1) * .01
            else:
                previsoes[nome]["probabilidade_alta"] = .25 + .5 * previstas
                previsoes[nome]["seed"] = 42
            previsoes[nome].to_parquet(destino / f"previsoes_{nome}_{bloco}.parquet", index=False)
        avaliacoes[bloco] = comparar_modelos(previsoes)
    features = ["open", "high", "low", "close", "volume"]
    gravar_json(destino / "normalizador.json", {"metodo": "standard", "features": features, "quantidade_candles_ajuste": 5})
    np.save(destino / "indices_ajuste_normalizador.npy", np.arange(5))
    for nome in ("lstm", "mamba"):
        (destino / nome).mkdir()
        (destino / nome / "melhor.pt").write_bytes(b"marcador sintetico, sem pesos ou treinamento")
        gravar_json(destino / nome / "historico.json", {"epocas": []})
    registro = {"contrato": "entregas45-v1", "estado": "concluido", "tipo_fold": "desenvolvimento", "protocolo": "1.6",
        "celula": celula, "configuracao": configuracao, "fold": fronteiras.__dict__, "features": features, "dimensao_entrada": 5,
        "contagens": {"treino": 20, "validacao": n, "teste": n},
        "modelos": {"lstm": {"backend": "torch.nn.LSTM"}, "mamba": {"backend": "pytorch"}},
        "sha256_manifesto_dataset": "dados_sinteticos", "sha256_codigo": "teste", "sha256_protocolo": "teste",
        "ambiente": {"versoes": {}}, "avaliacoes": avaliacoes, "arquivos": inventariar(destino)}
    gravar_json(destino / "resultado.json", registro)
    return destino


class TesteExperimentos(unittest.TestCase):
    def setUp(self):
        self.configuracao = json.loads((RAIZ / "configuracoes/treino_piloto_cpu.json").read_text(encoding="utf-8"))
        datas = pd.date_range("2022-01-01", periods=40, freq="1d", tz="UTC")
        precos = 100 + np.arange(40) + 2 * (np.arange(40) % 2)
        self.candles = pd.DataFrame({"par": "BTCUSDT", "granularidade": "1d", "abertura_utc": datas,
            "fim_utc": datas + pd.Timedelta(days=1), "open": precos, "high": precos + 1,
            "low": precos - 1, "close": precos, "volume": np.arange(40) + 10})
        self.amostras = construir_amostras(self.candles, np.arange(7, 39), "BTCUSDT", "1d", 7, 1, "24h")
        self.celula = gerar_celulas(self.configuracao)[0]

    def test_configuracao_bloqueia_finais_e_erro_de_digitacao(self):
        config = copy.deepcopy(self.configuracao)
        config["folds"] = ["F1"]
        with self.assertRaisesRegex(ValueError, "F1–F8"):
            validar_configuracao(config)
        config = {**self.configuracao, "epocas": 1}
        with self.assertRaisesRegex(ValueError, "Chaves"):
            validar_configuracao(config)
        with self.assertRaisesRegex(ValueError, "inteiro"):
            validar_configuracao({**self.configuracao, "largura_mamba": 32.0})

    def test_celula_diaria_complementar_reutiliza_identidade(self):
        self.assertEqual(gerar_celulas(self.configuracao), gerar_celulas({**self.configuracao, "tarefa": "proximo_candle"}))

    def test_janela_confere_timestamp_rotulo_e_lacuna(self):
        validar_amostras(self.candles, self.amostras, self.celula)
        alteradas = self.amostras.copy()
        alteradas.loc[0, "origem_utc"] += pd.Timedelta(hours=1)
        with self.assertRaisesRegex(ValueError, "Timestamp"):
            validar_amostras(self.candles, alteradas, self.celula)
        alteradas = self.amostras.copy()
        alteradas.loc[0, "classe_alta"] = 1 - alteradas.loc[0, "classe_alta"]
        with self.assertRaisesRegex(ValueError, "Rótulo"):
            validar_amostras(self.candles, alteradas, self.celula)
        candles = self.candles.copy()
        candles.loc[2, "fim_utc"] += pd.Timedelta(hours=1)
        with self.assertRaisesRegex(ValueError, "lacuna"):
            validar_amostras(candles, self.amostras, self.celula)

    def test_scaler_nao_usa_futuro_e_janela_preserva_ordem(self):
        blocos = {"treino": self.amostras.iloc[:8], "validacao": self.amostras.iloc[8:16], "teste": self.amostras.iloc[16:]}
        matriz, estado, indices = preparar_entradas(self.candles, blocos, "ohlcv", "standard")
        alterados = self.candles.copy()
        alterados.loc[indices.max() + 1:, ["open", "high", "low", "close", "volume"]] *= 100
        _, outro_estado, outros_indices = preparar_entradas(alterados, blocos, "ohlcv", "standard")
        self.assertEqual(estado, outro_estado)
        np.testing.assert_array_equal(indices, outros_indices)
        dados = JanelasTemporais(matriz, blocos["teste"])
        self.assertEqual(dados[0][0].shape, (7, 5))
        self.assertEqual(dados[0][1], blocos["teste"].iloc[0]["classe_alta"])

    def test_minmax_nao_corta_futuro_fora_da_faixa(self):
        blocos = {"treino": self.amostras.iloc[:8], "validacao": self.amostras.iloc[8:16], "teste": self.amostras.iloc[16:]}
        matriz, _, _ = preparar_entradas(self.candles, blocos, "ohlcv", "minmax")
        self.assertGreater(matriz[38, 4], 1)

    def test_pareamento_usa_datas_e_rejeita_populacao_parcial(self):
        previsoes = quadro_previsoes(self.amostras, np.full(len(self.amostras), 0.5))
        alinhado = alinhar_previsoes(previsoes, previsoes.iloc[::-1])
        self.assertEqual(len(alinhado), len(previsoes))
        with self.assertRaisesRegex(ValueError, "Populações"):
            alinhar_previsoes(previsoes, previsoes.iloc[1:])
        self.assertEqual(previsoes["classe_prevista"].sum(), 0)
        self.assertEqual(calcular_metricas(previsoes)["balanced_accuracy"], 0.5)

    def test_pt_conhecido_sinal_simetria_e_degeneracao(self):
        reais = np.tile([0, 1], 50)
        positivo = testar_pt(reais, reais)
        negativo = testar_pt(reais, 1 - reais)
        self.assertAlmostEqual(positivo["estatistica"], 0.5 / math.sqrt(0.25 / 100 - 0.25 / 10000))
        self.assertEqual(positivo["p_valor_bicaudal"], negativo["p_valor_bicaudal"])
        self.assertLess(negativo["estatistica"], 0)
        self.assertFalse(testar_pt(reais, np.zeros(100))["disponivel"])
        with self.assertRaises(ValueError):
            testar_pt([0, 1], [0, 0.5])

    def test_redes_produzem_logits_sem_treinar(self):
        with torch.inference_mode():
            for nome in ("lstm", "mamba"):
                modelo = criar_modelo(nome, self.configuracao, 5).eval()
                resultado = modelo(torch.zeros(2, 7, 5))
                self.assertEqual(tuple(resultado.shape), (2, 2))
                self.assertTrue(torch.isfinite(resultado).all())

    def test_fallback_e_causal(self):
        torch.manual_seed(42)
        modelo = Mamba(d_model=4, d_state=2).eval()
        entradas = torch.randn(1, 6, 4)
        alteradas = entradas.clone()
        alteradas[:, 3:] += 100
        with torch.inference_mode():
            np.testing.assert_allclose(modelo(entradas)[:, :3].numpy(), modelo(alteradas)[:, :3].numpy(), atol=1e-6)

    def test_artefato_alterado_nao_e_reutilizado(self):
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            (raiz / "dados.txt").write_text("original", encoding="utf-8")
            gravar_json(raiz / "resultado.json", {"contrato": "entregas45-v1", "estado": "concluido", "arquivos": inventariar(raiz)})
            verificar_resultado(raiz / "resultado.json")
            (raiz / "dados.txt").write_text("alterado", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "alterado"):
                verificar_resultado(raiz / "resultado.json")

    def test_consolidacao_media_por_fold_cobertura_e_duplicacao(self):
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            caminhos = [criar_execucao_sintetica(raiz, self.configuracao, fold, n, corretas)
                        for fold, n, corretas in (("D1", 4, True), ("D2", 8, False))]
            resultado = consolidar(caminhos, raiz / "resumo")
            grupo = resultado["grupos"][0]
            self.assertEqual(grupo["modelos"]["mamba"]["ba_media_folds"], 0.5)
            self.assertEqual(grupo["folds_ausentes"], ["D3", "D4"])
            self.assertFalse(grupo["cobertura_completa_desenvolvimento"])
            with self.assertRaisesRegex(ValueError, "mesma célula/fold"):
                consolidar([*caminhos, caminhos[0]], raiz / "duplicado")

    def test_auditoria_recalcula_metricas_e_rejeita_resumo_alterado(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino = criar_execucao_sintetica(Path(pasta), self.configuracao)
            registro, _ = auditar_execucao(destino)
            registro["avaliacoes"]["teste"]["metricas"]["mamba"]["balanced_accuracy"] = .99
            gravar_json(destino / "resultado.json", registro)
            with self.assertRaisesRegex(ValueError, "Resumo divergente"):
                auditar_execucao(destino)

    def test_auditoria_rejeita_fold_alterado_e_arquivo_omitido(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino = criar_execucao_sintetica(Path(pasta), self.configuracao)
            registro, _ = auditar_execucao(destino)
            original = copy.deepcopy(registro)
            registro["fold"]["fim_teste"] = "2024-01-01"
            gravar_json(destino / "resultado.json", registro)
            with self.assertRaisesRegex(ValueError, "Fronteiras"):
                auditar_execucao(destino)
            original["arquivos"].pop(ARQUIVOS_PAREADOS[0])
            gravar_json(destino / "resultado.json", original)
            with self.assertRaisesRegex(ValueError, "obrigatórios"):
                auditar_execucao(destino)

    def test_auditoria_rejeita_previsao_fora_do_fold_mesmo_com_hash_atualizado(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino = criar_execucao_sintetica(Path(pasta), self.configuracao)
            registro, _ = auditar_execucao(destino)
            caminho = destino / "previsoes_mamba_teste.parquet"
            quadro = pd.read_parquet(caminho)
            quadro["origem_utc"] += pd.Timedelta(days=400)
            quadro["alvo_fim_utc"] += pd.Timedelta(days=400)
            quadro.to_parquet(caminho, index=False)
            registro["arquivos"] = inventariar(destino)
            gravar_json(destino / "resultado.json", registro)
            with self.assertRaisesRegex(ValueError, "purga"):
                auditar_execucao(destino)

    def test_probabilidades_invalidas_nao_viram_classe_zero(self):
        for valor in (np.nan, np.inf, -0.1, 1.1):
            with self.assertRaisesRegex(ValueError, "Probabilidades"):
                quadro_previsoes(self.amostras, np.full(len(self.amostras), valor))

    def test_assinatura_preserva_edicoes_e_independe_de_quebra_de_linha(self):
        self.assertEqual(assinatura_codigo({"a.py": "x=1\r\n"}), assinatura_codigo({"a.py": "x=1\n"}))
        self.assertNotEqual(assinatura_codigo({"a.py": "x=1\n"}), assinatura_codigo({"a.py": "x=2\n"}))

    def test_snapshot_de_codigo_deve_corresponder_a_execucao(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino = criar_execucao_sintetica(Path(pasta), self.configuracao)
            registro, _ = auditar_execucao(destino)
            fontes = {"exemplo.py": "valor = 1\n"}
            gravar_json(destino / "codigo_fonte.json", fontes)
            gravar_json(destino / "configuracao.json", registro["configuracao"])
            gravar_json(destino / "ambiente.json", registro["ambiente"])
            (destino / "protocolo_executado.md").write_text("Protocolo sintético da verificação.", encoding="utf-8")
            registro.update(fontes_preservadas=True, sha256_codigo=assinatura_codigo(fontes),
                            sha256_protocolo=sha256_arquivo(destino / "protocolo_executado.md"), arquivos=inventariar(destino))
            gravar_json(destino / "resultado.json", registro)
            auditar_execucao(destino)
            gravar_json(destino / "codigo_fonte.json", {"exemplo.py": "valor = 2\n"})
            registro["arquivos"] = inventariar(destino)
            gravar_json(destino / "resultado.json", registro)
            with self.assertRaisesRegex(ValueError, "Snapshot diverge"):
                auditar_execucao(destino)

    def test_matriz_gerada_corresponde_ao_contrato_e_janela(self):
        plano = construir_plano()
        self.assertEqual(plano, json.loads((RAIZ / "dataview/src/lib/plano-experimental.json").read_text(encoding="utf-8")))
        self.assertEqual(documento_matriz(plano), (RAIZ / "docs/entregas/05_mamba_base/matriz_experimental.md").read_text(encoding="utf-8"))
        self.assertEqual([r["janela_14d"] for r in plano["resolucoes"]], [1344, 336, 84, 14])
        self.assertEqual(exemplo_temporal("15m", 7)["ultimo_candle_abertura_utc"], "2023-01-14T23:45:00+00:00")
        self.assertEqual(exemplo_temporal("15m", 7, "proximo_candle")["alvo_fim_utc"], "2023-01-15T00:15:00+00:00")
        with self.assertRaises(ValueError):
            exemplo_temporal("15m", 14, "proximo_candle")


if __name__ == "__main__":
    unittest.main()
