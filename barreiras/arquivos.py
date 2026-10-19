"""Serialização estrita e identidades reproduzíveis."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def identidade(objeto) -> str:
    return hashlib.sha256(json.dumps(objeto, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False).encode()).hexdigest()


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open('rb') as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b''):
            h.update(bloco)
    return h.hexdigest()


def salvar_json(caminho: Path, objeto) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(caminho.name + f'.{os.getpid()}.tmp')
    temporario.write_text(json.dumps(objeto, ensure_ascii=False, indent=2,
                                    allow_nan=False) + '\n', encoding='utf-8')
    temporario.replace(caminho)


def ler_json(caminho: Path):
    return json.loads(caminho.read_text(encoding='utf-8'))


def fontes() -> dict[str, str]:
    caminhos = sorted((RAIZ / 'barreiras').glob('*.py'))
    caminhos += sorted((RAIZ / 'modelo').glob('*.py'))
    caminhos += [RAIZ / 'docs/protocolo_experimental.md']
    return {str(p.relative_to(RAIZ)).replace('\\', '/'): sha256(p) for p in caminhos}
