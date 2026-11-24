"""Quatro contrastes fixos, incluindo diferença de diferenças da interação."""
import math
import numpy as np
import pandas as pd

CONTRASTES = {
    'huber_na_crua': {'crua_huber': 1., 'crua_mse': -1.},
    'crua_na_huber': {'crua_huber': 1., 'relativa_huber': -1.},
    'combinacao_menos_referencia': {'crua_huber': 1., 'relativa_mse': -1.},
    'interacao': {'crua_huber': 1., 'crua_mse': -1., 'relativa_huber': -1., 'relativa_mse': 1.},
}


def contraste(blocos, coeficientes, cfg):
    diarios, pontos, ns = [], {}, None
    for nome, b in blocos.items():
        formas = {np.asarray(b[v]).shape for v in coeficientes}
        if len(formas) != 1:
            raise ValueError('Variantes não pareadas.')
        forma = next(iter(formas))
        if len(forma) != 2 or forma[0] < 2 or forma[1] != len(b['origens']):
            raise ValueError('Dimensões de seeds/origens inválidas.')
        if ns is None:
            ns = forma[0]
        if ns != forma[0]:
            raise ValueError('Seeds divergentes entre blocos.')
        dif = sum(k * np.asarray(b[v], dtype=float) for v, k in coeficientes.items())
        if not np.isfinite(dif).all():
            raise ValueError('Contraste não finito.')
        pontos[nome] = float(dif.mean())
        cal = pd.DatetimeIndex(b['origens'])
        n = pd.Series(1, index=cal).resample('D').sum().to_numpy()
        soma = np.stack([pd.Series(d, index=cal).resample('D').sum().to_numpy() for d in dif])
        diarios.append((soma, n))
    intervalos = {}
    for largura in cfg['dias']:
        g = np.random.default_rng(cfg['seed'] + largura)
        amostras = []
        for _ in range(cfg['replicas']):
            seeds = g.integers(0, ns, size=ns)
            valores = []
            for soma, n in diarios:
                ini = g.integers(0, len(n), size=math.ceil(len(n)/largura))
                ix = ((ini[:, None]+np.arange(largura)) % len(n)).ravel()[:len(n)]
                valores.append(float(soma[seeds][:, ix].sum()/(ns*n[ix].sum())))
            amostras.append(float(np.mean(valores)))
        alpha = .05 / len(CONTRASTES)
        intervalos[str(largura)] = {
            'ic95': np.quantile(amostras, [.025, .975]).tolist(),
            'ic_bonferroni_98_75': np.quantile(amostras, [alpha/2, 1-alpha/2]).tolist()}
    media = float(np.mean(list(pontos.values())))
    ic = intervalos[str(cfg['principal'])]['ic_bonferroni_98_75']
    decisao = 'negativo' if media < 0 and ic[1] < 0 else 'positivo' if media > 0 and ic[0] > 0 else 'inconclusivo'
    return {'coeficientes': coeficientes, 'diferenca_mse': media, 'por_bloco': pontos,
            'intervalos': intervalos, 'decisao': decisao, 'replicas': cfg['replicas'],
            'seeds': ns, 'familia_contrastes': len(CONTRASTES),
            'interpretacao': 'Negativo favorece candidata nos contrastes simples; na interação significa ganho além da soma dos efeitos na escala aditiva de MSE.',
            'limites': 'Retrospectivo; blocos fixos, mesmos índices de seeds pareadas; sem garantia de generalização.'}
