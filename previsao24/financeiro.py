"""Compra diária Spot: decisão causal, saída temporal fixa e risco auditável."""
import numpy as np
import pandas as pd

def simular(previsoes,minutos,primeiro_minuto,fim_bloco,parametros,controle=False,agravado=False):
    f=parametros['taxa_agravada'] if agravado else parametros['taxa']
    s=parametros['slippage_agravado'] if agravado else parametros['slippage']
    f0,s0=parametros['taxa'],parametros['slippage']
    limiar=np.log((1+s0)*(1+f0)/((1-s0)*(1-f0)))
    capital=float(parametros['capital'])
    pico=capital
    drawdown=0.0
    risco_auditavel=True
    custos=0.0
    operacoes=[]
    curva=[]
    n_entradas=0
    minutos_expostos=0
    fim_minuto=int(pd.Timestamp(fim_bloco,tz='UTC').timestamp()//60)
    anteriores=-1
    for r in previsoes.itertuples(index=False):
        t=pd.Timestamp(r.origem_utc)
        if t.hour!=parametros['hora_utc'] or t.minute!=0:
            continue
        entrada=int(t.timestamp()//60)+parametros['latencia_minutos']
        saida=entrada+1440
        if saida>=fim_minuto:
            continue
        if entrada<anteriores:
            raise ValueError('Operações sobrepostas.')
        sinal=bool(controle or r.previsao>limiar)
        if not sinal:
            curva.append({'tempo_utc':t.isoformat(),'capital':capital})
            continue
        anteriores=saida
        n_entradas+=1
        minutos_expostos+=1440
        e,v=entrada-primeiro_minuto,saida-primeiro_minuto
        registro={'origem_utc':t.isoformat(),'entrada_minuto':entrada,'saida_minuto':saida,'previsao':float(r.previsao)}
        valido=(0<=e<v<len(minutos) and np.isfinite(minutos[[e,v],0]).all() and (minutos[[e,v],5]>0).all())
        if capital is None or not valido:
            registro.update(status='nao_auditavel',capital_entrada=capital,capital_saida=None,
                            motivo='preco_execucao_ausente_ou_sem_negocios' if not valido else 'capital_anterior_desconhecido')
            capital=None
            risco_auditavel=False
        else:
            a,b=float(minutos[e,0]),float(minutos[v,0])
            quantidade=capital/(a*(1+s)*(1+f))
            novo=quantidade*b*(1-s)*(1-f)
            custo=quantidade*a*((1+s)*(1+f)-1)+quantidade*b*(1-(1-s)*(1-f))
            custos+=custo
            caminho=minutos[e:v,3]
            if not np.isfinite(caminho).all():
                risco_auditavel=False
            else:
                marcas=np.r_[capital,quantidade*caminho*(1-s)*(1-f),novo]
                picos=np.maximum.accumulate(np.r_[pico,marcas])[1:]
                drawdown=max(drawdown,float(np.max(1-marcas/picos)))
                pico=max(pico,float(marcas.max()))
            registro.update(status='pontas_observadas',capital_entrada=capital,capital_saida=novo,quantidade=quantidade,
                            preco_entrada=a,preco_saida=b,custos=custo,retorno_liquido=novo/capital-1,
                            percurso_observavel=bool(np.isfinite(caminho).all()))
            capital=novo
        operacoes.append(registro)
        curva.append({'tempo_utc':pd.to_datetime(saida,unit='m',utc=True).isoformat(),'capital':capital})
    resumo={'capital_inicial':parametros['capital'],'capital_final':capital,
            'retorno_liquido':capital/parametros['capital']-1 if capital is not None else None,
            'drawdown':drawdown if risco_auditavel else None,'retorno_auditavel':capital is not None,
            'risco_auditavel':risco_auditavel,'entradas_planejadas':n_entradas,'minutos_expostos_planejados':minutos_expostos,
            'custos_observados':custos,'cenario':'agravado_sinais_base' if agravado else 'base','controle':controle}
    return resumo,operacoes,curva
