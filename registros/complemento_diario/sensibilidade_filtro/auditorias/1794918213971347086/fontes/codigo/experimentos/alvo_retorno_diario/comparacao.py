"""Contraste pareado com referência preservada; não reexecuta treino/backtest antigo."""
import numpy as np
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256
from .metricas import avaliar_precos


def executar(p,c):
    f=ler_json(p/'congelamento.json');ant=RAIZ/f['antecessora']['pasta'];res={}
    assert f['antecessora']['id']==c['antecessora']
    for fase in ('validacao','teste'):
        linhas=[];erros=[];logs=[]
        for seed in c['seeds']:
            a=np.load(ant/'publicacao/previsoes'/f'{fase}_{seed}.npz')
            b=np.load(p/'publicacao/previsoes'/f'{fase}_{seed}.npz')
            for k in ('y','ultimo_close','origens_ms','fim_alvo_ms'):np.testing.assert_array_equal(a[k],b[k])
            y=b['y'];u=b['ultimo_close'];ma=avaliar_precos(y,a['previsoes'],u);mb=avaliar_precos(y,b['previsoes'],u)
            pa=ant/'publicacao/carteiras'/fase/str(seed)/'base';pb=p/'publicacao/carteiras'/fase/str(seed)/'base'
            oa=ler_json(pa/'resultado.json')['metricas'];ob=ler_json(pb/'resultado.json')['metricas']
            erros.append(((b['previsoes']-y)/u)**2-((a['previsoes']-y)/u)**2)
            logs.append(np.diff(np.log(np.load(pb/'curva.npz')['saldos_diarios']))-np.diff(np.log(np.load(pa/'curva.npz')['saldos_diarios'])))
            linhas.append({'seed':seed,'preco':ma,'retorno':mb,'operacao_preco':oa,'operacao_retorno':ob})
        cis={};erros=np.asarray(erros);logs=np.asarray(logs);n=erros.shape[1]
        for bloco in (7,14,28):
            rng=np.random.default_rng(3105);deltas=[]
            for _ in range(2000):
                seeds=rng.integers(0,3,3);ix=(rng.integers(0,n-bloco+1,int(np.ceil(n/bloco)))[:,None]+np.arange(bloco)).ravel()[:n]
                deltas.append([float(erros[seeds][:,ix].mean()),float(logs[seeds][:,ix].mean())])
            cis[str(bloco)]={'delta_mse_retorno_ic95':np.quantile(np.array(deltas)[:,0],[.025,.975]).tolist(),
                             'delta_crescimento_log_ic95':np.quantile(np.array(deltas)[:,1],[.025,.975]).tolist()}
        medias={}
        for campo in ('preco','retorno','operacao_preco','operacao_retorno'):
            medias[campo]={k:float(np.mean([l[campo][k] for l in linhas])) for k in linhas[0][campo] if all(l[campo][k] is not None for l in linhas)}
        res[fase]={'seeds_pareadas':linhas,'medias':medias,'incerteza':cis}
        for nome in ('naive','sempre_comprado','sempre_vendido'):
            for cen in c['cenarios']:
                np.testing.assert_array_equal(np.load(ant/'publicacao/carteiras'/fase/nome/cen/'curva.npz')['saldos_diarios'],
                                              np.load(p/'publicacao/carteiras'/fase/nome/cen/'curva.npz')['saldos_diarios'])
    salvar_json(p/'publicacao/comparacao.json',{'referencia':f['antecessora'],'contraste':'novo alvo retorno menos alvo preço',
        'fases':res,'herdados_nao_contam_novos':True,'baselines_operacionais_identicas':True,
        'limites':'Três seeds, mesmos dias retrospectivos; não corrige busca histórica nem certifica lucro futuro.'})
