"""Métricas, operação e quatro efeitos pareados; nenhuma seleção pelo teste."""
import math
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,agora
from avaliacao.publicacao import conferir_previsoes
from avaliacao.mercado import carregar_minutos
from avaliacao.spot import simular


def contraste(origens,a,b,cfg):
    diferenca=np.asarray(a)-np.asarray(b)
    if len(diferenca)!=len(origens) or not np.isfinite(diferenca).all():raise ValueError('Contraste inválido.')
    diario=pd.DataFrame({'d':diferenca},index=pd.DatetimeIndex(origens)).resample('D')['d'].agg(['sum','count'])
    soma,n=diario['sum'].to_numpy(),diario['count'].to_numpy();intervalos={};ajustados={}
    for dias in cfg['dias']:
        g=np.random.default_rng(cfg['seed']+dias);valores=[]
        for _ in range(cfg['replicas']):
            ini=g.integers(0,len(diario),size=math.ceil(len(diario)/dias))
            ix=((ini[:,None]+np.arange(dias))%len(diario)).ravel()[:len(diario)]
            total=n[ix].sum()
            if not total:raise ValueError('Réplica vazia.')
            valores.append(soma[ix].sum()/total)
        intervalos[str(dias)]=np.quantile(valores,[.025,.975]).tolist()
        ajustados[str(dias)]=np.quantile(valores,[.05/4/2,1-.05/4/2]).tolist()
    return {'diferenca_mse_candidata_menos_referencia':float(diferenca.mean()),'ic95':intervalos,
        'ic9875_bonferroni_quatro':ajustados,'principal_dias':cfg['principal'],'replicas':cfg['replicas'],
        'familia_primaria':'quatro efeitos de taxa em validação; teste secundário',
        'limite':'exploratório, condicional aos modelos; ajuste dos quatro efeitos não corrige seleção histórica/checkpoints'}


def resumo_grupo(chaves,resultados,previsoes,parte):
    ms=[resultados[k]['metricas'][parte] for k in chaves]
    metricas={n:float(np.mean([m[n] for m in ms])) for n in ('mse','rmse','mae','habilidade_mse','vies','acuracia_direcional','acerto_balanceado_direcional')}
    metricas['mse_desvio_seeds']=float(np.std([m['mse'] for m in ms],ddof=1));metricas['mse_por_seed']={k:resultados[k]['metricas'][parte]['mse'] for k in chaves}
    ds=[previsoes[k,parte].loc[pd.DatetimeIndex(previsoes[k,parte].origem_utc).hour==0] for k in chaves]
    if len(ds[0]):
        mm=[float(np.mean((d.previsao-d.alvo)**2)) for d in ds];base=float(np.mean(ds[0].alvo**2))
        metricas['origens00utc']={'n_por_seed':len(ds[0]),'mse':float(np.mean(mm)),'habilidade_naive':1-float(np.mean(mm))/base}
    else:metricas['origens00utc']=None
    op={}
    for perfil in ('base','agravado','bruto_mesmos_sinais'):
        vs=[resultados[k]['spot'][perfil] for k in chaves]
        if not all(v['retorno_auditavel'] and v['risco_auditavel'] for v in vs):raise ValueError('Operação incompleta; não imputar zero.')
        op[perfil]={n:float(np.mean([v[n] for v in vs])) for n in ('retorno_liquido','drawdown','capital_final','entradas_planejadas','custos_observados','minutos_expostos_planejados')}
        op[perfil]['retorno_desvio_seeds']=float(np.std([v['retorno_liquido'] for v in vs],ddof=1))
    return {'n_seeds':len(chaves),'metricas':metricas,'spot':op}


