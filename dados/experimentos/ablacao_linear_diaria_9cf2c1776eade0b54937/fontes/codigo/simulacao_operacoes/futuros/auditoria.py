"""Reconstroi saldo/PnL/custos/funding sem chamar o simulador."""
import math
import numpy as np
from ..politicas import direcao

def conferir(resumo,trades,eventos,mercado,cfg):
    saldo=float(cfg['capital']);capital_sinal=saldo;taxa=cfg['custos'][resumo['cenario']]['taxa'];slip=cfg['custos'][resumo['cenario']]['slippage'];nf=0
    for t in trades:
        assert math.isclose(saldo,t['saldo_antes'],rel_tol=1e-12)
        assert math.isclose(capital_sinal,t['capital_conhecido_no_sinal'],rel_tol=1e-11,abs_tol=1e-8)
        lado=direcao(t['previsao_log'],resumo['politica'],resumo['modo'],cfg)
        nominal=min(t['capital_conhecido_no_sinal']*cfg['fracao_capital'],cfg['nocional_maximo'])
        esperado=math.floor(nominal/t['preco_conhecido_futuro']/cfg['passo_btc'])*cfg['passo_btc']*lado
        if abs(esperado)*t['preco_conhecido_futuro']<cfg['minimo_usdt']:esperado=0.
        if not t['recusa']:assert abs(t['quantidade_btc']-esperado)<1e-12
        q=t['quantidade_btc'];a=mercado.indice(t['entrada_minuto']);b=mercado.indice(t['saida_minuto'])
        if t['recusa']:
            preenchimento_esperado=mercado.negocio[a,0]*(1+np.sign(esperado)*slip)
            assert q==0 and abs(esperado)*preenchimento_esperado>saldo-abs(esperado)*preenchimento_esperado*taxa
        assert t['preco_conhecido_futuro']==mercado.negocio[a-cfg['latencia_minutos']-1,3]
        pe=mercado.negocio[a,0]*(1+np.sign(q)*slip);ps=mercado.negocio[b,0]*(1-np.sign(q)*slip)
        assert math.isclose(pe,t['entrada'],rel_tol=1e-12) and math.isclose(ps,t['saida'],rel_tol=1e-12)
        ev=mercado.funding[(mercado.funding[:,0]>t['entrada_minuto']*60000)&(mercado.funding[:,0]<=t['saida_minuto']*60000)]
        f=float(np.sum(-q*ev[:,1]*ev[:,2]));custo=abs(q)*(pe+ps)*taxa
        # Patrimonio conhecido antes da proxima origem, sem funding/precos posteriores.
        limite=(t['saida_minuto']-cfg['latencia_minutos'])*60000
        antecipados=ev[ev[:,0]<limite]
        capital_sinal=saldo-abs(q)*pe*taxa+float(np.sum(-q*antecipados[:,1]*antecipados[:,2]))+q*(mercado.marca[b-cfg['latencia_minutos']-1,3]-pe)
        saldo+=q*(ps-pe)+f-custo
        assert math.isclose(f,t['funding_liquido'],abs_tol=1e-9) and math.isclose(saldo,t['saldo_depois'],rel_tol=1e-11,abs_tol=1e-8)
        if q:
            for e in ev:
                registrado=eventos[nf];nf+=1
                assert registrado['timestamp_ms']==int(e[0]) and registrado['taxa']==e[1] and registrado['mark_price']==e[2]
                assert registrado['quantidade_btc']==q
                assert math.isclose(registrado['fluxo_usdt'],-q*e[1]*e[2],abs_tol=1e-9)
    assert nf==len(eventos)
    assert math.isclose(saldo,resumo['capital_final'],rel_tol=1e-11,abs_tol=1e-8)
    return {'status':'conferido','operacoes_diarias':len(trades),'eventos_funding':nf,'capital_recalculado':saldo,'fontes_futuras_no_sinal':False,
            'limite':'Contabilidade, preenchimentos e funding recalculados; trajetoria mark e limite prudencial testados separadamente, nao liquidacao Binance certificada.'}
