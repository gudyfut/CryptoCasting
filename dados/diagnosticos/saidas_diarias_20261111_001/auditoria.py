"""Conferência por mercado e contabilidade; não chama o simulador de saídas."""
import math
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import numpy as np


def conferir(r,curva,m,regras,distancia,politica,desempate,t,prev,ultimo,forcar):
    def arred(x,passo,acima):
        return float((Decimal(str(x))/Decimal(str(passo))).quantize(Decimal('1'),rounding=ROUND_CEILING if acima else ROUND_FLOOR)*Decimal(str(passo)))
    def perto(a,b):np.testing.assert_allclose(a,b,atol=1e-7,rtol=1e-11)
    def dec(x):return Decimal(str(x))
    caixa=regras['capital_inicial'];pico=caixa;dd=0.;ops={o['origem_ms']:o for o in r['operacoes']};saldos=[caixa];max_res=0.
    tick=regras['tick_preco'];fee=regras['comissao_por_lado'];slip=regras['slippage_por_lado']
    tempo=m['tempo'];ft=m['funding_tempo'];neg=m['negocio'];marca=m['marca']
    for origem,p,u in zip(t,prev,ultimo):
        lado=forcar if forcar is not None else (int(np.sign(p/u-1)) if p>0 and abs(p/u-1)>regras['filtro_retorno_absoluto'] else 0)
        ent=int(origem+regras['latencia_minutos']*60000);fim=ent+86400000
        a=int(np.searchsorted(tempo,ent));b=int(np.searchsorted(tempo,fim))
        if lado:
            pe=arred(float(neg[a,0]*(1+lado*slip)),tick,lado>0)
            q=arred(caixa*regras['fracao_nocional']/pe,regras['passo_quantidade'],False)
            if q*pe<regras['nocional_minimo']:lado=0
        if not lado:
            assert int(origem) not in ops;saldos.append(caixa);continue
        o=ops[int(origem)];assert o['lado']==lado and o['entrada_ms']==ent
        perto([pe,q,caixa],[o['preco_entrada'],o['quantidade'],o['caixa_antes']])
        sl=arred(pe*(1-lado*distancia),tick,lado<0);tp=arred(pe*(1+lado*distancia),tick,lado>0)
        trecho=neg[a:b];acerta_sl=trecho[:,2]<=sl if lado==1 else trecho[:,1]>=sl
        acerta_tp=(trecho[:,1]>=tp if lado==1 else trecho[:,2]<=tp) if politica=='stop_take' else np.zeros(len(trecho),bool)
        hits=np.flatnonzero(acerta_sl|acerta_tp) if politica!='prazo' else np.array([],dtype=int)
        if len(hits):
            ix=int(hits[0]);j=a+ix;op=float(neg[j,0]);gs=op<=sl if lado==1 else op>=sl
            gt=(op>=tp if lado==1 else op<=tp) and politica=='stop_take'
            amb=bool(acerta_sl[ix] and acerta_tp[ix] and not gs and not gt)
            motivo='stop' if gs or (not gt and acerta_sl[ix] and (not acerta_tp[ix] or desempate=='stop')) else 'take'
            ref=op if gs else (sl if motivo=='stop' else tp);saiu=int(tempo[j]+59999);k=j+1
        else:j=b;motivo='prazo';ref=float(neg[b,0]);saiu=fim;k=b;amb=False
        assert o['motivo']==motivo and o['saida_ms']==saiu and o['ambiguo']==amb
        perto(ref,o['referencia_saida']);ps=arred(ref*(1-lado*slip),tick,lado<0);perto(ps,o['preco_saida'])
        ids=np.flatnonzero((ft>=ent)&(ft<saiu));assert len(ids)==len(o['eventos_funding'])
        for h,e in zip(ids,o['eventos_funding']):
            assert int(ft[h])==e['tempo_ms'];perto([m['funding_taxa'][h],m['funding_preco'][h]],[e['taxa'],e['preco']])
        financiamento=-dec(lado)*dec(q)*sum((dec(m['funding_taxa'][h])*dec(m['funding_preco'][h]) for h in ids),Decimal(0))
        comissao=dec(q)*(dec(pe)+dec(ps))*dec(fee);bruto=dec(lado)*dec(q)*(dec(ps)-dec(pe));liq=bruto+financiamento-comissao
        perto([float(bruto),float(financiamento),float(comissao),float(liq)],[o['pnl_bruto'],o['funding'],o['comissao'],o['pnl_liquido']])
        inc=np.zeros(k-a)
        for h in ids:inc[int((ft[h]-ent)//60000)]+=-lado*q*m['funding_preco'][h]*m['funding_taxa'][h]
        credito=caixa-fee*q*pe+np.cumsum(inc)
        altos=credito+lado*q*((marca[a:k,1] if lado==1 else marca[a:k,2])-pe)
        baixos=credito+lado*q*((marca[a:k,2] if lado==1 else marca[a:k,1])-pe)
        env=np.column_stack([altos,baixos]).ravel();picos=np.maximum.accumulate(np.r_[pico,env])[1:]
        dd=max(dd,float(np.max(1-env/picos)));pico=max(pico,float(env.max()))
        assert np.all(baixos-q*marca[a:k,1]*fee>q*marca[a:k,1]*regras['buffer_prudencial'])
        novo=float(dec(caixa)+liq);max_res=max(max_res,abs(novo-o['caixa_depois']));perto(novo,o['caixa_depois'])
        # Mantém os bytes da cadeia publicada como referência do próximo lote.
        caixa=o['caixa_depois'];pico=max(pico,caixa);dd=max(dd,1-caixa/pico);saldos.append(caixa)
    assert len(ops)==r['metricas']['operacoes'];perto(saldos,curva['saldos_diarios'])
    perto(dd,r['metricas']['drawdown_maximo']);perto(caixa,r['metricas']['capital_final'])
    return {'operacoes_conferidas':len(ops),'residuo_maximo_usdt':max_res,'gatilhos_quantidades_pnl_funding_drawdown_conferidos':True}
