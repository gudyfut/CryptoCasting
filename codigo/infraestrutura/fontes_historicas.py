"""Leitura explícita dos bytes científicos preservados, sem executar fontes."""
import hashlib
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


class ArquivoFontes:
    INDICES = ('arquivo/desenvolvimento_encerrado/indice.json',
               'arquivo/fontes_referencia/indice.json',
               'arquivo/fontes_referencia/editoriais.json')

    def __init__(self, raiz):
        self.raiz = Path(raiz).resolve()
        self.entradas = {}
        self.pacotes = {}
        self.realocacoes = {}
        for nome in self.INDICES:
            indice = self.local(nome)
            if indice.name == 'indice.json' and not indice.exists():
                indice = indice.with_name('pesquisa.json')
            if not indice.is_file():
                continue
            dados = json.loads(indice.read_bytes())
            pacote = self.local(dados['pacote'])
            if hashlib.sha256(pacote.read_bytes()).hexdigest() != dados['pacote_sha256']:
                raise ValueError('Pacote historico divergente do indice')
            for caminho, entrada in dados['entradas'].items():
                caminho = self.normalizar(caminho)
                self.normalizar(entrada.get('membro', caminho))
                if entrada.get('destino'):
                    self.local(entrada['destino'])
                if caminho in self.entradas:
                    raise ValueError(f'Fonte historica ambigua: {caminho}')
                self.entradas[caminho] = entrada
                self.pacotes[caminho] = pacote
            for antigo, atual in dados.get('realocacoes', {}).items():
                self.realocacoes[self.normalizar(antigo)] = self.normalizar(atual)

    @staticmethod
    def normalizar(nome):
        texto = str(nome).replace('\\', '/')
        p = PurePosixPath(texto)
        if p.is_absolute() or '..' in p.parts or ':' in texto or texto in ('', '.'):
            raise ValueError(f'Caminho historico invalido: {nome}')
        return p.as_posix()

    def local(self, nome):
        p = (self.raiz / self.normalizar(nome)).resolve()
        if not p.is_relative_to(self.raiz):
            raise ValueError('Destino historico fora do repositorio')
        return p

    def contem(self, nome):
        return self.normalizar(nome) in self.entradas

    def original(self, nome):
        nome = self.normalizar(nome)
        entrada = self.entradas[nome]
        with ZipFile(self.pacotes[nome]) as pacote:
            dados = pacote.read(entrada.get('membro', nome))
        if hashlib.sha256(dados).hexdigest() != entrada['sha256']:
            raise ValueError(f'Fonte original divergente: {nome}')
        return dados

    def ler(self, nome):
        nome = self.normalizar(nome)
        entrada = self.entradas[nome]
        if entrada['tipo'] == 'movido':
            destino = entrada['destino']
            if self.local(destino).is_file():
                dados = self.local(destino).read_bytes()
            elif self.contem(destino):
                dados = self.original(destino)
            else:
                raise FileNotFoundError(destino)
        else:
            dados = self.original(nome)
        if hashlib.sha256(dados).hexdigest() != entrada['sha256']:
            raise ValueError(f'Fonte historica divergente: {nome}')
        return dados

    def conferir(self):
        for nome, entrada in self.entradas.items():
            self.ler(nome)
            self.original(nome)
            if entrada.get('destino'):
                destino = entrada['destino']
                dados = self.local(destino).read_bytes() if self.local(destino).is_file() else self.original(destino)
                if hashlib.sha256(dados).hexdigest() != entrada.get('sha256_destino', entrada['sha256']):
                    raise ValueError(f'Destino historico divergente: {nome}')
        return len(self.entradas)

    def extrair(self, destino, prefixo=''):
        destino = Path(destino).resolve()
        if destino.exists():
            raise FileExistsError('Use uma pasta de destino nova; nao sobrescrever arquivos')
        dados = {p: self.original(p) for p in self.entradas if p.startswith(prefixo)}
        destino.mkdir(parents=True, exist_ok=False)
        for nome, conteudo in dados.items():
            p = (destino / nome).resolve()
            if not p.is_relative_to(destino):
                raise ValueError('Extracao fora do destino')
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(conteudo)
        return len(dados)


def ler_fonte_preservada(raiz, nome):
    """Prioriza o caminho original existente: divergências nunca são ocultadas."""
    raiz = Path(raiz).resolve()
    caminho = (raiz / ArquivoFontes.normalizar(nome)).resolve()
    if not caminho.is_relative_to(raiz):
        raise ValueError('Fonte fora do repositorio')
    return caminho.read_bytes() if caminho.is_file() else ArquivoFontes(raiz).ler(nome)
