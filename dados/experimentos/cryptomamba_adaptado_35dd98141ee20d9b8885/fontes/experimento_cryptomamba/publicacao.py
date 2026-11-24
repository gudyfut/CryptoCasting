"""Comparação59séries nas mesmas origens; métricas de retorno e de preço."""
import math
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256
from avaliacao.publicacao import conferir_previsoes,contraste_temporal
from avaliacao.mercado import carregar_minutos
from avaliacao.spot import simular
from experimento_taxa_aprendizado.publicacao import resumo_grupo


def resumir(chaves,res,prev,parte):
    if len(chaves)>1:return resumo_grupo(chaves,res,prev,parte)
    k=chaves[0];r=res[k];m={n:r['metricas'][parte][n] for n in ('mse','rmse','mae','habilidade_mse','vies','acuracia_direcional','acerto_balanceado_direcional')}
    m.update(mse_desvio_seeds=None,mse_por_seed={k:m['mse']})
    q=prev[k,parte];d=q.loc[pd.DatetimeIndex(q.origem_utc).hour==0]
    if len(d):
        v=float(np.mean((d.previsao-d.alvo)**2));base=float(np.mean(d.alvo**2));m['origens00utc']={'n_por_seed':len(d),'mse':v,'habilidade_naive':1-v/base}
    else:m['origens00utc']=None
    op={}
    for perfil in ('base','agravado','bruto_mesmos_sinais'):
        v=r['spot'][perfil]
        if not v['retorno_auditavel'] or not v['risco_auditavel']:raise ValueError('Operação incompleta.')
        op[perfil]={n:v[n] for n in ('retorno_liquido','drawdown','capital_final','entradas_planejadas','custos_observados','minutos_expostos_planejados')};op[perfil]['retorno_desvio_seeds']=None
    return {'n_seeds':1,'metricas':m,'spot':op}


def metricas_preco(q):
    atual=q.close.to_numpy(float);real=q.preco_destino.to_numpy(float);prev=atual*np.exp(q.previsao.to_numpy(float))
    if not np.isfinite(prev).all() or not np.isfinite(real).all() or (real<=0).any():raise ValueError('Preço não finito/positivo; não truncar previsão.')
    erros=prev-real;n=len(q);base=atual-real
    mse=math.fsum(float(v)**2 for v in erros)/n
    return {'n':n,'mse_usdt2':mse,'rmse_usdt':math.sqrt(mse),'mae_usdt':math.fsum(abs(float(v)) for v in erros)/n,
        'mape_percentual':100*math.fsum(abs(float(e/p)) for e,p in zip(erros,real))/n,'mse_naive_usdt2':math.fsum(float(v)**2 for v in base)/n,
        'definicao':'C_atual*exp(previsao_log); não é previsão direta treinada em dólares'}


