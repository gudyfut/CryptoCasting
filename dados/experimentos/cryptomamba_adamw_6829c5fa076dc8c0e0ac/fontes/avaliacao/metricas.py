"""Erro de retorno, ganho contra persistência e diagnóstico direcional."""
import numpy as np

def calcular(real, previsto):
    y = np.asarray(real,dtype=np.float64)
    p = np.asarray(previsto,dtype=np.float64)
    if y.ndim != 1 or p.shape != y.shape or not len(y) or not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError('Vetores de avaliação inválidos.')
    erro = p-y
    mse = float(np.mean(erro**2))
    referencia = float(np.mean(y**2))
    sinais = np.sign(y)
    previstos = np.sign(p)
    recalls = [float(np.mean(previstos[sinais==k]==k)) if (sinais==k).any() else None for k in (-1,1)]
    return {'n':len(y),'mse':mse,'rmse':float(np.sqrt(mse)),'mae':float(np.mean(np.abs(erro))),
            'mse_naive':referencia,'habilidade_mse':1-mse/referencia if referencia>0 else None,
            'vies':float(erro.mean()),'acuracia_direcional':float(np.mean(previstos==sinais)),
            'acerto_balanceado_direcional':float(np.mean(recalls)) if all(v is not None for v in recalls) else None,
            'recall_queda':recalls[0],'recall_alta':recalls[1],
            'reais_queda':int((sinais<0).sum()),'reais_zero':int((sinais==0).sum()),'reais_alta':int((sinais>0).sum()),
            'previsoes_queda':int((previstos<0).sum()),'previsoes_zero':int((previstos==0).sum()),'previsoes_alta':int((previstos>0).sum())}
