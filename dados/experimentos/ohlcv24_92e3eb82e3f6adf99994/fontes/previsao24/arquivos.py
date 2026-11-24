"""Identidades, escrita atômica e verificação de artefatos científicos."""
from __future__ import annotations
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

def agora():
    return datetime.now(timezone.utc).isoformat()

def identidade(valor):
    return hashlib.sha256(json.dumps(valor, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()

def sha256(caminho):
    h = hashlib.sha256()
    with Path(caminho).open('rb') as arquivo:
        for bloco in iter(lambda: arquivo.read(4*1024*1024), b''):
            h.update(bloco)
    return h.hexdigest()

def salvar_json(caminho, valor):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    parcial = caminho.with_name(caminho.name + f'.{os.getpid()}.parcial')
    parcial.write_text(json.dumps(valor, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    parcial.replace(caminho)

def ler_json(caminho):
    return json.loads(Path(caminho).read_text(encoding='utf-8-sig'))

def fontes():
    caminhos = sorted((RAIZ/'previsao24').glob('*.py'))
    caminhos += [RAIZ/'run_previsao.py', RAIZ/'docs/protocolo_experimental.md']
    return {p.relative_to(RAIZ).as_posix(): sha256(p) for p in caminhos}

def verificar_arquivos(pasta, arquivos):
    pasta = Path(pasta).resolve()
    for relativo, esperado in arquivos.items():
        caminho = (pasta/relativo).resolve()
        if not caminho.is_relative_to(pasta) or sha256(caminho) != esperado:
            raise ValueError(f'Artefato ausente/alterado: {relativo}')
