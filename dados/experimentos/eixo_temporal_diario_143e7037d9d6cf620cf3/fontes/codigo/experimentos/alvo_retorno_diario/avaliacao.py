"""Publicação posterior aos controles/treinos; previsões e carteiras separadas."""
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,agora
from simulacao_operacoes.diaria_24h import simular,conferir


def carregar_mercado(ptr):
    p=RAIZ/ptr['pasta'];assert sha256(p/'manifesto.json')==ptr['manifesto_sha256']
    k=pd.read_parquet(p/'klines.parquet');m=pd.read_parquet(p/'markPriceKlines.parquet');f=pd.read_parquet(p/'funding.parquet')
    np.testing.assert_array_equal(k.open_time,m.open_time)
    assert np.all(np.diff(k.open_time)==60000) and f.fundingTime.is_unique
    assert np.isfinite(f[['fundingRate','markPrice']].to_numpy()).all() and (f.markPrice>0).all()
    cols=['open','high','low','close']
    return {'tempo':k.open_time.to_numpy(np.int64),'negocio':k[cols].to_numpy(float),'marca':m[cols].to_numpy(float),
            'funding_tempo':f.fundingTime.to_numpy(np.int64),'funding_taxa':f.fundingRate.to_numpy(float),'funding_preco':f.markPrice.to_numpy(float)}


def bootstrap(y,previsoes,ultimo,saldos,bloco):
    rng=np.random.default_rng(3105);n=len(y);delta=[];crescimento=[]
    erro=(previsoes-y[None,:])**2;erro_naive=(ultimo-y)**2;logs=np.diff(np.log(saldos),axis=1)
    for _ in range(2000):
        seeds=rng.integers(0,3,3)
        ix=(rng.integers(0,n-bloco+1,int(np.ceil(n/bloco)))[:,None]+np.arange(bloco)).ravel()[:n]
        delta.append(float(np.mean(erro[seeds][:,ix]-erro_naive[ix])))
        crescimento.append(float(np.mean(logs[seeds][:,ix])))
    return {'bloco_dias':bloco,'replicas':2000,'ic95_delta_mse_vs_naive_usdt2':np.quantile(delta,[.025,.975]).tolist(),
            'ic95_crescimento_log_diario':np.quantile(crescimento,[.025,.975]).tolist(),
            'limite':'Exploratório; três seeds e um ano retrospectivo; não corrige buscas anteriores.'}


def executar(p,c,dados,mercado_ptr):
    from .treinamento import carregar_rede,inferir
    from .metricas import avaliar_precos as metricas
    from .entradas import preco_equivalente,publicar_previsoes
    import torch
    pub=p/'publicacao';pub.mkdir(exist_ok=False)
    preds={f:[] for f in ('validacao','teste')};linhas=[]
    for seed in c['seeds']:
        d=p/'ajustes'/f'seed_{seed}';rede=carregar_rede(d,c)
        for fase in preds:
            z=dados[fase];ret=inferir(rede,z['x']);v=preco_equivalente(ret,z['ultimo_close']);preds[fase].append(v)
            if fase=='validacao':np.testing.assert_array_equal(ret,np.load(d/'validacao.npz')['previsoes'])
            arq=pub/'previsoes'/f'{fase}_{seed}.npz';arq.parent.mkdir(exist_ok=True)
            np.savez_compressed(arq,**publicar_previsoes(z,ret))
            linhas.append({'fase':fase,'seed':seed,'metricas':metricas(z['preco_alvo'],v,z['ultimo_close'])})
        del rede;torch.cuda.empty_cache()
    salvar_json(pub/'previsao.json',linhas)
    m=carregar_mercado(mercado_ptr);carteiras=[];resumo={}
    for fase,vs in preds.items():
        z=dados[fase];v=np.array(vs);unidades={str(s):(v[i],None) for i,s in enumerate(c['seeds'])}
        unidades.update(ensemble=(v.mean(axis=0),None),naive=(z['ultimo_close'],None),sempre_comprado=(z['ultimo_close'],1),sempre_vendido=(z['ultimo_close'],-1))
        saldos=[]
        for nome,(prev,forcar) in unidades.items():
            for cen,params in c['cenarios'].items():
                r,curvas=simular(z['origens_ms'],prev,z['ultimo_close'],m,c['operacoes'],params,forcar)
                conferir(r,curvas,c['operacoes']);dest=pub/'carteiras'/fase/nome/cen;dest.mkdir(parents=True)
                salvar_json(dest/'resultado.json',r);np.savez_compressed(dest/'curva.npz',**curvas)
                carteiras.append({'fase':fase,'unidade':nome,'cenario':cen,'pasta':dest.relative_to(RAIZ).as_posix(),'metricas':r['metricas']})
                if nome.isdigit() and cen=='base':saldos.append(curvas['saldos_diarios'])
                salvar_json(pub/'progresso.json',{'utc':agora(),'carteiras':len(carteiras),'total':70})
                del curvas
        principais=[l['metricas'] for l in linhas if l['fase']==fase]
        oper=[l['metricas'] for l in carteiras if l['fase']==fase and l['unidade'].isdigit() and l['cenario']=='base']
        resumo[fase]={'previsao_media_seeds':{k:float(np.mean([a[k] for a in principais])) for k in principais[0] if all(a[k] is not None for a in principais)},
             'operacao_media_seeds_base':{k:float(np.mean([a[k] for a in oper])) for k in oper[0] if all(a[k] is not None for a in oper)},
             'naive':metricas(z['preco_alvo'],z['ultimo_close'],z['ultimo_close']),
             'ensemble':metricas(z['preco_alvo'],v.mean(axis=0),z['ultimo_close']),
             'incerteza':{str(b):bootstrap(z['preco_alvo'],v,z['ultimo_close'],np.array(saldos),b) for b in (7,14,28)}}
    assert len(carteiras)==c['carteiras_previstas']
    salvar_json(pub/'carteiras.json',carteiras);salvar_json(pub/'resumo.json',{'utc':agora(),'resumos':resumo,'carteiras':len(carteiras),
        'seeds':c['seeds'],'media_individual_nao_ensemble':True,'teste_retrospectivo':True,'promocao_automatica':False})
    from .comparacao import executar as comparar
    comparar(p,c)
    return resumo
