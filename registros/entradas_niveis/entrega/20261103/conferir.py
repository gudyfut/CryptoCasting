"""Revisão posterior de leitura. Não chama treino, inferência ou simulador."""
from pathlib import Path
import math
import json
import shutil
import numpy as np
import pandas as pd

from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256
from experimentos.entradas_niveis.ciclo import conferir_execucao
from experimentos.huber_blocos.publicacao import auditar_ajuste, janela_operacional
from treinamento.preservacao import conferir as conferir_tentativa
from avaliacao.metricas import calcular
from avaliacao.publicacao import conferir_previsoes
from backtest_carteira.mercado import carregar as carregar_minutos
from backtest_carteira.auditoria import conferir as conferir_carteira

DEST=Path(__file__).resolve().parent
VS=['atual','crua','niveis_padronizados']
SEEDS=[17,42,2026,7,123,31415,271828,161803]


def igual(a,b):
    assert math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-14),(a,b)


def bootstrap_independente(blocos,a,z,replicas=2000):
    diarios=[]
    for b in blocos.values():
        erro=b[a]-b[z]
        datas=pd.DatetimeIndex(b['origens'])
        # Agrupamento diário por dataframe, independente do módulo de publicação.
        frame=pd.DataFrame(erro.T,index=datas)
        soma=frame.resample('D').sum().to_numpy().T
        n=pd.Series(1,index=datas).resample('D').sum().to_numpy()
        diarios.append((soma,n))
    saida={}
    for largura in (7,14,28):
        rng=np.random.default_rng(20261104+largura);valores=[]
        for _ in range(replicas):
            indices_seeds=rng.integers(0,8,size=8);partes=[]
            for soma,n in diarios:
                inicios=rng.integers(0,len(n),size=math.ceil(len(n)/largura))
                ix=((inicios[:,None]+np.arange(largura))%len(n)).ravel()[:len(n)]
                partes.append(float(soma[indices_seeds][:,ix].sum()/(8*n[ix].sum())))
            valores.append(float(np.mean(partes)))
        saida[str(largura)]={'ic95':np.quantile(valores,[.025,.975]).tolist(),
            'ic_bonferroni_98_333':np.quantile(valores,[.05/6,1-.05/6]).tolist()}
    return saida


def diagnosticar(q):
    p=q.previsao.to_numpy(float);y=q.alvo.to_numpy(float)
    dp=p-p.mean();dy=y-y.mean();cov=float(np.mean(dp*dy))
    mse=float(np.mean((p-y)**2))
    comp={'variancia_alvo':float(y.var()),'vies_quadrado':float((p.mean()-y.mean())**2),
          'variancia_previsao':float(p.var()),'menos_duas_covariancias':-2*cov}
    igual(sum(comp.values()),mse)
    return {'n':len(q),'media_previsao':float(p.mean()),'media_alvo':float(y.mean()),
        'desvio_previsao':float(p.std()),'desvio_alvo':float(y.std()),
        'razao_desvios':float(p.std()/y.std()),'previsoes_positivas':float(np.mean(p>0)),
        'previsoes_distintas':len(np.unique(p)),
        'pearson':float(np.corrcoef(p,y)[0,1]) if p.std()>0 else None,
        'spearman':float(q.previsao.corr(q.alvo,method='spearman')) if p.std()>0 else None,
        'vitórias_naive':float(np.mean(np.abs(p-y)<np.abs(y))),
        'p95_erro':float(np.quantile(np.abs(p-y),.95)),
        'max_abs_previsao':float(np.abs(p).max()),'decomposicao_mse':comp}


