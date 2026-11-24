"""Experimento isolado: apenas saídas; sem importar modelos ou treinamento."""
import math
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import numpy as np
from simulacao_operacoes.diaria_24h import decidir


def grade(valor, passo, acima):
    x=Decimal(str(valor))/Decimal(str(passo))
    # Decide o inteiro robustamente, mas materializa inteiro*tick/lot em float
    # como o motor original para reproduzir exatamente os preenchimentos.
    return int(x.to_integral_value(rounding=ROUND_CEILING if acima else ROUND_FLOOR))*passo


def saida(m,a,b,lado,entrada,distancia,politica,desempate):
    """Gatilho no contrato; barreiras na grade, simétricas antes do arredondamento.

    Abertura é observada antes dos extremos. Duplo toque sem ordem conhecida:
    SL primeiro no principal e TP primeiro na sensibilidade. TP em gap usa
    barreira conservadora; SL em gap usa abertura adversa. Preenchimento mercado
    aproximado após disparo, com slippage; não garante execução na exchange.
    """
    if politica=='prazo':return b,float(m['negocio'][b,0]),'prazo',False,None,None
    sl=entrada*(1-lado*distancia);tp=entrada*(1+lado*distancia)
    # Arredondamento dos gatilhos: aproximações inferiores/superiores do 1:1.
    tick=m['tick'];sl=grade(sl,tick,lado<0);tp=grade(tp,tick,lado>0)
    x=m['negocio'][a:b]
    toca_sl=x[:,2]<=sl if lado>0 else x[:,1]>=sl
    toca_tp=(x[:,1]>=tp if lado>0 else x[:,2]<=tp) if politica=='stop_take' else np.zeros(len(x),bool)
    ix=np.flatnonzero(toca_sl|toca_tp)
    if not len(ix):return b,float(m['negocio'][b,0]),'prazo',False,sl,tp if politica=='stop_take' else None
    j=int(ix[0]);abertura=float(x[j,0]);gap_sl=abertura<=sl if lado>0 else abertura>=sl
    gap_tp=(abertura>=tp if lado>0 else abertura<=tp) and politica=='stop_take'
    ambiguo=bool(toca_sl[j] and toca_tp[j] and not gap_sl and not gap_tp)
    if gap_sl:motivo='stop';preco=abertura
    elif gap_tp:motivo='take';preco=tp
    elif toca_sl[j] and (not toca_tp[j] or desempate=='stop'):motivo='stop';preco=sl
    else:motivo='take';preco=tp
    return a+j,float(preco),motivo,ambiguo,sl,tp if politica=='stop_take' else None


