"""Carteira spot sem dívida; previsão decide antes do preço de execução futuro."""
import math
import numpy as np
import pandas as pd
from .politicas import decisao

COLUNAS=['indice_candle','origem_utc','destino_utc','close','previsao']


def dias(previsoes, minutos, primeiro, cfg):
    if list(previsoes.columns)!=COLUNAS:raise ValueError('Entrada operacional proíbe alvo ou preço futuro observado.')
    q=previsoes.loc[pd.DatetimeIndex(previsoes.origem_utc).hour==0].copy().reset_index(drop=True)
    t=pd.DatetimeIndex(q.origem_utc)
    if not len(q) or t.tz is None or q.indice_candle.duplicated().any() or not t.is_monotonic_increasing:raise ValueError('Origens inválidas.')
    if (t.minute!=0).any() or (pd.DatetimeIndex(q.destino_utc)-t!=pd.Timedelta(hours=24)).any():raise ValueError('Horizonte/horário inválido.')
    if len(q)>1 and (t[1:]-t[:-1]!=pd.Timedelta(days=1)).any():raise ValueError('Não pular dias.')
    if not np.isfinite(q[['close','previsao']].to_numpy()).all() or (q.close<=0).any():raise ValueError('Previsão/preço inválido.')
    origem=np.asarray([int(v.timestamp()//60) for v in t],dtype=np.int64);execucoes=origem+cfg['latencia_minutos'];fim=int(execucoes[-1]+1440)
    a,b=int(origem[0]-1-primeiro),fim-primeiro
    if a<0 or b>=len(minutos):raise ValueError('Mercado insuficiente.')
    if not np.isfinite(minutos[a:b+1,:4]).all() or (minutos[a:b+1,:4]<=0).any():raise ValueError('Percurso de preços indisponível; não interpolar.')
    if not np.allclose(q.close,minutos[origem-1-primeiro,3],rtol=1e-12,atol=1e-10):raise ValueError('Close da origem não coincide com passado observado.')
    if (minutos[np.r_[execucoes,fim]-primeiro,5]<=0).any():raise ValueError('Execução sem negócios; não mudar data.')
    return q,execucoes,fim


def simular(previsoes,minutos,primeiro,cfg,politica,cenario):
    q,instantes,fim=dias(previsoes,minutos,primeiro,cfg)
    taxa,slip=[cfg['custos'][cenario][n] for n in ('taxa','slippage')]
    caixa=float(cfg['capital']);btc=0.;pico=caixa;dd=0.;exposicao_soma=0.;nmin=0
    ordens=[];curva=[];diarios=[];sinais=[];custos=0.;derrapagem=0.;volume=0.
    passo=cfg['passo_btc'];minimo=cfg['minimo_usdt']

    def valor(preco):return caixa+btc*preco
    def risco(e):
        nonlocal pico,dd
        if not math.isfinite(e) or e<=0:raise ValueError('Carteira inválida.')
        pico=max(pico,e);dd=max(dd,1-e/pico)
    def ponto(tempo,preco,motivo):
        e=valor(preco);risco(e)
        curva.append({'tempo_utc':pd.to_datetime(tempo,unit='m',utc=True),'capital':e,'caixa':caixa,'btc':btc,'preco_meio':preco,'motivo':motivo})
    def ordem(lado,fracao,tempo,motivo):
        nonlocal caixa,btc,custos,derrapagem,volume
        if not 0<fracao<=1:raise ValueError('Fração inválida.')
        meio=float(minutos[tempo-primeiro,0]);px=meio*(1+slip if lado=='comprar' else 1-slip)
        bruto=caixa*fracao/px if lado=='comprar' else btc*fracao
        qt=math.floor(bruto/passo)*passo
        r={'sequencia':len(ordens),'minuto':int(tempo),'lado':lado,'fracao':float(fracao),'motivo':motivo,'preco_meio':meio,'preco_execucao':px,'quantidade_bruta':qt,'caixa_antes':caixa,'btc_antes':btc}
        if bruto<=0:r['status']='sem_saldo'
        elif qt<=0 or qt*px<minimo:r['status']='recusada_filtro'
        else:
            notional=qt*px
            if lado=='comprar':
                comissao=qt*taxa;caixa-=notional;btc+=qt-comissao;ativo='BTC';custo=comissao*px
            else:
                comissao=notional*taxa;btc-=qt;caixa+=notional-comissao;ativo='USDT';custo=comissao
            if caixa<-1e-8 or btc<-1e-12:raise ValueError('Saldo negativo/posição descoberta.')
            custos+=custo;desliz=qt*abs(px-meio);derrapagem+=desliz;volume+=notional
            r.update(status='executada',notional_usdt=notional,comissao_ativo=ativo,comissao_quantidade=comissao,comissao_usdt=custo,slippage_usdt=desliz)
        r.update(caixa_depois=caixa,btc_depois=btc);ordens.append(r);ponto(tempo,meio,motivo+':'+r['status'])

    for i,r in enumerate(q.itertuples(index=False)):
        tempo=int(instantes[i]);meio=float(minutos[tempo-primeiro,0]);antes=valor(meio);ponto(tempo,meio,'antes_decisao')
        if diarios:
            diarios[-1]['capital_fim']=antes;diarios[-1]['retorno_log']=math.log(antes/diarios[-1]['capital_inicio'])
        diarios.append({'origem_utc':r.origem_utc,'capital_inicio':antes})
        # O sinal só depende da previsão já conhecida. Nenhum open futuro entra na política.
        acao,fracao=decisao(politica,float(r.previsao),cfg)
        if politica=='comprar_manter' and i>0:acao,fracao='manter',0.
        sinais.append({'origem_utc':r.origem_utc.isoformat(),'previsao_log':float(r.previsao),'acao':acao,'fracao':fracao})
        if politica=='diaria24' and i>0:ordem('vender',1.,tempo,'liquidacao_diaria')
        if acao!='manter' and (politica!='comprar_manter' or i==0):ordem(acao,fracao,tempo,'politica')
        proximo=int(instantes[i+1]) if i+1<len(instantes) else fim
        caminho=minutos[tempo-primeiro:proximo-primeiro,3];marcas=caixa+btc*caminho
        picos=np.maximum.accumulate(np.r_[pico,marcas])[1:];dd=max(dd,float(np.max(1-marcas/picos)));pico=max(pico,float(marcas.max()))
        exposicao_soma+=float(np.sum(btc*caminho/marcas));nmin+=len(caminho)
        horarios=np.arange(tempo,proximo);selecionados=np.flatnonzero((horarios+1)%60==0)
        for j in selecionados:
            curva.append({'tempo_utc':pd.to_datetime(int(horarios[j]+1),unit='m',utc=True),'capital':float(marcas[j]),'caixa':caixa,'btc':btc,'preco_meio':float(caminho[j]),'motivo':'marcacao_close'})
    meio=float(minutos[fim-primeiro,0]);ponto(fim,meio,'antes_terminal');ordem('vender',1.,fim,'liquidacao_terminal')
    final=valor(meio);diarios[-1].update(capital_fim=final,retorno_log=math.log(final/diarios[-1]['capital_inicio']))
    preenchidas=[r for r in ordens if r['status']=='executada']
    resumo={'capital_inicial':cfg['capital'],'capital_final':final,'caixa_final':caixa,'btc_residual':btc,'valor_residual_usdt':btc*meio,'retorno_liquido':final/cfg['capital']-1,'drawdown_minuto_close':dd,
        'exposicao_media':exposicao_soma/nmin,'minutos':nmin,'dias_decisao':len(q),'ordens_executadas':len(preenchidas),'compras':sum(r['lado']=='comprar' for r in preenchidas),'vendas':sum(r['lado']=='vender' for r in preenchidas),
        'ordens_recusadas_filtro':sum(r['status']=='recusada_filtro' for r in ordens),'comissoes_usdt':custos,'slippage_usdt':derrapagem,'giro_capital_inicial':volume/cfg['capital'],
        'inicio_utc':pd.to_datetime(int(instantes[0]),unit='m',utc=True).isoformat(),'fim_utc':pd.to_datetime(fim,unit='m',utc=True).isoformat(),'politica':politica,'cenario':cenario}
    assert math.isclose(sum(d['retorno_log'] for d in diarios),math.log(final/cfg['capital']),rel_tol=1e-10,abs_tol=1e-12)
    return resumo,ordens,pd.DataFrame(curva),pd.DataFrame(diarios),sinais
