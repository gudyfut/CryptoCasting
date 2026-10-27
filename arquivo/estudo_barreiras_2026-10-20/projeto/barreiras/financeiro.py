"""Contabilidade de uma posição comprada; incompletude futura nunca decide entradas."""
from __future__ import annotations

import numpy as np
import pandas as pd


def retorno_limite(distancia, superior=True, taxa=.001, slippage=.0005):
    return np.exp(distancia if superior else -distancia)*(1-slippage)*(1-taxa)/((1+slippage)*(1+taxa))-1


def simular(previsoes, minutos, primeiro_minuto, inicio, fim, *, filtro=True,
            agravado=False, superior_ambiguo=False, capital=10000.):
    inicio_min=int(pd.Timestamp(inicio).timestamp()//60)
    fim_min=int(pd.Timestamp(fim).timestamp()//60)
    origem_dataset=int(primeiro_minuto)
    inicio_i=inicio_min-origem_dataset
    fim_i=fim_min-origem_dataset
    if inicio_i<0 or fim_i>len(minutos) or inicio_i>=fim_i:
        raise ValueError('Período econômico fora dos dados.')
    taxa,slip=(.002,.001) if agravado else (.001,.0005)
    curva=np.full(fim_i-inicio_i,capital,np.float64)
    pior=curva.copy()
    exposicao=np.zeros(len(curva),bool)
    patrimonio=capital
    livre_desde=-1
    ordens=[]
    invalidacao=None
    for r in previsoes.itertuples(index=False):
        e=int(r.entrada_indice)
        origem=e-1
        if origem<=livre_desde or e<int(inicio_i) or e+int(r.horizonte)*60>=fim_i:
            continue
        d=float(r.distancia)
        ru,rl=retorno_limite(d),retorno_limite(d,False)
        if filtro and (r.p2<.6 or r.p2*ru+(1-r.p2)*rl<=0):
            continue
        # Rótulos/saídas só são consultados depois de a decisão causal ser tomada.
        if r.classe<0:
            invalidacao={'origem_utc':r.origem_utc.isoformat(),'motivo':int(r.motivo_nao_observado),
                         'mensagem':'Entrada selecionada; percurso/preço de execução não observável.'}
            curva[e-inicio_i:]=np.nan
            pior[e-inicio_i:]=np.nan
            break
        saida=int(r.saida_indice)
        conhecido=int(r.saida_conhecida_indice)
        if saida<e or saida>=fim_i:
            raise ValueError('Saída fora dos limites da operação.')
        a=float(r.preco_entrada)
        b=float(r.preco_saida)
        classe=int(r.classe)
        if r.ambiguo and superior_ambiguo:
            b=a*np.exp(d);classe=2
        fracao=min(1.,.01/-rl)
        desembolso=patrimonio*fracao
        quantidade=desembolso/(a*(1+slip)*(1+taxa))
        caixa=patrimonio-desembolso
        recebimento=quantidade*b*(1-slip)*(1-taxa)
        antes=patrimonio
        patrimonio=caixa+recebimento
        if saida>e:
            precos=minutos[e:saida,3]
            baixos=minutos[e:saida,2]
            if not np.isfinite(precos).all() or not np.isfinite(baixos).all():
                raise ValueError('Rotulagem inconsistente: posição atravessou lacuna.')
            curva[e-inicio_i:saida-inicio_i]=caixa+quantidade*precos*(1-slip)*(1-taxa)
            pior[e-inicio_i:saida-inicio_i]=caixa+quantidade*baixos*(1-slip)*(1-taxa)
        curva[saida-inicio_i:]=patrimonio
        pior[saida-inicio_i:]=patrimonio
        exposicao[e-inicio_i:max(e+1,conhecido)-inicio_i]=True
        livre_desde=conhecido
        taxas=quantidade*a*(1+slip)*taxa+quantidade*b*(1-slip)*taxa
        escorregamento=quantidade*(a+b)*slip
        ordens.append({'origem_utc':r.origem_utc,'entrada_utc':r.entrada_utc,'saida_utc':r.saida_utc,
             'saida_conhecida_indice':conhecido,'classe':classe,'ambiguo':bool(r.ambiguo),
             'preco_entrada':a,'preco_saida':b,'quantidade':quantidade,'fracao':fracao,
             'capital_antes':antes,'capital_depois':patrimonio,'lucro':patrimonio-antes,
             'taxas':taxas,'slippage':escorregamento,'duracao_minutos':conhecido-e,
             'p_superior':float(r.p2)})
    transacoes=pd.DataFrame(ordens)
    quadro=pd.DataFrame({'minuto_utc':np.arange(inicio_min,fim_min),'patrimonio':curva,
                        'pior_marca_observavel':pior,'exposto':exposicao})
    if invalidacao:
        return {'status':'nao_auditavel','invalidacao':invalidacao,'operacoes_antes_lacuna':len(ordens),
                'retorno_liquido':None,'drawdown_maximo':None},transacoes,quadro
    picos=np.maximum.accumulate(np.r_[capital,curva])[1:]
    perdas=np.array([r['lucro'] for r in ordens])
    ganhos=float(perdas[perdas>0].sum())
    prejuizos=float(-perdas[perdas<0].sum())
    resumo={'status':'auditavel','capital_inicial':capital,'capital_final':patrimonio,
            'retorno_liquido':patrimonio/capital-1,'drawdown_maximo':float((1-curva/picos).max()),
            'pior_marca_vs_pico_fechamento':float((1-pior/picos).max()),
            'operacoes':len(ordens),'origens':len(previsoes),
            'proporcao_origens_operadas':len(ordens)/len(previsoes) if len(previsoes) else 0.,
            'tempo_exposto':float(exposicao.mean()),'taxas':sum(r['taxas'] for r in ordens),
            'slippage':sum(r['slippage'] for r in ordens),
            'taxa_acerto_financeiro':float((perdas>0).mean()) if len(perdas) else None,
            'ganho_medio':float(perdas[perdas>0].mean()) if ganhos else None,
            'perda_media':float(perdas[perdas<0].mean()) if prejuizos else None,
            'profit_factor':ganhos/prejuizos if prejuizos else None,
            'duracao_media_minutos':float(np.mean([r['duracao_minutos'] for r in ordens])) if ordens else None,
            'saidas_por_classe':[sum(r['classe']==k for r in ordens) for k in range(3)]}
    return resumo,transacoes,quadro


def comprar_manter(previsoes,minutos,primeiro_minuto,inicio,fim,capital=10000.):
    if not len(previsoes):
        return {'status':'sem_origem','retorno_liquido':None}
    e=int(previsoes['entrada_indice'].iloc[0])
    v=int(pd.Timestamp(fim).timestamp()//60)-primeiro_minuto-1
    if not np.isfinite(minutos[e:v+1,:4]).all() or minutos[e,5]<=0 or minutos[v,5]<=0:
        return {'status':'nao_auditavel','retorno_liquido':None,'motivo':'Lacuna ou execução não observável durante buy-and-hold.'}
    a,b=minutos[e,0],minutos[v,0]
    q=capital/(a*1.0005*1.001)
    curva=q*minutos[e:v+1,3]*.9995*.999
    curva[-1]=q*b*.9995*.999
    picos=np.maximum.accumulate(np.r_[capital,curva])[1:]
    return {'status':'auditavel','retorno_liquido':float(curva[-1]/capital-1),
            'drawdown_maximo':float((1-curva/picos).max()),'capital_final':float(curva[-1])}
