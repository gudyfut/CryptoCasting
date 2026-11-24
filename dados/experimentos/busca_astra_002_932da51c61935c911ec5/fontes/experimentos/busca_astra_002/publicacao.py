"""Avaliação posterior: sem treinador ou proponente, carteiras F03 congeladas."""
import itertools
import math
import time
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,agora,conferir_arquivos
from .contrato import FINAIS,SEEDS,ancoras
from .metricas import medir,conferir_ajuste

def media(rs):
    campos=['mse','rmse','mae','q_mse','skill_percentual','q_mae','p95_erro_absoluto','vies','pearson','spearman','balanced_accuracy','cobertura','fracao_positiva','fracao_negativa','razao_sd']
    out={k:float(np.mean([r[k] for r in rs])) if all(r[k] is not None for r in rs) else None for k in campos}
    for k in ['recall','precisao']:
        out[k]={s:float(np.mean([r[k][s] for r in rs])) if all(r[k][s] is not None for r in rs) else None for s in ['alta','queda']}
    out['n_avaliacoes']=len(rs)
    return out

def intervalo(blocos,base,replicas=2000):
    diarios=[];pontos=[]
    for b,q in blocos.items():
        dif=q['candidata']-q[base];pontos.append(float(dif.mean()))
        t=q['origens'];contagens=pd.Series(1,index=t).resample('D').sum()
        assert (contagens==24).all(), 'Bootstrap requer dias completos e alinhados.'
        soma=np.stack([pd.Series(v,index=t).resample('D').sum().to_numpy() for v in dif])
        diarios.append(soma/24)
    ints={}
    for largura in [7,14,28]:
        rng=np.random.default_rng(20261104+largura);amostras=[]
        for _ in range(replicas):
            seeds=rng.integers(0,diarios[0].shape[0],diarios[0].shape[0]);valores=[]
            for d in diarios:
                n=d.shape[1];w=min(largura,n)
                # Blocos móveis sem ligar artificialmente fim e início do semestre.
                ini=rng.integers(0,n-w+1,math.ceil(n/w));ix=(ini[:,None]+np.arange(w)).ravel()[:n]
                valores.append(float(d[seeds][:,ix].mean()))
            amostras.append(float(np.mean(valores)))
        ints[str(largura)]={'ic95':np.quantile(amostras,[.025,.975]).tolist(),
            'ic98_333_bonferroni_tres':np.quantile(amostras,[.05/6,1-.05/6]).tolist()}
    return {'diferenca_mse':float(np.mean(pontos)),'intervalos':ints,'replicas':replicas,
        'limite':'Condicional à seleção e aos períodos retrospectivos; não elimina toda a seleção adaptativa.'}

