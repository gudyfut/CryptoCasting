"""Falhas e limites do ciclo, sem ajustar dados reais."""
import copy
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from infraestrutura.artefatos import RAIZ, salvar_json, ler_json
from treinamento.selecao import SelecaoEpoca, escolher_arima
from treinamento.configuracao import carregar, grade
from treinamento.preservacao import publicar, conferir, exclusividade
from treinamento.ciclo import conferir_autorizacao


class Contratos(unittest.TestCase):
    def test_empate_e_paciencia(self):
        s = SelecaoEpoca(2)
        self.assertTrue(s.observar(1, .3))
        self.assertFalse(s.observar(2, .3))
        self.assertFalse(s.parar)
        self.assertFalse(s.observar(3, .4))
        self.assertTrue(s.parar)
        self.assertEqual(s.epoca, 1)

    def test_nao_finito_e_ordem(self):
        for valor in (np.nan, np.inf, -.1):
            with self.assertRaises(ValueError):
                SelecaoEpoca(2).observar(1, valor)
        with self.assertRaises(ValueError):
            SelecaoEpoca(2).observar(2, .1)

    def test_ordem_arima_e_falha_total(self):
        c = [{'status': 'valido', 'ordem': o, 'mse_validacao': .1} for o in ([1,1,0],[0,1,1],[0,1,0])]
        self.assertEqual(escolher_arima(c)['ordem'], [0,1,0])
        with self.assertRaises(ValueError):
            escolher_arima([{'status': 'falhou'}])

    def test_grade_e_configuracao(self):
        c = carregar()
        g = grade(c)
        self.assertEqual(len(g), 10)
        self.assertEqual(sum(q.get('controle', False) for q in g), 2)
        self.assertEqual([q['chave'] for q in g[:4]], ['mamba_42','lstm_42','controle_mamba_42','controle_lstm_42'])
        self.assertEqual(len({q['chave'] for q in g}), 10)

    def test_configuracao_divergente_bloqueada(self):
        from treinamento import configuracao
        original = configuracao.ler_json
        def mudar(p):
            r = original(p)
            if Path(p).name == 'treinamento_ohlcv24_001.json':
                r['treino']['epocas'] = 99
            return r
        with patch.object(configuracao, 'ler_json', side_effect=mudar), self.assertRaises(ValueError):
            carregar()

    def test_publicacao_detecta_corrupcao(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p/'dados.txt').write_text('original')
            publicar(p)
            conferir(p)
            with self.assertRaises(FileExistsError):
                publicar(p)
            (p/'dados.txt').write_text('alterado')
            with self.assertRaises(ValueError):
                conferir(p)

    @unittest.skipUnless(os.name == 'posix', 'Lock do executor exige Linux/WSL.')
    def test_exclusividade_e_host(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            with exclusividade(p):
                with self.assertRaises(RuntimeError), exclusividade(p):
                    pass
            self.assertFalse(ler_json(p/'processo.json')['ativo'])
            salvar_json(p/'processo.json', {'ativo': True, 'host': 'outra_maquina'})
            with self.assertRaises(RuntimeError), exclusividade(p, retomar=True):
                pass

    @unittest.skipUnless(os.name == 'posix', 'Identidade de processo/boot exige Linux/WSL.')
    def test_retomada_processo_encerrado_preserva_incidente(self):
        import platform
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            antigo = {'ativo':True,'host':platform.node(),'boot':'boot_anterior','pid':999999,'inicio_proc':'0'}
            salvar_json(p/'processo.json', antigo)
            with self.assertRaises(RuntimeError), exclusividade(p):
                pass
            with exclusividade(p, retomar=True):
                pass
            incidentes = list((p/'incidentes').glob('*.json'))
            self.assertEqual(len(incidentes),1)
            self.assertEqual(ler_json(incidentes[0])['processo_anterior'],antigo)

    def test_exige_autorizacao_compativel(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'autorizacao.json'
            salvar_json(p, {'execucao': 'outro'})
            with self.assertRaises(ValueError):
                conferir_autorizacao(p, 'alvo', grade(carregar()))

    def test_naive_zero_real(self):
        from testes.modelos.apoio import conjunto
        from modelos.consumo import ConsumoModelos
        from modelos.naive import prever_naive
        c = ConsumoModelos(conjunto(), 'sintetico')
        self.assertNotEqual(c.especificacao.media_alvo, 0)
        self.assertTrue((prever_naive(c.solicitar('teste')).previsao == 0).all())

    def test_ajuste_arima_nao_acessa_teste(self):
        from testes.modelos.apoio import conjunto
        from modelos.consumo import ConsumoModelos
        from treinamento.arima import ajustar
        c = ConsumoModelos(conjunto(), 'sintetico')
        original = c.solicitar
        def restrito(parte, *args, **kwargs):
            self.assertIn(parte, ('treino', 'validacao'))
            return original(parte, *args, **kwargs)
        with tempfile.TemporaryDirectory() as tmp, patch.object(c, 'solicitar', side_effect=restrito):
            p = ajustar(c, carregar()['arima'], Path(tmp))
            candidatos = ler_json(Path(tmp)/'candidatos.json')
            self.assertEqual(len(candidatos), 9)
            self.assertEqual(p.indice_fim_ajuste, c.dados_ajuste_arima()['indice_fim_ajuste'])


if __name__ == '__main__':
    unittest.main()
