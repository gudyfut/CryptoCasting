"""Recalcula métricas e contrasta curvas arquivadas sem modificar a execução."""
import io
import json
from pathlib import Path
import zipfile
import numpy as np
from infraestrutura.artefatos import RAIZ, agora, conferir_arquivos, ler_json, salvar_json, sha256


def intervalo(diferencas, seed=20261113):
    x=np.asarray(diferencas,dtype=np.float64)
    if x.ndim==1:x=x[None,:];sortear=False
    else:sortear=True
    rng=np.random.default_rng(seed);n=x.shape[1];saida=[]
    for _ in range(2000):
        dias=(rng.integers(0,n-14+1,int(np.ceil(n/14)))[:,None]+np.arange(14)).ravel()[:n]
        seeds=rng.integers(0,len(x),len(x)) if sortear else np.arange(len(x))
        saida.append(float(x[seeds][:,dias].mean()))
    return {'media':float(x.mean()),'ic95':np.quantile(saida,[.025,.975]).tolist(),'bloco':14,'reamostra_seeds':sortear}


def principal():
    registro=RAIZ/'registros/lstm_diaria';ptr=ler_json(registro/'execucao.json');p=RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    f=ler_json(p/'congelamento.json');fecho=ler_json(p/'fechamento.json')
    assert fecho['situacao']=='concluido_controles_aprovados' and fecho['ajustes_cientificos']==12 and fecho['controles']==4
    assert fecho['resumo']['falhas_prudenciais']==0
    from .controles import conferir as conferir_controle
    for moeda in f['configuracao']['moedas']:conferir_controle(moeda)
    conferir_arquivos(p,fecho['arquivos']);conferir_arquivos(RAIZ,f['dependencias'])
    c=f['configuracao'];pub=p/'publicacao';pred=ler_json(pub/'previsao.json');ops=ler_json(pub/'operacoes.json')
    assert len(ops['carteiras'])==96 and not ops['falhas']
    p25=RAIZ/f['referencias']['referencia_2025']['pasta'];p26=RAIZ/f['referencias']['referencia_2026']['pasta']
    arima=RAIZ/f['referencias']['referencia_continuidade']['pasta']
    operacoes_continuidade=ler_json(arima/'resultados.json')['resultados']
    resultado={};n=0
    with zipfile.ZipFile(pub/'carteiras.zip') as novo,zipfile.ZipFile(p26/'carteiras.zip') as zip26:
        assert novo.testzip() is None
        for moeda in c['moedas']:
            resultado[moeda]={}
            assert ler_json(p/moeda/'controle.json')['aprovado']
            with zipfile.ZipFile(p25/moeda/'publicacao/carteiras.zip') as zip25:
                for ano in (2025,2026):
                    base=p25/moeda if ano==2025 else p26/moeda
                    with np.load(base/'dados/teste.npz' if ano==2025 else base/'entradas.npz',allow_pickle=False) as z:
                        y=z['y'].copy() if ano==2025 else z['alvo_retorno'].copy()
                        origens=z['origens_ms'].copy();ultimo=z['ultimo_close'].copy()
                    prev={}
                    for s in (*c['seeds'],'ensemble'):
                        nome=f'LSTM_{s}'
                        with np.load(pub/moeda/str(ano)/f'{nome}.npz',allow_pickle=False) as q:
                            np.testing.assert_array_equal(q['origens_ms'],origens);np.testing.assert_array_equal(q['alvo_retorno'],y)
                            prev[nome]=q['previsoes_retorno'].copy()
                        mse=float(np.mean((prev[nome]-y)**2));mae=float(np.mean(abs(prev[nome]-y)))
                        m=pred[moeda][str(ano)]['metricas'][nome]
                        np.testing.assert_allclose([m['mse_retorno'],m['mae_retorno']],[mse,mae],rtol=1e-12,atol=1e-15);n+=2
                    precos=np.mean([ultimo*(1+prev[f'LSTM_{s}']) for s in c['seeds']],axis=0)
                    np.testing.assert_array_equal(prev['LSTM_ensemble'],precos/ultimo-1)
                    basepred={}
                    for v in ('A','L','naive','linear'):
                        nomes=[f'{v}_{s}' for s in c['seeds']]+[f'{v}_ensemble'] if v in ('A','L') else [v]
                        for nome in nomes:
                            qpath=base/'publicacao/previsoes'/f'teste_{nome}.npz' if ano==2025 else base/f'{nome}.npz'
                            with np.load(qpath,allow_pickle=False) as q:
                                np.testing.assert_array_equal(q['origens_ms'],origens)
                                np.testing.assert_array_equal(q['alvo_retorno'],y)
                                basepred[nome]=q['previsoes_retorno'].copy()
                    comparacoes={}
                    for v in ('A','L','naive','linear'):
                        pares=np.array([(prev[f'LSTM_{s}']-y)**2-(basepred[f'{v}_{s}' if v in ('A','L') else v]-y)**2 for s in c['seeds']])
                        ref=basepred[f'{v}_ensemble' if v in ('A','L') else v]
                        comparacoes[v]=dict(media_seeds=intervalo(pares),ensemble=intervalo((prev['LSTM_ensemble']-y)**2-(ref-y)**2))
                    if ano==2025:
                        with np.load(arima/f'arima_{moeda}/teste.npz') as q:
                            np.testing.assert_array_equal(q['origens_ms'],origens)
                            basepred['arima']=q['previsoes_retorno'].copy()
                    referencia_ops=ler_json(p25/moeda/'publicacao/operacoes.json' if ano==2025 else p26/'operacoes.json')['carteiras']
                    zref=zip25 if ano==2025 else zip26
                    financeiro={}
                    for custo in (1,2,3):
                        curvas={};met={}
                        for nome in [f'LSTM_{s}' for s in c['seeds']]+['LSTM_ensemble']:
                            linha=next(q for q in ops['carteiras'] if q['moeda']==moeda and q['ano']==ano and q['unidade']==nome and q['custo']==custo)
                            with np.load(io.BytesIO(novo.read(linha['membro']+'/curva.npz')),allow_pickle=False) as q:
                                np.testing.assert_array_equal(q['origens_ms'],origens);curvas[nome]=q['saldos_diarios'].copy()
                            met[nome]=linha['metricas'];n+=1
                            np.testing.assert_allclose(curvas[nome][-1]/curvas[nome][0]-1,met[nome]['retorno_liquido'],atol=1e-12)
                        for v in ('A','L'):
                            for nome in [f'{v}_{s}' for s in c['seeds']]+[f'{v}_ensemble']:
                                linha=next(q for q in referencia_ops if q['unidade']==nome and q['custo']==custo and
                                           (q.get('fase')=='teste' if ano==2025 else q.get('moeda')==moeda))
                                with np.load(io.BytesIO(zref.read(linha['membro']+'/curva.npz')),allow_pickle=False) as q:
                                    np.testing.assert_array_equal(q['origens_ms'],origens);curvas[nome]=q['saldos_diarios'].copy()
                                met[nome]=linha['metricas']
                        financeiros={}
                        for v in ('A','L'):
                            individuos=np.array([np.diff(np.log(curvas[f'LSTM_{s}']))-np.diff(np.log(curvas[f'{v}_{s}'])) for s in c['seeds']])
                            ens=np.diff(np.log(curvas['LSTM_ensemble']))-np.diff(np.log(curvas[f'{v}_ensemble']))
                            financeiros[v]=dict(media_seeds=intervalo(individuos),ensemble=intervalo(ens))
                        referencias_extras={}
                        if ano==2025:
                            for nome in ('arima','naive','comprar_manter','sempre_comprado','sempre_vendido'):
                                modo='passivo' if nome=='comprar_manter' else 'liquida'
                                linha=next(q for q in operacoes_continuidade if q['moeda']==moeda and q['fase']=='teste' and
                                           q['unidade']==nome and q['custo']==custo and q['modo']==modo)
                                referencias_extras[nome]=linha['metricas']
                        else:
                            for nome in ('naive','linear','comprar_manter'):
                                linha=next(q for q in referencia_ops if q['moeda']==moeda and q['unidade']==nome and q['custo']==custo)
                                referencias_extras[nome]=linha['metricas']
                        financeiro[str(custo)]=dict(metricas=met,referencias_adicionais=referencias_extras,
                                                     contrastes_log_diario=financeiros)
                    resultado[moeda][str(ano)]=dict(n=len(y),comparacoes_mse=comparacoes,financeiro=financeiro,
                        mse_referencias={k:float(np.mean((v-y)**2)) for k,v in basepred.items()})
    recibo=dict(utc=agora(),situacao='conferencia_posterior_aprovada',execucao=ptr,metricas_e_saldos_recalculados=n,
                controles=4,carteiras=96,resultados=resultado,
                limite='Intervalos exploratórios em blocos e seeds, não independência do período ou equivalência. Auditoria de carteira por evento foi executada na publicação; esta leitura confere saldos finais e diferenças.')
    salvar_json(registro/'conferencia_posterior.json',recibo)
    print('CONFERENCIA_APROVADA',n,flush=True)


if __name__=='__main__':principal()
