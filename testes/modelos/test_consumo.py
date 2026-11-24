from infraestrutura.caminhos import CODIGO
import ast
from copy import deepcopy
from dataclasses import replace
import unittest
import numpy as np
import pandas as pd
from .apoio import conjunto
from infraestrutura.artefatos import RAIZ
from modelos import ConsumoModelos, prever_naive
from modelos.contratos import PedidoPrevisao, montar_resultado


class Consumo(unittest.TestCase):
    def setUp(self):
        self.q = conjunto()
        self.c = ConsumoModelos(self.q, 'sintetico')

    def test_janelas_exatas_canais_e_origem(self):
        for parte in self.q.partes:
            p = self.c.solicitar(parte, [0, len(self.q.partes[parte]) - 1])
            x = self.c.lote_neural(p).entradas
            self.assertEqual(x.shape, (2, 168, 5))
            for j, i in enumerate(p.origens.indice_candle):
                np.testing.assert_array_equal(x[j], self.q.matriz[i - 167:i + 1])
                self.assertEqual(p.origens.origem_utc.iloc[j], self.q.origens.origem_utc.iloc[i])

    def test_alvos_escalados_e_inversao(self):
        p = self.c.solicitar('treino', [1, 4])
        y = self.c.alvos_supervisionados(p, False)
        z = self.c.alvos_supervisionados(p)
        self.assertEqual(z.shape, (2,)); self.assertEqual(z.dtype, np.float32)
        np.testing.assert_allclose(self.c.decodificar_saida_neural(p, z), y, rtol=1e-6, atol=1e-9)
        with self.assertRaises(ValueError): self.c.decodificar_saida_neural(p, z[:, None])

    def test_naive_zero_real_nao_media_alvo(self):
        p = self.c.solicitar('teste', [0, 1])
        np.testing.assert_array_equal(prever_naive(p).previsao, [0., 0.])
        self.assertNotEqual(self.c.especificacao.media_alvo, 0.)
        np.testing.assert_array_equal(self.c.decodificar_saida_neural(p, [0, 0]), [self.c.especificacao.media_alvo] * 2)

    def test_futuro_fora_do_pedido_e_operacional_sem_alvo(self):
        p = self.c.solicitar('operacional', [0])
        self.assertNotIn('alvo', p.origens); self.assertNotIn('preco_destino', p.origens)
        with self.assertRaises(ValueError): self.c.alvos_supervisionados(p)
        with self.assertRaises(ValueError): PedidoPrevisao(p.identidade, p.particao, p.origens.assign(alvo=1.))

    def test_mudanca_no_futuro_nao_muda_janela(self):
        p = self.c.solicitar('validacao', [0])
        original = self.c.lote_neural(p).entradas.copy()
        self.q.matriz[:] = 999  # Consumidor tem cópia defensiva, sem referência mutável externa.
        np.testing.assert_array_equal(original, self.c.lote_neural(p).entradas)

    def test_canais_variaveis_e_identidade(self):
        c = ConsumoModelos(conjunto(['fechamento_relativo', 'volume_transformado']), 'sintetico2')
        p = c.solicitar('teste', [0]); self.assertEqual(c.lote_neural(p).entradas.shape, (1, 168, 2))
        with self.assertRaises(ValueError): self.c.lote_neural(p)
        q = conjunto(); q.escalas['canais'] = list(reversed(q.escalas['canais']))
        with self.assertRaises(ValueError): ConsumoModelos(q, 'errado')

    def test_rejeita_shapes_indices_e_pedidos_alterados(self):
        for indices in ([-1], [99999], [0, 0], [1.5], []):
            with self.assertRaises(ValueError): self.c.solicitar('treino', indices)
        p = self.c.solicitar('teste', [0]); p.origens.loc[0, 'close'] *= 2
        with self.assertRaises(ValueError): self.c.lote_neural(p)
        q = conjunto(); q.matriz = q.matriz.T
        with self.assertRaises(ValueError): ConsumoModelos(q, 'errado')

    def test_rejeita_alvo_deslocado_e_purga_violada(self):
        for coluna in ('alvo', 'preco_destino'):
            q = conjunto(); q.origens.loc[300, coluna] += .01
            with self.assertRaises(ValueError): ConsumoModelos(q, 'errado')
        q = conjunto(); q.partes['treino'] = q.partes['treino'].iloc[:-1]
        with self.assertRaises(ValueError): ConsumoModelos(q, 'errado')

    def test_arima_prefixo_limite_e_mesmas_origens(self):
        p = self.c.solicitar('validacao', [0, 10]); h = self.c.historico_arima(p)
        self.assertEqual(len(h.log_precos), int(p.origens.indice_candle.max()) + 1)
        np.testing.assert_array_equal(h.indices_origens, p.origens.indice_candle)
        ajuste = self.c.dados_ajuste_arima()
        self.assertEqual(len(ajuste['endog']), ajuste['indice_fim_ajuste'] + 1)
        self.assertLess(ajuste['indice_fim_ajuste'], int(p.origens.indice_candle.min()))
        self.assertLess(self.q.origens.origem_utc.iloc[ajuste['indice_fim_ajuste']], pd.Timestamp('2021-01-15T00:00Z'))

    def test_resultado_sem_broadcasting(self):
        p = self.c.solicitar('teste', [0, 1])
        for valor in (0., [[0.], [1.]], [0., float('nan')]):
            with self.assertRaises(ValueError): montar_resultado(p, valor)

    def test_fronteiras_sem_treino_ou_dependencia_historica(self):
        proibidos = {'previsao24', 'estudo_ohlcv', 'experimento_normalizacao', 'experimento_penalizacao'}
        for p in (RAIZ / 'codigo/modelos').glob('*.py'):
            arvore = ast.parse(p.read_text(encoding='utf-8'))
            for n in ast.walk(arvore):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                    self.assertNotIn(n.func.attr, ('fit', 'backward', 'step', 'smooth'), str(p))
                nomes = [a.name for a in n.names] if isinstance(n, ast.Import) else [n.module or ''] if isinstance(n, ast.ImportFrom) else []
                for nome in nomes:
                    self.assertNotIn(nome.split('.')[0], proibidos)
        for pacote in ('mercado_binance', 'entradas_modelo'):
            for p in (CODIGO/pacote).glob('*.py'):
                arvore = ast.parse(p.read_text(encoding='utf-8'))
                for n in ast.walk(arvore):
                    if isinstance(n, ast.ImportFrom): self.assertNotEqual((n.module or '').split('.')[0], 'modelos')


if __name__ == '__main__': unittest.main()
