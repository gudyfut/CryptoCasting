"""Motor determinístico minuto, preenchimentos adversos e carteira linear USD-M.

Não certifica liquidação/filtros históricos Binance. Envelopes intraminuto dão
um limite conservador de drawdown, não uma trajetória intraminuto observada.
"""
from dataclasses import dataclass
import math
import numpy as np
from avaliacao.metricas_operacionais import avaliar_patrimonio
from .mercado import MINUTO

COMISSAO = .0005
TICK = .1
PASSO = .001


def preencher(preco, lado_ordem, deslizamento):
    p = preco*(1+lado_ordem*deslizamento)
    # Arredondar sempre contra a ordem; nunca ganhar meio tick no backtest.
    return float((math.ceil(p/TICK-1e-10) if lado_ordem > 0 else math.floor(p/TICK+1e-10))*TICK)


@dataclass(frozen=True)
class Politica:
    limiar: float = 0.
    risco: float = .005
    cadencia: int = 1

    def __post_init__(self):
        if self.limiar not in (0.,.001,.002) or self.risco not in (.005,.01) or self.cadencia not in (1,4):
            raise ValueError('Política fora da grade.')


def volatilidade_horaria(candles):
    import pandas as pd
    r = np.log(candles.close.astype(float)).diff()
    return r.rolling(168,min_periods=168).std(ddof=1).to_numpy()*math.sqrt(24)


def funding_unitario(m, inicio, fim, lado, saida_protetiva):
    eventos = m.eventos[np.searchsorted(m.eventos,inicio):np.searchsorted(m.eventos,fim,side='right')]
    linhas=[]; total=0.
    for i in eventos:
        taxa = float(m.funding_taxa[i]); paga = lado*taxa > 0
        ambiguo = bool(i == fim and saida_protetiva)
        # Saída no open por tempo ocorre antes de settlement: tratada pelo chamador.
        marca = float(m.funding_preco[i]) if m.funding_exato[i] else float(m.marca[i,1 if paga else 2])
        valor = -lado*taxa*marca
        if ambiguo and valor > 0:
            valor = 0.
        total += valor
        linhas.append({'indice':int(i),'utc_ms':int(m.tempo[i]),'taxa':taxa,'marca':marca,
                       'por_btc':float(valor),'aproximado':not bool(m.funding_exato[i]),'ordem_ambigua':ambiguo})
    return total,linhas


def trajeto(m, entrada, lado, distancia, razao, deslizamento=.0005, horizonte=1440, barreiras=True):
    """Operação unitária. Entrada já deve respeitar latência; nenhuma regra de sinal."""
    if lado not in (-1,1) or distancia < .005 or not np.isfinite(distancia) or razao <= 0:
        raise ValueError('Barreira/lado inválido.')
    if entrada+horizonte >= len(m.tempo) or entrada < 0:
        raise ValueError('Horizonte sem cobertura.')
    if m.funding_evento[entrada]:
        raise ValueError('Entrada em minuto de funding bloqueada.')
    pe = preencher(m.negociacao[entrada,0],lado,deslizamento)
    stop = pe*math.exp(-lado*distancia); take = pe*math.exp(lado*razao*distancia)
    # Barrier trigger on traded prices. Includes entry minute AFTER its open fill.
    a=m.negociacao[entrada:entrada+horizonte]
    hits_stop = a[:,2] <= stop if lado==1 else a[:,1] >= stop
    hits_take = a[:,1] >= take if lado==1 else a[:,2] <= take
    hits=np.flatnonzero(hits_stop|hits_take) if barreiras else np.array([],dtype=int)
    if len(hits):
        j=int(hits[0]); saida=entrada+j
        motivo='stop' if hits_stop[j] else 'take'
        nivel=stop if motivo=='stop' else take
        # Stop gaps adverse; take never receives a favorable gap improvement.
        bruto=(min(nivel,a[j,0]) if lado==1 else max(nivel,a[j,0])) if motivo=='stop' else nivel
        # At entry the already filled price is the first eligible price, not prefill open.
        if j==0 and motivo=='stop':
            bruto=stop
        ambiguo=bool(hits_stop[j] and hits_take[j])
        fim_funding=saida
    else:
        saida=entrada+horizonte; motivo='tempo'; bruto=m.negociacao[saida,0]
        ambiguo=False; fim_funding=saida-1
    ps=preencher(bruto,-lado,deslizamento)
    fund, eventos=funding_unitario(m,entrada,fim_funding,lado,motivo!='tempo')
    custos=COMISSAO*(pe+ps)
    return {'entrada':int(entrada),'saida':int(saida),'lado':lado,'preco_entrada':pe,
        'preco_saida':ps,'stop':stop,'take':take,'motivo':motivo,'dupla_barreira':ambiguo,
        'comissao_por_btc':custos,'funding_por_btc':fund,'eventos_funding':eventos,
        'pnl_bruto_por_btc':lado*(ps-pe),'payoff':(lado*(ps-pe)-custos+fund)/pe,
        'deslizamento':deslizamento,'horizonte_minutos':horizonte,'barreiras_ativas':barreiras}


