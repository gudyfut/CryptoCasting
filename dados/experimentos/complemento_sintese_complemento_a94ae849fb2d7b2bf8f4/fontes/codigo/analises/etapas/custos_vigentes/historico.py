"""Importa somente primitivas históricas ausentes, sem restaurar pacotes no projeto."""
import importlib.abc
import importlib.util
import sys
from pathlib import Path
from infraestrutura.artefatos import RAIZ
from manutencao.arquivo_fontes import ArquivoFontes


class LeitorHistorico(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def __init__(self):
        self.arquivo = ArquivoFontes(RAIZ)
        self.carregados = {}

    def caminho(self, nome):
        for sufixo in ('/__init__.py', '.py'):
            p = nome.replace('.', '/')+sufixo
            if self.arquivo.contem(p): return p
        return None

    def find_spec(self, fullname, path=None, target=None):
        if not fullname.startswith(('backtest_carteira', 'experimento_busca_astra')):
            return None
        p = self.caminho(fullname)
        if p: return importlib.util.spec_from_loader(fullname, self, is_package=p.endswith('/__init__.py'))
        return None

    def create_module(self, spec): return None

    def exec_module(self, module):
        p = self.caminho(module.__name__); dados = self.arquivo.original(p)
        module.__file__ = str(RAIZ/p)
        if p.endswith('/__init__.py'): module.__path__ = [str((RAIZ/p).parent)]
        exec(compile(dados, module.__file__, 'exec'), module.__dict__)
        self.carregados[p] = self.arquivo.entradas[p]['sha256']


def instalar():
    leitor = LeitorHistorico(); sys.meta_path.append(leitor); return leitor
