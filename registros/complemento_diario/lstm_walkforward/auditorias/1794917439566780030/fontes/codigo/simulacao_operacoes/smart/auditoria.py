"""Reconciliação independente por caixa equivalente, sem usar Conta/simulador."""
import math
import numpy as np
from .politica import ordem_planejada


def conferir(resumo,ordens,eventos,mercado,cfg):
    futuro=resumo['braco']!='spot'
    funding=futuro and resumo['braco']!='futuro_sem_funding'
    custos=cfg['custos'][resumo['cenario']]
    taxa=custos['futuro' if futuro else 'spot'];slip=custos['slippage']
    caixa=float(cfg['capital']);q=0.;anterior=None;fund_total=0.;eventos_conferidos=0
    for ordem in ordens:
        tempo=ordem['minuto'];k=mercado.indice(tempo)
        ft=mercado.funding
        ev=ft[(ft[:,0]>anterior*60000)&(ft[:,0]<=tempo*60000)] if funding and anterior is not None else ft[:0]
        conhecido=caixa
        if ordem['motivo']=='decisao':
            origem=tempo-1
            ev_passados=ev[ev[:,0]<origem*60000]
            conhecido+=float(np.sum(-q*ev_passados[:,1]*ev_passados[:,2]))
            e_conhecida=conhecido+q*mercado.marca[mercado.indice(origem-1),3]
            assert math.isclose(e_conhecida,ordem['patrimonio_conhecido'],abs_tol=1e-7)
            preco=float(mercado.negocio[mercado.indice(origem-1),3])
            assert preco==ordem['preco_conhecido']
            if resumo['benchmark']=='caixa' or (resumo['benchmark']=='comprar_manter' and anterior is not None):
                esperado=0.
            else:
                esperado=ordem_planejada(ordem['previsao'],resumo['politica'],e_conhecida,preco,q,resumo['braco']=='futuro_bilateral' and resumo['benchmark'] is None,cfg)
            assert math.isclose(esperado,ordem['delta_planejado'],abs_tol=1e-10)
        else:
            esperado=-q if abs(q)*ordem['preco_conhecido']>=cfg['minimo_usdt'] else 0.
            assert math.isclose(esperado,ordem['delta_planejado'],abs_tol=1e-10)
        for v in ev:
            fluxo=-q*v[1]*v[2];caixa+=fluxo;fund_total+=fluxo
            if q:
                r=eventos[eventos_conferidos];eventos_conferidos+=1
                assert r['timestamp_ms']==int(v[0]) and r['taxa']==v[1] and r['mark']==v[2]
                assert math.isclose(r['btc'],q,abs_tol=1e-10) and math.isclose(r['fluxo'],fluxo,abs_tol=1e-7)
        antes=ordem['antes'];equivalente=antes['saldo']-antes['quantidade']*antes['preco_medio'] if futuro else antes['saldo']
        assert math.isclose(equivalente,caixa,abs_tol=1e-7) and math.isclose(q,antes['quantidade'],abs_tol=1e-10)
        planejada=ordem['delta_planejado'];executada=ordem['delta_executado']
        px=float(mercado.negocio[k,0])*(1+np.sign(planejada)*slip)
        assert math.isclose(px,ordem['preco_execucao'],abs_tol=1e-8)
        if ordem['status']=='executada':
            assert executada==planejada
        elif ordem['status'].startswith('recusada'):
            assert executada==0
            novo_q=q+planejada;novo_caixa=caixa-planejada*px-abs(planejada)*px*taxa
            mark=float(mercado.marca[k,0])
            assert (not futuro and novo_caixa < -1e-8) or (futuro and abs(novo_q)*mark>novo_caixa+novo_q*mark)
        else:
            assert executada==planejada==0
        custo=abs(executada)*px*taxa
        assert math.isclose(custo,ordem['comissao'],abs_tol=1e-7)
        caixa-=executada*px+custo;q+=executada
        if abs(q)<1e-12:q=0.
        depois=ordem['depois'];equivalente=depois['saldo']-depois['quantidade']*depois['preco_medio'] if futuro else depois['saldo']
        assert math.isclose(caixa,equivalente,abs_tol=1e-7) and math.isclose(q,depois['quantidade'],abs_tol=1e-10)
        if not futuro:assert caixa>=-1e-8 and q>=-1e-12
        anterior=tempo
    final=caixa+q*mercado.marca[mercado.indice(anterior),0]
    assert math.isclose(final,resumo['capital_final'],abs_tol=1e-7)
    assert math.isclose(fund_total,resumo['funding'],abs_tol=1e-7) and eventos_conferidos==len(eventos)
    return {'status':'conferido','capital_final_independente':final,'ordens_registradas':len(ordens),'eventos_funding':eventos_conferidos,
            'metodo':'Caixa equivalente independente confere conta Spot e colateral/PnL de futuros, plano causal, custos e funding. Nao replica liquidacao Binance.'}
