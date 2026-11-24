"""Futuros lineares: sinal diário causal, fechamento obrigatório após24h.

Sem modelo, alvo ou seleção de parâmetros. Não certifica liquidação da Binance.
"""
import math
import numpy as np


def decidir(previsao,ultimo_close,limiar):
    if not math.isfinite(previsao) or not math.isfinite(ultimo_close) or ultimo_close<=0:
        raise ValueError('Sinal inválido.')
    if previsao<=0:return 0
    r=previsao/ultimo_close-1
    return (1 if r>0 else -1) if abs(r)>limiar else 0


def arredondar_preco(preco,lado,tick):
    return (math.ceil(preco/tick) if lado>0 else math.floor(preco/tick))*tick


def simular(origens,previsoes,ultimo_close,mercado,regras,cenario,forcar_lado=None):
    origens=np.asarray(origens,dtype=np.int64);previsoes=np.asarray(previsoes);ultimo_close=np.asarray(ultimo_close)
    assert len(origens)==len(previsoes)==len(ultimo_close) and np.all(np.diff(origens)==86400000)
    t=mercado['tempo'];neg=mercado['negocio'];mark=mercado['marca'];ft=mercado['funding_tempo']
    taxa=mercado['funding_taxa'];fp=mercado['funding_preco']
    caixa=regras['capital_inicial'];pico=caixa;dd=0.;operacoes=[];saldos=[caixa];envelope=[caixa];tempos=[int(origens[0])]
    fee=regras['comissao_por_lado'];slip=regras['slippage_por_lado']*cenario['slippage_multiplicador']
    for ts,p,c in zip(origens,previsoes,ultimo_close):
        lado=decidir(float(p),float(c),regras['filtro_retorno_absoluto']) if forcar_lado is None else forcar_lado
        if cenario['lado'] and lado!=cenario['lado']:lado=0
        entrada=int(ts+regras['latencia_minutos']*60000);saida=entrada+regras['prazo_horas']*3600000
        a=int(np.searchsorted(t,entrada));b=int(np.searchsorted(t,saida))
        if b>=len(t) or t[a]!=entrada or t[b]!=saida:raise ValueError('Execução fora da cobertura.')
        if lado:
            pe=arredondar_preco(neg[a,0]*(1+lado*slip),lado,regras['tick_preco'])
            ps=arredondar_preco(neg[b,0]*(1-lado*slip),-lado,regras['tick_preco'])
            q=math.floor(caixa*regras['fracao_nocional']/pe/regras['passo_quantidade'])*regras['passo_quantidade']
            if q*pe<regras['nocional_minimo']:lado=0
        if lado:
            antes=caixa;fids=np.flatnonzero((ft>=entrada)&(ft<saida))
            valores=-lado*q*fp[fids]*taxa[fids]
            incrementos=np.zeros(b-a)
            np.add.at(incrementos,((ft[fids]-entrada)//60000).astype(int),valores)
            financiamento=np.cumsum(incrementos)
            custos_entrada=fee*q*pe;custos_saida=fee*q*ps
            credito=caixa-custos_entrada+financiamento
            alto=mark[a:b,1] if lado>0 else mark[a:b,2]
            baixo=mark[a:b,2] if lado>0 else mark[a:b,1]
            eqmax=credito+lado*q*(alto-pe);eqmin=credito+lado*q*(baixo-pe)
            # Envelope high/low conservador: não presume caminho intraminuto conhecido.
            picos=np.maximum.accumulate(np.r_[pico,eqmax])[1:]
            dd=max(dd,float(np.max(1-eqmin/picos)));pico=float(picos[-1])
            margem=eqmin-q*mark[a:b,1]*fee
            if (margem<=q*mark[a:b,1]*regras['buffer_prudencial']).any():
                raise ValueError('Violação prudencial; não fingir permanência até24h ou liquidar por regra inventada.')
            bruto=lado*q*(ps-pe);funding=float(math.fsum(valores));caixa+=bruto+funding-custos_entrada-custos_saida
            pico=max(pico,caixa);dd=max(dd,1-caixa/pico)
            env=np.column_stack([eqmax,eqmin]).ravel()
            envelope.extend(env.tolist());tempos.extend(np.repeat(t[a:b],2).tolist())
            operacoes.append({'origem_ms':int(ts),'entrada_ms':entrada,'saida_ms':saida,'lado':lado,'quantidade':q,
                 'preco_entrada':pe,'preco_saida':ps,'caixa_antes':antes,'caixa_depois':caixa,'pnl_bruto':bruto,
                 'comissao':custos_entrada+custos_saida,'funding':funding,'pnl_liquido':caixa-antes,
                 'eventos_funding':[{'tempo_ms':int(ft[i]),'taxa':float(taxa[i]),'preco':float(fp[i])} for i in fids]})
        envelope.append(caixa);tempos.append(saida);saldos.append(caixa)
    saldos=np.array(saldos);env=np.array(envelope);dd_recalculado=float(np.max(1-env/np.maximum.accumulate(env)))
    np.testing.assert_allclose(dd,dd_recalculado,atol=1e-12)
    log=np.diff(np.log(saldos));pnl=np.array([o['pnl_liquido'] for o in operacoes])
    ganhos=float(pnl[pnl>0].sum());perdas=float(-pnl[pnl<0].sum());g=float(log.mean())
    m={'capital_final':caixa,'retorno_liquido':caixa/regras['capital_inicial']-1,'drawdown_maximo':dd,
       'crescimento_log_diario':g,'retorno_anualizado':float(np.expm1(g*365)),
       'calmar':float(np.expm1(g*365)/dd) if dd else None,
       'sharpe_diario_rf_zero':float(log.mean()/log.std(ddof=1)*np.sqrt(365)) if len(log)>1 and log.std(ddof=1)>0 else None,
       'operacoes':len(operacoes),'compras':sum(o['lado']==1 for o in operacoes),'vendas':sum(o['lado']==-1 for o in operacoes),
       'taxa_acerto_liquido':float((pnl>0).mean()) if len(pnl) else None,'profit_factor':ganhos/perdas if perdas else None,
       'comissoes':sum(o['comissao'] for o in operacoes),'funding':sum(o['funding'] for o in operacoes),
       'pnl_compras':sum(o['pnl_liquido'] for o in operacoes if o['lado']==1),'pnl_vendas':sum(o['pnl_liquido'] for o in operacoes if o['lado']==-1),
       'fracao_dias_posicionado':len(operacoes)/len(origens),'previsoes_nao_positivas':int((previsoes<=0).sum())}
    return {'metricas':m,'operacoes':operacoes}, {'saldos_diarios':saldos,'patrimonio_envelope':env,'tempo_envelope':np.array(tempos,dtype=np.int64)}


def conferir(resultado,curvas,regras):
    """Ledger independente de preços de preenchimento já realizados, sem re-simular."""
    caixa=regras['capital_inicial']
    for o in resultado['operacoes']:
        assert o['saida_ms']-o['entrada_ms']==86400000
        q=o['quantidade'];lado=o['lado'];pe=o['preco_entrada'];ps=o['preco_saida']
        funding=-lado*q*math.fsum(e['taxa']*e['preco'] for e in o['eventos_funding'])
        comissao=q*(pe+ps)*regras['comissao_por_lado']
        liquido=lado*q*(ps-pe)+funding-comissao
        np.testing.assert_allclose([caixa,liquido,funding,comissao],[o['caixa_antes'],o['pnl_liquido'],o['funding'],o['comissao']],atol=1e-7,rtol=0)
        caixa+=liquido
        np.testing.assert_allclose(caixa,o['caixa_depois'],atol=1e-7,rtol=0)
    np.testing.assert_allclose(caixa,resultado['metricas']['capital_final'],atol=1e-7,rtol=0)
    env=curvas['patrimonio_envelope']
    np.testing.assert_allclose(np.max(1-env/np.maximum.accumulate(env)),resultado['metricas']['drawdown_maximo'],atol=1e-12)
    np.testing.assert_allclose(curvas['saldos_diarios'][-1],caixa,atol=1e-7,rtol=0)
    return True
