"""Medidas descritivas em retorno simples, sem escolher cortes por lucro."""
import math
import numpy as np


def medir(y,p):
    y,p=np.asarray(y,dtype=float),np.asarray(p,dtype=float)
    if y.ndim!=1 or y.shape!=p.shape or not len(y) or not np.isfinite([y,p]).all():
        raise ValueError('População inválida.')
    media=lambda v:math.fsum(map(float,v))/len(v)
    erro=p-y; my,mp=media(y),media(p); vy,vp=media((y-my)**2),media((p-mp)**2)
    cov=media((y-my)*(p-mp)); mse=media(erro**2); vi=(mp-my)**2
    np.testing.assert_allclose(mse,vi+vy+vp-2*cov,rtol=1e-12,atol=1e-15)
    base=media(y**2); lados={}
    for nome,sinal in [('alta',1),('queda',-1)]:
        ix=np.sign(y)==sinal
        lados[nome]={'n':int(ix.sum()),'recall':float(np.mean(np.sign(p[ix])==sinal)) if ix.any() else None}
    rec=[v['recall'] for v in lados.values() if v['recall'] is not None]
    return {'n':len(y),'mse':mse,'rmse':math.sqrt(mse),'mae':media(abs(erro)),
        'habilidade_naive':1-mse/base if base else None,'vies':media(erro),
        'media_real':my,'media_prevista':mp,'desvio_real':math.sqrt(vy),'desvio_previsto':math.sqrt(vp),
        'razao_desvios':math.sqrt(vp/vy) if vy else None,
        'correlacao':cov/math.sqrt(vy*vp) if vy*vp>0 else None,
        'acerto_sinal':float(np.mean(np.sign(p)==np.sign(y))),
        'balanced_accuracy':float(np.mean(rec)) if len(rec)==2 else None,
        'recall_por_lado':lados,'sinais':{'altas':int((p>0).sum()),'quedas':int((p<0).sum()),'zeros':int((p==0).sum())},
        'decomposicao_mse':{'vies_quadrado':vi,'variancia_real':vy,'variancia_prevista':vp,'menos_duas_covariancias':-2*cov}}


def ridge(x,y,xv,yv,grade=(.01,.1,1.,10.,100.)):
    x=np.asarray(x,dtype=float).reshape(len(x),-1); xv=np.asarray(xv,dtype=float).reshape(len(xv),-1)
    mx=x.mean(axis=0); my=float(np.mean(y)); xc=x-mx
    candidatos=[]; pesos=[]
    for penalizacao in grade:
        w=np.linalg.solve(xc.T@xc/len(x)+penalizacao*np.eye(x.shape[1]), xc.T@(y-my)/len(x))
        vies=my-mx@w; previsao=xv@w+vies
        candidatos.append({'lambda':penalizacao,'mse_validacao':float(np.mean((previsao-yv)**2))})
        pesos.append((w,float(vies)))
    escolha=min(range(len(grade)),key=lambda i:(candidatos[i]['mse_validacao'],i))
    return pesos[escolha],{'candidatos':candidatos,'indice':escolha,'lambda':grade[escolha],
        'criterio':'MSE médio de validação; ordem da grade desempata; intercepto sem penalização.'}
