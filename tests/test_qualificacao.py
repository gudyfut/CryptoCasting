"""Testes técnicos sintéticos, sem treinamento/otimizador ou resultados de mercado."""

import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from experimentos.configuracao import RAIZ, carregar_configuracao, gerar_celulas
from experimentos.qualificacao import conferir_checkpoint, verificar_modelos, verificar_preparacao, verificar_checkpoints
from experimentos.dados import JanelasTemporais
from experimentos.registro import ambiente, assinatura_codigo
from experimentos.treinamento import criar_modelo, fixar_seed, prever


class TestQualificacao(unittest.TestCase):
    def setUp(self):
        self.cpu = carregar_configuracao(RAIZ / "configuracoes/treino_piloto_cpu.json")
        self.nvidia = carregar_configuracao(RAIZ / "configuracoes/treino_piloto_nvidia.json")
        self.historico = {"epocas": [{"epoca": i, "loss_treino": 0.69, "ba_validacao": 0.5,
                                     "f1_macro_validacao": 0.4} for i in range(1, 12)]}
        self.salvo = {"epoca": 1, "ba_validacao": 0.5}
        self.resumo = {"melhor_epoca": 1, "melhor_ba_validacao": 0.5, "epocas_executadas": 11}

    def test_piloto_preserva_configuracao_e_delimita_escopo(self):
        esperado = {**self.cpu, "backend_mamba": "oficial", "dispositivo": "cuda"}
        self.assertEqual(self.nvidia, esperado)
        self.assertEqual(len(gerar_celulas(self.nvidia)), 1)

    def test_cuda_ausente_falha_antes_de_importar_mamba(self):
        with patch("torch.cuda.is_available", return_value=False), patch("experimentos.qualificacao.criar_modelo") as criar:
            with self.assertRaisesRegex(RuntimeError, "CUDA indisponível"):
                verificar_modelos(self.nvidia, 5, 7)
            criar.assert_not_called()

    def test_grade_completa_nao_e_preparacao_do_piloto(self):
        c = {**self.nvidia, "folds": ["D1", "D2"]}
        with self.assertRaisesRegex(ValueError, "exatamente uma célula"):
            verificar_preparacao(c)

    def test_forward_backward_sem_treino_cpu(self):
        with patch("torch.optim.AdamW", side_effect=AssertionError("Não criar otimizador")):
            resultado = verificar_modelos(self.cpu, 5, 7)
        self.assertEqual(resultado["mamba"]["backend"], "pytorch")
        for registro in resultado.values():
            self.assertEqual(registro["atualizacoes_pesos"], 0)
            self.assertEqual(registro["forward_backward_inferencia"], "aprovado")

    def test_primeiro_empate_e_parada_corretos(self):
        conferir_checkpoint(self.salvo, self.historico, self.resumo)

    def test_checkpoint_posterior_em_empate_rejeitado(self):
        with self.assertRaisesRegex(ValueError, "primeira melhor"):
            conferir_checkpoint({**self.salvo, "epoca": 2}, self.historico, self.resumo)

    def test_interrupcao_prematura_rejeitada(self):
        hist = {"epocas": self.historico["epocas"][:4]}
        with self.assertRaisesRegex(ValueError, "encerrado fora"):
            conferir_checkpoint(self.salvo, hist, {**self.resumo, "epocas_executadas": 4})

    def test_ignorar_parada_rejeitado(self):
        hist = copy.deepcopy(self.historico)
        hist["epocas"].append({**hist["epocas"][-1], "epoca": 12})
        with self.assertRaisesRegex(ValueError, "continuou após"):
            conferir_checkpoint(self.salvo, hist, {**self.resumo, "epocas_executadas": 12})

    def test_loss_invalida_rejeitada(self):
        hist = copy.deepcopy(self.historico)
        hist["epocas"][0]["loss_treino"] = float("nan")
        with self.assertRaisesRegex(ValueError, "métricas inválidas"):
            conferir_checkpoint(self.salvo, hist, self.resumo)

    def test_recarga_reproduz_e_detecta_previsao_divergente(self):
        # Auditoria de inventário/dados é testada na outra suíte. Aqui exercitamos
        # checkpoints reais de pesos aleatórios, sem qualquer ajuste de modelos.
        celula = gerar_celulas(self.cpu)[0]
        matriz = np.random.default_rng(42).normal(size=(10, 5)).astype(np.float32)
        quadro = pd.DataFrame({"par": ["BTCUSDT"] * 4,
            "origem_utc": pd.date_range("2022-10-01", periods=4, tz="UTC"),
            "alvo_fim_utc": pd.date_range("2022-10-02", periods=4, tz="UTC"),
            "indice_contexto_inicio": range(4), "indice_contexto_fim": range(6, 10),
            "classe_alta": [0, 1, 0, 1]})
        blocos = {b: quadro.copy() for b in ("treino", "validacao", "teste")}
        fixar_seed(42)
        resultado = {"id": "sintetico", "configuracao": self.cpu, "celula": celula,
                     "sha256_codigo": assinatura_codigo(), "sha256_manifesto_dataset": "sintetico",
                     "ambiente": ambiente(), "modelos": {n: self.resumo for n in ("lstm", "mamba")}}
        with tempfile.TemporaryDirectory() as temporaria:
            pasta = Path(temporaria)
            (pasta / "normalizador.json").write_text("{}", encoding="utf-8")
            np.save(pasta / "indices_ajuste_normalizador.npy", np.arange(10))
            for nome in ("lstm", "mamba"):
                modelo = criar_modelo(nome, self.cpu, 5)
                (pasta / nome).mkdir()
                torch.save({**self.salvo, "modelo": modelo.state_dict(), "nome_modelo": nome,
                            "celula": celula, "configuracao": self.cpu, "dimensao_entrada": 5}, pasta / nome / "melhor.pt")
                (pasta / nome / "historico.json").write_text(json.dumps(self.historico), encoding="utf-8")
                probabilidades = prever(modelo, DataLoader(JanelasTemporais(matriz, quadro), batch_size=32), torch.device("cpu"))
                for bloco in ("validacao", "teste"):
                    quadro.assign(probabilidade_alta=probabilidades, classe_prevista=probabilidades > .5).to_parquet(
                        pasta / f"previsoes_{nome}_{bloco}.parquet", index=False)
            with patch("experimentos.qualificacao.auditar_execucao", return_value=(resultado, {})), patch(
                    "experimentos.qualificacao.carregar_dados", return_value=(SimpleNamespace(resumo_manifesto="sintetico"), blocos, matriz, {}, np.arange(10))):
                verificado = verificar_checkpoints(pasta)
                self.assertTrue(verificado["modelos"]["mamba"]["blocos"]["teste"]["classes_identicas"])
                arquivo = pasta / "previsoes_mamba_teste.parquet"
                adulterado = pd.read_parquet(arquivo)
                adulterado.loc[0, "probabilidade_alta"] += .1
                adulterado.to_parquet(arquivo, index=False)
                with self.assertRaises(AssertionError):
                    verificar_checkpoints(pasta)


if __name__ == "__main__":
    unittest.main()