def executar():
    if (DEST/'conferencia.json').exists():raise FileExistsError('Conferência existente; não sobrescrever.')
    antes=RAIZ/'docs/resultados_entradas_niveis.md'
    shutil.copyfile(antes,DEST/'relatorio_automatico_antes.md')
    print('Conferindo fontes, preservação e oito artefatos de entrada...',flush=True)
    p,f,xs=conferir_execucao();ct=f['contrato'];c=ct['configuracao']
    assert ler_json(p/'progresso.json')['status']=='concluido' and not ler_json(p/'processo.json')['ativo']
    assert not ler_json(RAIZ/'registros/entradas_niveis/processo.json')['ativo']
    pt=ler_json(p/'publicacao.json');pub=p/pt['pasta']
    assert sha256(pub/'manifesto.json')==pt['manifesto_sha256']
    arquivos=ler_json(pub/'manifesto.json')['arquivos']
    for nome,h in arquivos.items():assert sha256(pub/nome)==h,nome
    r=ler_json(pub/'resultados.json')
    assert len(r['por_ajuste'])==96 and len(r['carteiras'])==600
    pred=RAIZ/c['predecessor']['pasta'];pf=ler_json(pred/'congelamento.json')
    qs={};diagnosticos={};erros={b:{'origens':None} for b in c['blocos']}
    celulas=[]
    for key,res in r['por_ajuste'].items():
        b,variante,seed=key.split('_',1)[0],None,None
        for v in VS:
            if key.startswith(b+'_'+v+'_'):
                variante=v;seed=int(key.rsplit('_',1)[1]);break
        assert variante in VS and seed in SEEDS
        t=RAIZ/res['tentativa_origem'];conferir_tentativa(t)
        cfg=pf['contrato']['receitas'][b]['mse'] if variante=='atual' else ct['receitas'][b][variante]
        auditar_ajuste(t,pf if variante=='atual' else f,xs[b][variante],cfg)
        assert res['recarga_exata'] and res['parametros']==20257
        celulas.append((b,variante,seed))
        diagnosticos[key]={}
        for parte in ('validacao','teste','operacional'):
            q=pd.read_parquet(t/f'previsoes_{parte}.parquet')
            conferir_previsoes(q,xs[b][variante]._conjunto.partes[parte],res['metricas'].get(parte))
            qs[b,variante,seed,parte]=q
            if parte!='operacional':
                calc=calcular(q.alvo,q.previsao)
                for k in ('mse','rmse','mae','vies','acuracia_direcional','acerto_balanceado_direcional'):
                    igual(calc[k],res['metricas'][parte][k])
            if parte=='teste':
                diario=q.loc[pd.DatetimeIndex(q.origem_utc).hour==0].reset_index(drop=True)
                diagnosticos[key]={'horario':diagnosticar(q),'diario':diagnosticar(diario)}
    assert set(celulas)=={(b,v,s) for b in c['blocos'] for v in VS for s in SEEDS}
    for v in c['variantes_novas']:
        t=p/'controles'/f'B1_{v}_42/tentativa_001'
        auditar_ajuste(t,f,xs['B1'][v],ct['receitas']['B1'][v],True)
        a=ler_json(p/f'controle_{v}.json');assert a['mesma_epoca']
        assert max(a['maxima_diferenca_previsoes'].values())<1e-5
    print('96 modelos principais,2 controles e métricas conferidos.',flush=True)
    medias={};comparacoes={};globais_por_seed={}
    for b in c['blocos']:
        medias[b]={};comparacoes[b]={}
        for v in VS:
            for parte in ('validacao','teste'):
                rr=[r['por_ajuste'][f'{b}_{v}_{s}']['metricas'][parte] for s in SEEDS]
                for campo in ('mse','rmse','mae','vies'):
                    igual(float(np.mean([a[campo] for a in rr])),r['medias_por_bloco'][b][parte][v][campo])
                igual(float(np.std([a['mse'] for a in rr],ddof=1)),r['medias_por_bloco'][b][parte][v]['mse_desvio_seeds'])
            ds=[diagnosticos[f'{b}_{v}_{s}'] for s in SEEDS]
            medias[b][v]={}
            for parte in ('horario','diario'):
                campos=('media_previsao','media_alvo','desvio_previsao','desvio_alvo','razao_desvios',
                    'previsoes_positivas','pearson','spearman','vitórias_naive','p95_erro','max_abs_previsao')
                medias[b][v][parte]={k:float(np.mean([a[parte][k] for a in ds])) for k in campos}
                medias[b][v][parte]['decomposicao_mse']={k:float(np.mean([a[parte]['decomposicao_mse'][k] for a in ds]))
                    for k in ds[0][parte]['decomposicao_mse']}
            erros[b][v]=np.stack([(qs[b,v,s,'teste'].previsao-qs[b,v,s,'teste'].alvo).to_numpy()**2 for s in SEEDS])
            calendario=pd.DatetimeIndex(qs[b,v,SEEDS[0],'teste'].origem_utc)
            if erros[b]['origens'] is not None:assert erros[b]['origens'].equals(calendario)
            erros[b]['origens']=calendario
        for a,z in [('crua','atual'),('niveis_padronizados','atual'),('crua','niveis_padronizados')]:
            ds=[r['por_ajuste'][f'{b}_{a}_{s}']['metricas']['teste']['mse']-r['por_ajuste'][f'{b}_{z}_{s}']['metricas']['teste']['mse'] for s in SEEDS]
            comparacoes[b][a+'_menos_'+z]={'seeds_menor_mse':sum(d<0 for d in ds),
                'diferenca_relativa_pct':100*(r['medias_por_bloco'][b]['teste'][a]['mse']/r['medias_por_bloco'][b]['teste'][z]['mse']-1)}
    for v in VS:
        globais_por_seed[v]={str(s):float(np.mean([r['por_ajuste'][f'{b}_{v}_{s}']['metricas']['teste']['mse'] for b in c['blocos']])) for s in SEEDS}
        for parte in ('validacao','teste'):
            for campo in ('mse','rmse','mae','vies'):
                igual(float(np.mean([r['medias_por_bloco'][b][parte][v][campo] for b in c['blocos']])),r['medias_globais'][parte][v][campo])
    contrastes={}
    for key,t in r['contrastes']['teste'].items():
        a,z=t['candidata'],t['referencia'];refeito=bootstrap_independente(erros,a,z)
        for dias,d in refeito.items():
            for nome,ic in d.items():np.testing.assert_allclose(ic,t['intervalos'][dias][nome],rtol=1e-11,atol=1e-15)
        media=float(np.mean([float((b[a]-b[z]).mean()) for b in erros.values()]))
        igual(media,t['diferenca_mse'])
        base=r['medias_globais']['teste'][z]['mse']
        contrastes[key]={'diferenca_mse':media,'diferenca_relativa_pct':100*media/base,'ic_relativos_pct':{
            k:{nome:[100*x/base for x in ic] for nome,ic in d.items()} for k,d in refeito.items()},'decisao':t['decisao']}
    print('Três contrastes,7/14/28dias,2.000 réplicas recalculados independentemente.',flush=True)
    cb=pf['contrato']['carteira'];minutos,primeiro=carregar_minutos(RAIZ/cb['pasta'],cb['contrato']);opcfg=cb['contrato']['configuracao']
    financeiros={};novos=0
    for i,(key,res) in enumerate(r['carteiras'].items()):
        b,v,s,pol,custo=key.split('/')
        if res['herdado']:
            origem=RAIZ/res['publicacao_origem'];d=origem/'carteiras'/res['chave_origem']
        else:d=pub/'carteiras'/key;novos+=1
        resumo=ler_json(d/'resumo.json');ordens=ler_json(d/'ordens.json');di=pd.read_parquet(d/'diarios.parquet')
        if v=='benchmark':q=qs[b,'atual',SEEDS[0],'operacional'].copy();q['previsao']=0.
        else:q=qs[b,v,int(s),'operacional']
        q=janela_operacional(q,c['blocos'][b]['teste'][1])
        ver=conferir_carteira(q,minutos,primeiro,opcfg,pol,custo,resumo,ordens,di)
        for k in ('capital_final','retorno_liquido','drawdown_minuto_close','exposicao_media','comissoes_usdt','slippage_usdt'):
            igual(resumo[k],res[k])
        executadas=[o for o in ordens if o['status']=='executada']
        assert len(executadas)==resumo['ordens_executadas']
        financeiros[key]={'ordens_executadas':len(executadas),'compras':resumo['compras'],'vendas':resumo['vendas'],
            'dias':len(di),'herdado':res['herdado'],'reconstrucao_conferida':ver['status']=='conferido'}
        if (i+1)%100==0:print('Carteiras reconstruídas:',i+1,'/600',flush=True)
    assert novos==384
    for b,grupos in r['medias_operacionais_por_bloco'].items():
        for key,m in grupos.items():
            v,pol,custo=key.split('/');rr=[r['carteiras'][f'{b}/{v}/{s}/{pol}/{custo}'] for s in SEEDS]
            for k in ('retorno_liquido','drawdown_minuto_close','exposicao_media','capital_final','comissoes_usdt','slippage_usdt'):
                igual(float(np.mean([a[k] for a in rr])),m[k])
    analise={'execucao':f['id'],'diagnosticos_por_modelo':diagnosticos,'diagnosticos_medios_por_bloco':medias,
        'comparacoes_seeds_por_bloco':comparacoes,'mse_global_por_seed':globais_por_seed,
        'contrastes_independentes':contrastes,'conferencia_operacional':financeiros,
        'decomposicao':'MSE=var(alvo)+(media_prev-media_alvo)^2+var(prev)-2cov(prev,alvo). Diagnóstico descritivo, sem novo ajuste ou previsão.'}
    salvar_json(DEST/'analise.json',analise)
    rec={'utc':agora(),'situacao':'conferido','execucao':f['id'],'fontes':len(ct['fontes']),
        'publicacao_arquivos':len(arquivos),'publicacao_resultados_sha256':sha256(pub/'resultados.json'),
        'preservados':len(ler_json(RAIZ/'registros/entradas_niveis/preservacao_antes.json')['arquivos']),
        'principais_novos':64,'controles_reais':2,'referencias_herdadas':32,'metricas_modelos':96,
        'carteiras_reconstruidas':600,'novas':384,'herdadas':216,'contrastes_recalculados':3,
        'novos_treinamentos':0,'nova_inferencia':0,'novas_simulacoes':0,
        'recarga':'Recibos exatos da execução/checkpoints conferidos; não repetida inferência nesta revisão.',
        'script_sha256':sha256(Path(__file__)),'analise_sha256':sha256(DEST/'analise.json')}
    salvar_json(DEST/'conferencia.json',rec)
    salvar_json(DEST/'manifesto.json',{'arquivos':{p.name:sha256(p) for p in DEST.iterdir() if p.is_file() and p.name!='manifesto.json'}})
    print(json.dumps(rec,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':executar()