def publicar(pasta,cfg,partes,tentativas,referencias):
    raiz=pasta/'publicacoes';dest=raiz/f'tentativa_{len(list(raiz.glob("tentativa_*")))+1:03d}';dest.mkdir(parents=True)
    novos={f'cryptomamba_{s}':t for s,t in tentativas.items()};todos={**novos,**referencias};prev={};res={};conf={}
    minutos,primeiro=carregar_minutos(RAIZ/cfg['mercado_pasta'],cfg['par'])
    for k,t in todos.items():
        rr=ler_json(t/'resultado.json');conf[k]={};precos={}
        for b in ('validacao','teste','operacional'):
            q=pd.read_parquet(t/f'previsoes_{b}.parquet');conf[k][b]=conferir_previsoes(q,partes[b],rr['metricas'].get(b));prev[k,b]=q
            if b!='operacional':precos[b]=metricas_preco(q)
        spot={}
        for nome,agravado in [('base',False),('agravado',True)]:
            resumo,ops,curva=simular(prev[k,'operacional'],minutos,primeiro,cfg['divisao']['teste'][1],cfg['operacao'],agravado=agravado);spot[nome]=resumo
            for ponto in curva:
                data=pd.Timestamp(ponto['tempo_utc'])
                if data.minute==0:ponto['tempo_utc']=(data+pd.Timedelta(minutes=cfg['operacao']['latencia_minutos'])).isoformat()
            salvar_json(dest/k/f'operacoes_{nome}.json',ops);salvar_json(dest/k/f'curva_{nome}.json',curva)
        bruto=prev[k,'operacional'].copy();f,s=cfg['operacao']['taxa'],cfg['operacao']['slippage'];limiar=np.log((1+s)*(1+f)/((1-s)*(1-f)))
        bruto['previsao']=(bruto.previsao>limiar).astype(float);spot['bruto_mesmos_sinais']=simular(bruto,minutos,primeiro,cfg['divisao']['teste'][1],dict(cfg['operacao'],taxa=0.,slippage=0.))[0]
        res[k]={'metricas':rr['metricas'],'metricas_preco':precos,'spot':spot,'tentativa_origem':t.relative_to(RAIZ).as_posix() if t.is_relative_to(RAIZ) else str(t),'origem_ajuste':'novo' if k in novos else 'herdado'}
    seeds=cfg['seeds'];grupos={'cryptomamba_seis':[f'cryptomamba_{s}' for s in seeds],'cryptomamba_tres':[f'cryptomamba_{s}' for s in (17,42,2026)],'lstm_tres':[f'lstm_{s}' for s in (17,42,2026)],'naive':['naive'],'arima':['arima']}
    for n in (8,16,32,64):
        grupos[f'estado{n}_taxa0002']=[f'estado{n}_{s}' for s in seeds];grupos[f'estado{n}_taxa0001']=[f'taxa0001_estado{n}_{s}' for s in seeds]
    medias={};contrastes={};principal={}
    for b in ('validacao','teste'):
        medias[b]={};perdas={}
        for nome,ks in grupos.items():
            medias[b][nome]=resumir(ks,res,prev,b)
            medias[b][nome]['metricas_preco']={m:float(np.mean([res[k]['metricas_preco'][b][m] for k in ks])) for m in ('mse_usdt2','rmse_usdt','mae_usdt','mape_percentual','mse_naive_usdt2')}
            perdas[nome]=np.mean([(prev[k,b].previsao.to_numpy()-prev[k,b].alvo.to_numpy())**2 for k in ks],axis=0)
        pares=[('cryptomamba_seis','estado16_taxa0002'),('cryptomamba_seis','naive'),('cryptomamba_tres','lstm_tres')]
        contrastes[b]={f'{a}_menos_{z}':contraste_temporal(partes[b].origem_utc,perdas[a],perdas[z],cfg['bootstrap']) for a,z in pares}
        if b=='validacao':
            v=contrastes[b]['cryptomamba_seis_menos_estado16_taxa0002'];principal={'media_mse_menor':bool(perdas['cryptomamba_seis'].mean()<perdas['estado16_taxa0002'].mean()),'ic95_principal_inteiramente_favoravel':v['ic95'][str(cfg['bootstrap']['principal'])][1]<0,'promocao_automatica':False}
    salvar_json(dest/'conferencia_metricas.json',conf)
    salvar_json(dest/'resultados.json',{'utc':agora(),'natureza':'CryptoMamba adaptado; comparação de abordagem composta, retrospectiva; não reprodução literal','novos':len(novos),'herdados':len(referencias),'por_ajuste':res,'medias':medias,'contrastes':contrastes,'criterio_primario':principal,
        'limites':['Núcleo percorre canais, contexto168→14 por projeção aprendida.','Dados/alvo/normalização e orçamento diferentes do artigo.','Adam/arquitetura/perda/lote/dropout/scheduler mudam juntos; não atribuir ganho a um só fator.','RMSE por seed médio, não raiz da média do MSE; sem ensemble.','2024/2025já conhecidos; não holdout novo nem walk-forward.']})
    salvar_json(dest/'manifesto.json',{'arquivos':{p.relative_to(dest).as_posix():sha256(p) for p in dest.rglob('*') if p.is_file()}})
    salvar_json(pasta/'publicacao.json',{'pasta':dest.relative_to(pasta).as_posix(),'manifesto_sha256':sha256(dest/'manifesto.json')})
