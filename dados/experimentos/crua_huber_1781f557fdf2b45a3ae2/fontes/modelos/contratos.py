"""Tipos comuns: identidade e unidades acompanham dados e previsões."""
from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class EspecificacaoModelo:
    identidade: str
    canais: tuple[str, ...]
    contexto: int
    intervalo_minutos: int
    horizonte_minutos: int
    media_alvo: float
    escala_alvo: float

    def __post_init__(self):
        if not self.identidade or not self.canais or len(set(self.canais)) != len(self.canais):
            raise ValueError('Identidade/canais inválidos.')
        if any(type(v) is not int or v <= 0 for v in (self.contexto, self.intervalo_minutos, self.horizonte_minutos)):
            raise ValueError('Dimensões temporais inválidas.')
        if self.horizonte_minutos % self.intervalo_minutos:
            raise ValueError('Horizonte não é múltiplo do intervalo.')
        if not np.isfinite([self.media_alvo, self.escala_alvo]).all() or self.escala_alvo <= 0:
            raise ValueError('Escala do alvo inválida.')

    @property
    def dimensao_entrada(self):
        return len(self.canais)

    @property
    def horizonte_passos(self):
        return self.horizonte_minutos // self.intervalo_minutos


@dataclass(frozen=True)
class PedidoPrevisao:
    identidade: str
    particao: str
    origens: pd.DataFrame  # Somente índice, origem, destino programado e close atual.

    def __post_init__(self):
        q = self.origens
        if list(q.columns) != ['indice_candle', 'origem_utc', 'destino_utc', 'close'] or q.empty:
            raise ValueError('Pedido não pode conter alvo ou preço futuro observado.')
        if not np.isfinite(q.close).all() or (q.close <= 0).any() or q.indice_candle.duplicated().any():
            raise ValueError('Origens/preços inválidos no pedido.')
        a, b = pd.DatetimeIndex(q.origem_utc), pd.DatetimeIndex(q.destino_utc)
        if a.tz is None or b.tz is None or a.hasnans or b.hasnans or (b <= a).any():
            raise ValueError('Tempos inválidos no pedido.')


@dataclass(frozen=True)
class LoteNeural:
    especificacao: EspecificacaoModelo
    entradas: np.ndarray  # float32 [lote, tempo, canais]; nenhum alvo neste tipo.


@dataclass(frozen=True)
class HistoricoARIMA:
    identidade: str
    log_precos: np.ndarray  # Grade regular com NaN em lacunas; sem compactar o tempo.
    indices_origens: np.ndarray
    horizonte_passos: int
    base_log_preco: float
    ultimo_indice_ajuste_permitido: int


def vetor_finito(valores, tamanho, nome):
    v = np.asarray(valores, dtype=np.float64)
    if v.shape != (tamanho,) or not np.isfinite(v).all():
        raise ValueError(f'{nome} exige vetor finito [{tamanho}], sem broadcasting.')
    return v


def montar_resultado(pedido, previsoes_log_retorno):
    v = vetor_finito(previsoes_log_retorno, len(pedido.origens), 'Previsão')
    q = pedido.origens.copy(deep=True)
    q['previsao'] = v
    return q  # Nunca adiciona alvo ou preço futuro observado à entrada do modelo.
