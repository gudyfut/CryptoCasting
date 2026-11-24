"""Auditor por conta de colateral/preço médio, independente do caixa equivalente."""
import math
from decimal import Decimal
import numpy as np
from simulacao_operacoes.revisada.conta import Conta


def conferir(r,cv,m,regras,modo,t,prev,ultimo,forcar,agenda=None,filtrar_ordens=True):
    def perto(a,b):np.testing.assert_allclose(a,b,atol=1e-7,rtol=1e-10)
    conta=Conta(regras['capital_inicial'],True);tempo=m['tempo'];fee=regras['comissao_por_lado'];slip=regras['slippage_por_lado'];tick=regras['tick_preco'];passo=regras['passo_quantidade']
    def preencher(preco,lado):return (math.ceil(preco*(1+lado*slip)/tick) if lado>0 else math.floor(preco*(1+lado*slip)/tick))*tick
    def liquidavel(preco):
        q=conta.quantidade
        if not q:return conta.saldo
        fill=preencher(preco,-int(np.sign(q)))
        return conta.patrimonio(fill)-abs(q)*fill*fee
    ordens=r['ordens'];cursor=0;pico=conta.saldo;dd=0.;equities=[conta.saldo];res=0.;fids_total=0;rejeicoes=[]
    for i,(origem,pr,u,d) in enumerate(zip(t,prev,ultimo,r['dias'])):
        entrada=int(origem+regras['latencia_minutos']*60000);fim=entrada+86400000
        a=int(np.searchsorted(tempo,entrada));b=int(np.searchsorted(tempo,fim));p=float(m['negocio'][a,0]);li=liquidavel(p)
        perto(li,d['patrimonio_liquidavel_inicio']);lado=forcar if forcar is not None else (int(np.sign(pr/u-1)) if pr>0 and abs(pr/u-1)>regras['filtro_retorno_absoluto'] else 0)
        alvo=0
        if lado:
            pe=preencher(p,lado);alvo=lado*math.floor(li*regras['fracao_nocional']/pe/passo)
            if abs(alvo)*passo*pe<regras['nocional_minimo']:alvo=0
        if modo=='agenda':alvo=int(agenda[i])
        assert alvo==d['alvo_lotes'];anterior=int(round(conta.quantidade/passo))
        if modo=='diaria':deltas=[-anterior,alvo]
        elif anterior*alvo<0:deltas=[-anterior,alvo]
        else:deltas=[alvo-anterior]
        for dl in [v for v in deltas if v]:
            delta=dl*passo;fill=preencher(p,int(np.sign(dl)))
            reduzir=conta.quantidade*delta<0 and abs(delta)<=abs(conta.quantidade)+1e-10
            if filtrar_ordens:
                assert abs(delta)>=regras.get('quantidade_minima',passo)-1e-10
                assert abs(delta)<=regras.get('quantidade_maxima',float('inf'))+1e-10
                if not reduzir and abs(delta)*fill<regras['nocional_minimo']-1e-10:
                    rejeicoes.append((entrada,dl));continue
            o=ordens[cursor];cursor+=1
            assert o['tempo_ms']==entrada and o['delta_lotes']==dl
            fill=preencher(p,int(np.sign(dl)));perto(fill,o['preenchimento']);perto(o['preco_contrato'],p)
            perto(conta.saldo-conta.quantidade*conta.preco_medio,o['caixa_antes'])
            assert o['reduce_only']==reduzir
            com,realizado=conta.negociar(delta,fill,fee,reduce_only=reduzir)
            perto(com,o['comissao']);perto(conta.quantidade,o['quantidade_depois'])
            perto(conta.saldo-conta.quantidade*conta.preco_medio,o['caixa_depois'])
            assert abs(conta.quantidade/passo-round(conta.quantidade/passo))<1e-8
        perto(conta.quantidade,d['quantidade']);q=conta.quantidade
        ids=np.flatnonzero((m['funding_tempo']>=entrada)&(m['funding_tempo']<fim)) if q else np.array([],int)
        vals=-q*m['funding_preco'][ids]*m['funding_taxa'][ids];inc=np.zeros(b-a)
        for h,v in zip(ids,vals):inc[int((m['funding_tempo'][h]-entrada)//60000)]+=v
        credito=conta.saldo+np.cumsum(inc)
        if q:
            alta=credito+q*((m['marca'][a:b,1] if q>0 else m['marca'][a:b,2])-conta.preco_medio)
            baixa=credito+q*((m['marca'][a:b,2] if q>0 else m['marca'][a:b,1])-conta.preco_medio)
            env=np.column_stack([alta,baixa]).ravel();dd=max(dd,float(np.max(1-env/np.maximum.accumulate(np.r_[pico,env])[1:])));pico=max(pico,float(env.max()))
            assert np.all(baixa-abs(q)*m['marca'][a:b,1]*fee>abs(q)*m['marca'][a:b,1]*regras['buffer_prudencial'])
        for h,v in zip(ids,vals):
            e=r['funding'][fids_total];fids_total+=1
            assert e['tempo_ms']==int(m['funding_tempo'][h]);perto([e['quantidade'],e['taxa'],e['preco'],e['valor']],[q,m['funding_taxa'][h],m['funding_preco'][h],v])
        conta.saldo+=float(math.fsum(vals));eq=liquidavel(float(m['negocio'][b,0]));equities.append(eq)
        perto(eq,d['patrimonio_liquidavel_fim']);perto(float(math.fsum(vals)),d['funding'])
        pico=max(pico,eq);dd=max(dd,1-eq/pico)
    if conta.quantidade:
        o=ordens[cursor];cursor+=1;assert o['tempo_ms']==int(t[-1]+regras['latencia_minutos']*60000+86400000)
        delta=-conta.quantidade;fill=preencher(o['preco_contrato'],int(np.sign(delta)));perto(fill,o['preenchimento'])
        assert o['reduce_only'];com,_=conta.negociar(delta,fill,fee,reduce_only=True);perto(com,o['comissao'])
    assert conta.quantidade==0 and cursor==len(ordens) and fids_total==len(r['funding'])
    assert rejeicoes==[(x['tempo_ms'],x['delta_lotes']) for x in r['rejeicoes']]
    perto(equities,cv['saldos_diarios']);perto(dd,r['metricas']['drawdown_maximo']);perto(conta.saldo,r['metricas']['capital_final'])
    # Reconciliação adicional em Decimal de todos os débitos de execução/funding.
    D=lambda x:Decimal(str(x));saldo=D(regras['capital_inicial']);q=D(0)
    for o in ordens:saldo-=D(o['delta'])*D(o['preenchimento'])+D(o['comissao']);q+=D(o['delta'])
    for e in r['funding']:saldo+=D(e['valor'])
    assert abs(q)<Decimal('1e-10');res=abs(float(saldo)-conta.saldo);assert res<1e-7
    return {'dias':len(t),'ordens':cursor,'fundings':fids_total,'residuo_usdt':res,'conta_independente_e_decimal':True}
