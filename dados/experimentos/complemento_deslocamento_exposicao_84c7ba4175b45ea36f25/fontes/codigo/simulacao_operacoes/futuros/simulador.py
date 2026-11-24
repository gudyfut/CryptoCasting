import math
import numpy as np
import pandas as pd
from ..previsoes import diarias
from ..politicas import direcao
from .contabilidade import quantidade,preenchimento,pnl,funding,LimiteMargem

def simular(previsoes,mercado,cfg,politica,modo,cenario):
    if cfg['latencia_minutos']!=1:raise ValueError('Este ciclo exige latencia fixa de um minuto.')
    if cfg['alavancagem_maxima']!=1 or not 0<cfg['fracao_capital']<1:raise ValueError('Primeiro ciclo limitado a1x com reserva de colateral.')
    qd=diarias(previsoes);saldo=float(cfg['capital']);capital_sinal=saldo;pico=saldo;dd=0.;buffer_min=math.inf
    taxa,slip=[cfg['custos'][cenario][k] for k in ['taxa','slippage']]
    trades=[];fundamentos=[];curva=[];exposicao=0.;minutos=0;financiamento=0.;taxas=0.;derrapagem=0.;pnl_meio=0.
    for n,r in enumerate(qd.itertuples(index=False)):
        origem=int(r.origem_utc.timestamp()//60);ini=origem+cfg['latencia_minutos'];fim=ini+1440
        a,b=mercado.indice(ini),mercado.indice(fim);conhecido=mercado.indice(origem-1)
        lado=direcao(float(r.previsao),politica,modo,cfg)
        ref=float(mercado.negocio[conhecido,3]);qt=quantidade(capital_sinal,ref,lado,cfg)
        entrada_meio=float(mercado.negocio[a,0]);saida_meio=float(mercado.negocio[b,0]);antes=saldo
        pe=preenchimento(entrada_meio,qt,slip) if qt else entrada_meio
        ps=preenchimento(saida_meio,-qt,slip) if qt else saida_meio
        recusa=None
        if qt and (mercado.negocio[a,4]<=0 or mercado.negocio[b,4]<=0):raise ValueError('Sem negocios no minuto de execucao; nao mover data.')
        if qt and abs(qt)*pe>saldo-abs(qt)*pe*taxa:
            recusa='nocional_excederia_1x_apos_gap_ou_custos';qt=0.;pe=entrada_meio;ps=saida_meio
        custo_e=abs(qt)*pe*taxa;custo_s=abs(qt)*ps*taxa
        saldo_entrada=saldo-custo_e
        ft=mercado.funding
        i=np.searchsorted(ft[:,0],ini*60000,side='right');j=np.searchsorted(ft[:,0],fim*60000,side='right')
        eventos=ft[i:j];pagamentos=-qt*eventos[:,2]*eventos[:,1]
        fluxos=np.zeros(b-a+1)
        indices=(eventos[:,0]//60000).astype(np.int64)-ini
        np.add.at(fluxos,indices,pagamentos)
        cumul=np.cumsum(fluxos)
        equidade=saldo_entrada+cumul[:-1]+qt*(mercado.marca[a:b,3]-pe)
        # Minimo antes/depois de funding no minuto e extremos mark; envelope prudente2%.
        base=saldo_entrada+np.minimum(cumul[:-1],cumul[:-1]-fluxos[:-1])
        margens=np.stack([base+qt*(mercado.marca[a:b,k]-pe)-cfg['buffer_margem']*abs(qt)*mercado.marca[a:b,k] for k in [1,2]])
        menor=float(margens.min());buffer_min=min(buffer_min,menor)
        if menor<=0 or (equidade<=0).any():raise LimiteMargem(f'Margem fora do envelope em{r.origem_utc}; liquidacao real nao modelada, resultado bloqueado.')
        # Funding no instante exato de saida pertence a posicao anterior.
        previo_saida=saldo_entrada+float(pagamentos.sum())+qt*(mercado.marca[b,0]-pe)
        if previo_saida<=cfg['buffer_margem']*abs(qt)*mercado.marca[b,0]:raise LimiteMargem('Margem insuficiente antes de fechar.')
        bruto=pnl(qt,pe,ps);saldo=saldo_entrada+bruto-custo_s+float(pagamentos.sum())
        if saldo<=0:raise LimiteMargem('Capital nao positivo ao fechar.')
        pico_seq=np.maximum.accumulate(np.r_[pico,equidade,saldo]);valores=np.r_[pico,equidade,saldo]
        dd=max(dd,float(np.max(1-valores/pico_seq)));pico=float(pico_seq[-1])
        exposicao+=float(np.sum(abs(qt)*mercado.marca[a:b,3]/equidade));minutos+=len(equidade)
        proximo_sinal=equidade[-2] # close23:59:59, antes da proxima origem00:00/funding.
        trade={'origem_utc':r.origem_utc.isoformat(),'entrada_minuto':ini,'saida_minuto':fim,'previsao_log':float(r.previsao),
            'lado':int(np.sign(qt)),'quantidade_btc':qt,'capital_conhecido_no_sinal':float(capital_sinal),'preco_conhecido_futuro':ref,
            'saldo_antes':antes,'preco_entrada_meio':entrada_meio,'preco_saida_meio':saida_meio,'entrada':pe,'saida':ps,
            'taxa_entrada':custo_e,'taxa_saida':custo_s,'funding_liquido':float(pagamentos.sum()),'pnl_execucao':bruto,
            'slippage_usdt':abs(qt)*(abs(pe-entrada_meio)+abs(ps-saida_meio)),'pnl_sem_custos_execucao':pnl(qt,entrada_meio,saida_meio),
            'saldo_depois':saldo,'recusa':recusa,'buffer_minimo':menor}
        trades.append(trade)
        if qt:
            for ev,cash in zip(eventos,pagamentos):fundamentos.append({'origem_utc':r.origem_utc.isoformat(),'timestamp_ms':int(ev[0]),'taxa':float(ev[1]),'mark_price':float(ev[2]),'quantidade_btc':qt,'fluxo_usdt':float(cash)})
        for z in np.arange(59,len(equidade),60):curva.append({'minuto':ini+int(z)+1,'capital':float(equidade[z]),'posicao_btc':qt})
        curva.append({'minuto':fim,'capital':saldo,'posicao_btc':0.})
        financiamento+=trade['funding_liquido'];taxas+=custo_e+custo_s;derrapagem+=trade['slippage_usdt'];pnl_meio+=trade['pnl_sem_custos_execucao'];capital_sinal=float(proximo_sinal)
    assert math.isclose(saldo,cfg['capital']+pnl_meio-derrapagem-taxas+financiamento,rel_tol=1e-10,abs_tol=1e-8)
    resumo={'capital_inicial':cfg['capital'],'capital_final':saldo,'retorno_liquido':saldo/cfg['capital']-1,
        'drawdown_mark_close':dd,'exposicao_media':exposicao/minutos,'funding_liquido':financiamento,'comissoes':taxas,'slippage':derrapagem,
        'pnl_sem_custos_execucao':pnl_meio,'operacoes':sum(t['lado']!=0 for t in trades),'compradas':sum(t['lado']>0 for t in trades),
        'vendidas':sum(t['lado']<0 for t in trades),'dias_caixa':sum(t['lado']==0 for t in trades),'recusas':sum(t['recusa'] is not None for t in trades),
        'buffer_minimo_usdt':buffer_min,'liquidacoes_simuladas':0,'politica':politica,'modo':modo,'cenario':cenario,'dias':len(trades)}
    return resumo,trades,pd.DataFrame(curva),fundamentos