def publicar(pasta,grade,configs,partes,tentativas,referencias):
    raiz=pasta/'publicacoes';destino=raiz/f'tentativa_{len(list(raiz.glob("tentativa_*")))+1:03d}';destino.mkdir(parents=True)
    cfg=configs[8];minutos,primeiro=carregar_minutos(RAIZ/cfg['mercado_pasta'],cfg['par'])
    novos={f'taxa0001_estado{n}_{s}':t for (n,s),t in tentativas.items()};todos={**novos,**referencias}
    if len(todos)!=len(novos)+len(referencias):raise ValueError('Chaves colidiram.')
    res={};prev={};conferencias={}
    for k,t in todos.items():
        r=ler_json(t/'resultado.json');conferencias[k]={}
        for b in ('validacao','teste','operacional'):
            q=pd.read_parquet(t/f'previsoes_{b}.parquet');conferencias[k][b]=conferir_previsoes(q,partes[b],r['metricas'].get(b));prev[k,b]=q
        spot={}
        for nome,agravado in [('base',False),('agravado',True)]:
            resumo,ops,curva=simular(prev[k,'operacional'],minutos,primeiro,cfg['divisao']['teste'][1],cfg['operacao'],agravado=agravado);spot[nome]=resumo
            for ponto in curva:
                data=pd.Timestamp(ponto['tempo_utc'])
                if data.minute==0:ponto['tempo_utc']=(data+pd.Timedelta(minutes=cfg['operacao']['latencia_minutos'])).isoformat()
            salvar_json(destino/k/f'operacoes_{nome}.json',ops);salvar_json(destino/k/f'curva_{nome}.json',curva)
        bruto=prev[k,'operacional'].copy();f,s=cfg['operacao']['taxa'],cfg['operacao']['slippage']
        bruto['previsao']=(bruto.previsao>np.log((1+s)*(1+f)/((1-s)*(1-f)))).astype(float)
        spot['bruto_mesmos_sinais']=simular(bruto,minutos,primeiro,cfg['divisao']['teste'][1],dict(cfg['operacao'],taxa=0.,slippage=0.))[0]
        qs=prev[k,'teste'];trimestres={}
        for n in range(1,5):
            v=qs.loc[pd.DatetimeIndex(qs.origem_utc).quarter==n]
            trimestres[str(n)]={'n':len(v),'mse':float(np.mean((v.previsao-v.alvo)**2)) if len(v) else None,'mse_naive':float(np.mean(v.alvo**2)) if len(v) else None}
        res[k]={'metricas':r['metricas'],'spot':spot,'trimestres':trimestres,
            'origem_ajuste':'novo' if k in novos else 'herdado','tentativa_origem':t.relative_to(RAIZ).as_posix() if t.is_relative_to(RAIZ) else str(t)}
    medias={};contrastes={};criterio={}
    for b in ('validacao','teste'):
        medias[b]={};contrastes[b]={}
        for n in grade['estados']:
            ks=[f'taxa0001_estado{n}_{s}' for s in grade['seeds']];refs=[f'estado{n}_{s}' for s in grade['seeds']]
            for rotulo,chaves in [('candidata',ks),('referencia',refs)]:medias[b][f'{rotulo}_estado{n}']=resumo_grupo(chaves,res,prev,b)
            a=np.mean([(prev[k,b].previsao.to_numpy()-prev[k,b].alvo.to_numpy())**2 for k in ks],axis=0)
            z=np.mean([(prev[k,b].previsao.to_numpy()-prev[k,b].alvo.to_numpy())**2 for k in refs],axis=0)
            c=contraste(partes[b].origem_utc,a,z,cfg['bootstrap']);c['variacao_mse_percentual']=float(100*(a.mean()/z.mean()-1))
            contrastes[b][str(n)]=c
            if b=='validacao':criterio[str(n)]={'evidencia_favoravel_procedimento':bool(a.mean()<z.mean() and c['ic9875_bonferroni_quatro'][str(cfg['bootstrap']['principal'])][1]<0),'promocao_automatica':False}
    salvar_json(destino/'conferencia_metricas.json',conferencias)
    salvar_json(destino/'resultados.json',{'utc':agora(),'natureza':cfg['exposicao'],'por_ajuste':res,'medias':medias,'contrastes':contrastes,'criterio_validacao':criterio,
        'novos':len(novos),'herdados':len(referencias),'metodo_medias':'média aritmética das métricas por seed, inclusive RMSE; não ensemble/carteira',
        'limites':['Seleção e multiplicidade históricas não são corrigidas pelo ajuste de quatro efeitos.','2024/2025 retrospectivos; divisão fixa, não walk-forward.','Sem repetição real extra; reprodução sintética e recarga exata.','Spot R0 preservada; sem execução de conta ou livro.']})
    salvar_json(destino/'manifesto.json',{'arquivos':{q.relative_to(destino).as_posix():sha256(q) for q in destino.rglob('*') if q.is_file()}})
    salvar_json(pasta/'publicacao.json',{'pasta':destino.relative_to(pasta).as_posix(),'manifesto_sha256':sha256(destino/'manifesto.json')})
