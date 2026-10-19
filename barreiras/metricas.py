"""Métricas multiclasse calculáveis diretamente das previsões registradas."""
from __future__ import annotations

import numpy as np


def erros(y, probabilidades):
    y = np.asarray(y, dtype=np.int64)
    p = np.asarray(probabilidades, dtype=np.float64)
    if p.shape != (len(y),3) or not np.isfinite(p).all() or (p < 0).any() or (p > 1).any():
        raise ValueError('Probabilidades inválidas.')
    if not np.allclose(p.sum(axis=1), 1, atol=1e-6) or not np.isin(y,[0,1,2]).all() or len(y)==0:
        raise ValueError('Rótulos ou normalização de probabilidade inválidos.')
    nll = -np.log(np.maximum(p[np.arange(len(y)),y],1e-7))
    brier = ((p-np.eye(3)[y])**2).sum(axis=1)
    return nll, brier


def calcular(y, probabilidades, ambiguos=None):
    y = np.asarray(y,dtype=np.int64)
    p = np.asarray(probabilidades,dtype=np.float64)
    nll,brier = erros(y,p)
    previstos=p.argmax(axis=1)
    matriz=np.zeros((3,3),np.int64)
    np.add.at(matriz,(y,previstos),1)
    suporte=matriz.sum(axis=1)
    contagem_prevista=matriz.sum(axis=0)
    recall=np.divide(matriz.diagonal(),suporte,out=np.zeros(3,float),where=suporte>0)
    precisao=np.divide(matriz.diagonal(),contagem_prevista,out=np.zeros(3,float),where=contagem_prevista>0)
    f1=np.divide(2*precisao*recall,precisao+recall,out=np.zeros(3,float),where=(precisao+recall)>0)
    calibracao=[]
    for k in range(3):
        bins=np.minimum((p[:,k]*10).astype(int),9)
        calibracao.append([{'n':int((bins==b).sum()),
                           'previsao_media':float(p[bins==b,k].mean()) if (bins==b).any() else None,
                           'frequencia':float((y[bins==b]==k).mean()) if (bins==b).any() else None}
                          for b in range(10)])
    resultado={'n':len(y),'log_loss':float(nll.mean()),'brier':float(brier.mean()),
               'balanced_accuracy':float(recall.mean()) if (suporte>0).all() else None,
               'macro_f1':float(f1.mean()) if (suporte>0).all() else None,
               'matriz_confusao':matriz.tolist(),'suporte':suporte.tolist(),
               'recall':[float(recall[k]) if suporte[k] else None for k in range(3)],
               'precisao':[float(precisao[k]) if contagem_prevista[k] else None for k in range(3)],
               'calibracao':calibracao}
    if ambiguos is not None:
        a=np.asarray(ambiguos,bool)
        alternativo=y.copy()
        alternativo[a]=2
        outra_nll,outro_brier=erros(alternativo,p)
        resultado['ambiguidade']={'n':int(a.sum()),'log_loss_superior_primeiro':float(outra_nll.mean()),
             'limite_inferior_log_loss':float(np.minimum(nll,outra_nll).mean()),
             'limite_superior_log_loss':float(np.maximum(nll,outra_nll).mean()),
             'limite_inferior_brier':float(np.minimum(brier,outro_brier).mean()),
             'limite_superior_brier':float(np.maximum(brier,outro_brier).mean())}
    return resultado