def publicar(p,prazo):
    assert not (p/'publicacao.json').exists()
    dest=p/'publicacao';dest.mkdir(exist_ok=False)
    variantes=['candidata',*ancoras()];metricas={};previsoes={};perdas={};celulas={}
    for b in FINAIS:
        observado=None;perdas[b]={};metricas[b]={}
        for v in variantes:
            ms=[];es=[]
            for s in SEEDS:
                pasta=p/'final'/v/f'{b}_{s}';r,a=conferir_ajuste(pasta)
                q=pd.read_parquet(pasta/'previsoes_teste.parquet')
                if observado is None:observado=q.drop(columns='previsao')
                else:pd.testing.assert_frame_equal(observado,q.drop(columns='previsao'))
                m=medir(q.alvo,q.previsao);np.testing.assert_allclose(m['mse'],r['teste']['mse'],rtol=1e-12,atol=1e-15)
                # Seleção auditada sem inferir correção apenas da presença de checkpoint.
                ep=ler_json(pasta/'epocas.json');sel=ler_json(pasta/'selecao.json')
                assert min(ep,key=lambda x:(x['mse_validacao'],x['epoca']))['epoca']==sel['epoca']==r['epoca']
                assert r['recarga_exata'] and r['seed']==s and r['bloco']==b
                celulas[f'{b}/{v}/{s}']={'metricas':m,'diario_00utc':a['partes']['teste']['diario_00utc'],
                    'epoca':r['epoca'],'parametros':r['parametros'],'manifesto_sha256':sha256(pasta/'manifesto_ajuste.json')}
                ms.append(m);es.append((q.previsao-q.alvo).to_numpy()**2);previsoes[b,v,s]=q
            metricas[b][v]=media(ms);perdas[b][v]=np.stack(es)
        perdas[b]['origens']=pd.DatetimeIndex(observado.origem_utc)
        perdas[b]['naive']=np.tile(observado.alvo.to_numpy()**2,(8,1))
        metricas[b]['naive']=medir(observado.alvo,np.zeros(len(observado)))
    globais={v:media([celulas[f'{b}/{v}/{s}']['metricas'] for b in FINAIS for s in SEEDS]) for v in variantes}
    globais['naive']=media([metricas[b]['naive'] for b in FINAIS])
    por_seed={v:{str(s):media([celulas[f'{b}/{v}/{s}']['metricas'] for b in FINAIS]) for s in SEEDS} for v in variantes}
    assert len(celulas)==96
    resultado={'utc':agora(),'celulas':celulas,'por_bloco':metricas,'medias':globais,'por_seed':por_seed,
        'contrastes':{base:intervalo(perdas,base) for base in [*ancoras(),'naive']},'natureza':'retrospectiva',
        'limites':['Busca adaptativa; oito seeds não garantem certeza.','Média de modelos individuais, não ensemble.',
                  'Carteiras reiniciam por bloco; não compor retornos entre blocos.','Lucro retrospectivo não demonstra lucro futuro.']}
    salvar_json(dest/'previsao.json',resultado)
    from simulacao_operacoes.previsoes import COLUNAS,diarias
    from simulacao_operacoes.smart.mercado import carregar
    from simulacao_operacoes.revisada.simulador import simular
    from simulacao_operacoes.revisada.auditoria import conferir
    f=ler_json(p/'congelamento.json');fp=RAIZ/f['operacional']['pasta']
    assert sha256(fp/'congelamento.json')==f['operacional']['congelamento_sha256']
    of=ler_json(fp/'congelamento.json')['assinatura'];conferir_arquivos(RAIZ,of['fontes'])
    cfg=of['configuracao'];mercados=carregar(of['spot'],of['futuros'])
    series={k:diarias(q[COLUNAS]) for k,q in previsoes.items()}
    grade=[]
    for (b,v,s),pol,br,custo in itertools.product(series,['smart','direcional_filtrada'],['spot','futuro_bilateral'],['base','estresse']):
        grade.append((b,v,s,pol,br,custo,None))
    for b,v,br,custo in itertools.product(FINAIS,['caixa','comprar_manter'],['spot','futuro_bilateral'],['base','estresse']):
        grade.append((b,v,None,'smart',br,custo,v))
    assert len(grade)==800
    resumos=[];manifestos={}
    for i,(b,v,s,pol,br,custo,bench) in enumerate(grade,1):
        if time.time()>=prazo:raise TimeoutError('Prazo global interrompeu publicação; preservar parcial sem concluir.')
        d=dest/'carteiras'/b/v/str(s)/pol/br/custo;d.mkdir(parents=True,exist_ok=False)
        serie=series[b,'candidata',42] if bench else series[b,v,s]
        mercado=mercados['spot' if br=='spot' else 'futuro']
        r,o,e,c,di=simular(serie,mercado,cfg,pol,br,custo,bench)
        aud=conferir(r,o,e,mercado,cfg,serie)
        for n,z in [('resumo',r),('ordens',o),('funding',e),('diarios',di),('auditoria',aud)]:salvar_json(d/(n+'.json'),z)
        c.to_parquet(d/'curva.parquet',index=False)
        m={z.name:sha256(z) for z in d.iterdir() if z.is_file()};salvar_json(d/'manifesto.json',{'arquivos':m});conferir_arquivos(d,m)
        manifestos[(d/'manifesto.json').relative_to(dest).as_posix()]=sha256(d/'manifesto.json')
        resumos.append({'bloco':b,'modelo':v,'seed':s,**r,'componentes':aud['decomposicao_futuros']})
        if i%10==0:salvar_json(p/'progresso_publicacao.json',{'utc':agora(),'carteiras_concluidas':i,'total':800})
    campos=['retorno_liquido','drawdown','giro','exposicao_media','exposicao_vendida','comissoes','slippage','funding']
    agregados={}
    for v,pol,br,custo in itertools.product([*variantes,'caixa','comprar_manter'],['smart','direcional_filtrada'],['spot','futuro_bilateral'],['base','estresse']):
        rs=[r for r in resumos if (r['modelo'],r['politica'],r['braco'],r['cenario'])==(v,pol,br,custo)]
        if not rs:continue
        agregados['/'.join([v,pol,br,custo])]={'n':len(rs),**{k:{'media':float(np.mean([r[k] for r in rs])),
            'minimo':float(min(r[k] for r in rs)),'maximo':float(max(r[k] for r in rs))} for k in campos}}
    salvar_json(dest/'operacao.json',{'carteiras':resumos,'medias_e_amplitudes':agregados,'quantidade':800,'politica_f03_congelada':f['operacional']})
    resultado['operacao_arquivo']='operacao.json';salvar_json(dest/'resultados.json',resultado)
    manifesto={'arquivos':{z.name:sha256(z) for z in dest.iterdir() if z.is_file()},'carteiras':manifestos}
    salvar_json(dest/'manifesto.json',manifesto);conferir_arquivos(dest,manifesto['arquivos']);conferir_arquivos(dest,manifestos)
    salvar_json(p/'publicacao.json',{'utc':agora(),'pasta':dest.relative_to(RAIZ).as_posix(),'manifesto_sha256':sha256(dest/'manifesto.json'),'ajustes_principais':96,'carteiras':800})
    return resultado
