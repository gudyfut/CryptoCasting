import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from manutencao.arquivo_fontes import ArquivoFontes
from manutencao.auditar_repositorio import AuditorOrganizado


class ArquivoTeste(unittest.TestCase):
    def setUp(self):
        temporarios = Path(__file__).resolve().parent/'.temporarios'
        temporarios.mkdir(parents=True,exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=temporarios)
        self.raiz = Path(self.tmp.name)
        self.pasta = self.raiz/'arquivo/desenvolvimento_encerrado'
        self.pasta.mkdir(parents=True)
        self.conteudo = b'print("fonte original")\r\n'
        self.hash = hashlib.sha256(self.conteudo).hexdigest()
        self.gravar()

    def tearDown(self):
        self.tmp.cleanup()
        try:
            self.raiz.parent.rmdir()
        except OSError:
            pass

    def gravar(self, conteudo=None, tipo='zip', nome='legado/run.py'):
        with ZipFile(self.pasta/'fontes.zip','w') as z:
            z.writestr(nome, self.conteudo if conteudo is None else conteudo)
        dados={'pacote':'arquivo/desenvolvimento_encerrado/fontes.zip',
               'pacote_sha256':hashlib.sha256((self.pasta/'fontes.zip').read_bytes()).hexdigest(),
               'entradas':{nome:{'tipo':tipo,'membro':nome,'sha256':self.hash}}}
        if tipo=='movido':
            dados['entradas'][nome]['destino']='novo/run.py'
            (self.raiz/'novo').mkdir(exist_ok=True)
            (self.raiz/'novo/run.py').write_bytes(self.conteudo)
        (self.pasta/'indice.json').write_text(json.dumps(dados),encoding='utf-8')

    def test_bytes_originais_inclusive_finais_linha(self):
        self.assertEqual(ArquivoFontes(self.raiz).ler('legado/run.py'),self.conteudo)

    def test_extracao_nao_sobrescreve(self):
        arq=ArquivoFontes(self.raiz)
        destino=self.raiz/'recuperado'
        self.assertEqual(arq.extrair(destino),1)
        self.assertEqual((destino/'legado/run.py').read_bytes(),self.conteudo)
        with self.assertRaises(FileExistsError):arq.extrair(destino)

    def test_conteudo_alterado_rejeitado(self):
        self.gravar(conteudo=b'alterado')
        with self.assertRaises(ValueError):ArquivoFontes(self.raiz).ler('legado/run.py')

    def test_pacote_alterado_rejeitado(self):
        with (self.pasta/'fontes.zip').open('ab') as f:f.write(b'alteracao')
        with self.assertRaises(ValueError):ArquivoFontes(self.raiz)

    def test_caminho_fora_do_destino_rejeitado(self):
        self.gravar(nome='../fora.py')
        with self.assertRaises(ValueError):ArquivoFontes(self.raiz)

    def test_destino_movido_e_recuperacao_do_original(self):
        self.gravar(tipo='movido')
        arq=ArquivoFontes(self.raiz)
        (self.raiz/'novo/run.py').unlink()
        with self.assertRaises(FileNotFoundError):arq.ler('legado/run.py')
        arq.extrair(self.raiz/'recuperado')
        self.assertEqual((self.raiz/'recuperado/legado/run.py').read_bytes(),self.conteudo)

    def test_auditor_confere_mesmo_hash_antigo(self):
        a=AuditorOrganizado(self.raiz,True)
        a.conferir('legado/run.py',self.hash)
        self.assertEqual(a.erros,[])
        self.assertEqual(a.ausentes,set())
        self.assertIn('legado/run.py',a.arquivados)
        a.conferir('legado/run.py','0'*64)
        self.assertTrue(a.erros)

    def test_arquivo_local_divergente_nao_e_ocultado_pelo_pacote(self):
        (self.raiz/'legado').mkdir()
        (self.raiz/'legado/run.py').write_bytes(b'alterado')
        a=AuditorOrganizado(self.raiz,True)
        a.conferir('legado/run.py',self.hash)
        self.assertTrue(a.erros)
        self.assertEqual(a.arquivados,set())

    def test_ausencia_sem_mapeamento_permanece_erro(self):
        a=AuditorOrganizado(self.raiz,True)
        a.conferir('ausente.py',self.hash)
        self.assertIn('ausente.py',a.ausentes)


if __name__=='__main__':unittest.main()
