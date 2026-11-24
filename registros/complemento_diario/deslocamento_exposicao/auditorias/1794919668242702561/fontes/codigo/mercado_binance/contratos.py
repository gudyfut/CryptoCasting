"""Contrato temporal UTC e campos de mercado, independente de qualquer estudo."""
from dataclasses import dataclass
import re
import numpy as np
import pandas as pd

COLUNAS_BRUTAS = ['tempo', 'open', 'high', 'low', 'close', 'volume', 'fim',
                 'volume_cotacao', 'negocios', 'compra_base', 'compra_cotacao', 'ignorar']
VALORES = ['open', 'high', 'low', 'close', 'volume', 'negocios', 'volume_cotacao', 'compra_base', 'compra_cotacao']
OHLCV = ['open', 'high', 'low', 'close', 'volume']


def utc(valor):
    t = pd.Timestamp(valor)
    if pd.isna(t) or t.tzinfo is None:
        raise ValueError('Timestamp deve declarar fuso horário, preferencialmente Z/UTC.')
    return t.tz_convert('UTC')


def validar_par(par):
    if not isinstance(par, str) or not re.fullmatch(r'[A-Z0-9]{5,30}', par):
        raise ValueError('Par inválido; usar identificador Spot, como BTCUSDT.')
    return par


@dataclass(frozen=True)
class Periodo:
    inicio: pd.Timestamp
    fim: pd.Timestamp

    def __post_init__(self):
        object.__setattr__(self, 'inicio', utc(self.inicio))
        object.__setattr__(self, 'fim', utc(self.fim))
        if self.inicio >= self.fim or self.inicio.value % 60_000_000_000 or self.fim.value % 60_000_000_000:
            raise ValueError('Período [início,fim) deve ser crescente e alinhado ao minuto.')

    @property
    def minutos(self):
        return int((self.fim - self.inicio) / pd.Timedelta(minutes=1))

    def json(self):
        return {'inicio': self.inicio.isoformat(), 'fim': self.fim.isoformat()}

    def meses(self):
        if self.inicio.day != 1 or self.fim.day != 1 or self.inicio != self.inicio.normalize() or self.fim != self.fim.normalize():
            raise ValueError('Arquivos mensais exigem meses completos.')
        cortes = pd.date_range(self.inicio, self.fim, freq='MS')
        return [Periodo(a,b) for a,b in zip(cortes[:-1],cortes[1:])]


def conferir_candles(q, intervalo):
    if not isinstance(intervalo, int) or isinstance(intervalo,bool) or intervalo <= 0 or 1440 % intervalo:
        raise ValueError('Intervalo deve ser um divisor inteiro positivo de 1440 minutos.')
    necessarias = {'inicio_utc','fim_utc','completo', *OHLCV}
    if not necessarias <= set(q.columns) or not len(q):
        raise ValueError('Contrato de candles ausente/vazio.')
    a = pd.DatetimeIndex(q['inicio_utc']); b = pd.DatetimeIndex(q['fim_utc'])
    if a.tz is None or b.tz is None or a.hasnans or b.hasnans:
        raise ValueError('Calendário exige timestamps válidos com fuso.')
    passo = pd.Timedelta(minutes=intervalo)
    if (a[1:]-a[:-1] != passo).any() or (b-a != passo).any() or (a.as_unit('ns').asi8 % passo.value).any():
        raise ValueError('Calendário não é uma grade completa alinhada em UTC.')
    if q['completo'].dtype != bool:
        raise ValueError('Indicador completo deve ser booleano, sem ausências.')
    v = q[OHLCV].to_numpy(float); ok = q['completo'].to_numpy()
    if np.isinf(v).any() or not np.isfinite(v[ok]).all() or not np.isnan(v[~ok]).all():
        raise ValueError('Candle incompleto deve ter OHLCV ausente; completo deve ser finito.')
    o,h,l,c,vol = v[ok].T
    if (v[ok,:4] <= 0).any() or (vol < 0).any() or (h < np.maximum(o,c)).any() or (l > np.minimum(o,c)).any() or (h < l).any():
        raise ValueError('Geometria/preços/volume inválidos.')
