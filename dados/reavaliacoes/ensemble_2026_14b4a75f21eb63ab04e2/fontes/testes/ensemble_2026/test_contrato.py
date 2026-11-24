import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd

from analises.etapas.ensemble_2026.entradas import preparar
from entradas_modelo.cryptomamba_diario import preparar as preparar_antigo
from entradas_modelo.padronizacao_diaria import transformar
from mercado_futuros.periodo_publico import api, validar_diario

DIA = 86400000


class Contrato(unittest.TestCase):
    def setUp(self):
        inicio = int(pd.Timestamp('2025-12-01', tz='UTC').timestamp()*1000)
        t = np.arange(inicio, inicio+50*DIA, DIA)
        preco = 100+np.arange(50)*.1
        self.diario = pd.DataFrame(dict(open_time=t, open=preco, high=preco+2,
                                       low=preco-2, close=preco+1, volume=np.arange(50)+100,
                                       close_time=t+DIA-1))
        self.cfg = dict(contexto_dias=14, normalizar=True, canais=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
                        volume_divisor=1000000000, periodos={'teste':['2025-12-01', '2026-01-20']})
        self.escalas = dict(media=[1600000000, 100, 100, 100, 100, .000001],
                            escala=[36000000, 10, 10, 10, 10, .000001])

    def test_janelas_iguais_a_receita_anterior(self):
        cfg = copy.deepcopy(self.cfg)
        cfg['normalizar'] = False
        ref = preparar_antigo(self.diario, cfg)['teste']
        obtido = preparar(self.diario, ref['origens_ms'], self.cfg, self.escalas)
        np.testing.assert_array_equal(obtido['x'], transformar(ref['x'], self.escalas))
        np.testing.assert_array_equal(obtido['ultimo_close'], ref['ultimo_close'])
        np.testing.assert_array_equal(obtido['y'], ref['y'])

    def test_alterar_futuro_nao_altera_entrada(self):
        origem = self.diario.open_time.iloc[31]
        antes = preparar(self.diario, np.array([origem]), self.cfg, self.escalas)
        alterado = self.diario.copy()
        alterado.loc[alterado.open_time >= origem, ['open','high','low','close','volume']] *= 7
        depois = preparar(alterado, np.array([origem]), self.cfg, self.escalas)
        np.testing.assert_array_equal(antes['x'], depois['x'])
        np.testing.assert_array_equal(antes['ultimo_close'], depois['ultimo_close'])
        self.assertNotEqual(antes['y'][0], depois['y'][0])

    def test_janeiro_usa_contexto_de_dezembro_sem_reajuste(self):
        origem = int(pd.Timestamp('2026-01-01', tz='UTC').timestamp()*1000)
        copia = copy.deepcopy(self.escalas)
        z = preparar(self.diario, np.array([origem]), self.cfg, self.escalas)
        self.assertEqual(z['x'].shape, (1,6,14))
        self.assertEqual(z['ultimo_close'][0], self.diario.close.iloc[30])
        self.assertEqual(self.escalas, copia)
        self.assertEqual(z['fim_alvo_ms'][0], origem+DIA-1)

    def test_calendario_incompleto_recusado(self):
        with self.assertRaises(AssertionError):
            preparar(self.diario.drop(index=25), self.diario.open_time.to_numpy()[31:33], self.cfg, self.escalas)

    def test_api_fronteira_so_dois_minutos_com_proveniencia(self):
        inicio = int(self.diario.open_time.iloc[31])
        dados = [[t,100,101,99,100,5,t+59999,500,1,2,200,0] for t in [inicio,inicio+60000]]
        with tempfile.TemporaryDirectory() as pasta, patch('mercado_futuros.periodo_publico.baixar', return_value=json.dumps(dados).encode()):
            q, fontes = api(Path(pasta), 'BTCUSDT', 'klines', '1m', inicio, inicio+120000, 'teste')
            self.assertEqual(len(q), 2)
            self.assertEqual(len(fontes), 1)
            self.assertTrue((Path(pasta)/fontes[0]['arquivo']).exists())

    def test_diario_nao_aceita_candle_parcial(self):
        q = self.diario.copy()
        q.loc[0, 'close_time'] -= 1
        with self.assertRaises(AssertionError):
            validar_diario(q, int(q.open_time.iloc[0]), int(q.open_time.iloc[-1])+DIA)
