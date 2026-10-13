"""Identidade das execuções e persistência atômica, sem sobrescrever evidências."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import subprocess
from pathlib import Path
import torch

from camada_dados.armazenamento import sha256_arquivo
from .configuracao import RAIZ


def gravar_json(caminho: Path, dados: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporario.replace(caminho)


def identidade(dados: dict) -> str:
    return hashlib.sha256(json.dumps(dados, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:20]


def capturar_codigo() -> dict[str, str]:
    """Preserva o código efetivo, inclusive edições locais; normaliza CRLF/LF."""
    caminhos = [RAIZ / nome for nome in ("run_treino.py", "run_avaliacao.py", "requirements.txt")]
    for pasta in ("experimentos", "modelo", "baseline_ar1", "pre_processamento", "camada_dados"):
        caminhos.extend((RAIZ / pasta).glob("*.py"))
    return {p.relative_to(RAIZ).as_posix(): p.read_text(encoding="utf-8") for p in sorted(caminhos)}


def assinatura_codigo(fontes: dict[str, str] | None = None) -> str:
    resumo = hashlib.sha256()
    for caminho, conteudo in sorted((capturar_codigo() if fontes is None else fontes).items()):
        resumo.update(caminho.encode("utf-8"))
        resumo.update(b"\0")
        resumo.update(conteudo.replace("\r\n", "\n").encode("utf-8"))
        resumo.update(b"\0")
    return resumo.hexdigest()


def ambiente() -> dict:
    versoes = {"python": platform.python_version()}
    for pacote in ("torch", "numpy", "pandas", "scikit-learn", "pyarrow", "mamba-ssm", "causal-conv1d"):
        try:
            versoes[pacote] = importlib.metadata.version(pacote)
        except importlib.metadata.PackageNotFoundError:
            versoes[pacote] = None
    def git(*argumentos):
        try:
            return subprocess.check_output(["git", *argumentos], cwd=RAIZ, stderr=subprocess.DEVNULL, text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            return None
    return {"versoes": versoes, "sistema": platform.platform(), "cpu": platform.processor(),
            "cuda_pytorch": torch.version.cuda, "cudnn": torch.backends.cudnn.version(),
            "cuda_disponivel": torch.cuda.is_available(),
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "commit": git("rev-parse", "HEAD"), "alteracoes_locais": git("status", "--porcelain")}


def inventariar(diretorio: Path) -> dict:
    return {p.relative_to(diretorio).as_posix(): {"sha256": sha256_arquivo(p), "bytes": p.stat().st_size}
            for p in sorted(diretorio.rglob("*")) if p.is_file() and p.name not in ("resultado.json", "estado.json") and not p.name.endswith(".tmp")}


def verificar_resultado(caminho: Path, obrigatorios: tuple[str, ...] = ()) -> dict:
    resultado = json.loads(caminho.read_text(encoding="utf-8"))
    if resultado.get("contrato") != "entregas45-v1" or resultado.get("estado") != "concluido":
        raise ValueError(f"Execução incompleta/incompatível: {caminho}")
    arquivos = resultado.get("arquivos")
    if not isinstance(arquivos, dict) or not arquivos or not set(obrigatorios).issubset(arquivos):
        raise ValueError("Inventário vazio ou artefatos obrigatórios ausentes.")
    for relativo, registro in arquivos.items():
        arquivo = (caminho.parent / relativo).resolve()
        if (not arquivo.is_relative_to(caminho.parent.resolve()) or not arquivo.is_file()
                or arquivo.stat().st_size != registro["bytes"] or sha256_arquivo(arquivo) != registro["sha256"]):
            raise ValueError(f"Artefato ausente ou alterado: {relativo}")
    return resultado
