import copy
import unittest
from infraestrutura.artefatos import RAIZ,ler_json
from experimentos.ablacao_linear_diaria.contratos import conferir_configuracao,receita


class Contratos(unittest.TestCase):
    def setUp(self):
        self.c=ler_json(RAIZ/'configuracoes/ablacao_linear_diaria_001.json')
        self.anterior=ler_json(RAIZ/'configuracoes/penalizacao_seletiva_diaria_001.json')

    def test_unico_fator(self):
        self.assertTrue(conferir_configuracao(self.c,self.anterior))
        a,l=receita(self.c,'A'),receita(self.c,'L')
        self.assertTrue(a.pop('ramos_mamba'));self.assertFalse(l.pop('ramos_mamba'))
        self.assertEqual(a,l)

    def test_rejeita_mudancas_cientificas(self):
        for campo,valor in [('taxa',.001),('epocas',201),('weight_decay',0),('lote',64),('parada_antecipada',True)]:
            c=copy.deepcopy(self.c);c['treinamento'][campo]=valor
            with self.assertRaises(AssertionError):conferir_configuracao(c,self.anterior)
        for campo in ('operacoes','padronizacao'):
            c=copy.deepcopy(self.c);c[campo]={}
            with self.assertRaises(AssertionError):conferir_configuracao(c,self.anterior)


if __name__=='__main__':unittest.main()
