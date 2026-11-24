import copy
import unittest
import numpy as np
from infraestrutura.artefatos import RAIZ,ler_json
from tests_padronizacao_diaria.test_contratos import Padronizacao,AlvoRetorno,ContratosHerdados,IsolamentoHerdado
from tests_cryptomamba_diario.test_contratos import dados_artificiais
from entradas_modelo.padronizacao_diaria import preparar_com_escalas
from experimentos.sem_penalizacao_diaria.contratos import conferir_configuracao


class SemPenalizacao(unittest.TestCase):
    def setUp(self):
        self.nova=ler_json(RAIZ/'configuracoes/sem_penalizacao_diaria_001.json')
        self.antiga=ler_json(RAIZ/'configuracoes/padronizacao_diaria_001.json')

    def test_unico_fator(self):
        self.assertTrue(conferir_configuracao(self.nova,self.antiga))
        for campo,valor in [('taxa',.001),('lote',64),('scheduler_gamma',.1),('epocas',500)]:
            c=copy.deepcopy(self.nova);c['treinamento'][campo]=valor
            with self.assertRaises(AssertionError):conferir_configuracao(c,self.antiga)
        c=copy.deepcopy(self.nova);c['arquitetura']['estado']=32
        with self.assertRaises(AssertionError):conferir_configuracao(c,self.antiga)

    def test_dados_identicos(self):
        a,ea=preparar_com_escalas(dados_artificiais(),self.antiga)
        b,eb=preparar_com_escalas(dados_artificiais(),self.nova)
        self.assertEqual(ea,eb)
        for fase in a:
            for k in a[fase]:np.testing.assert_array_equal(a[fase][k],b[fase][k])

    def test_comparacao_nao_importa_executor(self):
        from experimentos.sem_penalizacao_diaria import comparacao
        self.assertTrue(callable(comparacao.executar))


if __name__=='__main__':unittest.main()
