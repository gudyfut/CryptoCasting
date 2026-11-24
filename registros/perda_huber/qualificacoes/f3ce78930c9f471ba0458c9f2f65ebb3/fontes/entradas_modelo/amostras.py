"""Divisões purgadas e normalização exclusivamente ajustada no treino."""
import numpy as np
import pandas as pd
from mercado_binance.contratos import utc


def separar(origens,x,contexto,divisao,passo_origens=1):
    if (not isinstance(contexto,int) or isinstance(contexto,bool) or contexto<1 or contexto>len(origens)
            or not isinstance(passo_origens,int) or isinstance(passo_origens,bool) or passo_origens<1):
        raise ValueError('Contexto/passo de origens inválido.')
    if list(divisao)!=['treino','validacao','teste']:
        raise ValueError('Definir treino, validação e teste nesta ordem.')
    fronteira=None
    for limites in divisao.values():
        if len(limites)!=2:
            raise ValueError('Cada partição exige [início,fim).')
        a,b=map(utc,limites)
        if a>=b or (fronteira is not None and a<fronteira):
            raise ValueError('Divisões fora de ordem ou sobrepostas.')
        fronteira=b
    if x.ndim!=2 or len(x)!=len(origens) or not np.array_equal(origens.indice_candle,np.arange(len(x))):
        raise ValueError('Índices/entradas desalinhados.')
    valido=np.isfinite(x).all(axis=1)
    causal=pd.Series(valido).rolling(contexto,min_periods=contexto).sum().eq(contexto).to_numpy()
    # Grade fixada pelo primeiro candle do artefato; não depende de perdas ou retornos futuros.
    causal = causal & ((np.arange(len(origens))%passo_origens)==0)
    observado=causal&np.isfinite(origens['alvo'].to_numpy())
    partes={}
    for nome,limites in divisao.items():
        inicio,fim=map(utc,limites)
        periodo=(origens.origem_utc>=inicio)&(origens.origem_utc<fim)
        q=origens.loc[periodo&observado&(origens.destino_utc<fim)].copy()
        if q.empty:
            raise ValueError(f'Partição sem exemplos válidos: {nome}')
        partes[nome]=q
        if nome=='teste':
            partes['operacional']=origens.loc[periodo&causal].copy()
    return partes


def ajustar_escalas(x,treino,contexto,canais):
    usados=np.zeros(len(x),bool)
    for i in treino.indice_candle.to_numpy(np.int64):
        if i<contexto-1 or i>=len(x):
            raise ValueError('Índice de treino não permite contexto completo.')
        usados[i-contexto+1:i+1]=True
    valores=x[usados]
    y=treino.alvo.to_numpy(np.float64)
    if not len(valores) or not np.isfinite(valores).all() or not np.isfinite(y).all():
        raise ValueError('Escalas não podem receber lacunas.')
    media=valores.mean(axis=0);desvio=valores.std(axis=0,ddof=0)
    constantes=desvio==0;desvio=np.where(constantes,1.,desvio)
    escala_alvo=float(y.std(ddof=0))
    if escala_alvo<=0:
        raise ValueError('Alvo de treino não tem variância positiva.')
    escalas={'canais':canais,'media_entrada':media.tolist(),'escala_entrada':desvio.tolist(),
             'canais_constantes':constantes.tolist(),'candles_unicos_ajuste':int(usados.sum()),
             'primeiro_indice_ajuste':int(np.flatnonzero(usados)[0]),'ultimo_indice_ajuste':int(np.flatnonzero(usados)[-1]),
             'media_alvo':float(y.mean()),'escala_alvo':escala_alvo,
             'regra':'união de candles únicos dos contextos de treino; ddof=0; constante recebe escala 1'}
    return escalas


def aplicar_escalas(x,escalas):
    media=np.asarray(escalas['media_entrada']);escala=np.asarray(escalas['escala_entrada'])
    if x.ndim!=2 or x.shape[1]!=len(media) or escala.shape!=media.shape or not np.isfinite(media).all() or not np.isfinite(escala).all() or (escala<=0).any():
        raise ValueError('Dimensão ou valores do scaler incompatíveis.')
    return ((x-media)/escala).astype(np.float32)
