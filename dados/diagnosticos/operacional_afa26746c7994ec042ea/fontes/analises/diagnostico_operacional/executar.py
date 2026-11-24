"""Leitura identificada de previsões, alvos e operações já publicados."""
from pathlib import Path
import json
import shutil
import traceback
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, sha256, identidade, agora, conferir_arquivos
from simulacao_operacoes.operacional.mercado import carregar
from .metricas import resumo, estatistica_canal, quintis_c, bootstrap, decompor_operacao, correlacao, direcao

CONFIG = 'configuracoes/diagnostico_operacional_001.json'


def limpar(v):
    if isinstance(v,dict): return {str(k):limpar(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [limpar(x) for x in v]
    if isinstance(v,np.ndarray): return limpar(v.tolist())
    if isinstance(v,np.generic): return limpar(v.item())
    if isinstance(v,float) and not np.isfinite(v): return None
    return v


def salvar(p,v): salvar_json(p,limpar(v))


def inventario(c):
    ptr=ler_json(RAIZ/c['origem']); assert ptr['id']==c['execucao_origem']
    p=RAIZ/ptr['pasta']; assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    f=ler_json(p/'congelamento.json')
    conferir_arquivos(RAIZ,f['fontes']); conferir_arquivos(p/'fontes',f['fontes'])
    conferir_arquivos(RAIZ,f['preservacao'])
    fechado=ler_json(RAIZ/'registros/operacional_futuros/fechamento.json')
    assert sha256(p/'publicacao/manifesto.json')==fechado['publicacao_sha256']
    conferir_arquivos(p/'publicacao',ler_json(p/'publicacao/manifesto.json')['arquivos'])
    conferir_arquivos(RAIZ,fechado['documentos']); conferir_arquivos(RAIZ,fechado['conferencias_sha256'])
    paths={RAIZ/k for k in f['fontes']} | {RAIZ/k for k in f['preservacao']}
    paths |= {RAIZ/k for k in fechado['documentos']} | {RAIZ/k for k in fechado['conferencias_sha256']}
    paths |= set((p/'publicacao').glob('*.json')) | {p/'congelamento.json',p/'ajustes.json',RAIZ/c['origem'],RAIZ/'registros/operacional_futuros/fechamento.json'}
    jobs=ler_json(p/'ajustes.json'); assert len(jobs)==74 and sum(not j['controle'] for j in jobs)==72
    for j in jobs:
        d=RAIZ/j['pasta']; a=d/'ajuste'; co=ler_json(a/'conclusao.json')
        assert co['status']=='concluido' and co['recarga_exata']
        for fase in c['fases']:
            assert sha256(a/(fase+'.npz'))==co[fase+'_sha256']
        assert sha256(a/co['checkpoint'])==co['checkpoint_sha256']
        paths |= set(d.glob('*.json')) | set(d.glob('*.npz')) | set(a.glob('*.json')) | set(a.glob('*.npz')) | {a/co['checkpoint']}
    carteiras=ler_json(p/'publicacao/carteiras.json'); assert len(carteiras)==1260
    for ca in carteiras:
        d=RAIZ/ca['pasta']; m=ler_json(d/'manifesto.json'); conferir_arquivos(d,m['arquivos'])
        paths |= {d/k for k in m['arquivos']} | {d/'manifesto.json'}
    paths |= set((p/'avaliacoes').glob('*/*/*/politica_escolhida.json'))
    dados_ptr=RAIZ/'registros/operacional_futuros/dados/execucao.json'; dm=ler_json(dados_ptr); d=RAIZ/dm['pasta']
    assert sha256(d/'manifesto.json')==dm['manifesto_sha256']
    conferir_arquivos(d,ler_json(d/'manifesto.json')['arquivos'])
    paths |= {dados_ptr,d/'manifesto.json'} | {d/(k+'.parquet') for k in ['klines','markPriceKlines','funding']}
    return ptr,jobs,carteiras,{x.relative_to(RAIZ).as_posix():sha256(x) for x in sorted(paths)}


def ler_previsoes(jobs,c):
    mercado,h=carregar(final=False); close=h.close.to_numpy(float); ts=h.close_time.to_numpy()+1
    terminal=np.log(h.close.shift(-24)/h.close).to_numpy()
    ret1=np.log(h.close/h.close.shift(1))
    vol=ret1.rolling(168).std(ddof=1).to_numpy()*np.sqrt(24)
    tendencia=np.log(h.close/h.close.shift(72)).to_numpy()
    # Excursões descritivas a partir do fechamento observado, sem preço de execução.
    maximo=np.full(len(h),np.nan); minimo=maximo.copy()
    for i in range(len(h)-24):
        maximo[i]=h.high.iloc[i+1:i+25].max()/close[i]-1
        minimo[i]=h.low.iloc[i+1:i+25].min()/close[i]-1
    pjob=next(j for j in jobs if j['receita_id']=='P0' and not j['controle'])
    with np.load(RAIZ/pjob['pasta']/'contrato_alvos.npz') as z:
        pay=z['alvos'].copy(); motivos=z['motivos'].copy(); fim=z['realizacao_ms'].copy()
    quadros=[]; canais=[]; treino=[]; cortes=[]; drift=[]; comuns={}
    for j in jobs:
        if j['controle']: continue
        d=RAIZ/j['pasta']; a=d/'ajuste'; s=ler_json(a/'escalas.json'); co=ler_json(a/'conclusao.json')
        ct=ler_json(d/'contrato_dados.json'); hist=ler_json(a/'progresso.json')['historico']
        assert co['epoca']==min(hist,key=lambda x:x['mse_validacao'])['epoca']
        treino.append({'receita':j['receita_id'],'recorte':j['recorte']['id'],'seed':j['seed'],
            'epoca_selecionada':co['epoca'],'epocas_executadas':len(hist),
            'perda_treino_inicial':hist[0]['perda_treino'],'perda_treino_final':hist[-1]['perda_treino'],
            'mse_v_inicial':hist[0]['mse_validacao'],'mse_v_melhor':co['metricas']['validacao']['mse'],
            'mse_v_final':hist[-1]['mse_validacao'],'gradiente_maximo':max(x['norma_gradiente_maxima'] for x in hist)})
        ids_t=np.flatnonzero((ts>=ct['origens']['treino']['primeira_ms'])&(ts<=ct['origens']['treino']['ultima_ms']))
        assert len(ids_t)==ct['origens']['treino']['n']
        lado_t=1 if pay[ids_t,0].mean()>=pay[ids_t,1].mean() else -1
        maioria_t=1 if np.mean(terminal[ids_t]>0)>=np.mean(terminal[ids_t]<0) else -1
        edges_vol=np.quantile(vol[ids_t],[1/3,2/3])
        if j['receita']['familia_alvo']=='payoff':
            with np.load(d/'contrato_alvos.npz') as z:
                assert np.array_equal(z['alvos'],pay,equal_nan=True)
        # Diagnóstico de mudança das entradas, com mesmas fórmulas causais registradas.
        rep=j['receita']['representacao']; x=h[['open','high','low','close','volume']].astype(float).copy()
        if rep!='crua':
            x.iloc[:,:4]=np.log(x.iloc[:,:4])
            if rep=='relativa': x.iloc[:,:4]=x.iloc[:,:4].sub(np.log(h.close.shift(1)),axis=0)
            x['volume']=np.log1p(h.volume)
        if j['receita'].get('momentum'):
            for k in [24,72,168]: x[f'momentum_{k}']=np.log(h.close/h.close.shift(k))
        if j['receita'].get('volatilidade'):
            for k in [24,168]: x[f'volatilidade_{k}']=ret1.rolling(k).std(ddof=1)
        if j['receita'].get('volume_relativo'):
            v=np.log1p(h.volume)
            for k in [24,168]: x[f'volume_relativo_{k}']=v-v.rolling(k).mean()
        assert list(x.columns)==ct['canais']
        suporte=np.arange(ids_t[0]-j['receita']['contexto_horas']+1,ids_t[-1]+1)
        mt=x.iloc[suporte].mean().to_numpy(); st=x.iloc[suporte].std(ddof=0).to_numpy()
        pad=np.array(s['padronizar']); assert np.allclose(mt[pad],np.array(s['media_entrada'])[pad])
        assert np.allclose(st[pad],np.array(s['escala_entrada'])[pad])
        cortes.append({'job':j['id'],'volatilidade_tercis_t':edges_vol.tolist(),'lado_treino':lado_t,'maioria_direcao_treino':maioria_t})
        por_fase={}
        for fase in c['fases']:
            with np.load(a/(fase+'.npz')) as z:
                ids=z['indices']; orig=z['origens_ms']; p=z['previsoes']; y=z['alvos']
                assert np.array_equal(ts[ids],orig)
                key=(j['recorte']['id'],fase)
                if key in comuns: assert np.array_equal(orig,comuns[key])
                else: comuns[key]=orig.copy()
                esperado=terminal[ids,None] if p.shape[1]==1 else pay[ids]
                assert np.allclose(y,esperado,rtol=1e-12,atol=1e-14)
                assert np.isfinite(p).all() and np.isfinite(y).all()
                mse=float(np.mean((p-y)**2)); assert np.isclose(mse,co['metricas'][fase]['mse'],rtol=1e-12)
                funding=np.array([mercado.estimativa_funding(int(t)) for t in orig])
                if p.shape[1]==1:
                    predpreco=np.expm1(p[:,0]); scores=np.column_stack([predpreco-.002-funding,-predpreco-.002+funding])
                    direcional=np.sign(p[:,0]); magnitude=abs(predpreco)
                else:
                    scores=p.copy(); predpreco=np.full(len(p),np.nan)
                    direcional=np.sign(p[:,0]-p[:,1]); magnitude=np.max(p,axis=1)
                lado=np.where(scores[:,0]>scores[:,1],1,np.where(scores[:,1]>scores[:,0],-1,0))
                escolhido=np.where(lado>0,pay[ids,0],np.where(lado<0,pay[ids,1],0))
                data=pd.to_datetime(orig,unit='ms',utc=True)
                q=pd.DataFrame({'receita':j['receita_id'],'recorte':j['recorte']['id'],'seed':j['seed'],'fase':fase,
                    'origem_ms':orig,'indice':ids,'dia':orig//86400000,'mes':data.strftime('%Y-%m'),'hora':data.hour,
                    'p_long':scores[:,0],'p_short':scores[:,1],'y_long':pay[ids,0],'y_short':pay[ids,1],
                    'score':np.max(scores,axis=1),'lado':lado,'direcao_preco':direcional,'magnitude':magnitude,
                    'previsao_terminal_simples':predpreco,'retorno_terminal':np.expm1(terminal[ids]),
                    'payoff_escolhido':escolhido,'payoff_lado_treino':pay[ids,0 if lado_t>0 else 1],
                    'acerto_maioria_treino':maioria_t*np.expm1(terminal[ids])>0,
                    'erro2':np.mean((p-y)**2,axis=1),'erro2_zero':np.mean(y**2,axis=1),
                    'erro2_media':np.mean((y-np.array(s['media_alvo']))**2,axis=1),'erro_abs':np.mean(abs(p-y),axis=1),
                    'volatilidade_passada':vol[ids],'regime_vol':np.searchsorted(edges_vol,vol[ids])+1,
                    'tendencia_passada':tendencia[ids],'excursao_alta24':maximo[ids],'excursao_baixa24':minimo[ids],
                    'motivo_long':motivos[ids,0],'motivo_short':motivos[ids,1],
                    'fim_long_ms':fim[ids,0],'fim_short_ms':fim[ids,1]})
                q['motivo_escolhido']=np.where(lado>0,q.motivo_long,np.where(lado<0,q.motivo_short,'empate'))
                por_fase[fase]=q
                for k in range(p.shape[1]):
                    canais.append({'receita':j['receita_id'],'recorte':j['recorte']['id'],'seed':j['seed'],'fase':fase,
                        'canal':['terminal'][k] if p.shape[1]==1 else ['compra','venda'][k],
                        'sinal_alvo':direcao(p[:,k],y[:,k]),**estatistica_canal(p[:,k],y[:,k])})
                for k,nome in enumerate(x.columns):
                    zscore=(x[nome].iloc[ids].to_numpy()-mt[k])/max(st[k],1e-15)
                    drift.append({'receita':j['receita_id'],'recorte':j['recorte']['id'],'seed':j['seed'],'fase':fase,'canal':nome,
                        'media_em_std_t':float(zscore.mean()),'std_em_std_t':float(zscore.std()),
                        'fracao_fora_3std_t':float(np.mean(abs(zscore)>3)),
                        'escala_aplicada_no_modelo':bool(pad[k]),'populacao':'ultimo candle da janela'})
        for fase,q in por_fase.items():
            q['quintil_c'],limites=quintis_c(por_fase['calibracao'].score,q.score,c['quantis_calibracao'])
            q['regime_tendencia']=np.where(q.tendencia_passada>0,'alta72h','queda72h')
            if fase=='comparacao': cortes[-1]['quintis_score_c']=limites.tolist()
            quadros.append(q)
    return pd.concat(quadros,ignore_index=True),canais,treino,cortes,drift


def tabelas(q,c):
    saida={}
    for nome,colunas in [('celulas',['receita','fase','recorte','seed']),('receitas',['receita','fase']),
                         ('por_recorte',['receita','fase','recorte']),('por_seed',['receita','fase','seed']),
                         ('meses',['receita','fase','mes']),('horas',['receita','fase','hora']),
                         ('volatilidade',['receita','fase','regime_vol']),('tendencia',['receita','fase','regime_tendencia']),
                         ('quintis',['receita','fase','quintil_c'])]:
        saida[nome]=[{**dict(zip(colunas,k)),**resumo(g)} for k,g in q.groupby(colunas,sort=True)]
    faixas=[]; limiares=[]; cadencias=[]; estabilidade=[]; lados=[]
    for (r,fase),g in q.groupby(['receita','fase'],sort=True):
        met={'receita':r,'fase':fase}
        bordas=c['limites_magnitude']+[float('inf')]
        # R0: módulo da previsão de preço; payoff: score máximo, negativos em grupo próprio.
        for lo,hi in [(-float('inf'),0)]+list(zip(bordas[:-1],bordas[1:])):
            z=g[(g.magnitude>=lo)&(g.magnitude<hi)]
            faixas.append({**met,'minimo':lo,'maximo':hi,'unidade':'variacao_preco_absoluta' if r=='R0' else 'payoff_liquido_previsto',**resumo(z)})
        for lim in c['limiares_score_descritivos']:
            z=g[g.score>lim]
            limiares.append({**met,'limiar':lim,'cobertura':len(z)/len(g),**resumo(z)})
        for h in c['cadencias_diagnosticas_horas']:
            z=g[g.origem_ms%(h*3600000)==0]
            cadencias.append({**met,'cadencia_horas':h,**resumo(z)})
        for lado in [1,-1]:
            z=g[g.lado==lado]; lados.append({**met,'lado':lado,'filtro':'todos',**resumo(z)})
            z=z[z.score>0]; lados.append({**met,'lado':lado,'filtro':'score_positivo',**resumo(z)})
        for fold,z in g.groupby('recorte'):
            w=z.pivot(index='origem_ms',columns='seed',values='lado'); sc=z.pivot(index='origem_ms',columns='seed',values='score')
            pares=[]
            for i in range(len(w.columns)):
                for j in range(i+1,len(w.columns)):
                    pares.append({'seeds':[int(w.columns[i]),int(w.columns[j])],
                        'concordancia_lado':float(np.mean(w.iloc[:,i]==w.iloc[:,j])),
                        'correlacao_score':correlacao(sc.iloc[:,i],sc.iloc[:,j])})
            estabilidade.append({**met,'recorte':fold,'origens':len(w),'unanimidade_lado':float((w.nunique(axis=1)==1).mean()),'pares':pares})
    saida.update(faixas=faixas,limiares=limiares,cadencias=cadencias,estabilidade=estabilidade,lados=lados)
    # Ensemble apenas como diagnóstico de previsões, sem nova carteira/seleção.
    ens=[]
    for (r,fase,fold),g in q.groupby(['receita','fase','recorte']):
        e=g.groupby('origem_ms')[['p_long','p_short','y_long','y_short','retorno_terminal']].mean()
        lado=np.sign(e.p_long-e.p_short); payoff=np.where(lado>0,e.y_long,np.where(lado<0,e.y_short,0))
        ens.append({'receita':r,'fase':fase,'recorte':fold,'n':len(e),
                    'acuracia_preferencia':float(np.mean(lado*e.retorno_terminal>0)),
                    'payoff_medio_preferencia':float(np.mean(payoff)),
                    'fracao_score_positivo':float(np.mean(e[['p_long','p_short']].max(axis=1)>0))})
    saida['ensemble_posterior']=ens
    celulas=pd.DataFrame(saida['celulas'])
    campos=['mse','mse_zero','mse_media_treino','mae','acuracia','balanced_accuracy','payoff_escolhido_medio']
    saida['medias_celulas']=[{'receita':r,'fase':f,'celulas':len(g),
        **{k:float(g[k].mean()) for k in campos}} for (r,f),g in celulas.groupby(['receita','fase'])]
    return saida


def ler_operacoes(carteiras,q):
    qs=q.set_index(['receita','recorte','seed','fase','origem_ms']); linhas=[]; resumo_carteiras=[]
    for ca in carteiras:
        v=ca['vinculo']; r=ler_json(RAIZ/ca['pasta']/'resultado.json'); ms=r['metricas']
        soma=0
        for o in r['operacoes']:
            valores=decompor_operacao(o); soma+=valores['liquido']
            if 'receita' not in v: continue
            fase='calibracao' if v['papel']=='calibracao' else 'comparacao'
            key=(v['receita'],v['recorte'],v['seed'],fase,o['origem_ms']); z=qs.loc[key]
            linhas.append({'receita':v['receita'],'recorte':v['recorte'],'seed':v['seed'],'fase':fase,
                'carteira':ca['pasta'],'cenario':v.get('cenario','C_grade'),'origem_ms':o['origem_ms'],
                'lado':o['lado'],'motivo':o['motivo'],'horas':(o['saida_ms']-o['entrada_ms'])/3600000,
                'quantidade':o['quantidade'],'payoff':o['payoff'],'dupla_barreira':o['dupla_barreira'],
                'score':z.score,'acerto_terminal':bool(o['lado']*z.retorno_terminal>0),
                'retorno_terminal':z.retorno_terminal,**valores})
        assert np.isclose(ms['capital_final']-ms['capital_inicial'],soma,atol=1e-7,rtol=1e-10)
        resumo_carteiras.append({'pasta':ca['pasta'],**v,'retorno':ms['retorno_liquido'],'operacoes':len(r['operacoes']),
            'rejeicoes':len(r['rejeicoes']),'pnl_recalculado':soma,'residuo':soma-(ms['capital_final']-ms['capital_inicial'])})
    trades=pd.DataFrame(linhas); grupos=[]
    # C contém políticas sobre as mesmas oportunidades: resumo por carteira preservado,
    # nunca interpretado como amostra independente de trades.
    s=trades[(trades.fase=='comparacao')&(trades.cenario=='base')]
    for colunas in [['receita','recorte','seed'],['receita','recorte','lado'],['receita','recorte','motivo']]:
        for keys,g in s.groupby(colunas):
            ganhos=g.liquido[g.liquido>0].sum(); perdas=-g.liquido[g.liquido<0].sum()
            grupos.append({**dict(zip(colunas,keys)),'agrupamento':'+'.join(colunas),'n':len(g),
                'taxa_lucro':float((g.liquido>0).mean()),'acerto_terminal':float(g.acerto_terminal.mean()),
                'acertos_terminais_com_perda':int((g.acerto_terminal&(g.liquido<=0)).sum()),
                'acertos_terminais':int(g.acerto_terminal.sum()),'horas_media':float(g.horas.mean()),
                'profit_factor':float(ganhos/perdas) if perdas else None,
                'expectativa_usdt':float(g.liquido.mean()),
                **{k:float(g[k].sum()) for k in ['bruto_com_slippage','comissao','funding','liquido']}})
    return trades,resumo_carteiras,grupos


def executar():
    c=ler_json(RAIZ/CONFIG); assert c['novos_treinamentos']==c['novas_carteiras']==0
    ptr,jobs,carteiras,originais=inventario(c)
    fontes={p.relative_to(RAIZ).as_posix():sha256(p) for p in sorted((RAIZ/'analises/diagnostico_operacional').glob('*.py'))}
    fontes.update({p.relative_to(RAIZ).as_posix():sha256(p) for p in sorted((RAIZ/'tests_diagnostico_operacional').glob('*.py'))})
    fontes[CONFIG]=sha256(RAIZ/CONFIG); fontes['docs/adr/0029-diagnostico-operacional.md']=sha256(RAIZ/'docs/adr/0029-diagnostico-operacional.md')
    assinatura={'configuracao':c,'fontes':fontes,'origem':ptr,'entradas':originais}
    codigo=identidade(assinatura)[:20]; dest=RAIZ/'dados/diagnosticos'/('operacional_'+codigo)
    if dest.exists(): raise RuntimeError('Tentativa já existe: preservar e conferir, não sobrescrever.')
    dest.mkdir(parents=True); salvar(dest/'congelamento.json',assinatura)
    for nome in fontes:
        alvo=dest/'fontes'/nome; alvo.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(RAIZ/nome,alvo)
    salvar(dest/'inicio.json',{'utc':agora(),'id':codigo,'autorizacao':'Pedido explícito do pesquisador neste chat para diagnosticar e organizar previsões existentes.','treinos':0,'carteiras_novas':0})
    try:
        q,canais,treino,cortes,drift=ler_previsoes(jobs,c)
        q.to_parquet(dest/'observacoes.parquet',index=False)
        salvar(dest/'canais.json',canais); salvar(dest/'treinamento.json',treino); salvar(dest/'cortes_causais.json',cortes); salvar(dest/'mudanca_entradas.json',drift)
        salvar(dest/'tabelas.json',tabelas(q,c))
        inc=[]
        for r,g in q[q.fase=='comparacao'].groupby('receita',sort=True):
            inc.extend([{'receita':r,**x} for x in bootstrap(g,c['bootstrap'])])
        salvar(dest/'incerteza.json',inc)
        trades,carteiras_auditadas,grupos=ler_operacoes(carteiras,q)
        trades.to_parquet(dest/'operacoes_herdadas.parquet',index=False)
        salvar(dest/'carteiras_conferidas.json',carteiras_auditadas); salvar(dest/'atribuicao_operacoes.json',grupos)
        from .figuras import gerar
        gerar(dest)
        conferir_arquivos(RAIZ,originais); conferir_arquivos(RAIZ,fontes)
        auditoria={'utc':agora(),'conferido':True,'entradas_preservadas':len(originais),'fontes':len(fontes),
            'ajustes_principais':72,'controles_fora_medias':2,'arquivos_previsoes':216,'observacoes':len(q),
            'origens_S_por_receita':int(q[(q.fase=='comparacao')&(q.receita=='R0')].origem_ms.nunique()),
            'carteiras_reconciliadas':len(carteiras_auditadas),'residuo_maximo_usdt':max(abs(x['residuo']) for x in carteiras_auditadas),
            'novos_treinos':0,'novas_carteiras':0,'final_2024_2025_lido':False,
            'verificacoes':['hashes publicados, checkpoints, dados e preservação histórica','origens comuns, alvos recalculados de preços/contratos','MSE conferido com conclusões','scalers T e checkpoint mínimo V','contabilidade de todas as carteiras','hashes de entradas antes/depois']}
        salvar(dest/'auditoria.json',auditoria)
        arquivos={p.relative_to(dest).as_posix():sha256(p) for p in sorted(dest.rglob('*')) if p.is_file()}
        salvar(dest/'manifesto.json',{'id':codigo,'utc':agora(),'arquivos':arquivos,'natureza':c['natureza']})
        reg=RAIZ/'registros/diagnostico_operacional'
        ponteiro={'id':codigo,'pasta':dest.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(dest/'congelamento.json'),'manifesto_sha256':sha256(dest/'manifesto.json')}
        salvar(reg/'execucao.json',ponteiro)
        salvar(reg/'estado.json',{'utc':agora(),'situacao':'diagnostico_calculado_aguarda_revisao','execucao':ponteiro,'origem':ptr,'relatorio':'docs/diagnostico_operacional.md',**auditoria})
        print(json.dumps({'execucao':ponteiro,'auditoria':auditoria},ensure_ascii=False))
    except Exception:
        salvar(dest/'incidente.json',{'utc':agora(),'erro':traceback.format_exc()}); raise
