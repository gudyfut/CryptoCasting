"""Persistência idempotente do manifesto detalhado e do resumo tabular."""

from __future__ import annotations

import csv
import json
from pathlib import Path


class RepositorioManifesto:
    def __init__(self, diretorio: Path) -> None:
        self.diretorio = diretorio
        self.caminho_jsonl = diretorio / "manifesto_coleta.jsonl"
        self.caminho_csv = diretorio / "resumo_cobertura.csv"

    def salvar(self, registro: dict[str, object]) -> None:
        self.diretorio.mkdir(parents=True, exist_ok=True)
        registros = self._ler()
        registros[str(registro["chave"])] = registro
        ordenados = [registros[chave] for chave in sorted(registros)]
        self._escrever_jsonl(ordenados)
        self._escrever_csv(ordenados)

    def _ler(self) -> dict[str, dict[str, object]]:
        if not self.caminho_jsonl.exists():
            return {}
        registros = {}
        for linha in self.caminho_jsonl.read_text(encoding="utf-8").splitlines():
            if linha.strip():
                registro = json.loads(linha)
                registros[registro["chave"]] = registro
        return registros

    def _escrever_jsonl(self, registros: list[dict[str, object]]) -> None:
        temporario = self.caminho_jsonl.with_suffix(".jsonl.tmp")
        texto = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in registros)
        temporario.write_text(texto, encoding="utf-8")
        temporario.replace(self.caminho_jsonl)

    def _escrever_csv(self, registros: list[dict[str, object]]) -> None:
        campos = [
            "par", "intervalo", "competencia", "status", "quantidade_esperada",
            "quantidade_observada", "lacunas", "duplicatas", "checksum_valido", "zip_valido",
            "timestamp_minimo_utc", "timestamp_maximo_utc", "erros", "avisos",
        ]
        temporario = self.caminho_csv.with_suffix(".csv.tmp")
        with temporario.open("w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=campos, extrasaction="ignore")
            escritor.writeheader()
            escritor.writerows(registros)
        temporario.replace(self.caminho_csv)
