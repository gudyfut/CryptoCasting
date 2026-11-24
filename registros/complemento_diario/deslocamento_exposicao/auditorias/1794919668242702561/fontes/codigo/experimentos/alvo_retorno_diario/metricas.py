import math
import numpy as np


def metricas_retorno(y,p,ultimo=None):
    y,p=np.asarray(y,dtype=np.float64),np.asarray(p,dtype=np.float64)
    if y.shape!=p.shape or y.ndim!=1 or not np.isfinite(p).all():raise ValueError('Retornos inválidos.')
    mse=float(np.mean((p-y)**2));base=float(np.mean(y**2))
    return {'n':len(y),'mse_retorno':mse,'rmse_retorno':math.sqrt(mse),'mae_retorno':float(np.mean(abs(p-y))),
            'vies_retorno':float(np.mean(p-y)),'mse_naive_retorno':base,'habilidade_mse_retorno_naive':1-mse/base if base else None,
            'acerto_sinal':float(np.mean(np.sign(p)==np.sign(y))),'retornos_previstos_menores_igual_menos_um':int((p<=-1).sum())}


def avaliar_precos(y,p,ultimo):
    r=metricas(y,p,ultimo)
    r.update(metricas_retorno(np.asarray(y)/ultimo-1,np.asarray(p)/ultimo-1))
    return r

def metricas(y,p,ultimo):
    y,p,ultimo=[np.asarray(v,dtype=np.float64) for v in (y,p,ultimo)]
    if y.shape!=p.shape or y.shape!=ultimo.shape or y.ndim!=1 or not np.isfinite(p).all():
        raise ValueError('Previsões inválidas ou broadcasting.')
    erro=p-y;real=y/ultimo-1;prev=p/ultimo-1
    mse=float(np.mean(erro**2));naive=float(np.mean((ultimo-y)**2))
    return {'n':len(y),'mse_usdt2':mse,'rmse_usdt':math.sqrt(mse),'mae_usdt':float(abs(erro).mean()),
            'mape_pct':float((abs(erro)/y).mean()*100),'mse_naive_usdt2':naive,
            'habilidade_mse_naive':1-mse/naive if naive else None,'mae_retorno':float(abs(prev-real).mean()),
            'acerto_sinal':float(np.mean(np.sign(prev)==np.sign(real))),
            'vies_retorno':float(np.mean(prev-real)),'precos_previstos_nao_positivos':int((p<=0).sum())}


