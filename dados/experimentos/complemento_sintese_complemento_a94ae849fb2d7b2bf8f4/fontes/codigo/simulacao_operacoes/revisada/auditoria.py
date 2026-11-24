"""Auditor independente: não importa política, conta, regras ou simulador F03."""
import math
from decimal import Decimal, ROUND_DOWN
import numpy as np


def proximo_plano(r, o, e, q, cfg):
    passo=cfg['filtros']['futuro' if r['braco']!='spot' else 'spot']['passo']
    if o['motivo']=='terminal':
        bruto=-q
    elif r['benchmark']=='caixa' or (r['benchmark']=='comprar_manter' and o['minuto']!=r['primeiro_minuto']):
        bruto=0.
    else:
        sinal=o['previsao'];p=o['preco_conhecido'];bilateral=r['braco']=='futuro_bilateral' and r['benchmark'] is None
        d=max(-1.,min(1.,(1-math.exp(-max(-1.,min(1.,sinal))))/cfg['escala_smart']))
        if not d:
            bruto=0.
        elif r['politica']=='smart':
            bruto=d*q if d<0 and not bilateral else d*max(0.,cfg['fracao_maxima']*e-math.copysign(1.,d)*q*p)/p
        else:
            abrir=(bilateral or d>0) and (r['politica']!='direcional_filtrada' or abs(sinal)>cfg['limiar_entrada'])
            bruto=(-q+(d*cfg['fracao_maxima']*e/p if abrir else 0.)) if q*d<0 else (d*max(0.,cfg['fracao_maxima']*e-abs(q)*p)/p if abrir else 0.)
    return math.copysign(float((Decimal(str(abs(bruto)))/Decimal(str(passo))).to_integral_value(rounding=ROUND_DOWN)*Decimal(str(passo))),bruto)


