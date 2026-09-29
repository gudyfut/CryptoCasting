"""Operações locais seguras: escrita atômica, hash e integridade de ZIP."""

from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path


def sha256_arquivo(caminho: Path) -> str:
    resumo = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def extrair_checksum(texto: str) -> str:
    correspondencia = re.search(r"\b[a-fA-F0-9]{64}\b", texto)
    if not correspondencia:
        raise ValueError("Checksum SHA-256 não encontrado no arquivo oficial.")
    return correspondencia.group(0).lower()


def validar_zip(caminho: Path, nome_csv_esperado: str) -> None:
    with zipfile.ZipFile(caminho) as arquivo_zip:
        if arquivo_zip.testzip() is not None:
            raise ValueError("O ZIP contém um membro corrompido.")
        nomes_csv = [nome for nome in arquivo_zip.namelist() if nome.lower().endswith(".csv")]
        if nomes_csv != [nome_csv_esperado]:
            raise ValueError(
                f"Esperado exatamente {nome_csv_esperado}; encontrados: {nomes_csv}."
            )
