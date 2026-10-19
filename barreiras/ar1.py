"""AR(1) horário com difusão intrahora explicitada no protocolo."""
from __future__ import annotations

import hashlib
import time

import numpy as np
import torch

from .arquivos import salvar_json


def ajustar(horas,ultima_origem):
    r=horas.loc[horas['origem_utc']<=ultima_origem,'retorno'].to_numpy(np.float64)
    x,y=r[:-1],r[1:]
    validos=np.isfinite(x)&np.isfinite(y)
    x,y=x[validos],y[validos]
    matriz=np.column_stack([np.ones(len(x)),x])
    if len(x)<3 or np.linalg.matrix_rank(matriz)!=2:
        raise ValueError('AR(1): ajuste singular ou insuficiente.')
    c,phi=np.linalg.lstsq(matriz,y,rcond=None)[0]
    variancia=float(np.square(y-matriz@np.array([c,phi])).sum()/(len(y)-2))
    if abs(phi)>=1 or not np.isfinite(variancia) or variancia<=0:
        raise ValueError('AR(1): parâmetros fora do contrato; não truncar coeficiente.')
    return {'intercepto':float(c),'phi':float(phi),'sigma_residual':float(np.sqrt(variancia)),
            'n':len(x),'ultima_origem_ajuste':ultima_origem.isoformat()}


def semente_origem(par,fold,origem,semente=20261018,banco=0):
    texto=f'{semente}|{par}|{fold}|{origem}|{banco}'
    return int(hashlib.sha256(texto.encode()).hexdigest()[:15],16)


@torch.inference_mode()
def probabilidades(ajuste,retorno_anterior,sigma,horizontes,semente,*,trajetorias=4096,dispositivo='cuda'):
    if trajetorias%4096:
        raise ValueError('Monte Carlo usa bancos de 4096 trajetórias para aninhamento exato.')
    # Cada banco tem tamanho fixo e seed própria: aumentar o orçamento preserva
    # as primeiras trajetórias. Os sorteios por hora preservam prefixos entre H.
    contagens=np.zeros((len(horizontes),3),np.int64)
    for banco in range(trajetorias//4096):
        gerador=torch.Generator(device=dispositivo).manual_seed(semente+banco)
        anterior=torch.full((4096,),float(retorno_anterior),device=dispositivo,dtype=torch.float64)
        nivel=torch.zeros_like(anterior)
        passos=torch.arange(1,61,device=dispositivo,dtype=torch.float64).unsqueeze(1)/60
        classes=torch.full((len(horizontes),4096),1,device=dispositivo,dtype=torch.int64)
        ativos=torch.ones_like(classes,dtype=torch.bool)
        entrada=None
        for hora in range(max(horizontes)+1):
            ruido=torch.randn((60,4096),generator=gerador,device=dispositivo,dtype=torch.float64)
            ruido*=ajuste['sigma_residual']/np.sqrt(60)
            media=ajuste['intercepto']+ajuste['phi']*anterior
            retorno=ruido.cumsum(dim=0)+passos*media.unsqueeze(0)
            precos=nivel.unsqueeze(0)+retorno
            if entrada is None:
                entrada=precos[0].clone()
            relativo=precos-entrada.unsqueeze(0)
            for k,h in enumerate(horizontes):
                quantidade=min(60,h*60+1-hora*60)
                if quantidade<=0:
                    continue
                d=sigma*np.sqrt(h)
                acima=relativo[:quantidade]>=d
                abaixo=relativo[:quantidade]<=-d
                iu=torch.where(acima.any(dim=0),acima.to(torch.int64).argmax(dim=0),61)
                il=torch.where(abaixo.any(dim=0),abaixo.to(torch.int64).argmax(dim=0),61)
                superior=(iu<il)&ativos[k]
                inferior=(il<=iu)&(il<61)&ativos[k]
                classes[k,superior]=2
                classes[k,inferior]=0
                ativos[k]&=~(superior|inferior)
            anterior=retorno[-1]
            nivel=precos[-1]
        for k in range(len(horizontes)):
            contagens[k]+=torch.bincount(classes[k],minlength=3).cpu().numpy()
    return (contagens+.5)/(trajetorias+1.5)


def prever_quadro(ajuste,horas,quadro,celula,destino,dispositivo='cuda'):
    resultados=[]
    inicio=time.perf_counter()
    for i,r in enumerate(quadro.itertuples(index=False)):
        retorno=float(horas.loc[int(r.indice_hora),'retorno'])
        seed=semente_origem(celula['par'],celula['fold'],r.origem_utc.isoformat())
        p=probabilidades(ajuste,retorno,float(r.sigma),[celula['horizonte']],seed,dispositivo=dispositivo)[0]
        resultados.append(p)
        if (i+1)%100==0:
            salvar_json(destino/'progresso_ar1.json',{'origens_concluidas':i+1,'total':len(quadro),'segundos':time.perf_counter()-inicio})
            print(f'AR(1) {celula["par"]}/{celula["fold"]}/H{celula["horizonte"]}: {i+1}/{len(quadro)}',flush=True)
    return np.asarray(resultados)