def gerar_alvos(m, candles, k_stop=1., razao=1.5):
    """Exemplos sobrepostos unitários; zero posição/capital de carteira envolvido."""
    sigma=volatilidade_horaria(candles); n=len(candles)
    alvos=np.full((n,2),np.nan); realizacao=np.full((n,2),-1,np.int64)
    motivos=np.full((n,2),'indisponivel',dtype='U16')
    for i in range(336,n-25):
        origem=int(candles.close_time.iloc[i])+1; entrada=m.indice(origem+MINUTO)
        if m.funding_evento[entrada]:
            # Fixed observable exclusion is forbidden between families: shift one minute,
            # only if settlement present in target; instead refuse unsupported schedule.
            raise ValueError('Origem horária inesperadamente coincide com funding após latência.')
        for j,lado in enumerate((1,-1)):
            r=trajeto(m,entrada,lado,max(k_stop*sigma[i],.005),razao)
            alvos[i,j]=r['payoff']; realizacao[i,j]=m.tempo[r['saida']]+MINUTO
            motivos[i,j]=r['motivo']
    return alvos,realizacao,motivos


def escores(previsao, familia, funding_estimado, deslizamento):
    p=np.asarray(previsao,float)
    if not np.isfinite(p).all():
        raise ValueError('Sinal não finito.')
    if familia=='payoff' and p.shape==(2,):
        return p.copy()
    if familia!='terminal' or p.shape!=(1,):
        raise ValueError('Dimensão/família do sinal inválida.')
    # Estimativa fixa no cenário base; estresse altera fills, não a decisão.
    r=math.expm1(float(p[0]))
    custo=2*(COMISSAO+.0005)
    return np.array([r-custo-funding_estimado,-r-custo+funding_estimado])


