"""Confere previsões, controles, saldos e abrangência da execução encerrada."""
import io
import zipfile
import numpy as np
from infraestrutura.artefatos import RAIZ, agora, conferir_arquivos, ler_json, salvar_json, sha256


def intervalo(diferencas):
    x=np.asarray(diferencas,dtype=np.float64)
    individual=x.ndim==2
    if not individual:x=x[None,:]
    rng=np.random.default_rng(20261113);n=x.shape[1];replicas=[]
    for _ in range(2000):
        dias=(rng.integers(0,n-13,int(np.ceil(n/14)))[:,None]+np.arange(14)).ravel()[:n]
        seeds=rng.integers(0,len(x),len(x)) if individual else np.arange(len(x))
        replicas.append(float(x[seeds][:,dias].mean()))
    return dict(media=float(x.mean()),ic95=np.quantile(replicas,[.025,.975]).tolist(),
                bloco=14,reamostra_seeds=individual)


def principal():
    reg=RAIZ/'registros/walkforward_diario';ptr=ler_json(reg/'execucao.json');p=RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    f=ler_json(p/'congelamento.json');fecho=ler_json(p/'fechamento.json');c=f['configuracao']
    assert fecho['situacao']=='concluido_controles_aprovados'
    assert fecho['ajustes_cientificos']==24 and fecho['controles']==2
    assert fecho['resumo']['falhas_prudenciais']==0
    conferir_arquivos(p,fecho['arquivos']);conferir_arquivos(RAIZ,f['referencias']['arquivos'])
    pub=p/'publicacao';pre=ler_json(pub/'previsao.json');ops=ler_json(pub/'operacoes.json')
    assert len(ops['carteiras'])==108 and not ops['falhas']
    for v in ('A','L'):assert ler_json(p/'B1'/f'controle_{v}.json')['aprovado']
    resumo={};n=0
    with zipfile.ZipFile(pub/'carteiras.zip') as pacote:
        assert pacote.testzip() is None
        for bloco in c['blocos']:
            b=bloco['id'];resumo[b]={}
            with np.load(p/b/'dados/teste.npz',allow_pickle=False) as z:
                y=z['y'].copy();origens=z['origens_ms'].copy();ultimo=z['ultimo_close'].copy()
            curvas={}
            for v in c['variantes']:
                mse=[];precos=[]
                for seed in c['seeds']:
                    nome=f'{v}_{seed}'
                    with np.load(pub/b/'previsoes'/f'{nome}.npz',allow_pickle=False) as q:
                        np.testing.assert_array_equal(q['origens_ms'],origens);np.testing.assert_array_equal(q['alvo_retorno'],y)
                        valor=float(np.mean((q['previsoes_retorno']-y)**2));precos.append(q['previsoes'].copy())
                    np.testing.assert_allclose(valor,pre[b]['metricas'][nome]['mse_retorno'],atol=1e-15,rtol=1e-12)
                    mse.append(valor);n+=1
                with np.load(pub/b/'previsoes'/f'{v}_ensemble.npz',allow_pickle=False) as q:
                    np.testing.assert_array_equal(q['previsoes'],np.mean(precos,axis=0))
                    emse=float(np.mean((q['previsoes_retorno']-y)**2))
                    np.testing.assert_allclose(emse,pre[b]['metricas'][f'{v}_ensemble']['mse_retorno'],atol=1e-15,rtol=1e-12)
                linhas={}
                for nome in [f'{v}_{s}' for s in c['seeds']]+[f'{v}_ensemble']:
                    linha=next(x for x in ops['carteiras'] if x['bloco']==b and x['unidade']==nome and x['custo']==1)
                    with np.load(io.BytesIO(pacote.read(linha['membro']+'/curva.npz')),allow_pickle=False) as q:
                        np.testing.assert_array_equal(q['origens_ms'],origens)
                        np.testing.assert_allclose(q['saldos_diarios'][-1]/q['saldos_diarios'][0]-1,
                                                   linha['metricas']['retorno_liquido'],atol=1e-12)
                        curvas[nome]=q['saldos_diarios'].copy()
                    linhas[nome]=linha['metricas'];n+=1
                resumo[b][v]=dict(mse_medio=float(np.mean(mse)),mse_ensemble=emse,
                                  retorno_medio=float(np.mean([linhas[f'{v}_{s}']['retorno_liquido'] for s in c['seeds']])),
                                  retorno_ensemble=linhas[f'{v}_ensemble']['retorno_liquido'],
                                  drawdown_ensemble=linhas[f'{v}_ensemble']['drawdown_maximo'])
            resumo[b]['naive_mse']=float(np.mean(y*y));resumo[b]['origens']=len(y)
            diarias=np.array([np.diff(np.log(curvas[f'A_{s}']))-np.diff(np.log(curvas[f'L_{s}'])) for s in c['seeds']])
            ensemble=np.diff(np.log(curvas['A_ensemble']))-np.diff(np.log(curvas['L_ensemble']))
            resumo[b]['contraste_log_A_menos_L']=dict(media_seeds=intervalo(diarias),ensemble=intervalo(ensemble))
    salvar_json(reg/'conferencia_posterior.json',dict(utc=agora(),situacao='conferencia_posterior_aprovada',execucao=ptr,
                verificacoes=n,controles=2,carteiras=108,resumo=resumo,
                limite='Conferência das métricas principais e saldos; auditoria por evento está na publicação. Períodos retrospectivos.'))
    print('CONFERENCIA_APROVADA',n,flush=True)


if __name__=='__main__':principal()
