"""Contrato somente de avaliação: preços minuto e settlements nunca são sinais."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json

MINUTO = 60000


@dataclass
class Mercado:
    tempo: np.ndarray
    negociacao: np.ndarray  # open, high, low, close
    marca: np.ndarray
    funding_taxa: np.ndarray
    funding_preco: np.ndarray
    funding_evento: np.ndarray
    funding_exato: np.ndarray
    funding_publicado: np.ndarray
    funding_intervalo: np.ndarray

    def __post_init__(self):
        n = len(self.tempo)
        if n < 2 or np.any(np.diff(self.tempo) != MINUTO):
            raise ValueError('Mercado minuto descontínuo.')
        for a in (self.negociacao, self.marca):
            if a.shape != (n, 4) or not np.isfinite(a).all() or (a <= 0).any():
                raise ValueError('Preços inválidos.')
            if (a[:,1] < a[:,[0,2,3]].max(axis=1)).any() or (a[:,2] > a[:,[0,1,3]].min(axis=1)).any():
                raise ValueError('OHLC inconsistente.')
        for a in (self.funding_taxa, self.funding_preco, self.funding_evento,
                  self.funding_exato, self.funding_publicado, self.funding_intervalo):
            if a.shape != (n,):
                raise ValueError('Dimensão funding inválida.')
        if not np.isfinite(self.funding_taxa).all():
            raise ValueError('Taxa de funding não finita.')
        self.eventos = np.flatnonzero(self.funding_evento)

    def indice(self, ms):
        i = int(np.searchsorted(self.tempo, ms))
        if i >= len(self.tempo) or self.tempo[i] != ms:
            raise ValueError('Instante sem observação minuto.')
        return i

    def estimativa_funding(self, sinal_ms):
        # Publicação só é presumida um minuto DEPOIS do timestamp real.
        eventos = self.eventos
        j = np.searchsorted(self.funding_publicado[eventos], sinal_ms, side='right')-1
        if j < 0:
            return 0.
        k = eventos[j]
        return float(self.funding_taxa[k]*24/self.funding_intervalo[k])


def de_quadros(k, m, f):
    k = k.sort_values('open_time').reset_index(drop=True)
    m = m.sort_values('open_time').reset_index(drop=True)
    t = k.open_time.to_numpy(dtype=np.int64)
    if not np.array_equal(t, m.open_time.to_numpy(dtype=np.int64)):
        raise ValueError('Marca e negociação não alinhadas.')
    n = len(t); taxas = np.zeros(n); precos = np.full(n, np.nan)
    evento = np.zeros(n, bool); exato = np.zeros(n, bool)
    publicado = np.zeros(n, np.int64); intervalo = np.full(n, 8.)
    for r in f.sort_values('fundingTime').to_dict('records'):
        ts = int(r['fundingTime']); i = int(np.searchsorted(t, ts//MINUTO*MINUTO))
        if i >= n or t[i] != ts//MINUTO*MINUTO or evento[i]:
            raise ValueError('Settlement ausente/duplicado.')
        evento[i] = True; taxas[i] = float(r['fundingRate'])
        p = float(r.get('markPrice', np.nan)); exato[i] = bool(np.isfinite(p) and p > 0)
        precos[i] = p if exato[i] else np.nan
        publicado[i] = ts+MINUTO
        intervalo[i] = float(r.get('intervalo_horas', 8.))
        if not np.isfinite(intervalo[i]) or intervalo[i] <= 0:
            raise ValueError('Intervalo funding inválido.')
    cols = ['open','high','low','close']
    return Mercado(t, k[cols].to_numpy(float), m[cols].to_numpy(float), taxas,
                   precos, evento, exato, publicado, intervalo)


def carregar(final=False):
    ponteiros = ['registros/operacional_futuros/dados/execucao.json']
    if final:
        ponteiros.append('registros/mercado_futuros/execucao.json')
    quadros = {nome: [] for nome in ('klines','markPriceKlines','funding')}
    for nome in ponteiros:
        p = RAIZ/ler_json(RAIZ/nome)['pasta']
        for tipo in quadros:
            quadros[tipo].append(pd.read_parquet(p/(tipo+'.parquet')))
    q = {nome: pd.concat(v, ignore_index=True) for nome,v in quadros.items()}
    mercado = de_quadros(q['klines'],q['markPriceKlines'],q['funding'])
    # Agregação não modifica artefatos da coleta.
    k = q['klines']; agrupador = k.open_time//3600000*3600000
    h = k.groupby(agrupador).agg(open=('open','first'),high=('high','max'),
        low=('low','min'),close=('close','last'),volume=('volume','sum'))
    h.index.name='open_time'; h=h.reset_index(); h['close_time']=h.open_time+3599999
    return mercado,h