def simular(m, origens, previsoes, sigmas, familia, politica, inicio_ms, fim_ms,
            k_stop=1., razao=1.5, deslizamento=.0005, somente_lado=0, baseline=None):
    origens=np.asarray(origens,np.int64); previsoes=np.asarray(previsoes,float)
    sigmas=np.asarray(sigmas,float)
    if origens.ndim!=1 or len(origens)==0 or (np.diff(origens)<=0).any() or len(sigmas)!=len(origens):
        raise ValueError('Origens/sigmas inválidos.')
    if previsoes.shape!=(len(origens),2 if familia=='payoff' else 1) or not np.isfinite(previsoes).all():
        raise ValueError('Previsões sem cobertura/dimensão.')
    if not np.isfinite(sigmas).all() or (sigmas<0).any():
        raise ValueError('Volatilidade inválida.')
    if origens[0]<inicio_ms or origens[-1]>=fim_ms:
        raise ValueError('Sinais fora do bloco.')
    if baseline not in (None,'caixa','comprado','vendido','tendencia'):
        raise ValueError('Baseline inválida.')
    caixa=10000.; curva=[caixa]; tempos=[inicio_ms/1000]; trades=[]; rejeicoes=[]
    livre_apos=-1; prudencial=False
    for pos,(origem,p,sigma) in enumerate(zip(origens,previsoes,sigmas)):
        if baseline=='caixa': break
        if origem//3600000%politica.cadencia or origem <= livre_apos:
            continue
        entrada=m.indice(int(origem+MINUTO))
        if baseline is None and origem+(1442*MINUTO)>=fim_ms:
            continue
        if m.funding_evento[entrada]:
            rejeicoes.append({'origem_ms':int(origem),'motivo':'funding_na_entrada'}); continue
        if baseline in ('comprado','vendido'):
            scores=np.array([1.,-1.])*(1 if baseline=='comprado' else -1)
        elif baseline=='tendencia':
            scores=np.array([float(p[0]),-float(p[0])])
        else:
            scores=escores(p,familia,m.estimativa_funding(origem),deslizamento)
        if somente_lado: scores[1 if somente_lado==1 else 0]=-np.inf
        if scores[0]==scores[1] or max(scores)<=politica.limiar:
            continue
        lado=1 if scores[0]>scores[1] else -1
        dist=max(k_stop*sigma,.005)
        conhecido=float(m.negociacao[m.indice(int(origem))-1,3])
        risco_preco=abs(math.expm1(-lado*dist))+2*(COMISSAO+.0005)
        nocional=min(caixa*politica.risco/risco_preco,.95*caixa,50000.) if baseline is None else min(.95*caixa,50000.)
        preco_estimado=preencher(conhecido,lado,deslizamento)
        qtd=math.floor(nocional/preco_estimado/PASSO+1e-10)*PASSO
        if baseline:
            fim_trade=fim_ms-MINUTO
            if baseline=='tendencia':
                for proxima,previsao in zip(origens[pos+1:],previsoes[pos+1:]):
                    if np.sign(previsao[0])!=lado and proxima+MINUTO<fim_ms:
                        fim_trade=int(proxima+MINUTO);break
            horizonte=m.indice(int(fim_trade))-entrada
            if horizonte<=0: continue
            tr=trajeto(m,entrada,lado,dist,razao,deslizamento,horizonte,barreiras=False)
        else:
            tr=trajeto(m,entrada,lado,dist,razao,deslizamento)
        pe=tr['preco_entrada']
        if qtd*pe<100 or qtd*pe>min(.95*caixa,50000.)+1e-8 or qtd<=0:
            rejeicoes.append({'origem_ms':int(origem),'motivo':'filtro_ou_gap_sem_redimensionar'}); continue
        tr.update(origem_ms=int(origem),quantidade=qtd,caixa_antes=caixa)
        caixa-=qtd*pe*COMISSAO
        curva.append(caixa); tempos.append(m.tempo[entrada]/1000)
        fim=tr['saida']; inclui_barra=tr['motivo']!='tempo'
        idx=np.arange(entrada,fim+int(inclui_barra))
        cumul=np.zeros(len(idx)); eventos=tr['eventos_funding']
        for e in eventos:
            cumul[idx>=e['indice']]+=qtd*e['por_btc']
        if len(idx):
            alto=caixa+cumul+lado*qtd*(m.marca[idx,1 if lado==1 else 2]-pe)
            baixo=caixa+cumul+lado*qtd*(m.marca[idx,2 if lado==1 else 1]-pe)
            adverso=m.marca[idx,2 if lado==1 else 1]
            margem=baixo/(qtd*adverso)
            falhas=np.flatnonzero((margem<=.02)|(baixo<=0))
            if len(falhas):
                z=int(falhas[0]); fim=int(idx[z]); prudencial=True
                # Preserve adverse minute envelope. Exit at worst traded price of minute.
                ps=preencher(m.negociacao[fim,2 if lado==1 else 1],-lado,deslizamento)
                fund,ev=funding_unitario(m,entrada,fim,lado,True)
                tr.update(saida=fim,preco_saida=ps,motivo='prudencial',funding_por_btc=fund,
                    eventos_funding=ev,comissao_por_btc=COMISSAO*(pe+ps),
                    pnl_bruto_por_btc=lado*(ps-pe),payoff=(lado*(ps-pe)+fund-COMISSAO*(pe+ps))/pe)
                idx=idx[:z+1]; alto=alto[:z+1]; baixo=baixo[:z+1]
            # High then low is an explicitly conservative bound, not invented tick data.
            for j,h,l in zip(idx,alto,baixo):
                curva.extend((float(h),float(l))); tempos.extend((m.tempo[j]/1000,m.tempo[j]/1000))
        caixa=tr['caixa_antes']+qtd*(tr['pnl_bruto_por_btc']+tr['funding_por_btc']-tr['comissao_por_btc'])
        tr.update(caixa_depois=caixa,entrada_ms=int(m.tempo[entrada]),saida_ms=int(m.tempo[tr['saida']]),
                  pnl_liquido=qtd*(tr['pnl_bruto_por_btc']+tr['funding_por_btc']-tr['comissao_por_btc']))
        trades.append(tr); curva.append(caixa); tempos.append(m.tempo[tr['saida']]/1000)
        livre_apos=(m.tempo[tr['saida']]-MINUTO-1 if baseline and tr['motivo']=='tempo'
                    else m.tempo[tr['saida']]+MINUTO)
        if prudencial or caixa<=0: break
    curva.append(caixa); tempos.append(fim_ms/1000)
    met=avaliar_patrimonio(curva,tempos)
    met.update(operacoes=len(trades),saida_prudencial=prudencial,
        giro=sum(t['quantidade']*(t['preco_entrada']+t['preco_saida']) for t in trades)/10000,
        comissoes=sum(t['quantidade']*t['comissao_por_btc'] for t in trades),
        funding=sum(t['quantidade']*t['funding_por_btc'] for t in trades),
        pnl_compras=sum(t['pnl_liquido'] for t in trades if t['lado']==1),
        pnl_vendas=sum(t['pnl_liquido'] for t in trades if t['lado']==-1),
        funding_aproximado=sum(e['aproximado'] for t in trades for e in t['eventos_funding']),
        drawdown_envelope_conservador=True)
    return {'metricas':met,'operacoes':trades,'rejeicoes':rejeicoes,
            'patrimonio':np.asarray(curva),'segundos_utc':np.asarray(tempos)}
