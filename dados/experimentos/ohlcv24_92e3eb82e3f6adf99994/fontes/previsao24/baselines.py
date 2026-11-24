"""ARIMA terminal em espaço de estados e persistência explícita."""
import time
import warnings
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from .arquivos import agora, salvar_json
from .metricas import calcular

def projecao_filtrada(resultado, horizonte=24):
    """E[y_(t+h)|y_<=t], sem usar estados suavizados ou valores futuros."""
    sistema=resultado.model.ssm
    z=np.asarray(sistema['design'])
    transicao=np.asarray(sistema['transition'])
    if z.ndim!=2 or transicao.ndim!=2 or np.any(sistema['obs_intercept']) or np.any(sistema['state_intercept']):
        raise ValueError('Contrato exige sistema constante sem interceptos.')
    return (z @ np.linalg.matrix_power(transicao,horizonte) @ resultado.filter_results.filtered_state).reshape(-1)

def prever_arima(log_precos, ordem, parametros, base):
    valores=(np.asarray(log_precos)-base)*100.0
    filtrado=ARIMA(valores,order=tuple(ordem),trend='n',enforce_stationarity=True,enforce_invertibility=True).filter(parametros)
    previsao=projecao_filtrada(filtrado)/100+base-np.asarray(log_precos)
    if tuple(ordem)==(0,1,0):
        # Identidade analítica: evitar que cancelamento numérico invente um sinal.
        previsao=np.where(np.isfinite(log_precos),0.0,np.nan)
    return previsao,filtrado

def ajustar(horas,blocos,configuracao,destino):
    destino.mkdir(parents=True,exist_ok=True)
    log_precos=np.log(horas['close'].to_numpy(np.float64))
    base=float(log_precos[np.flatnonzero(np.isfinite(log_precos))[0]])
    ultimo=int(blocos['treino']['indice_hora'].max())+24
    fim_validacao=int(blocos['validacao']['indice_hora'].max())
    iv=blocos['validacao']['indice_hora'].to_numpy(np.int64)
    candidatos=[]
    salvar_json(destino/'candidatos.json',{'status':'em_andamento','inicio_utc':agora(),'candidatos':[]})
    for ordem in configuracao['arima']['ordens']:
        registro={'ordem':ordem,'inicio_utc':agora(),'fim_ajuste_indice':ultimo}
        inicio=time.perf_counter()
        try:
            with warnings.catch_warnings(record=True) as avisos:
                warnings.simplefilter('always')
                ajuste=ARIMA((log_precos[:ultimo+1]-base)*100,order=tuple(ordem),trend='n',
                              enforce_stationarity=True,enforce_invertibility=True).fit(method_kwargs={'maxiter':configuracao['arima']['maxiter']})
            registro['avisos']=[str(a.message) for a in avisos]
            if not ajuste.mle_retvals.get('converged',False) or not np.isfinite(ajuste.params).all():
                raise ValueError('Candidato não convergiu ou tem parâmetros inválidos.')
            p,_=prever_arima(log_precos[:fim_validacao+1],ordem,ajuste.params,base)
            metricas=calcular(blocos['validacao']['alvo'],p[iv])
            registro.update(status='valido',parametros=ajuste.params.tolist(),nomes_parametros=ajuste.param_names,validacao=metricas)
        except Exception as erro:
            registro.update(status='falha',erro=f'{type(erro).__name__}: {erro}')
        registro.update(segundos=time.perf_counter()-inicio,fim_utc=agora())
        candidatos.append(registro)
        salvar_json(destino/'candidatos.json',{'status':'em_andamento','candidatos':candidatos})
        print(f"ARIMA {ordem}: {registro['status']} mse={registro.get('validacao',{}).get('mse')}",flush=True)
    validos=[r for r in candidatos if r['status']=='valido']
    if not validos:
        raise RuntimeError('Nenhum ARIMA válido. Preservar tentativas e bloquear célula.')
    melhor=min(validos,key=lambda r:(r['validacao']['mse'],sum(r['ordem'][::2]),r['ordem'][0],r['ordem'][2]))
    salvar_json(destino/'selecao.json',{'ordem':melhor['ordem'],'parametros':melhor['parametros'],'base_log_preco':base,
                                    'fim_ajuste_indice':ultimo,'mse_validacao':melhor['validacao']['mse'],'selecao_utc':agora()})
    # Só agora projetar o teste. O filtro incorpora cada observação no seu tempo.
    fim=max(int(q['indice_hora'].max()) for q in blocos.values())
    previsto,filtrado=prever_arima(log_precos[:fim+1],melhor['ordem'],melhor['parametros'],base)
    # Conferência contra previsão oficial em prefixos sem acesso ao futuro.
    indices=blocos['teste']['indice_hora'].to_numpy(np.int64)
    diferencas=[]
    for i in indices[np.linspace(0,len(indices)-1,7,dtype=int)]:
        prefixo=ARIMA((log_precos[:i+1]-base)*100,order=tuple(melhor['ordem']),trend='n').filter(melhor['parametros'])
        referencia=float(np.asarray(prefixo.get_forecast(24).predicted_mean)[-1])/100+base-log_precos[i]
        diferencas.append(abs(referencia-previsto[i]))
    if max(diferencas)>1e-10:
        raise ValueError('Projeção ARIMA divergiu do get_forecast em prefixos causais.')
    resultado={'modelo':'arima','ordem':melhor['ordem'],'candidatos_validos':len(validos),'candidatos_falhos':len(candidatos)-len(validos),
               'conferencia_prefixos_max':max(diferencas),'metricas':{},'segundos':sum(r['segundos'] for r in candidatos)}
    for nome,q in blocos.items():
        if nome=='treino':
            continue
        saida=q[['origem_utc','destino_utc','indice_hora','close','preco_destino','alvo']].copy()
        saida['previsao']=previsto[q['indice_hora'].to_numpy(np.int64)]
        saida.to_parquet(destino/f'previsoes_{nome}.parquet',index=False)
        if nome!='operacional':
            resultado['metricas'][nome]=calcular(saida['alvo'],saida['previsao'])
    salvar_json(destino/'candidatos.json',{'status':'concluido','candidatos':candidatos})
    salvar_json(destino/'resultado.json',resultado)
    return resultado
