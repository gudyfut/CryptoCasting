"""Métricas independentes recalculadas das previsões desnormalizadas."""
import math
import numpy as np
import pandas as pd
from infraestrutura.artefatos import ler_json,salvar_json,sha256,conferir_arquivos

def medir(y,p):
    y,p=np.asarray(y,float),np.asarray(p,float)
    assert y.ndim==1 and y.shape==p.shape and len(y)>0
    assert np.isfinite(y).all() and np.isfinite(p).all()
    e=p-y;mse=math.fsum(float(z)**2 for z in e)/len(e)
    mn=math.fsum(float(z)**2 for z in y)/len(y);an=float(np.abs(y).mean())
    assert mn>0 and an>0, 'Alvo degenerado.'
    corr=lambda a,b:float(np.corrcoef(a,b)[0,1]) if a.std()>1e-15 and b.std()>1e-15 else None
    rec={};prec={}
    for s,n in [(1,'alta'),(-1,'queda')]:
        rec[n]=float(np.mean(p[y*s>0]*s>0)) if (y*s>0).any() else None
        prec[n]=float(np.mean(y[p*s>0]*s>0)) if (p*s>0).any() else None
    grupos=[]
    if p.std()>1e-15:
        for ids in np.array_split(np.argsort(p,kind='stable'),min(5,len(y))):
            grupos.append({'n':len(ids),'previsto':float(p[ids].mean()),'observado':float(y[ids].mean())})
    return {'n':len(y),'mse':mse,'rmse':math.sqrt(mse),'mae':float(np.abs(e).mean()),'p95_erro_absoluto':float(np.quantile(np.abs(e),.95)),
        'mse_naive':mn,'mae_naive':an,'q_mse':mse/mn,'skill_percentual':100*(1-mse/mn),'q_mae':float(np.abs(e).mean())/an,
        'vies':float(e.mean()),'media_previsao':float(p.mean()),'media_alvo':float(y.mean()),'sd_previsao':float(p.std()),'sd_alvo':float(y.std()),
        'razao_sd':float(p.std()/y.std()) if y.std()>0 else None,'pearson':corr(y,p),
        'spearman':corr(pd.Series(y).rank().to_numpy(),pd.Series(p).rank().to_numpy()),
        'recall':rec,'precisao':prec,'balanced_accuracy':float(np.mean(list(rec.values()))) if all(v is not None for v in rec.values()) else None,
        'cobertura':float(np.mean(p!=0)),'fracao_positiva':float(np.mean(p>0)),'fracao_negativa':float(np.mean(p<0)),
        'quintis':grupos,'quintis_limite':'Ordenação descritiva; empates divididos estavelmente; constante sem quintis.'}

def avaliar(pasta,dados):
    r=ler_json(pasta/'resultado.json');conferir_arquivos(pasta,ler_json(pasta/'conclusao.json')['arquivos'])
    mediana=float(np.median(dados.y[dados.indices['treino']]))
    maioria=1 if np.mean(dados.y[dados.indices['treino']]>0)>=np.mean(dados.y[dados.indices['treino']]<0) else -1
    out={'partes':{},'constantes_treino':{'media':dados.ym,'mediana':mediana,'maioria_sinal':maioria}}
    for parte in dados.indices:
        if parte=='treino':continue
        d=pd.read_parquet(pasta/f'previsoes_{parte}.parquet');y=d.alvo.to_numpy();p=d.previsao.to_numpy()
        m=medir(y,p);np.testing.assert_allclose(m['mse'],r[parte]['mse'],rtol=1e-12,atol=1e-15)
        diario=d.loc[pd.DatetimeIndex(d.origem_utc).hour==0]
        out['partes'][parte]={'modelo':m,'diario_00utc':medir(diario.alvo,diario.previsao),
            'media_constante':medir(y,np.full(len(y),dados.ym)), 'mediana_constante':medir(y,np.full(len(y),mediana)),
            'naive':medir(y,np.zeros(len(y))),'maioria_treino_balanced_accuracy':medir(y,np.full(len(y),maioria))['balanced_accuracy']}
    salvar_json(pasta/'avaliacao.json',out)
    salvar_json(pasta/'manifesto_ajuste.json',{'conclusao_sha256':sha256(pasta/'conclusao.json'),'avaliacao_sha256':sha256(pasta/'avaliacao.json')})
    return out

def conferir_ajuste(pasta):
    m=ler_json(pasta/'manifesto_ajuste.json')
    assert sha256(pasta/'conclusao.json')==m['conclusao_sha256'] and sha256(pasta/'avaliacao.json')==m['avaliacao_sha256']
    conferir_arquivos(pasta,ler_json(pasta/'conclusao.json')['arquivos'])
    return ler_json(pasta/'resultado.json'),ler_json(pasta/'avaliacao.json')

def controle(a,b):
    ra,aa=conferir_ajuste(a);rb,ab=conferir_ajuste(b)
    assert ra['epoca']==rb['epoca']
    out={}
    for parte in aa['partes']:
        x=pd.read_parquet(a/f'previsoes_{parte}.parquet');y=pd.read_parquet(b/f'previsoes_{parte}.parquet')
        pd.testing.assert_frame_equal(x.drop(columns='previsao'),y.drop(columns='previsao'))
        d=float(np.max(np.abs(x.previsao-y.previsao)));assert d<=1e-5
        rel=abs(aa['partes'][parte]['modelo']['mse']-ab['partes'][parte]['modelo']['mse'])/aa['partes'][parte]['modelo']['mse'];assert rel<=1e-4
        out[parte]={'maxima_diferenca':d,'diferenca_relativa_mse':rel}
    return {'mesma_epoca':True,'partes':out}