def conferir(resumo,ordens,eventos,mercado,cfg,previsoes=None):
    futuro=resumo['braco']!='spot'
    regras=cfg['filtros']['futuro' if futuro else 'spot']
    custos=cfg['custos'][resumo['cenario']];taxa=custos['futuro' if futuro else 'spot'];slip=custos['slippage']
    caixa=float(cfg['capital']);q=0.;anterior=None;fund_total=0.;contador=0;comissoes=0.;derrapagem=0.
    resumo_plano=dict(resumo,primeiro_minuto=ordens[0]['minuto'])
    sinais={} if previsoes is None else {int(x.origem_utc.timestamp()//60)+1:float(x.previsao) for x in previsoes.itertuples()}
    componentes={s:{'preco':0.,'custos':0.,'funding':0.} for s in ['comprado','vendido']}
    ultimo_meio=None
    plano=0.;q_grupo=0.;status_anterior=None
    for o in ordens:
        tempo=o['minuto'];k=mercado.indice(tempo)
        ft=mercado.funding
        ev=ft[(ft[:,0]>anterior*60000)&(ft[:,0]<=tempo*60000)] if futuro and anterior is not None else ft[:0]
        conhecido=caixa
        if o['parte']==0:
            q_grupo=q
            if o['motivo']=='decisao':
                origem=tempo-1
                ep=ev[ev[:,0]<origem*60000]
                conhecido+=float(np.sum(-q*ep[:,1]*ep[:,2]))
                patrimonio=conhecido+q*mercado.marca[mercado.indice(origem-1),3]
                assert math.isclose(patrimonio,o['patrimonio_conhecido'],abs_tol=1e-7)
                assert o['preco_conhecido']==float(mercado.negocio[mercado.indice(origem-1),3])
                if sinais and resumo['benchmark'] is None:assert o['previsao']==sinais[tempo]
            else:
                patrimonio=o['patrimonio_conhecido']
                assert o['preco_conhecido']==float(mercado.negocio[k-1,3])
            plano=proximo_plano(resumo_plano,o,patrimonio,q,cfg)
            assert math.isclose(plano,o['delta_decisao'],abs_tol=1e-10), (plano,o['delta_decisao'])
        else:
            assert o['parte']==1 and o['minuto']==anterior and futuro and plano*q_grupo<0
        if futuro and plano*q_grupo<0:
            reducao=math.copysign(min(abs(plano),abs(q_grupo)),plano)
            esperado=reducao if o['parte']==0 else plano-reducao
            assert o['reduce_only']==(o['parte']==0)
        else:
            esperado=plano
            assert not o['reduce_only']
        assert math.isclose(esperado,o['delta_planejado'],abs_tol=1e-10)
        meio=float(mercado.negocio[k,0]);mark=float(mercado.marca[k,0])
        lado='comprado' if q>=0 else 'vendido'
        if ultimo_meio is not None:componentes[lado]['preco']+=q*(meio-ultimo_meio)
        for v in ev:
            fluxo=-q*v[1]*v[2];caixa+=fluxo;fund_total+=fluxo;componentes[lado]['funding']+=fluxo
            if q:
                evento=eventos[contador];contador+=1
                assert evento['timestamp_ms']==int(v[0]) and evento['taxa']==v[1] and evento['mark']==v[2]
                assert math.isclose(evento['btc'],q,abs_tol=1e-10) and math.isclose(evento['fluxo'],fluxo,abs_tol=1e-7)
        a=o['antes'];equivalente=a['saldo']-a['quantidade']*a['preco_medio'] if futuro else a['saldo']
        assert math.isclose(equivalente,caixa,abs_tol=1e-7) and math.isclose(q,a['quantidade'],abs_tol=1e-10)
        pedido=o['delta_planejado'];feito=o['delta_executado']
        px=meio*(1+np.sign(pedido)*slip)
        assert px==o['preco_execucao'] and meio==o['preco_meio'] and mark==o['preco_mark']
        taxa_btc=pedido*taxa if not futuro and pedido>0 else 0.
        q_novo=round(q+pedido-taxa_btc,12)
        caixa_novo=caixa-pedido*px-(abs(pedido)*px*taxa if futuro or pedido<0 else 0.)
        if pedido==0:status='sem_ordem'
        elif o['parte'] and status_anterior!='executada':status='recusada_reducao_previa'
        elif abs(pedido)>regras['maximo_btc']+1e-12:status='recusada_tamanho_pesquisa'
        elif abs(pedido)*o['preco_conhecido']<regras['minimo'] and not o['reduce_only']:status='abaixo_minimo'
        elif not futuro and caixa_novo < -1e-8:status='recusada_saldo_apos_gap'
        elif futuro and (q*q_novo<0 or abs(q_novo)>abs(q)+1e-12) and abs(q_novo)*mark>caixa_novo+q_novo*mark:status='recusada_exposicao_apos_gap'
        else:status='executada'
        assert o['status']==status
        assert feito==(pedido if status=='executada' else 0.)
        if feito:
            if o['reduce_only']:assert q*feito<0 and abs(feito)<=abs(q)+1e-12
            if futuro:
                lado_custo='comprado' if (q>0 if o['reduce_only'] else feito>0) else 'vendido'
                componentes[lado_custo]['custos']+=abs(feito)*(px*taxa+abs(px-meio))
            caixa=caixa_novo;q=q_novo
            if abs(q)<1e-12:q=0.
        custo=abs(feito)*px*taxa;comissoes+=custo;derrapagem+=abs(feito)*abs(px-meio)
        assert math.isclose(custo,o['comissao'],abs_tol=1e-7)
        assert math.isclose(o['comissao_btc'],feito*taxa if not futuro and feito>0 else 0.,abs_tol=1e-12)
        b=o['depois'];equivalente=b['saldo']-b['quantidade']*b['preco_medio'] if futuro else b['saldo']
        assert math.isclose(equivalente,caixa,abs_tol=1e-7) and math.isclose(b['quantidade'],q,abs_tol=1e-10)
        if not futuro:assert caixa>=-1e-8 and q>=-1e-12
        anterior=tempo;ultimo_meio=meio;status_anterior=status
    final=caixa+q*mark
    assert math.isclose(final,resumo['capital_final'],abs_tol=1e-7)
    assert math.isclose(comissoes,resumo['comissoes'],abs_tol=1e-7) and math.isclose(derrapagem,resumo['slippage'],abs_tol=1e-7)
    assert math.isclose(fund_total,resumo['funding'],abs_tol=1e-7) and contador==len(eventos)
    if futuro:
        componentes['comprado' if q>=0 else 'vendido']['preco']+=q*(mark-ultimo_meio)
        for c in componentes.values():c['liquido']=c['preco']-c['custos']+c['funding']
        assert math.isclose(sum(c['liquido'] for c in componentes.values()),final-cfg['capital'],abs_tol=1e-7)
    return {'status':'conferido','capital_final_independente':final,'ordens_registradas':len(ordens),'eventos_funding':contador,
            'decomposicao_futuros':componentes if futuro else None,
            'metodo':'Caixa equivalente, formulas independentes de plano, execucao, comissao recebida, margem e funding; nao e replica integral da exchange.'}
