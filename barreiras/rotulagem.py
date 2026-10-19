"""Primeiro toque observado; não usa o fechamento final como substituto do caminho."""
from __future__ import annotations

import numpy as np
from numba import njit


@njit(cache=True)
def rotular(minutos, entradas, distancias, horizonte_minutos):
    n = len(entradas)
    classes = np.full(n, -1, np.int8)
    saidas = np.full(n, -1, np.int64)
    conhecidos = np.full(n, -1, np.int64)
    precos = np.full(n, np.nan, np.float64)
    ambiguos = np.zeros(n, np.bool_)
    # 0=observado; 1=entrada ausente/sem negócios; 2=lacuna no caminho;
    # 3=fim de dados; 4=expiração sem negócio observado.
    motivos = np.full(n, 3, np.int8)
    for i in range(n):
        e = entradas[i]
        v = e + horizonte_minutos
        if e < 0 or e >= len(minutos):
            continue
        a = minutos[e, 0]
        if not np.isfinite(a) or minutos[e, 5] <= 0:
            motivos[i] = 1
            continue
        u = a * np.exp(distancias[i])
        l = a * np.exp(-distancias[i])
        interrompido = False
        for j in range(e, min(v, len(minutos))):
            o, h, baixo = minutos[j, 0], minutos[j, 1], minutos[j, 2]
            if not (np.isfinite(o) and np.isfinite(h) and np.isfinite(baixo)):
                motivos[i] = 2
                interrompido = True
                break
            if minutos[j, 5] <= 0:
                continue
            classe = -1
            preco = np.nan
            conhecido = j
            if o >= u:
                classe, preco = 2, o
            elif o <= l:
                classe, preco = 0, o
            elif baixo <= l:
                classe, preco, conhecido = 0, l, j+1
                ambiguos[i] = h >= u
            elif h >= u:
                classe, preco, conhecido = 2, u, j+1
            if classe >= 0:
                classes[i], precos[i], saidas[i], conhecidos[i] = classe, preco, j, conhecido
                motivos[i] = 0
                break
        if classes[i] >= 0 or interrompido or v >= len(minutos):
            continue
        if not np.isfinite(minutos[v, 0]):
            motivos[i] = 2
        elif minutos[v, 5] <= 0:
            motivos[i] = 4
        else:
            classes[i], precos[i], saidas[i], conhecidos[i] = 1, minutos[v, 0], v, v
            motivos[i] = 0
    return classes, saidas, conhecidos, precos, ambiguos, motivos