def simular(t,prev,ultimo,m,regras,distancia,politica,desempate='stop',forcar=None):
    assert politica in ('prazo','stop','stop_take') and desempate in ('stop','take')
    assert np.all(np.diff(t)==86400000) and len(t)==len(prev)==len(ultimo)
    tempo=m['tempo'];neg=m['negocio'];mark=m['marca'];ft=m['funding_tempo']
    fee=regras['comissao_por_lado'];slip=regras['slippage_por_lado'];tick=regras['tick_preco']
    m=dict(m,tick=tick);caixa=regras['capital_inicial'];pico=caixa;dd=0.;ops=[];saldos=[caixa];dds=[0.]
    exposto=0
    for ts,p,u in zip(t,prev,ultimo):
        lado=decidir(float(p),float(u),regras['filtro_retorno_absoluto']) if forcar is None else forcar
        ent=int(ts+regras['latencia_minutos']*60000);fim=ent+86400000
        a=int(np.searchsorted(tempo,ent));b=int(np.searchsorted(tempo,fim))
        assert b<len(tempo) and tempo[a]==ent and tempo[b]==fim
        if lado:
            pe=grade(float(neg[a,0]*(1+lado*slip)),tick,lado>0)
            q=grade(caixa*regras['fracao_nocional']/pe,regras['passo_quantidade'],False)
            if q*pe<regras['nocional_minimo']:lado=0
        if lado:
            j,referencia,motivo,ambiguo,sl,tp=saida(m,a,b,lado,pe,distancia,politica,desempate)
            # Toque intraminuto: instante exato desconhecido; convenção fim do minuto.
            saiu=fim if motivo=='prazo' else int(tempo[j]+59999)
            ps=grade(referencia*(1-lado*slip),tick,lado<0)
            k=b if motivo=='prazo' else j+1
            ids=np.flatnonzero((ft>=ent)&(ft<saiu));taxas=m['funding_taxa'];precos=m['funding_preco']
            fv=-lado*q*precos[ids]*taxas[ids]
            inc=np.zeros(k-a);np.add.at(inc,((ft[ids]-ent)//60000).astype(int),fv)
            ce=fee*q*pe;cs=fee*q*ps;credito=caixa-ce+np.cumsum(inc)
            alto=mark[a:k,1] if lado>0 else mark[a:k,2]
            baixo=mark[a:k,2] if lado>0 else mark[a:k,1]
            eqmax=credito+lado*q*(alto-pe);eqmin=credito+lado*q*(baixo-pe)
            # Envelope conservador inclui o minuto inteiro do toque, cuja ordem
            # marca/contrato e trajetória intraminuto não são observadas.
            picos=np.maximum.accumulate(np.r_[pico,eqmax])[1:]
            dd=max(dd,float(np.max(1-eqmin/picos)));pico=float(picos[-1])
            if np.any(eqmin-q*mark[a:k,1]*fee<=q*mark[a:k,1]*regras['buffer_prudencial']):
                raise ValueError('Violação prudencial: preservar incidente, sem inventar liquidação.')
            antes=caixa;fund=float(math.fsum(fv));bruto=lado*q*(ps-pe);caixa+=bruto+fund-ce-cs
            assert caixa>0
            pico=max(pico,caixa);dd=max(dd,1-caixa/pico);exposto+=saiu-ent
            ops.append({'origem_ms':int(ts),'entrada_ms':ent,'saida_ms':saiu,'prazo_ms':fim,'minuto_saida_ms':int(tempo[j]),
                'lado':lado,'quantidade':q,'preco_entrada':pe,'preco_saida':ps,'referencia_saida':referencia,
                'stop_preco':sl,'take_preco':tp,'motivo':motivo,'ambiguo':ambiguo,'caixa_antes':antes,'caixa_depois':caixa,
                'pnl_bruto':bruto,'comissao':ce+cs,'funding':fund,'pnl_liquido':caixa-antes,
                'eventos_funding':[{'tempo_ms':int(ft[h]),'taxa':float(taxas[h]),'preco':float(precos[h])} for h in ids]})
        saldos.append(caixa);dds.append(dd)
    saldos=np.array(saldos);logs=np.diff(np.log(saldos));pnl=np.array([o['pnl_liquido'] for o in ops]);g=float(logs.mean())
    perdas=float(-pnl[pnl<0].sum());ganhos=float(pnl[pnl>0].sum())
    met={'capital_final':caixa,'retorno_liquido':caixa/regras['capital_inicial']-1,'drawdown_maximo':dd,
        'crescimento_log_diario':g,'retorno_anualizado':float(np.expm1(g*365)),
        'sharpe_diario_rf_zero':float(g/logs.std(ddof=1)*np.sqrt(365)) if len(logs)>1 and logs.std(ddof=1)>0 else None,
        'calmar':float(np.expm1(g*365)/dd) if dd else None,'operacoes':len(ops),
        'compras':sum(o['lado']==1 for o in ops),'vendas':sum(o['lado']==-1 for o in ops),
        'taxa_acerto_liquido':float(np.mean(pnl>0)) if len(pnl) else None,'profit_factor':ganhos/perdas if perdas else None,
        'comissoes':sum(o['comissao'] for o in ops),'funding':sum(o['funding'] for o in ops),
        'pnl_compras':sum(o['pnl_liquido'] for o in ops if o['lado']==1),'pnl_vendas':sum(o['pnl_liquido'] for o in ops if o['lado']==-1),
        'fracao_dias_posicionado':len(ops)/len(t),'fracao_tempo_posicionado':exposto/(len(t)*86400000),
        'previsoes_nao_positivas':int(np.sum(prev<=0)),
        **{n:sum(o['motivo']==n for o in ops) for n in ('stop','take','prazo')},'ambiguas':sum(o['ambiguo'] for o in ops)}
    return {'metricas':met,'operacoes':ops}, {'saldos_diarios':saldos,'drawdown_acumulado':np.array(dds)}
