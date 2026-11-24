"""Padronização congelada por canal nos candles únicos do treino.

Parte dos valores float32 efetivamente entregues à referência; momentos e
transformação em float64, saída float32. Não altera alvos/preços da operação.
"""
from copy import deepcopy
import hashlib
import math
import numpy as np
from entradas_modelo.retorno_diario import preparar as preparar_referencia

RECEITA = {'metodo':'zscore_por_canal','ajuste':'candles_unicos_janelas_treino',
           'ddof':0,'aritmetica':'float64_sobre_entrada_float32_da_referencia',
           'momentos':'math_fsum_float64','saida':'float32','canal_constante':'escala_um','clipping':None}


def configurar_referencia(c):
    r=deepcopy(c)
    assert r['normalizar'] is True and r.pop('padronizacao')==RECEITA
    r['normalizar']=False
    return r


def candles_unicos(x):
    if x.ndim!=3 or x.shape[1:]!=(6,14) or not len(x):raise ValueError('Janelas incompatíveis.')
    if not np.isfinite(x).all():raise ValueError('Entrada não finita.')
    np.testing.assert_array_equal(x[1:,:,:-1],x[:-1,:,1:])
    return np.concatenate((x[0].T,x[1:,:,-1]),axis=0).astype(np.float64)


def ajustar_escalas(treino):
    unicos=candles_unicos(treino['x'])
    # Ordem explícita independente de strides/rotinas de redução NumPy Windows/WSL.
    media=np.array([math.fsum(map(float,col))/len(unicos) for col in unicos.T])
    desvio=np.array([math.sqrt(math.fsum((float(v)-float(m))**2 for v in col)/len(unicos)) for col,m in zip(unicos.T,media)])
    escala=np.where(desvio==0,1.,desvio)
    if not np.isfinite(escala).all() or (escala<=0).any():raise ValueError('Escala inválida.')
    return {'receita':RECEITA,'media':media.tolist(),'desvio_observado':desvio.tolist(),
            'escala':escala.tolist(),'candles_unicos':len(unicos),
            'primeiro_candle_ms':int(treino['origens_ms'][0]-14*86400000),
            'ultimo_candle_ms':int(treino['origens_ms'][-1]-86400000),
            'valores_ajuste_sha256':hashlib.sha256(unicos.astype('<f8').tobytes()).hexdigest()}


def transformar(x,escalas):
    media=np.asarray(escalas['media']);escala=np.asarray(escalas['escala'])
    assert media.shape==escala.shape==(6,) and (escala>0).all()
    z=((x.astype(np.float64)-media[None,:,None])/escala[None,:,None]).astype(np.float32)
    if not np.isfinite(z).all():raise ValueError('Entrada padronizada não finita.')
    return z


def preparar_com_escalas(diario,c):
    dados=preparar_referencia(diario,configurar_referencia(c))
    escalas=ajustar_escalas(dados['treino'])
    for fase in dados.values():fase['x']=transformar(fase['x'],escalas)
    return dados,escalas


def preparar(diario,c):return preparar_com_escalas(diario,c)[0]
