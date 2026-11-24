"""Médias de modelos, blocos com peso igual e três contrastes predefinidos."""
import math
import numpy as np
import pandas as pd

PARES = [('crua', 'atual'), ('niveis_padronizados', 'atual'), ('crua', 'niveis_padronizados')]


def contraste(blocos, candidata, referencia, replicas=2000, dias=(7,14,28), seed=20261104):
    diarios, pontos = [], {}
    ns = None
    for nome, b in blocos.items():
        a, z = np.asarray(b[candidata]), np.asarray(b[referencia])
        if a.shape != z.shape or a.ndim != 2 or not np.isfinite(a-z).all():
            raise ValueError('Perdas/seeds não pareadas.')
        if ns is None: ns = a.shape[0]
        if a.shape[0] != ns or a.shape[1] != len(b['origens']):
            raise ValueError('Origens/seeds divergentes.')
        dif = a-z; pontos[nome] = float(dif.mean())
        cal = pd.DatetimeIndex(b['origens'])
        n = pd.Series(1, index=cal).resample('D').sum().to_numpy()
        soma = np.stack([pd.Series(d, index=cal).resample('D').sum().to_numpy() for d in dif])
        diarios.append((soma,n))
    intervalos = {}
    for largura in dias:
        g = np.random.default_rng(seed+largura); amostras = []
        for _ in range(replicas):
            seeds = g.integers(0,ns,size=ns); valores = []
            for soma,n in diarios:
                ini = g.integers(0,len(n),size=math.ceil(len(n)/largura))
                ix = ((ini[:,None]+np.arange(largura)) % len(n)).ravel()[:len(n)]
                valores.append(float(soma[seeds][:,ix].sum()/(ns*n[ix].sum())))
            amostras.append(float(np.mean(valores)))
        alpha = .05/3
        intervalos[str(largura)] = {'ic95': np.quantile(amostras,[.025,.975]).tolist(),
            'ic_bonferroni_98_333': np.quantile(amostras,[alpha/2,1-alpha/2]).tolist()}
    media = float(np.mean(list(pontos.values())))
    ic = intervalos['14' if '14' in intervalos else str(dias[0])]['ic_bonferroni_98_333']
    decisao = 'melhora' if media<0 and ic[1]<0 else 'piora' if media>0 and ic[0]>0 else 'inconclusivo'
    return {'candidata': candidata, 'referencia': referencia, 'diferenca_mse': media, 'por_bloco': pontos,
        'intervalos': intervalos, 'decisao': decisao, 'replicas': replicas, 'seeds': ns,
        'limites': 'Retrospectivo; quatro blocos fixos, mesmos índices de seeds pareadas entre blocos; não garante generalização.'}
