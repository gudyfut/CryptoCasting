"""Referência diária ARIMA(p,1,q), log-preço, parâmetros fixos do treino.

Grade p/q0..2 sem deriva herdada como especificação, nunca seus parâmetros
horários. Validação escolhe por MSE de retorno simples. Filtragem é causal.
"""
from dataclasses import asdict
import json
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from modelos.arima import criar_sistema,prever_arima,ParametrosARIMA
from modelos.contratos import HistoricoARIMA
from treinamento.selecao import escolher_arima


def salvar(p,obj):Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def historico(logs,indices,base,ultimo_treino,identidade):
    return HistoricoARIMA(identidade,np.asarray(logs,float),np.asarray(indices,dtype=np.int64),1,float(base),int(ultimo_treino))


def conferir_direto(h,p,previsoes):
    """API de previsão de um passo versus propagação das matrizes do contrato."""
    i=h.indices_origens;v=h.log_precos[:int(i.max())+1]
    filtrado=criar_sistema((v-p.base_log_preco)*100,p.ordem).filter(np.array(p.valores))
    ini=int(i.min())+1;fim=int(i.max())+1
    previsto=np.asarray(filtrado.get_prediction(start=ini,end=fim).predicted_mean)
    r=previsto[i+1-ini]/100+p.base_log_preco-v[i]
    if p.ordem==(0,1,0):r=np.zeros(len(i))
    np.testing.assert_allclose(previsoes,r,atol=1e-11,rtol=1e-9)


def ajustar(diario,cfg,dados,identidade,destino):
    destino=Path(destino);destino.mkdir(exist_ok=False)
    diario=diario.sort_values('open_time');times=diario.open_time.to_numpy(np.int64);closes=diario.close.to_numpy(float)
    assert np.all(np.diff(times)==86400000) and np.isfinite(closes).all() and (closes>0).all()
    ini,fim=[int(pd.Timestamp(s,tz='UTC').timestamp()*1000) for s in cfg['periodos']['treino']]
    treino=np.flatnonzero((times>=ini)&(times<fim));assert treino[0]==0
    logs=np.log(closes);base=float(logs[treino].mean());ultimo=int(treino[-1]);endog=(logs[treino]-base)*100
    indices={}
    for fase,z in dados.items():
        ix=np.searchsorted(times,z['origens_ms'])-1
        assert (ix>=ultimo).all();np.testing.assert_array_equal(times[ix]+86400000,z['origens_ms'])
        np.testing.assert_array_equal(closes[ix],z['ultimo_close']);indices[fase]=ix
    hv=historico(logs,indices['validacao'],base,ultimo,identidade)
    y=dados['validacao']['y']/dados['validacao']['ultimo_close']-1
    candidatos=[]
    def fit(ordem):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always');a=criar_sistema(endog,ordem).fit(method_kwargs={'maxiter':200})
        if not a.mle_retvals.get('converged',False):raise ValueError('ARIMA não convergiu')
        par=ParametrosARIMA(identidade,tuple(ordem),tuple(float(x) for x in a.params),tuple(a.param_names),base,ultimo)
        return par,[str(q.message) for q in w]
    for ar in range(3):
        for ma in range(3):
            ordem=[ar,1,ma];r={'ordem':ordem,'status':'falhou'}
            try:
                par,avisos=fit(ordem);retlog=prever_arima(hv,par);pre=np.expm1(retlog)
                conferir_direto(hv,par,retlog)
                r.update(status='valido',mse_validacao=float(np.mean((pre-y)**2)),parametros=asdict(par),avisos=avisos)
            except (ValueError,RuntimeError,np.linalg.LinAlgError) as e:r['erro']=repr(e)
            candidatos.append(r);salvar(destino/'candidatos.json',candidatos)
    selecao=escolher_arima(candidatos);salvar(destino/'selecao.json',selecao)
    val=selecao['parametros'];p=ParametrosARIMA(val['identidade'],tuple(val['ordem']),tuple(val['valores']),tuple(val['nomes']),val['base_log_preco'],val['indice_fim_ajuste'])
    repetido,avisos=fit(p.ordem);np.testing.assert_array_equal(p.valores,repetido.valores)
    saidas={};metricas={}
    for fase,z in dados.items():
        h=historico(logs,indices[fase],base,ultimo,identidade);retlog=prever_arima(h,p);conferir_direto(h,p,retlog)
        np.testing.assert_array_equal(retlog,prever_arima(h,repetido))
        primeiro=int(indices[fase][0]);alterado=logs.copy();alterado[primeiro+1:]+=2.
        h0=historico(logs,np.array([primeiro]),base,ultimo,identidade);h1=historico(alterado,np.array([primeiro]),base,ultimo,identidade)
        np.testing.assert_array_equal(prever_arima(h0,p),prever_arima(h1,p))
        retorno=np.expm1(retlog);preco=z['ultimo_close']*(1+retorno);alvo=z['y']/z['ultimo_close']-1
        saidas[fase]=preco;np.savez_compressed(destino/f'{fase}.npz',origens_ms=z['origens_ms'],previsoes=preco,previsoes_retorno=retorno,ultimo_close=z['ultimo_close'],y=z['y'])
        metricas[fase]={'mse_retorno':float(np.mean((retorno-alvo)**2)),'mse_naive_retorno':float(np.mean(alvo**2)),
            'mae_retorno':float(np.mean(np.abs(retorno-alvo))),'fracao_sinais_acima_filtro':float(np.mean(np.abs(retorno)>.002))}
    salvar(destino/'controle.json',{'parametros_repetidos_exatos':True,'previsoes_repetidas_exatas':True,'api_previsao_independente_conferida':True,
        'causalidade_por_perturbacao_futura':True,'ajuste_apenas_treino':True,'selecionou_apenas_validacao':True,
        'ajustes_candidatos':9,'controle_adicional':1,'epoca_fim_treino_ms':int(times[ultimo]+86399999),'metricas':metricas})
    return saidas
