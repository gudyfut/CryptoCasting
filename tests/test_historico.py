import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from experimentos.historico import registrar_execucao


class TestHistorico(unittest.TestCase):
    def test_falha_preservada_sem_resultado_e_sem_sobrescrita(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            origem = raiz / "tentativa_1"
            origem.mkdir()
            original = '{"estado":"falhou","erro":"memória insuficiente"}'
            (origem / "estado.json").write_text(original, encoding="utf-8")
            pasta = registrar_execucao(origem, raiz / "historico", titulo="Tentativa interrompida")
            registro = json.loads((pasta / "registro.json").read_text(encoding="utf-8"))
            self.assertEqual(registro["estado_execucao"], "falhou")
            self.assertIsNone(registro["execucao_utc"])
            self.assertEqual((pasta / "originais/estado.json").read_text(encoding="utf-8"), original)
            with self.assertRaises(FileExistsError):
                registrar_execucao(origem, raiz / "historico", titulo="Não pode apagar o primeiro registro")

    def test_previsoes_temporais_exportadas_e_pesos_identificados(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            origem = raiz / "piloto"
            origem.mkdir()
            (origem / "resultado.json").write_text('{"estado":"concluido"}', encoding="utf-8")
            quadro = pd.DataFrame({"origem_utc": pd.date_range("2023-01-01", periods=2, tz="UTC"), "classe_alta": [0, 1], "probabilidade_alta": [.42, .62]})
            quadro["probabilidade_alta"] = quadro["probabilidade_alta"].astype("float32")
            quadro.to_parquet(origem / "previsoes_teste.parquet", index=False)
            (origem / "melhor.pt").write_bytes(b"peso de teste, nao carregar")
            pasta = registrar_execucao(origem, raiz / "historico", titulo="Registro descritivo", situacao="inconclusivo")
            exportado = pd.read_csv(pasta / "previsoes/previsoes_teste.csv", float_precision="round_trip")
            self.assertEqual(exportado.classe_alta.tolist(), [0, 1])
            self.assertEqual(exportado.probabilidade_alta.tolist(), quadro.probabilidade_alta.tolist())
            self.assertEqual(pd.to_datetime(exportado.origem_utc, utc=True).tolist(), quadro.origem_utc.tolist())
            r = json.loads((pasta / "registro.json").read_text(encoding="utf-8"))
            self.assertEqual(r["arquivos"]["melhor.pt"]["sha256_original"], hashlib.sha256(b"peso de teste, nao carregar").hexdigest())
            self.assertFalse((pasta / "originais/melhor.pt").exists())
            self.assertTrue((raiz / "historico/LINHA_DO_TEMPO.md").is_file())

    def test_origem_invalida_e_destino_aninhado_rejeitados(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            with self.assertRaises(ValueError):
                registrar_execucao(raiz, raiz / "hist", titulo="Vazio")
            (raiz / "estado.json").write_text('{"estado":"interrompido"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                registrar_execucao(raiz, raiz / "hist", titulo="Recursão proibida")

    def test_json_corrompido_guardado_mas_nao_aprovado(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            origem = raiz / "falha"
            origem.mkdir()
            (origem / "resultado.json").write_text('{"parcial":', encoding="utf-8")
            with self.assertRaises(ValueError):
                registrar_execucao(origem, raiz / "hist", titulo="Corrompido", situacao="validado_tecnicamente")
            pasta = registrar_execucao(origem, raiz / "hist", titulo="Corrompido", situacao="em_revisao")
            registro = json.loads((pasta / "registro.json").read_text(encoding="utf-8"))
            self.assertTrue(registro["avisos"])
            self.assertEqual((pasta / "originais/resultado.json").read_text(encoding="utf-8"), '{"parcial":')


if __name__ == "__main__":
    unittest.main()
