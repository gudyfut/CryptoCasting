"""Contratos do pós-processamento visual, separados dos testes do ciclo fechado."""
import importlib.util
from pathlib import Path
import unittest
import pandas as pd

caminho = Path(__file__).resolve().parents[2] / "scripts/exportar_explorador.py"
especificacao = importlib.util.spec_from_file_location("exportacao_visual", caminho)
modulo = importlib.util.module_from_spec(especificacao)
especificacao.loader.exec_module(modulo)


class AlinhamentoVisual(unittest.TestCase):
    def quadro(self):
        q = pd.DataFrame({"origem_utc": pd.to_datetime(["2023-01-01T00:00Z", "2023-01-01T01:00Z"]), "classe": [0, 2]})
        for c in ("entrada_utc", "expiracao_utc", "saida_utc"):
            q[c] = q.origem_utc + pd.Timedelta(minutes=1)
        q["preco_entrada"], q["preco_saida"], q["distancia"], q["ambiguo"] = 100., 101., .01, False
        return q

    def test_alinha_por_tempo_mesmo_com_linhas_invertidas(self):
        q = self.quadro()
        r = modulo.alinhar({"mamba": q, "lstm": q.iloc[::-1]})
        self.assertEqual(r["mamba"].classe.tolist(), r["lstm"].classe.tolist())

    def test_rejeita_origem_duplicada_ou_ausente(self):
        q = self.quadro()
        with self.assertRaises(ValueError):
            modulo.alinhar({"mamba": pd.concat([q, q.iloc[:1]])})
        with self.assertRaises(ValueError):
            modulo.alinhar({"mamba": q, "lstm": q.iloc[:1]})

    def test_rejeita_desfecho_diferente_no_mesmo_instante(self):
        q = self.quadro()
        outro = q.copy(); outro.loc[0, "classe"] = 2
        with self.assertRaises(ValueError):
            modulo.alinhar({"mamba": q, "lstm": outro})


if __name__ == "__main__":
    unittest.main()
