"""Diagnósticos descritivos: não selecionam checkpoint, política ou exemplos."""
import numpy as np
import pandas as pd


def correlacao(a,b,postos=False):
    a=np.asarray(a,float);b=np.asarray(b,float)
    if len(a)<2 or len(np.unique(a))<2 or len(np.unique(b))<2:return None
    if postos:
        a=pd.Series(a).rank(method='average').to_numpy();b=pd.Series(b).rank(method='average').to_numpy()
    return float(np.corrcoef(a,b)[0,1])


def resumir(q,referencia):
    if not q.indice_candle.equals(referencia.indice_candle):raise ValueError('Origens não pareadas.')
    y=q.alvo.to_numpy(float);p=q.previsao.to_numpy(float);z=referencia.previsao.to_numpy(float)
    if not np.array_equal(y,referencia.alvo.to_numpy(float)):raise ValueError('Alvos não pareados.')
    if not (np.isfinite(y).all() and np.isfinite(p).all() and np.isfinite(z).all()):raise ValueError('Dados não finitos.')
    erro=np.abs(p-y);eb=np.abs(z-y);base=float(np.mean(eb**2))
    return {'n':len(q),'mse':float(np.mean(erro**2)),'mae':float(erro.mean()),
            'mediana_erro_absoluto':float(np.median(erro)),'p95_erro_absoluto':float(np.quantile(erro,.95)),
            'habilidade_mse':1-float(np.mean(erro**2))/base if base>0 else None,
            'vitorias_referencia':float(np.mean(erro<eb)),'empates_referencia':float(np.mean(erro==eb)),
            'derrotas_referencia':float(np.mean(erro>eb)),'vies':float(np.mean(p-y)),
            'pearson':correlacao(p,y),'spearman':correlacao(p,y,True),
            'desvio_previsao':float(p.std()),'desvio_alvo':float(y.std()),'previsoes_distintas':len(np.unique(p))}


def faixas_validacao(validacao,avaliacao):
    v=validacao.previsao.to_numpy(float);p=avaliacao.previsao.to_numpy(float)
    if len(np.unique(v))==1:
        cortes=np.array([],dtype=float)
    else:cortes=np.unique(np.quantile(v,[.2,.4,.6,.8]))
    grupos=np.searchsorted(cortes,p,side='left');linhas=[]
    for i in range(len(cortes)+1):
        q=avaliacao.loc[grupos==i]
        linhas.append({'faixa':i+1,'limite_inferior':float(cortes[i-1]) if i else None,
                       'limite_superior':float(cortes[i]) if i<len(cortes) else None,
                       'n':len(q),'previsao_media':float(q.previsao.mean()) if len(q) else None,
                       'retorno_observado_medio':float(q.alvo.mean()) if len(q) else None})
    return {'cortes_derivados_somente_validacao':cortes.tolist(),'faixas':linhas,
            'natureza':'diagnóstico retrospectivo, sem limiar operacional ou seleção pelo teste'}


def analisar(q,validacao,naive):
    todos=resumir(q,naive)
    diario=pd.DatetimeIndex(q.origem_utc).hour==0;dv=pd.DatetimeIndex(validacao.origem_utc).hour==0
    labels=pd.DatetimeIndex(q.origem_utc).strftime('%Y').astype(str)+'Q'+pd.DatetimeIndex(q.origem_utc).quarter.astype(str)
    partes={}
    for label in sorted(set(labels)):
        sel=np.asarray(labels==label);partes[label]=resumir(q.loc[sel].reset_index(drop=True),naive.loc[sel].reset_index(drop=True))
    return {'todas_origens':todos,'origens00utc':resumir(q.loc[diario].reset_index(drop=True),naive.loc[diario].reset_index(drop=True)),
            'trimestres':partes,'faixas00utc':faixas_validacao(validacao.loc[dv],q.loc[diario])}
