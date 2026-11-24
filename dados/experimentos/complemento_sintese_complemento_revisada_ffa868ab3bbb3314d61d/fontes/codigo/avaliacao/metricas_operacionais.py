"""Métricas de patrimônio, separadas de previsão e de qualquer simulador.

A curva deve incluir capital inicial, marcação e custos em ordem temporal.
Nenhum resultado desta função identifica probabilidade de lucro ou ruína.
"""
from __future__ import annotations
import math
import numpy as np


def avaliar_patrimonio(patrimonio, segundos_utc):
    e = np.asarray(patrimonio, dtype=np.float64)
    t = np.asarray(segundos_utc, dtype=np.float64)
    if e.ndim != 1 or e.shape != t.shape or len(e) < 2:
        raise ValueError('Curva e instantes precisam ter a mesma dimensão unidimensional.')
    if not np.isfinite(e).all() or not np.isfinite(t).all() or e[0] <= 0:
        raise ValueError('Curva não finita ou capital inicial inválido.')
    if (np.diff(t) < 0).any() or t[-1] <= t[0]:
        raise ValueError('Curva sem ordem/duração temporal válida.')
    dias = float((t[-1] - t[0]) / 86400)
    picos = np.maximum.accumulate(e)
    dd = 1 - e / picos
    maxdd = float(dd.max())
    insolvente = bool((e <= 0).any())
    g = None if insolvente else math.log(float(e[-1] / e[0])) / dias
    try:
        cagr = None if g is None else math.expm1(365*g)
    except OverflowError:
        cagr = None
    calmar = None if cagr is None or maxdd <= 1e-12 else cagr / maxdd
    if calmar is not None and not math.isfinite(calmar):
        calmar = None
    ultimo_pico, duracao, em_queda = float(t[0]), 0., False
    for x, pico, instante in zip(e, picos, t):
        if x >= pico:
            if em_queda:
                duracao = max(duracao, float(instante)-ultimo_pico)
            em_queda = False
            ultimo_pico = float(instante)
        else:
            em_queda = True
            duracao = max(duracao, float(instante)-ultimo_pico)
    return {'dias': dias, 'capital_inicial': float(e[0]), 'capital_final': float(e[-1]),
        'retorno_liquido': float(e[-1]/e[0]-1), 'crescimento_log_diario': g,
        'cagr': cagr, 'drawdown_maximo': maxdd, 'calmar': calmar,
        'insolvente': insolvente, 'tempo_maximo_abaixo_pico_dias': duracao/86400,
        'drawdown_final_aberto': bool(e[-1] < picos[-1])}


def resumo_pareado(linhas, recortes, seeds):
    """Não calcula score de grade parcial e não transforma caixa em Calmar infinito."""
    esperado = {(b, s) for b in recortes for s in seeds}
    chaves = [(r['recorte'], r['seed']) for r in linhas]
    if len(chaves) != len(set(chaves)) or set(chaves) != esperado:
        raise ValueError('Cobertura bloco×seed incompleta ou duplicada.')
    nomes = ['retorno_liquido', 'crescimento_log_diario', 'drawdown_maximo', 'calmar']
    saida = {'celulas': len(linhas), 'medias': {}, 'medianas': {}, 'quantis_10_90': {}}
    for nome in nomes:
        v = [r['metricas'][nome] for r in linhas]
        if any(x is not None and not math.isfinite(x) for x in v):
            raise ValueError(f'Métrica não finita: {nome}')
        # Uma média não pode esconder as células indefinidas selecionando só as boas.
        if any(x is None for x in v):
            saida['medias'][nome] = saida['medianas'][nome] = saida['quantis_10_90'][nome] = None
        else:
            saida['medias'][nome] = float(np.mean(v))
            saida['medianas'][nome] = float(np.median(v))
            saida['quantis_10_90'][nome] = np.quantile(v, [.1, .9]).tolist()
    saida['score_calmar'] = saida['medianas']['calmar']
    saida['insolvencias'] = sum(bool(r['metricas']['insolvente']) for r in linhas)
    saida['maior_drawdown'] = max(r['metricas']['drawdown_maximo'] for r in linhas)
    return saida
