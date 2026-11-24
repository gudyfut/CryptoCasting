"""Primitivas de reexecução financeira; modelos, seleção e filtros históricos permanecem fixos."""
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import math
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json, sha256

COLUNAS = ['indice_candle','origem_utc','destino_utc','close','previsao']


@lru_cache(maxsize=40)
def congelamento(nome): return ler_json(RAIZ/'dados/experimentos'/nome/'congelamento.json')


def contrato(nome):
    f=congelamento(nome);return f.get('contrato',f.get('assinatura',f))


def localizar(v, chaves):
    if isinstance(v,dict):
        if chaves.issubset(v):return v
        for x in v.values():
            r=localizar(x,chaves)
            if r is not None:return r
    elif isinstance(v,list):
        for x in v:
            r=localizar(x,chaves)
            if r is not None:return r
    return None


@lru_cache(maxsize=4)
def spot(par='BTCUSDT'):
    p=RAIZ/'dados/mercado/binance_spot/449aab6c79dbf88aa625'
    nomes=sorted((p/'minutos'/par).glob('*.parquet'))
    q=pd.concat([pd.read_parquet(n) for n in nomes],ignore_index=True)
    t=pd.DatetimeIndex(q.inicio_utc);assert (t[1:]-t[:-1]==pd.Timedelta(minutes=1)).all()
    x=q[['open','high','low','close','volume','negocios']].to_numpy(float,copy=True)
    x[~q.completo.to_numpy()]=np.nan
    return x,int(t[0].timestamp()//60)


def q_sinais(sinais):
    minutos,primeiro=spot();t=pd.to_datetime([x['origem_utc'] for x in sinais],utc=True)
    tempos=np.array([int(v.timestamp()//60) for v in t],dtype=np.int64)
    return pd.DataFrame({'indice_candle':tempos//60,'origem_utc':t,'destino_utc':t+pd.Timedelta(hours=24),
        'close':minutos[tempos-1-primeiro,3], 'previsao':[x['previsao_log'] for x in sinais]})[COLUNAS]


def resumo_spot24(job):
    q=RAIZ/job['fonte'];pub=next(v for v in q.parents if v.parent.name=='publicacoes')
    j=ler_json(pub/'resultados.json');chave=q.parent.relative_to(pub).as_posix()
    return j['por_ajuste'][chave]['spot'][job['cenario']]


def spot24(job, fator):
    from avaliacao.spot import simular
    q=RAIZ/job['fonte'];obj=ler_json(q)
    if job['tipo']=='spot24_preliminar':ops=obj['ordens'];esperado=obj['estrategia']
    else:ops=obj;esperado=resumo_spot24(job)
    cfg=localizar(contrato(job['pai']),{'hora_utc','taxa','slippage','taxa_agravada'})
    if cfg is None:cfg=ler_json(RAIZ/'configuracoes/mamba_estado8_001.json')['operacao']
    cfg=deepcopy(cfg);cen=job['cenario'];taxa=cfg['taxa' if cen=='base' else 'taxa_agravada'];slip=cfg['slippage' if cen=='base' else 'slippage_agravado']
    # A via de estresse do motor permite separar custo de execução do limiar base.
    cfg['taxa_agravada']=taxa;cfg['slippage_agravado']=slip*fator
    minutos,primeiro=spot(esperado.get('par','BTCUSDT'))
    dados=pd.DataFrame([{'origem_utc':o['origem_utc'],'previsao':o['previsao']} for o in ops],columns=['origem_utc','previsao'])
    fim=pd.to_datetime(max(o['saida_minuto'] for o in ops)+1,unit='m').isoformat() if ops else '2026-01-01'
    resumo,novas,curva=simular(dados,minutos,primeiro,fim,cfg,controle=esperado.get('controle',False),agravado=True)
    resumo['cenario']=esperado['cenario']
    for k in ('par','modelo','contexto','seed','arquivo'):
        if k in esperado:resumo[k]=esperado[k]
    if 'distribuicao_operacoes_observadas' in esperado:
        valores=[o['retorno_liquido'] for o in novas if o['status']=='pontas_observadas']
        a=deepcopy(esperado['distribuicao_operacoes_observadas'])
        if valores:a.update(n=len(valores),ganhos=sum(v>0 for v in valores),perdas=sum(v<0 for v in valores),zeros=sum(v==0 for v in valores),mediana=float(np.median(valores)),minimo=min(valores),maximo=max(valores))
        resumo['distribuicao_operacoes_observadas']=a
    return esperado,resumo,{'operacoes':novas,'curva':curva,'slippage_por_lado':slip*fator}


def spot_retida(job,fator):
    from backtest_carteira.simulador import simular
    cfg=localizar(contrato(job['pai']),{'custos','risco_smart','passo_btc','minimo_usdt'})
    if cfg is None:cfg=contrato('backtest_carteira_8ec8a66648313caa48e3')['configuracao']
    cfg=deepcopy(cfg);original=ler_json(RAIZ/job['resumo']);caso=original['cenario']
    custo=deepcopy(cfg['custos'][caso]);custo['slippage']*=fator
    cfg['custos']['execucao_vigente']=custo
    sinais=ler_json(RAIZ/job['fonte']);q=q_sinais(sinais);minutos,primeiro=spot()
    resumo,ordens,curva,diarios,novos_sinais=simular(q,minutos,primeiro,cfg,original['politica'],'execucao_vigente')
    resumo['cenario']=caso
    return original,resumo,{'ordens':ordens,'diarios':diarios.to_dict('records'),'sinais':novos_sinais,'slippage_por_lado':custo['slippage']}


@lru_cache(maxsize=16)
def mercado_diario(pasta):
    from experimentos.generalizacao_moedas.avaliacao import carregar_mercado
    return carregar_mercado({'pasta':pasta,'manifesto_sha256':sha256(RAIZ/pasta/'manifesto.json')})


def diaria(job,fator):
    from simulacao_operacoes.diaria_24h import simular,conferir
    f=congelamento(job['pai']);base=RAIZ/job['base'];moeda=base.parts[-1] if base.name!='continuacao_001' else base.parent.name
    if 'moedas' in f:c=f['moedas'][moeda]['configuracao'];mp=f['moedas'][moeda]['mercado']
    else:c=f['configuracao'];mp=f['mercado_minuto']
    registro=job['registro'];fase,nome,cen=[registro[k] for k in ('fase','unidade','cenario')]
    q=np.load(base/'publicacao/previsoes'/f'{fase}_{c["seeds"][0]}.npz');u=q['ultimo_close'];t=q['origens_ms']
    if nome.isdigit():prev=np.load(base/'publicacao/previsoes'/f'{fase}_{nome}.npz')['previsoes'];forcar=None
    elif nome=='ensemble':prev=np.mean([np.load(base/'publicacao/previsoes'/f'{fase}_{s}.npz')['previsoes'] for s in c['seeds']],axis=0);forcar=None
    else:prev=u;forcar={'naive':None,'sempre_comprado':1,'sempre_vendido':-1}[nome]
    regras=deepcopy(c['operacoes']);regras['slippage_por_lado']*=fator
    r,cv=simular(t,prev,u,mercado_diario(mp['pasta']),regras,c['cenarios'][cen],forcar);conferir(r,cv,regras)
    return ler_json(RAIZ/job['fonte'])['metricas'],r['metricas'],{'operacoes':r['operacoes'],'saldos_diarios':cv['saldos_diarios'].tolist(),'slippage_por_lado':regras['slippage_por_lado']*c['cenarios'][cen]['slippage_multiplicador']}


@lru_cache(maxsize=3)
def mercados_retidos(nome):
    from simulacao_operacoes.smart.mercado import carregar
    a=contrato(nome);return carregar(a['spot'],a['futuros'])


@lru_cache(maxsize=1)
def mercado_f01():
    from mercado_futuros.contexto import carregar_contexto
    from simulacao_operacoes.futuros.mercado import Mercado
    a=contrato('futuros_3e17e6fc15b66ca60313');return Mercado(*carregar_contexto(a['mercado']))


@lru_cache(maxsize=200)
def previsao_serie(pasta):
    return pd.read_parquet(RAIZ/pasta/'previsoes_teste.parquet')[COLUNAS]


def futuro(job,fator):
    ct=contrato(job['pai']);cfg=deepcopy(ct['configuracao']);g=job['grade'];case=g['cenario'];custo=deepcopy(cfg['custos'][case]);custo['slippage']*=fator
    cfg['custos']['execucao_vigente']=custo;q=previsao_serie(ct['series'][g['serie']]['pasta'])
    if job['tipo']=='futuro24':
        from simulacao_operacoes.futuros.simulador import simular
        if g['seed'] is None:q=q.assign(previsao={'sempre_comprado':.1,'sempre_vendido':-.1,'caixa':0.}[g['modelo']])
        r,trades,curva,fund=simular(q,mercado_f01(),cfg,g['politica'],g['modo'],'execucao_vigente')
        extra={'operacoes':trades,'funding':fund,'curva':curva.to_dict('records')}
    else:
        if job['pai'].startswith('revisao_'):from simulacao_operacoes.revisada.simulador import simular
        else:from simulacao_operacoes.smart.simulador import simular
        mercado=mercados_retidos(job['pai'])['spot' if g['braco']=='spot' else 'futuro']
        r,ordens,eventos,curva,diarios=simular(q,mercado,cfg,g['politica'],g['braco'],'execucao_vigente',g['benchmark'])
        extra={'ordens':ordens,'eventos':eventos,'diarios':diarios,'curva':curva.to_dict('records')}
    r['cenario']=case;extra['slippage_por_lado']=custo['slippage']
    return ler_json(RAIZ/job['fonte']),r,extra


def executar(job,fator):
    if job['tipo'] in ('spot24','spot24_preliminar'):return spot24(job,fator)
    if job['tipo']=='spot_retida':return spot_retida(job,fator)
    if job['tipo']=='diaria':return diaria(job,fator)
    if job['tipo'] in ('retida','futuro24'):return futuro(job,fator)
    if job['tipo']=='operacional':return operacional(job,fator)
    raise NotImplementedError(job['tipo'])


@lru_cache(maxsize=1)
def mercado_operacional():
    from simulacao_operacoes.operacional.mercado import carregar
    from simulacao_operacoes.operacional.motor import volatilidade_horaria
    m,h=carregar();return m,h,volatilidade_horaria(h)


def operacional(job,fator):
    from simulacao_operacoes.operacional.motor import Politica,simular
    from simulacao_operacoes.operacional.auditoria import conferir
    p=RAIZ/job['fonte'];antigo=ler_json(p);v=ler_json(p.parent/'manifesto.json')['vinculo']
    cen=v.get('cenario','base');slip={'base':.0005,'custo2x':.001,'custo3x':.0015,'comprado':.0005,'vendido':.0005}[cen]
    if 'custo' in v:slip=.0005*v['custo']
    # Sem tentativa de ordem nem rejeição, o custo de preenchimento não participa.
    if not antigo['operacoes'] and not antigo['rejeicoes']:
        z=np.load(p.parent/'curva.npz')
        return antigo['metricas'],deepcopy(antigo['metricas']),{'operacoes':[],'rejeicoes':[],
            'slippage_por_lado':slip*fator,'patrimonio':z['patrimonio'].tolist(),'segundos_utc':z['segundos_utc'].tolist(),
            'heranca_caixa_sem_ordens':True}
    f=congelamento(job['pai']);c=f.get('configuracao',f.get('proposta'));m,h,sigma=mercado_operacional()
    recortes=c['recortes'] if 'recortes' in c else c['calendario']['desenvolvimento']
    rec=next(r for r in recortes if r['id']==v['recorte']);fase='calibracao' if v.get('papel')=='calibracao' else 'comparacao'
    inicio,fim=[int(pd.Timestamp(t,tz='UTC').timestamp()*1000) for t in rec[fase]]
    baseline=v.get('baseline');k,razao=1.,1.5
    if baseline:
        origens=h.close_time.to_numpy(np.int64)+1;ids=np.flatnonzero((origens>=inicio)&(origens+60000<fim))
        close=h.close.astype(float);tendencia=np.sign(close.ewm(span=24,adjust=False,min_periods=168).mean()-close.ewm(span=168,adjust=False,min_periods=168).mean()).to_numpy()
        origens=origens[ids];prev=tendencia[ids,None];fam='terminal';pol=Politica()
    else:
        jobs=ler_json(RAIZ/'dados/experimentos'/job['pai']/'ajustes.json');braco=v.get('braco',v.get('receita'))
        jj=[j for j in jobs if not j['controle'] and j.get('braco',j.get('receita_id'))==braco and j['recorte']['id']==v['recorte']]
        unidade=str(v.get('unidade',v.get('seed')));seeds={str(j['seed']):j for j in jj}
        seed=unidade if unidade in seeds else str(jj[0]['seed'])
        z=dict(np.load(RAIZ/seeds[seed]['pasta']/'ajuste'/f'{fase}.npz'));origens=z['origens_ms'];ids=z['indices'];prev=z['previsoes']
        receita=c.get('receita',jj[0].get('receita'));fam=receita['familia_alvo'];k,razao=receita['barreiras_payoff']
        if unidade=='ensemble':prev=np.mean([np.load(RAIZ/j['pasta']/'ajuste'/f'{fase}.npz')['previsoes'] for j in jj],axis=0)
        if unidade=='media_t':prev=np.broadcast_to(ler_json(RAIZ/jj[0]['pasta']/'ajuste/escalas.json')['media_alvo'],prev.shape).copy()
        pol=Politica(**(v['politica'] if isinstance(v.get('politica'),dict) else c['politica_fixa']))
        if fase=='comparacao' and v.get('papel')=='comparacao':
            escolha=next(q/'politica_escolhida.json' for q in p.parents if (q/'politica_escolhida.json').exists())
            if ler_json(escolha)['indice'] is None:prev=np.zeros((len(origens),2));fam='payoff'
    r=simular(m,origens,prev,sigma[ids],fam,pol,inicio,fim,k,razao,slip*fator,
              {'comprado':1,'vendido':-1}.get(cen,0),baseline)
    conferir(r,m,inicio,fim)
    extra={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in r.items() if k!='metricas'}
    extra['slippage_por_lado']=slip*fator
    return antigo['metricas'],r['metricas'],extra


def conferir_reproducao(a,b):
    for k,v in a.items():
        if k in ('retorno_original','retorno_posnorm','diferenca_retorno'):continue # contrastes recompostos após os dois pais
        if isinstance(v,(int,float)) and not isinstance(v,bool):
            if not isinstance(b.get(k),(int,float)):raise ValueError(f'Metrica ausente {k}')
            np.testing.assert_allclose(v,b[k],atol=1e-7,rtol=1e-10,err_msg=k)
        elif v is None and k in b:assert b[k] is None,k
