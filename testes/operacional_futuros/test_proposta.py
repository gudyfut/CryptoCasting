from copy import deepcopy
import unittest
from infraestrutura.artefatos import ler_json
from experimentos.operacional_futuros.contrato import CONFIGURACAO, validar_proposta


class Proposta(unittest.TestCase):
    def setUp(self):
        self.cfg=ler_json(CONFIGURACAO)

    def test_orcamento_e_estado_nao_executavel(self):
        c=validar_proposta(self.cfg)
        self.assertEqual(c['politicas'],12)
        self.assertEqual(c['ajustes_maximos'],185)

    def test_nao_inferir_autorizacao(self):
        for chave in ['treinamento','conta_real','api_paga']:
            c=deepcopy(self.cfg);c['autorizacao'][chave]=True
            with self.assertRaises(ValueError):validar_proposta(c)

    def test_calibracao_futura_rejeitada(self):
        c=deepcopy(self.cfg);c['calendario']['desenvolvimento'][0]['calibracao']=['2023-07-01','2023-10-01']
        with self.assertRaises(ValueError):validar_proposta(c)

    def test_seed_duplicada_rejeitada(self):
        c=deepcopy(self.cfg);c['seeds']['exploracao']=[42,42,2026]
        with self.assertRaises(ValueError):validar_proposta(c)

    def test_custo_favoravel_alterado_rejeitado(self):
        c=deepcopy(self.cfg);c['execucao_proposta']['comissao_taker_por_lado']=0.
        with self.assertRaises(ValueError):validar_proposta(c)


if __name__=='__main__':unittest.main()
