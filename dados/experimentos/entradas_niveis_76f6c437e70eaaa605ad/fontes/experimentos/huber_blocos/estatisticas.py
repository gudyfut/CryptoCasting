"""Contraste pareado, pesos iguais por bloco, seeds e dias reamostrados."""
import math
import numpy as np
import pandas as pd


def contraste(blocos, cfg):
    """Cada bloco contém origens e perdas [seed, origem] das duas variantes."""
    diarios=[];pontos=[];ns=None
    for b in blocos.values():
        a,z=np.asarray(b['huber'],float),np.asarray(b['mse'],float)
        if a.shape!=z.shape or a.ndim!=2 or not np.isfinite(a-z).all():raise ValueError('Perdas não pareadas.')
        if ns is None:ns=a.shape[0]
        if a.shape[0]!=ns or a.shape[1]!=len(b['origens']):raise ValueError('Seeds/origens divergentes.')
        dif=a-z;pontos.append(float(dif.mean()))
        calendario=pd.DatetimeIndex(b['origens'])
        n=pd.Series(1,index=calendario).resample('D').sum().to_numpy()
        soma=np.stack([pd.Series(d,index=calendario).resample('D').sum().to_numpy() for d in dif])
        diarios.append((soma,n))
    intervalos={};condicionais={}
    for largura in cfg['dias']:
        g=np.random.default_rng(cfg['seed']+largura);amostras=[];fixas=[]
        for _ in range(cfg['replicas']):
            seeds=g.integers(0,ns,size=ns);valores=[];sem_seeds=[]
            for soma,n in diarios:
                ini=g.integers(0,len(n),size=math.ceil(len(n)/largura))
                ix=((ini[:,None]+np.arange(largura))%len(n)).ravel()[:len(n)]
                total=n[ix].sum()
                if total==0:raise ValueError('Réplica vazia.')
                valores.append(float(soma[seeds][:,ix].sum()/(ns*total)))
                sem_seeds.append(float(soma[:,ix].sum()/(ns*total)))
            amostras.append(float(np.mean(valores)));fixas.append(float(np.mean(sem_seeds)))
        intervalos[str(largura)]=np.quantile(amostras,[.025,.975]).tolist()
        condicionais[str(largura)]=np.quantile(fixas,[.025,.975]).tolist()
    return {'diferenca_mse_huber_menos_mse':float(np.mean(pontos)),'por_bloco':dict(zip(blocos,pontos)),
        'ic95_seeds_e_tempo':intervalos,'ic95_tempo_condicional':condicionais,'principal_dias':cfg['principal'],
        'replicas':cfg['replicas'],'metodo':'Blocos fixos com peso igual; seeds pareadas compartilhadas entre blocos e dias circulares dentro de cada bloco; sem atravessar fronteiras.',
        'limites':'Condicional a quatro períodos e ajustes existentes; não elimina seleção adaptativa ou garante vantagem futura.'}
