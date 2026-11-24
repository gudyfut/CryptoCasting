"""Reconstrução independente dos saldos e do risco a partir dos lançamentos."""
import math
import numpy as np
from .simulador import dias


def conferir(previsoes,minutos,primeiro,cfg,politica,cenario,resumo,ordens,diarios):
    q,tempos,fim=dias(previsoes,minutos,primeiro,cfg)
    f,s=cfg['custos'][cenario]['taxa'],cfg['custos'][cenario]['slippage']
    caixa=float(cfg['capital']);btc=0.;pico=caixa;dd=0.;custo=0.;derrap=0.;giro=0.;exp=0.;nmin=0;pos=0
    def igual(a,b):
        if not math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-8):raise ValueError(f'Lançamento/risco divergente: {a} != {b}')
    def marcar(preco):
        nonlocal pico,dd
        e=caixa+btc*preco;pico=max(pico,e);dd=max(dd,1-e/pico);return e
    def validar_ordem(lado,frac,t,motivo):
        nonlocal caixa,btc,custo,derrap,giro,pos
        r=ordens[pos];pos+=1;assert (r['minuto'],r['lado'],r['motivo'],r['sequencia'])==(int(t),lado,motivo,pos-1);igual(r['fracao'],frac)
        p=float(minutos[t-primeiro,0]);px=p*(1+s if lado=='comprar' else 1-s);igual(px,r['preco_execucao']);igual(caixa,r['caixa_antes']);igual(btc,r['btc_antes'])
        bruto=caixa*frac/px if lado=='comprar' else btc*frac;qt=math.floor(bruto/cfg['passo_btc'])*cfg['passo_btc'];igual(qt,r['quantidade_bruta'])
        status='sem_saldo' if bruto<=0 else 'recusada_filtro' if qt<=0 or qt*px<cfg['minimo_usdt'] else 'executada';assert status==r['status']
        if status=='executada':
            notional=qt*px;fee=qt*f if lado=='comprar' else notional*f;feeusd=fee*px if lado=='comprar' else fee
            igual(feeusd,r['comissao_usdt']);igual(fee,r['comissao_quantidade']);igual(notional,r['notional_usdt']);igual(qt*abs(px-p),r['slippage_usdt'])
            assert r['comissao_ativo']==('BTC' if lado=='comprar' else 'USDT')
            if lado=='comprar':caixa-=notional;btc+=qt-fee
            else:caixa+=notional-fee;btc-=qt
            custo+=feeusd;derrap+=qt*abs(px-p);giro+=notional
        igual(caixa,r['caixa_depois']);igual(btc,r['btc_depois']);marcar(p)
    for i,r in enumerate(q.itertuples(index=False)):
        t=int(tempos[i]);p=float(minutos[t-primeiro,0]);ini=marcar(p);igual(ini,float(diarios.capital_inicio.iloc[i]))
        if i:igual(ini,float(diarios.capital_fim.iloc[i-1]))
        # Formulação por preços, distinta da função de decisão que o executor utiliza.
        previsto=float(r.close)*math.exp(float(r.previsao));atual=float(r.close)
        acao='manter';frac=0.
        if politica=='smart':
            d=(previsto-atual)/(cfg['risco_smart']*previsto)
            if d>0:acao='comprar';frac=min(d,1.)
            elif d<0:acao='vender';frac=min(-d,1.)
        elif politica=='vanilla':
            if abs((previsto-atual)/atual)>=cfg['limiar_vanilla']:acao='comprar' if previsto>atual else 'vender';frac=1.
        elif politica=='diaria24':
            fb,sb=cfg['custos']['base']['taxa'],cfg['custos']['base']['slippage']
            if float(r.previsao)>math.log((1+sb)*(1+fb)/((1-sb)*(1-fb))):acao='comprar';frac=1.
            if i:validar_ordem('vender',1.,t,'liquidacao_diaria')
        elif politica=='comprar_manter':
            if i==0:acao='comprar';frac=1.
        elif politica!='caixa':raise ValueError('Política não reconhecida.')
        if acao!='manter':validar_ordem(acao,frac,t,'politica')
        prox=int(tempos[i+1]) if i+1<len(tempos) else fim
        valores=caixa+btc*minutos[t-primeiro:prox-primeiro,3];picos=np.maximum.accumulate(np.r_[pico,valores])[1:]
        dd=max(dd,float(np.max(1-valores/picos)));pico=max(pico,float(valores.max()));exp+=float(np.sum((valores-caixa)/valores));nmin+=len(valores)
    marcar(float(minutos[fim-primeiro,0]));validar_ordem('vender',1.,fim,'liquidacao_terminal');assert pos==len(ordens)
    final=caixa+btc*float(minutos[fim-primeiro,0]);igual(final,resumo['capital_final']);igual(final,float(diarios.capital_fim.iloc[-1]));igual(dd,resumo['drawdown_minuto_close']);igual(exp/nmin,resumo['exposicao_media'])
    igual(custo,resumo['comissoes_usdt']);igual(derrap,resumo['slippage_usdt']);igual(giro/cfg['capital'],resumo['giro_capital_inicial']);igual(caixa,resumo['caixa_final']);igual(btc,resumo['btc_residual'])
    igual(float(diarios.retorno_log.sum()),math.log(final/cfg['capital']))
    return {'status':'conferido','ordens_reconstruidas':pos,'minutos_risco':nmin,'capital_final':final,'drawdown_recalculado':dd,'fontes_futuras_na_decisao':False}
