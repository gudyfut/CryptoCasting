"""Cinco canais causais, origens comuns e escalas ajustadas só no treino."""
import numpy as np
import pandas as pd

CANAIS = ['abertura_relativa', 'maxima_relativa', 'minima_relativa',
          'fechamento_relativo', 'volume_transformado']


def transformar(horas):
    # Não carregar máscaras de 336h/4 moedas do dataset preliminar como se fossem desta população.
    h = horas[['indice_hora','origem_utc','open','high','low','close','volume']].copy().reset_index(drop=True)
    tempos = pd.to_datetime(h['origem_utc'], utc=True)
    if not (tempos.diff().iloc[1:] == pd.Timedelta(hours=1)).all():
        raise ValueError('Calendário deve ser horário regular, incluindo lacunas explícitas.')
    if not np.array_equal(h['indice_hora'], np.arange(len(h))):
        raise ValueError('Índice horário não corresponde à posição.')
    valores = h[['open', 'high', 'low', 'close', 'volume']].to_numpy(np.float64)
    if np.isinf(valores).any():
        raise ValueError('OHLCV infinito.')
    finitos = np.isfinite(valores).all(axis=1)
    o, a, b, c, v = valores.T
    invalido = ((valores[:, :4] <= 0).any(axis=1) | (v < 0)
                | (a < np.maximum(o, c)) | (b > np.minimum(o, c)) | (a < b))
    if np.any(finitos & invalido):
        raise ValueError('Preço, volume ou geometria OHLC inválidos.')
    anterior = np.r_[np.nan, c[:-1]]
    with np.errstate(divide='ignore', invalid='ignore'):
        x = np.column_stack([np.log(valores[:, :4] / anterior[:, None]), np.log1p(v)])
    # Um candle parcial nunca entra como informação válida.
    x[~finitos] = np.nan
    h['origem_utc'] = tempos
    h['destino_utc'] = tempos + pd.Timedelta(hours=24)
    h['preco_destino'] = h['close'].shift(-24)
    h['alvo'] = np.log(h['preco_destino'] / h['close'])
    return h, x


def separar(horas, x, c):
    w = c['contexto']
    causal = pd.Series(np.isfinite(x).all(axis=1)).rolling(w, min_periods=w).sum().eq(w).to_numpy()
    observavel = causal & np.isfinite(horas['alvo'].to_numpy())
    blocos = {}
    for nome, limites in c['divisao'].items():
        inicio, fim = [pd.Timestamp(t, tz='UTC') for t in limites]
        periodo = (horas['origem_utc'] >= inicio) & (horas['origem_utc'] < fim)
        mascara = periodo & observavel & (horas['destino_utc'] < fim)
        blocos[nome] = horas.loc[mascara].copy()
        if blocos[nome].empty:
            raise ValueError(f'Partição vazia: {nome}')
        if nome == 'teste':
            # Ausência do preço FUTURO não pode excluir uma decisão operacional.
            blocos['operacional'] = horas.loc[periodo & causal].copy()
    return blocos


def padronizar(x, treino, w):
    usados = np.zeros(len(x), dtype=bool)
    for i in treino['indice_hora'].to_numpy(np.int64):
        if i < w - 1:
            raise ValueError('Contexto insuficiente.')
        usados[i - w + 1:i + 1] = True
    ajuste = x[usados]
    if not len(ajuste) or not np.isfinite(ajuste).all():
        raise ValueError('Entradas inválidas para ajuste de escalas.')
    media = ajuste.mean(axis=0)
    desvio = ajuste.std(axis=0, ddof=0)
    constante = desvio == 0
    escala = np.where(constante, 1., desvio)
    y = treino['alvo'].to_numpy(np.float64)
    sy = float(y.std(ddof=0))
    if not np.isfinite(y).all() or sy <= 0:
        raise ValueError('Alvo de treino não tem escala positiva finita.')
    escalas = {'canais': CANAIS, 'media_entrada': media.tolist(), 'escala_entrada': escala.tolist(),
               'canais_constantes': constante.tolist(), 'horas_unicas_ajuste': int(usados.sum()),
               'primeiro_indice_ajuste': int(np.flatnonzero(usados)[0]),
               'ultimo_indice_ajuste': int(np.flatnonzero(usados)[-1]),
               'media_alvo': float(y.mean()), 'escala_alvo': sy,
               'regra': 'união de horas únicas dos contextos de treino; ddof=0; constante recebe escala 1'}
    return ((x - media) / escala).astype(np.float32), escalas


def preparar(horas, c):
    h, x = transformar(horas)
    blocos = separar(h, x, c)
    matriz, escalas = padronizar(x, blocos['treino'], c['contexto'])
    return h, matriz, blocos, escalas
