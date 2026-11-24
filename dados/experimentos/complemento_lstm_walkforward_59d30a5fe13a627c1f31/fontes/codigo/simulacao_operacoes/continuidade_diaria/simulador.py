"""Perpétuo linear por caixa equivalente; nunca representa saldo disponível.

Patrimônio = caixa equivalente + quantidade assinada * preço.
Uma negociação delta atualiza caixa em -delta*preenchimento-comissão;
funding é caixa. É algebricamente equivalente à contabilidade por preço médio.
"""
import math
from decimal import Decimal, ROUND_FLOOR
import numpy as np
from simulacao_operacoes.diaria_24h import decidir, arredondar_preco


def lotes(valor,passo):
    return int((Decimal(str(valor))/Decimal(str(passo))).to_integral_value(rounding=ROUND_FLOOR))


def simular(t,previsoes,ultimo,m,regras,modo,forcar=None,agenda=None,filtrar_ordens=True):
    assert modo in ('diaria','liquida','agenda')
    assert np.all(np.diff(t)==86400000) and len(t)==len(previsoes)==len(ultimo)
    if modo=='agenda':assert agenda is not None and len(agenda)==len(t)
    capital=regras['capital_inicial'];passo=regras['passo_quantidade'];fee=regras['comissao_por_lado'];slip=regras['slippage_por_lado'];tick=regras['tick_preco']
    caixa=capital;q_lotes=0;pico=capital;dd=0.;patrimonios=[capital];risco=[0.];ordens=[];dias=[];funding=[];rejeicoes=[]
    tempo=m['tempo'];neg=m['negocio'];marca=m['marca'];ft=m['funding_tempo']
    indices=np.searchsorted(tempo,np.r_[t+regras['latencia_minutos']*60000,t[-1]+regras['latencia_minutos']*60000+86400000])
    assert np.all(tempo[indices]==np.r_[t+regras['latencia_minutos']*60000,t[-1]+regras['latencia_minutos']*60000+86400000])
    def executar(delta_lotes,preco,ts,motivo):
        nonlocal caixa,q_lotes
        if not delta_lotes:return
        delta=delta_lotes*passo;preenchimento=arredondar_preco(preco*(1+math.copysign(slip,delta)),int(np.sign(delta)),tick)
        reduzir=q_lotes*delta_lotes<0 and abs(delta_lotes)<=abs(q_lotes)
        if filtrar_ordens:
            if abs(delta)<regras.get('quantidade_minima',passo)-1e-10:
                raise ValueError('Ordem menor que quantidade mínima; conferir grade do instrumento.')
            if abs(delta)>regras.get('quantidade_maxima',float('inf'))+1e-10:
                raise ValueError('Ordem maior que quantidade máxima; não inventar fragmentação.')
            if not reduzir and abs(delta)*preenchimento<regras['nocional_minimo']-1e-10:
                rejeicoes.append({'tempo_ms':int(ts),'delta_lotes':delta_lotes,'nocional':abs(delta)*preenchimento,'motivo':'aumento_abaixo_nocional_minimo'})
                return
        comissao=abs(delta)*preenchimento*fee;antes=caixa
        caixa-=delta*preenchimento+comissao;q_lotes+=delta_lotes
        ordens.append({'tempo_ms':int(ts),'delta_lotes':delta_lotes,'delta':delta,'preco_contrato':preco,'preenchimento':preenchimento,
            'comissao':comissao,'custo_slippage_ticks':delta*(preenchimento-preco),'caixa_antes':antes,'caixa_depois':caixa,
            'quantidade_depois':q_lotes*passo,'motivo':motivo,'reduce_only':reduzir})
    for i,(origem,previsao,u) in enumerate(zip(t,previsoes,ultimo)):
        a=int(indices[i]);b=int(indices[i+1]);p=float(neg[a,0]);q_ant=q_lotes*passo
        # Mesmo orçamento conservador de 95%: patrimônio que estaria disponível
        # após zerar a posição ao preço adverso e pagar comissão. Na execução
        # líquida esse custo hipotético serve só para dimensionar, não é debitado.
        if q_lotes:
            fechamento=arredondar_preco(p*(1-math.copysign(slip,q_ant)),-int(np.sign(q_lotes)),tick)
            liquidavel=caixa+q_ant*fechamento-abs(q_ant)*fechamento*fee
        else:liquidavel=caixa
        assert liquidavel>0
        lado=decidir(float(previsao),float(u),regras['filtro_retorno_absoluto']) if forcar is None else forcar
        alvo=0
        if lado:
            pe=arredondar_preco(p*(1+lado*slip),lado,tick)
            # Conserva a regra histórica de lotes no dimensionamento comparável.
            alvo=lado*math.floor(liquidavel*regras['fracao_nocional']/pe/passo)
            if abs(alvo)*passo*pe<regras['nocional_minimo']:alvo=0
        if modo=='agenda':alvo=int(agenda[i]);assert np.sign(alvo)==lado or alvo==0
        if modo=='diaria':executar(-q_lotes,p,tempo[a],'zerar_diario');executar(alvo,p,tempo[a],'abrir_diario')
        elif q_lotes*alvo<0:
            executar(-q_lotes,p,tempo[a],'fechar_inversao');executar(alvo,p,tempo[a],'abrir_inversao')
        else:executar(alvo-q_lotes,p,tempo[a],'ajustar_liquido')
        q=q_lotes*passo
        ids=np.flatnonzero((ft>=tempo[a])&(ft<tempo[b])) if q_lotes else np.array([],dtype=int)
        valores=-q*m['funding_preco'][ids]*m['funding_taxa'][ids];inc=np.zeros(b-a)
        np.add.at(inc,((ft[ids]-tempo[a])//60000).astype(int),valores)
        credito=caixa+np.cumsum(inc)
        if q_lotes:
            eqmax=credito+q*(marca[a:b,1] if q>0 else marca[a:b,2])
            eqmin=credito+q*(marca[a:b,2] if q>0 else marca[a:b,1])
            picos=np.maximum.accumulate(np.r_[pico,eqmax])[1:]
            if np.any(eqmin-abs(q)*marca[a:b,1]*fee<=abs(q)*marca[a:b,1]*regras['buffer_prudencial']):
                raise ValueError('Violação prudencial; não inventar liquidação.')
            dd=max(dd,float(np.max(1-eqmin/picos)));pico=float(picos[-1])
        f=float(math.fsum(valores));caixa+=f
        for h,v in zip(ids,valores):funding.append({'tempo_ms':int(ft[h]),'quantidade':q,'taxa':float(m['funding_taxa'][h]),'preco':float(m['funding_preco'][h]),'valor':float(v)})
        final=float(neg[b,0]);liquidacao=arredondar_preco(final*(1-math.copysign(slip,q)),-int(np.sign(q)),tick) if q_lotes else final
        eq=caixa+q*liquidacao-abs(q)*liquidacao*fee
        pico=max(pico,eq);dd=max(dd,1-eq/pico)
        dias.append({'origem_ms':int(origem),'entrada_ms':int(tempo[a]),'fim_ms':int(tempo[b]),'lado_sinal':int(lado),
            'alvo_lotes':alvo,'quantidade':q,'preco_inicio':p,'preco_fim':final,'funding':f,
            'pnl_movimento_contrato':q*(final-p),'patrimonio_liquidavel_inicio':liquidavel,'patrimonio_liquidavel_fim':eq,
            'patrimonio_marcado_contrato_fim':caixa+q*final})
        patrimonios.append(eq);risco.append(dd)
    executar(-q_lotes,float(neg[indices[-1],0]),tempo[indices[-1]],'fechamento_final')
    np.testing.assert_allclose(caixa,patrimonios[-1],atol=1e-7,rtol=0)
    patrimonio=np.array(patrimonios);logs=np.diff(np.log(patrimonio));g=float(logs.mean());mudancas=np.diff(patrimonio)
    comissoes=sum(o['comissao'] for o in ordens);execucao=sum(o['custo_slippage_ticks'] for o in ordens)
    bruto=sum(d['pnl_movimento_contrato'] for d in dias);fund=sum(e['valor'] for e in funding)
    np.testing.assert_allclose(capital+bruto+fund-comissoes-execucao,caixa,atol=1e-7,rtol=0)
    pos=[d for d in dias if d['quantidade']];blocos=sum(d['quantidade']!=0 and (i==0 or dias[i-1]['quantidade']*d['quantidade']<=0) for i,d in enumerate(dias))
    perdem=float(-mudancas[mudancas<0].sum());ganham=float(mudancas[mudancas>0].sum())
    met={'capital_final':caixa,'retorno_liquido':caixa/capital-1,'drawdown_maximo':dd,'crescimento_log_diario':g,
        'retorno_anualizado':float(np.expm1(g*365)),'sharpe_diario_rf_zero':float(g/logs.std(ddof=1)*np.sqrt(365)) if len(logs)>1 and logs.std(ddof=1)>0 else None,
        'calmar':float(np.expm1(g*365)/dd) if dd else None,'ordens':len(ordens),'dias_posicionado':len(pos),'blocos_posicao':blocos,
        'dias_comprado':sum(d['quantidade']>0 for d in dias),'dias_vendido':sum(d['quantidade']<0 for d in dias),'fracao_tempo_posicionado':len(pos)/len(t),
        'volume_negociado_usdt':sum(abs(o['delta'])*o['preenchimento'] for o in ordens),'comissoes':comissoes,'ajustes_aguardando_minimo':len(rejeicoes),
        'custo_slippage_ticks':execucao,'funding':fund,'pnl_movimento_contrato':bruto,
        'dias_lucrativos_fracao':float(np.mean(mudancas>0)),'profit_factor_diario':ganham/perdem if perdem else None}
    return {'metricas':met,'ordens':ordens,'dias':dias,'funding':funding,'rejeicoes':rejeicoes}, {'saldos_diarios':patrimonio,'drawdown_acumulado':np.array(risco)}
