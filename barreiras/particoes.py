"""Cortes temporais e transformações ajustadas exclusivamente no treino."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .configuracao import COLUNAS, FOLDS


def separar(amostras: pd.DataFrame, comuns: np.ndarray, fold: str):
    limites = FOLDS[fold].limites()
    blocos = {}
    for nome, a, b in zip(('treino','validacao','teste'), limites[:-1], limites[1:]):
        parte = amostras.loc[amostras['origem_utc'].ge(a) & amostras['origem_utc'].lt(b)].copy()
        purgada = parte['expiracao_maxima_utc'].lt(b)
        comum = comuns[parte['indice_hora'].to_numpy(np.int64)]
        parte = parte.loc[purgada & comum].reset_index(drop=True)
        if len(parte) == 0 or (parte['classe'] < 0).any():
            raise ValueError(f'Bloco vazio ou rótulos inválidos: {fold}/{nome}')
        if not parte['origem_utc'].is_monotonic_increasing or parte['origem_utc'].duplicated().any():
            raise ValueError('Origens fora de ordem ou repetidas.')
        if (parte['expiracao_maxima_utc'] >= b).any():
            raise ValueError('Vazamento: rótulo cruza limite temporal.')
        ambiguos = int(parte['ambiguo'].sum())
        toques = int(parte['classe'].ne(1).sum())
        if ambiguos / len(parte) > .01 or (toques and ambiguos/toques > .05):
            raise ValueError(f'Gate de ambiguidade excedido: {fold}/{nome}. Refinar dados, não descartar rótulos.')
        blocos[nome] = parte
    # Populações econômicas não utilizam observabilidade futura nem máscara comum.
    teste = amostras.loc[amostras['origem_utc'].ge(limites[2]) &
                         amostras['origem_utc'].lt(limites[3]) &
                         amostras['expiracao_utc'].lt(limites[3])].copy().reset_index(drop=True)
    blocos['operacional'] = teste
    return blocos


def ajustar_escalas(horas: pd.DataFrame, treino: pd.DataFrame) -> tuple[np.ndarray, dict]:
    usados = np.zeros(len(horas), bool)
    for i in treino['indice_hora'].to_numpy(np.int64):
        if i < 167:
            raise ValueError('Contexto insuficiente.')
        usados[i-167:i+1] = True
    valores = horas[list(COLUNAS)].to_numpy(np.float64)
    selecao = valores[usados]
    if not np.isfinite(selecao).all():
        raise ValueError('Entrada de treino não finita.')
    media = selecao.mean(axis=0)
    escala = selecao.std(axis=0, ddof=0)
    escala[escala == 0] = 1
    aux = np.log(treino['distancia'].to_numpy(np.float64))
    media_aux, escala_aux = float(aux.mean()), float(aux.std())
    if escala_aux == 0:
        escala_aux = 1.0
    metadados = {'media': media.tolist(), 'escala': escala.tolist(), 'media_aux': media_aux,
                 'escala_aux': escala_aux, 'linhas_unicas_ajuste': int(usados.sum()),
                 'primeira_hora_ajuste': horas.loc[usados,'origem_utc'].min().isoformat(),
                 'ultima_hora_ajuste': horas.loc[usados,'origem_utc'].max().isoformat(),
                 'ultima_origem_treino': treino['origem_utc'].max().isoformat(),
                 'ultima_expiracao_treino': treino['expiracao_maxima_utc'].max().isoformat()}
    return ((valores-media)/escala).astype(np.float32), metadados
