"""Médias individuais: sem ensemble, imputação de operação ou peso por seed favorável."""
import math
import numpy as np
import pandas as pd


def resumir(chaves,res,prev,parte):
    n=len(chaves);ms=[res[k]['metricas'][parte] for k in chaves]
    campos=('mse','rmse','mae','habilidade_mse','vies','acuracia_direcional','acerto_balanceado_direcional')
    m={k:float(np.mean([x[k] for x in ms])) for k in campos}
    m['mse_desvio_seeds']=float(np.std([x['mse'] for x in ms],ddof=1)) if n>1 else None
    m['mse_por_seed']={k:res[k]['metricas'][parte]['mse'] for k in chaves}
    qs=[prev[k,parte].loc[pd.DatetimeIndex(prev[k,parte].origem_utc).hour==0] for k in chaves]
    if len(qs[0]):
        mse=float(np.mean([np.mean((q.previsao-q.alvo)**2) for q in qs]));base=float(np.mean(qs[0].alvo**2))
        m['origens00utc']={'n_por_seed':len(qs[0]),'mse':mse,'habilidade_naive':1-mse/base if base else None}
    else:m['origens00utc']=None
    op={}
    for perfil in ('base','agravado','bruto_mesmos_sinais'):
        vs=[res[k]['spot'][perfil] for k in chaves]
        if not all(x['retorno_auditavel'] and x['risco_auditavel'] for x in vs):raise ValueError('Operação incompleta não é zero.')
        op[perfil]={k:float(np.mean([x[k] for x in vs])) for k in ('retorno_liquido','drawdown','capital_final','entradas_planejadas','custos_observados','minutos_expostos_planejados')}
        op[perfil]['retorno_desvio_seeds']=float(np.std([x['retorno_liquido'] for x in vs],ddof=1)) if n>1 else None
    return {'n_seeds':n,'metricas':m,'spot':op}


def metricas_preco(q):
    c=q.close.to_numpy(float);real=q.preco_destino.to_numpy(float);p=c*np.exp(q.previsao.to_numpy(float))
    if not np.isfinite(p).all() or not np.isfinite(real).all() or (real<=0).any():raise ValueError('Preço inválido.')
    n=len(q);e=p-real;mse=math.fsum(float(v)**2 for v in e)/n
    return {'n':n,'mse_usdt2':mse,'rmse_usdt':math.sqrt(mse),'mae_usdt':math.fsum(abs(float(v)) for v in e)/n,
        'mape_percentual':100*math.fsum(abs(float(v/y)) for v,y in zip(e,real))/n,
        'mse_naive_usdt2':math.fsum(float(v)**2 for v in c-real)/n,
        'definicao':'C_atual*exp(previsao_log); não é previsão direta treinada em dólares'}
