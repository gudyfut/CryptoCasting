"""Ponte validada entre artefato de entradas e consumidores; sem Torch ou ajuste."""
from copy import deepcopy
from pathlib import Path
import numpy as np
import pandas as pd
from entradas_modelo import carregar_conjunto
from infraestrutura.artefatos import identidade, ler_json, sha256
from .contratos import EspecificacaoModelo, PedidoPrevisao, LoteNeural, HistoricoARIMA, vetor_finito

COLUNAS_PEDIDO = ['indice_candle', 'origem_utc', 'destino_utc', 'close']


class ConsumoModelos:
    def __init__(self, conjunto, identidade_dados):
        if not isinstance(identidade_dados, str) or not identidade_dados:
            raise ValueError('Identidade dos dados obrigatória.')
        self._conjunto = deepcopy(conjunto)
        c = self._conjunto.contrato
        e = self._conjunto.escalas
        x = self._conjunto.matriz
        h = self._conjunto.origens
        canais = c['canais']
        if (not isinstance(canais, list) or not canais or len(set(canais)) != len(canais)
                or not all(isinstance(v, str) and v for v in canais)
                or c['dimensao_entrada'] != len(canais) or e['canais'] != canais):
            raise ValueError('Nomes/ordem/dimensão de canais e escalas incompatíveis.')
        for k in ('contexto_passos', 'intervalo_minutos', 'horizonte_minutos', 'passo_origens'):
            if type(c[k]) is not int or c[k] < 1:
                raise ValueError(f'Dimensão temporal inválida: {k}')
        if c['horizonte_minutos'] % c['intervalo_minutos'] or c['alvo'] != 'log_retorno_terminal':
            raise ValueError('Horizonte ou alvo incompatível.')
        if c['normalizacao'] != 'zscore_treino' or c['dtype'] != 'float32':
            raise ValueError('Escala/dtype desconhecido.')
        if x.shape != (len(h), len(canais)) or x.dtype != np.float32 or np.isinf(x).any():
            raise ValueError('Matriz de entradas incompatível.')
        medias = vetor_finito(e['media_entrada'], len(canais), 'Médias dos canais')
        escalas = vetor_finito(e['escala_entrada'], len(canais), 'Escalas dos canais')
        if (escalas <= 0).any() or not np.isfinite([e['media_alvo'], e['escala_alvo']]).all() or e['escala_alvo'] <= 0:
            raise ValueError('Escalas devem ser finitas e positivas.')
        if not np.array_equal(h.indice_candle, np.arange(len(h))):
            raise ValueError('Índice não corresponde à posição na matriz.')
        tempos = pd.DatetimeIndex(h.origem_utc)
        destinos = pd.DatetimeIndex(h.destino_utc)
        if tempos.tz is None or destinos.tz is None or tempos.hasnans or destinos.hasnans:
            raise ValueError('Origem/destino precisam de fuso e valores válidos.')
        if ((tempos[1:] - tempos[:-1] != pd.Timedelta(minutes=c['intervalo_minutos'])).any()
                or (destinos - tempos != pd.Timedelta(minutes=c['horizonte_minutos'])).any()):
            raise ValueError('Grade ou destino deslocado em relação ao horizonte.')
        close = h.close.to_numpy(float)
        if np.isinf(close).any() or (close[np.isfinite(close)] <= 0).any():
            raise ValueError('Preço de fechamento inválido.')
        passos = c['horizonte_minutos'] // c['intervalo_minutos']
        futuro = h.close.shift(-passos).to_numpy(float)
        if (not np.allclose(h.preco_destino, futuro, rtol=1e-12, atol=1e-15, equal_nan=True)
                or not np.allclose(h.alvo, np.log(futuro / close), rtol=1e-12, atol=1e-15, equal_nan=True)):
            raise ValueError('Alvo/preço terminal desalinhado.')
        self._validar_particoes()
        chave = identidade({'dados': identidade_dados, 'contrato': c, 'escalas': e})
        self.especificacao = EspecificacaoModelo(chave, tuple(canais), c['contexto_passos'],
                                                c['intervalo_minutos'], c['horizonte_minutos'],
                                                float(e['media_alvo']), float(e['escala_alvo']))
        self.identidade_dados = identidade_dados

    def _validar_particoes(self):
        q = self._conjunto
        c, h = q.contrato, q.origens
        if set(q.partes) != {'treino', 'validacao', 'teste', 'operacional'}:
            raise ValueError('Partições incompletas/desconhecidas.')
        if list(c['divisao']) != ['treino', 'validacao', 'teste']:
            raise ValueError('Divisões fora de ordem.')
        valido = pd.Series(np.isfinite(q.matriz).all(axis=1)).rolling(c['contexto_passos']).sum().eq(c['contexto_passos']).to_numpy()
        valido = valido & (np.arange(len(h)) % c['passo_origens'] == 0)
        fronteira = None
        for nome in ('treino', 'validacao', 'teste', 'operacional'):
            a, b = map(pd.Timestamp, c['divisao']['teste' if nome == 'operacional' else nome])
            if a.tzinfo is None or b.tzinfo is None or a >= b:
                raise ValueError('Limites temporais inválidos.')
            if nome != 'operacional':
                if fronteira is not None and a < fronteira:
                    raise ValueError('Partições sobrepostas.')
                fronteira = b
            mascara = valido & (h.origem_utc >= a).to_numpy() & (h.origem_utc < b).to_numpy()
            if nome != 'operacional':
                mascara = mascara & np.isfinite(h.alvo) & (h.destino_utc < b)
            esperado = h.loc[mascara]
            recebido = q.partes[nome]
            if esperado.empty or not np.array_equal(esperado.indice_candle, recebido.indice_candle):
                raise ValueError(f'Origens/janelas/purga incompatíveis: {nome}')
            for coluna in ('origem_utc', 'destino_utc', 'close', 'preco_destino', 'alvo'):
                if not esperado[coluna].reset_index(drop=True).equals(recebido[coluna].reset_index(drop=True)):
                    raise ValueError(f'Partição desalinhada: {nome}/{coluna}')

    def solicitar(self, particao, posicoes=None):
        if particao not in self._conjunto.partes:
            raise ValueError('Partição desconhecida.')
        q = self._conjunto.partes[particao]
        if posicoes is not None:
            i = np.asarray(posicoes)
            if (i.ndim != 1 or not np.issubdtype(i.dtype, np.integer) or len(i) == 0
                    or (i < 0).any() or (i >= len(q)).any() or len(np.unique(i)) != len(i)):
                raise ValueError('Posições inválidas ou duplicadas.')
            q = q.iloc[i]
        return PedidoPrevisao(self.especificacao.identidade, particao, q[COLUNAS_PEDIDO].copy().reset_index(drop=True))

    def _indices(self, pedido):
        if pedido.identidade != self.especificacao.identidade or pedido.particao not in self._conjunto.partes:
            raise ValueError('Pedido pertence a outro conjunto/contrato.')
        q = pedido.origens
        if list(q.columns) != COLUNAS_PEDIDO or q.empty:
            raise ValueError('Pedido deve conter somente informações conhecidas na origem.')
        i = q.indice_candle.to_numpy()
        permitidos = self._conjunto.partes[pedido.particao].indice_candle.to_numpy()
        if not np.issubdtype(i.dtype, np.integer) or len(np.unique(i)) != len(i) or not np.isin(i, permitidos).all():
            raise ValueError('Índice fora da população aprovada.')
        esperado = self._conjunto.origens.iloc[i][COLUNAS_PEDIDO].reset_index(drop=True)
        if not esperado.equals(q.reset_index(drop=True)):
            raise ValueError('Metadados do pedido foram alterados.')
        return i

    def lote_neural(self, pedido):
        i = self._indices(pedido)
        return LoteNeural(self.especificacao, self._conjunto.janelas(i))

    def alvos_supervisionados(self, pedido, padronizados=True):
        i = self._indices(pedido)
        if pedido.particao == 'operacional':
            raise ValueError('População operacional não é conjunto supervisionado.')
        y = self._conjunto.origens.alvo.to_numpy()[i].copy()
        if padronizados:
            return ((y - self.especificacao.media_alvo) / self.especificacao.escala_alvo).astype(np.float32)
        return y

    def decodificar_saida_neural(self, pedido, valores):
        self._indices(pedido)
        z = vetor_finito(valores, len(pedido.origens), 'Saída normalizada')
        return z * self.especificacao.escala_alvo + self.especificacao.media_alvo

    def _limite_ajuste_arima(self):
        # Mesmo limite da referência: inclui destinos conhecidos dos alvos de treino.
        return int(self._conjunto.partes['treino'].indice_candle.max()) + self.especificacao.horizonte_passos

    def historico_arima(self, pedido):
        i = self._indices(pedido)
        valores = np.log(self._conjunto.origens.close.to_numpy(float)[:int(i.max()) + 1]).copy()
        observados = np.flatnonzero(np.isfinite(valores))
        if not len(observados):
            raise ValueError('Histórico sem preço observado.')
        return HistoricoARIMA(self.especificacao.identidade, valores, i.copy(),
                              self.especificacao.horizonte_passos, float(valores[observados[0]]),
                              self._limite_ajuste_arima())

    def dados_ajuste_arima(self):
        """Entrega só a série permitida de treino. NÃO estima parâmetros."""
        ultimo = self._limite_ajuste_arima()
        serie = np.log(self._conjunto.origens.close.to_numpy(float)[:ultimo + 1]).copy()
        base = float(serie[np.flatnonzero(np.isfinite(serie))[0]])
        return {'endog': (serie - base) * 100., 'base_log_preco': base,
                'indice_fim_ajuste': ultimo, 'identidade': self.especificacao.identidade}


def carregar_consumo(pasta):
    pasta = Path(pasta)
    conjunto = carregar_conjunto(pasta)  # Confere também toda a cadeia de origem.
    return ConsumoModelos(conjunto, sha256(pasta / 'manifesto.json'))
