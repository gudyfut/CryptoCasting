"""F03: motor temporal derivado de F02, com execução e políticas explicitamente revistas."""
import math
from dataclasses import asdict, replace
import numpy as np
import pandas as pd
from simulacao_operacoes.previsoes import diarias
from simulacao_operacoes.futuros.contabilidade import LimiteMargem
from .conta import Conta
from .politica import ordem_planejada
from .regras import filtros, quantizar, separar_ordem, aumenta_risco


def simular(previsoes, mercado, cfg, politica, braco, cenario, benchmark=None):
    if cfg['latencia_minutos'] != 1 or cfg['fracao_maxima'] != .95:
        raise ValueError('Esta rodada fixa latencia1min e teto95%.')
    if braco not in cfg['bracos'] or cenario not in cfg['custos']:
        raise ValueError('Braco/cenario invalido.')
    dados=diarias(previsoes)
    futuro=braco!='spot'
    bilateral=braco=='futuro_bilateral' and benchmark is None
    usa_funding=futuro and braco!='futuro_sem_funding'
    custos=cfg['custos'][cenario]
    taxa=custos['futuro' if futuro else 'spot'];slip=custos['slippage']
    regras=filtros(cfg,futuro)
    conta=Conta(float(cfg['capital']),futuro)
    patrimonio_conhecido=conta.saldo
    ordens=[];eventos=[];curva=[];diarios=[]
    pico=conta.saldo;drawdown=0.;buffer_min=math.inf
    exposicao=0.;exposicao_vendida=0.;nmin=0

    def risco(valores):
        nonlocal pico,drawdown
        valores=np.atleast_1d(valores)
        if not np.isfinite(valores).all() or (valores<=0).any():
            raise LimiteMargem('Patrimonio invalido; nao truncar perda.')
        picos=np.maximum.accumulate(np.r_[pico,valores])[1:]
        drawdown=max(drawdown,float(np.max(1-valores/picos)))
        pico=max(pico,float(valores.max()))

    def executar(delta, instante, conhecido, motivo, previsao=None):
        nonlocal conta
        k=mercado.indice(instante)
        meio=float(mercado.negocio[k,0]);mark=float(mercado.marca[k,0])
        partes=separar_ordem(delta,conta.quantidade,futuro)
        reducao_ok=True
        for parte,(pedido,reduzir) in enumerate(partes):
            antes=asdict(conta)
            risco(conta.patrimonio(mark))
            preco=meio*(1+np.sign(pedido)*slip)
            status='sem_ordem';comissao=0.;realizado=0.;executada=0.
            # Quantidade definida antes do fill; gaps não redimensionam a ordem.
            if pedido:
                if mercado.negocio[k,4]<=0:
                    raise ValueError('Minuto sem negocios; nao inventar fill.')
                candidata=replace(conta)
                if parte and not reducao_ok:
                    status='recusada_reducao_previa'
                elif abs(pedido)>regras['maximo_btc']+1e-12:
                    status='recusada_tamanho_pesquisa'
                elif abs(pedido)*conhecido < regras['minimo'] and not reduzir:
                    status='abaixo_minimo'
                elif not futuro and pedido>0 and candidata.saldo-pedido*preco < -1e-8:
                    status='recusada_saldo_apos_gap'
                else:
                    comissao,realizado=candidata.negociar(pedido,preco,taxa,reduce_only=reduzir)
                    if futuro and aumenta_risco(conta.quantidade,candidata.quantidade) and abs(candidata.quantidade)*mark>candidata.patrimonio(mark):
                        status='recusada_exposicao_apos_gap';comissao=0.;realizado=0.
                    else:
                        conta=candidata;executada=pedido;status='executada'
            if reduzir:reducao_ok=status=='executada'
            risco(conta.patrimonio(mark))
            ordens.append({'minuto':instante,'motivo':motivo,'parte':parte,'reduce_only':reduzir,'previsao':previsao,
                'patrimonio_conhecido':float(patrimonio_conhecido),'preco_conhecido':conhecido,
                'delta_decisao':delta,'delta_planejado':pedido,'delta_executado':executada,'preco_meio':meio,'preco_execucao':preco,
                'preco_mark':mark,'status':status,'antes':antes,'depois':asdict(conta),
                'comissao':comissao,'ativo_comissao':'BTC' if not futuro and executada>0 else 'USDT',
                'comissao_btc':executada*taxa if not futuro and executada>0 else 0.,
                'slippage':abs(executada)*abs(preco-meio),'pnl_realizado':realizado})
            curva.append({'minuto':instante,'patrimonio':conta.patrimonio(mark),'btc':conta.quantidade,'evento':'ordem'})

    for i,r in enumerate(dados.itertuples(index=False)):
        origem=int(r.origem_utc.timestamp()//60);inicio=origem+1;fim=inicio+1440
        a,b=mercado.indice(inicio),mercado.indice(fim)
        preco_conhecido=float(mercado.negocio[mercado.indice(origem-1),3])
        sinal=float(r.previsao)
        if benchmark=='caixa' or (benchmark=='comprar_manter' and i>0):
            delta=0.
        else:
            sinal=1. if benchmark=='comprar_manter' else sinal
            delta=ordem_planejada(sinal,politica,patrimonio_conhecido,preco_conhecido,conta.quantidade,bilateral,cfg,futuro)
        capital_inicio=conta.patrimonio(float(mercado.marca[a,0]))
        executar(delta,inicio,preco_conhecido,'decisao',sinal)
        q=conta.quantidade
        ft=mercado.funding
        e=ft[(ft[:,0]>inicio*60000)&(ft[:,0]<=fim*60000)] if usa_funding else ft[:0]
        fluxos=-q*e[:,1]*e[:,2]
        por_minuto=np.zeros(b-a+1)
        np.add.at(por_minuto,(e[:,0]//60000).astype(np.int64)-inicio,fluxos)
        acumulado=np.cumsum(por_minuto)
        offset=conta.saldo-q*conta.preco_medio if futuro else conta.saldo
        equidade=offset+q*mercado.marca[a:b,3]+acumulado[:-1]
        risco(equidade)
        if futuro:
            base=offset+np.minimum(acumulado[:-1],acumulado[:-1]-por_minuto[:-1])
            margem=min(float(np.min(base+q*mercado.marca[a:b,k]-cfg['buffer_margem']*abs(q)*mercado.marca[a:b,k])) for k in [1,2])
            buffer_min=min(buffer_min,margem)
            if margem<=0:
                raise LimiteMargem('Envelope prudencial violado; liquidacao real nao modelada.')
        exposicao+=float(np.sum(abs(q)*mercado.marca[a:b,3]/equidade))
        exposicao_vendida+=float(np.sum(max(-q,0.)*mercado.marca[a:b,3]/equidade))
        nmin+=len(equidade)
        patrimonio_conhecido=float(equidade[-2])
        conta.saldo+=float(fluxos.sum())
        if q:
            for v,fluxo in zip(e,fluxos):
                eventos.append({'timestamp_ms':int(v[0]),'taxa':float(v[1]),'mark':float(v[2]),'btc':q,'fluxo':float(fluxo)})
        for z in np.arange(59,len(equidade),60):
            curva.append({'minuto':inicio+int(z)+1,'patrimonio':float(equidade[z]),'btc':q,'evento':'mark_close'})
        terminal=conta.patrimonio(float(mercado.marca[b,0]))
        risco(terminal)
        if futuro and terminal<=cfg['buffer_margem']*abs(q)*mercado.marca[b,0]:
            raise LimiteMargem('Margem insuficiente na fronteira diaria.')
        diarios.append({'origem_utc':r.origem_utc.isoformat(),'inicio':capital_inicio,'fim':terminal})
    # Liquidação programada só no fim do bloco. Resíduo abaixo do mínimo fica marcado.
    conhecido=float(mercado.negocio[b-1,3])
    delta=quantizar(-conta.quantidade,regras['passo'])
    executar(delta,fim,conhecido,'terminal')
    final=conta.patrimonio(float(mercado.marca[b,0]))
    diarios[-1]['fim']=final
    for d in diarios:d['retorno_log']=math.log(d['fim']/d['inicio'])
    assert math.isclose(sum(d['retorno_log'] for d in diarios),math.log(final/cfg['capital']),abs_tol=1e-10)
    feitas=[o for o in ordens if o['status']=='executada']
    resumo={'capital_inicial':cfg['capital'],'capital_final':final,'retorno_liquido':final/cfg['capital']-1,
        'drawdown':drawdown,'exposicao_media':exposicao/nmin,'exposicao_vendida':exposicao_vendida/nmin,
        'comissoes':sum(o['comissao'] for o in feitas),'slippage':sum(o['slippage'] for o in feitas),
        'funding':sum(e['fluxo'] for e in eventos),'ordens':len(feitas),'recusas':sum(o['status'].startswith('recusada') for o in ordens),
        'giro':sum(abs(o['delta_executado'])*o['preco_execucao'] for o in feitas)/cfg['capital'],
        'abaixo_minimo':sum(o['status']=='abaixo_minimo' for o in ordens),
        'btc_residual':conta.quantidade,'residuo_usdt':abs(conta.quantidade)*float(mercado.marca[b,0]),'buffer_minimo':buffer_min if futuro else None,
        'dias':len(dados),'politica':politica,'braco':braco,'cenario':cenario,'benchmark':benchmark}
    return resumo,ordens,eventos,pd.DataFrame(curva),diarios
