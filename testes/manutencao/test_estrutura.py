"""Instalação, preservação e separação entre leitura histórica e execução."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from infraestrutura.caminhos import RAIZ, CODIGO, localizar_raiz
from infraestrutura.artefatos import abrir_artefato, conferir_arquivos, identidade, fontes
from infraestrutura.fontes_historicas import ArquivoFontes, ler_fonte_preservada


class Estrutura(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.raiz = Path(self.temporario.name)
        self.original = b'fonte cientifica\r\n'
        self.resumo = hashlib.sha256(self.original).hexdigest()
        self.nome = 'modelo/rede.py'
        pasta = self.raiz / 'arquivo/fontes_referencia'
        pasta.mkdir(parents=True)
        pacote = pasta / 'fontes.zip'
        with ZipFile(pacote, 'w') as z:
            z.writestr(self.nome, self.original)
        (pasta / 'indice.json').write_text(json.dumps({
            'pacote': 'arquivo/fontes_referencia/fontes.zip',
            'pacote_sha256': hashlib.sha256(pacote.read_bytes()).hexdigest(),
            'entradas': {self.nome: {'tipo': 'zip', 'sha256': self.resumo}},
            'realocacoes': {self.nome: 'codigo/modelo/rede.py'},
        }), encoding='utf-8')

    def test_fonte_original_independe_da_versao_de_trabalho(self):
        atual = self.raiz / 'codigo/modelo/rede.py'
        atual.parent.mkdir(parents=True)
        atual.write_text('versao de trabalho', encoding='utf-8')
        arq = ArquivoFontes(self.raiz)
        self.assertEqual(arq.conferir(), 1)
        self.assertEqual(arq.original(self.nome), self.original)
        self.assertEqual(ler_fonte_preservada(self.raiz, self.nome), self.original)

    def test_clone_publico_confere_o_indice_de_pesquisa(self):
        pasta = self.raiz / 'arquivo/fontes_referencia'
        (pasta / 'indice.json').rename(pasta / 'pesquisa.json')
        self.assertEqual(ArquivoFontes(self.raiz).conferir(), 1)
        (pasta / 'fontes.zip').write_bytes(b'corrompido')
        with self.assertRaises(ValueError):
            ArquivoFontes(self.raiz)

    def test_caminho_original_divergente_nao_e_mascarado(self):
        p = self.raiz / self.nome
        p.parent.mkdir(parents=True)
        p.write_bytes(b'divergente')
        self.assertNotEqual(hashlib.sha256(ler_fonte_preservada(self.raiz, self.nome)).hexdigest(), self.resumo)

    def test_executor_nao_aceita_arquivo_em_substituicao_a_fonte_real(self):
        with self.assertRaises(ValueError):
            conferir_arquivos(self.raiz, {self.nome: self.resumo})

    def test_leitura_de_artefato_confere_original_preservado(self):
        pasta = self.raiz / 'dados/exemplo'
        pasta.mkdir(parents=True)
        assinatura = {'fontes': {}, 'originais': {self.nome: self.resumo}}
        manifesto = {'id': identidade(assinatura)[:20], 'tipo': 'teste',
                     'assinatura': assinatura, 'arquivos': {}}
        (pasta / 'manifesto.json').write_text(json.dumps(manifesto), encoding='utf-8')
        with patch('infraestrutura.artefatos.RAIZ', self.raiz):
            self.assertEqual(abrir_artefato(pasta)['id'], manifesto['id'])
            original = self.raiz / self.nome
            original.parent.mkdir(parents=True)
            original.write_bytes(b'alterado')
            with self.assertRaisesRegex(ValueError, 'Fonte original'):
                abrir_artefato(pasta)

    def test_fontes_fora_do_projeto_sao_rejeitadas(self):
        for nome in ('../fora.py', '/fora.py', 'C:/fora.py'):
            with self.assertRaises(ValueError):
                ler_fonte_preservada(self.raiz, nome)

    def test_instalacao_funciona_fora_do_diretorio_corrente(self):
        r = subprocess.run([sys.executable, '-B', '-c',
            'from infraestrutura.caminhos import RAIZ; import modelos, comandos.dados; print(RAIZ)'],
            cwd=self.raiz, capture_output=True, text=True, check=True)
        self.assertEqual(Path(r.stdout.strip()), RAIZ)
        self.assertEqual(localizar_raiz(CODIGO / 'modelos/mamba.py'), RAIZ)

    def test_assinatura_inclui_fontes_e_testes_nos_caminhos_reais(self):
        itens = fontes('infraestrutura', 'testes/dados')
        self.assertIn('codigo/infraestrutura/caminhos.py', itens)
        self.assertIn('testes/dados/test_mercado.py', itens)
        self.assertTrue(all((RAIZ / p).is_file() for p in itens))
        with self.assertRaises(FileNotFoundError):
            fontes('pacote_inexistente')

    def test_codigo_nao_importa_suites_e_entradas_nao_dependem_de_experimentos(self):
        arquivos = list(CODIGO.rglob('*.py'))
        self.assertGreater(len(arquivos), 100)
        for p in arquivos:
            for n in ast.walk(ast.parse(p.read_text(encoding='utf-8-sig'))):
                nomes = [a.name for a in n.names] if isinstance(n, ast.Import) else [n.module or ''] if isinstance(n, ast.ImportFrom) else []
                for nome in nomes:
                    topo = nome.split('.')[0]
                    self.assertFalse(topo == 'testes' or topo.startswith('tests_'), str(p))
                    if p.parent == CODIGO / 'entradas_modelo':
                        self.assertNotEqual(topo, 'experimentos', str(p))
