"""Localização explícita do checkout, independente do diretório do comando."""
from pathlib import Path


def localizar_raiz(origem=None):
    origem = Path(origem or __file__).resolve()
    for pasta in (origem.parent, *origem.parents):
        if (pasta / 'AGENTS.md').is_file() and (pasta / 'configuracoes').is_dir():
            return pasta
    raise FileNotFoundError('Raiz do CryptoCasting não encontrada; use o checkout do projeto.')


RAIZ = localizar_raiz()
CODIGO = RAIZ / 'codigo'
TESTES = RAIZ / 'testes'
