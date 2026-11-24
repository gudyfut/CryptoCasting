"""Conferência posterior de leitura. Nunca treina, simula ou sobrescreve publicação."""
from pathlib import Path
import math
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, sha256, agora, conferir_arquivos


def diario(operacoes, marca, inicio, fim):
    saldos=[10000.]
    for limite in range(inicio+86400000,fim+1,86400000):
        saldo=10000.
        for t in operacoes:
            if t['entrada_ms']>=limite:break
            if t['saida_ms']<limite:
                saldo=t['caixa_depois']
            else:
                q=t['quantidade'];entrada=t['preco_entrada']
                saldo=t['caixa_antes']-.0005*q*entrada
                saldo+=q*math.fsum(e['por_btc'] for e in t['eventos_funding'] if e['utc_ms']<limite)
                saldo+=t['lado']*q*(float(marca.loc[limite-60000])-entrada)
                break
        saldos.append(saldo)
    return np.array(saldos)


def incerteza_retornos(pares,dias,replicas=2000):
    rng=np.random.default_rng(1205);deltas=[]
    for _ in range(replicas):
        sementes=rng.integers(0,3,3);recortes=[]
        for a,b in pares:
            n=a.shape[1];k=min(dias,n)
            ix=(rng.integers(0,n-k+1,int(np.ceil(n/k)))[:,None]+np.arange(k)).ravel()[:n]
            recortes.append(np.mean(np.expm1(b[sementes][:,ix].sum(axis=1))-np.expm1(a[sementes][:,ix].sum(axis=1))))
        deltas.append(np.mean(recortes))
    return {'ic95_pp':(100*np.quantile(deltas,[.025,.975])).tolist(),'replicas':replicas,'bloco_dias':dias,
            'nota':'Diagnóstico posterior da média das carteiras/seeds; bootstrap pareado de seeds/dias; não corrige a exploração histórica.'}


def executar():
    reg=RAIZ/'registros/historico_treino';ptr=ler_json(reg/'execucao.json');p=RAIZ/ptr['pasta'];pub=p/'publicacao'
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    recibo=ler_json(reg/'fechamento.json');assert sha256(RAIZ/recibo['arquivo'])==recibo['sha256']
    freeze=ler_json(p/'congelamento.json');fecho=ler_json(p/'fechamento.json')
    fontes=freeze['fontes'];conferir_arquivos(RAIZ,fontes);conferir_arquivos(p/'fontes',fontes)
    conferir_arquivos(p,fecho['arquivos']);conferir_arquivos(RAIZ,freeze['preservacao'])
    assert not ler_json(p/'processo.json')['ativo']
    jobs=ler_json(p/'ajustes.json');assert len(jobs)==20 and all(j['status']=='concluido' for j in jobs)
    principais=[j for j in jobs if not j['controle']];assert len(principais)==18
    assert len({(j['braco'],j['recorte']['id'],j['seed']) for j in principais})==18
    assert all(ler_json(p/('controle_'+b+'.json'))['aprovado'] for b in ('acumulado','movel12'))
    previsao=[];populacoes={}
    for j in principais:
        a=RAIZ/j['pasta']/'ajuste';z=np.load(a/'comparacao.npz');y=z['alvos'];pred=z['previsoes']
        metricas={'mse':float(np.mean((pred-y)**2)),'mae':float(np.mean(abs(pred-y))),
                  'mse_zero':float(np.mean(y*y)),
                  'mse_media_t':float(np.mean((y-np.array(ler_json(a/'escalas.json')['media_alvo']))**2))}
        antigo=ler_json(a/'conclusao.json');assert antigo['recarga_exata']
        for k in ('mse','mae'):np.testing.assert_allclose(metricas[k],antigo['metricas']['comparacao'][k],rtol=1e-12)
        chave=(j['recorte']['id'],j['seed'])
        if chave in populacoes:
            for k in ('alvos','origens_ms'):np.testing.assert_array_equal(z[k],populacoes[chave][k])
        else:populacoes[chave]={k:z[k] for k in ('alvos','origens_ms')}
        previsao.append({'braco':j['braco'],'recorte':j['recorte']['id'],'seed':j['seed'],**metricas,
                         'epoca':antigo['epoca'],'epocas_executadas':antigo['epocas_executadas'],'segundos':antigo['segundos']})
    curvas=list(pub.rglob('curva.npz'));assert len(curvas)==456
    residuo=0.
    for arquivo in curvas:
        r=ler_json(arquivo.parent/'resultado.json');e=np.load(arquivo)['patrimonio'];saldo=10000.
        for t in r['operacoes']:
            q=t['quantidade'];pe=t['preco_entrada'];ps=t['preco_saida']
            liquido=q*(t['lado']*(ps-pe)-.0005*(pe+ps)+math.fsum(ev['por_btc'] for ev in t['eventos_funding']))
            residuo=max(residuo,abs(saldo-t['caixa_antes']),abs(liquido-t['pnl_liquido']))
            saldo+=liquido
            residuo=max(residuo,abs(saldo-t['caixa_depois']))
        residuo=max(residuo,abs(saldo-e[-1]),abs(saldo-r['metricas']['capital_final']))
        np.testing.assert_allclose(r['metricas']['retorno_liquido'],e[-1]/e[0]-1,rtol=0,atol=1e-12)
        np.testing.assert_allclose(r['metricas']['drawdown_maximo'],np.max(1-e/np.maximum.accumulate(e)),rtol=0,atol=1e-12)
    assert residuo<1e-7
    fixas=ler_json(pub/'carteiras_fixas.json');sel=ler_json(pub/'carteiras_selecionadas_C.json')
    base=[x for x in fixas if x['unidade'].isdigit() and x['cenario']=='base'];assert len(base)==18
    por_recorte=[];por_seed=[]
    for campo,saida in [('recorte',por_recorte),('seed',por_seed)]:
        for valor in sorted({v[campo] for v in previsao},key=str):
            for braco in ('acumulado','movel12'):
                pp=[v for v in previsao if v[campo]==valor and v['braco']==braco]
                oo=[v['metricas'] for v in base if v['braco']==braco and
                    (v['recorte']==valor if campo=='recorte' else v['unidade']==str(valor))]
                saida.append({campo:valor,'braco':braco,'mse':float(np.mean([v['mse'] for v in pp])),
                              'retorno':float(np.mean([v['retorno_liquido'] for v in oo])),
                              'drawdown':float(np.mean([v['drawdown_maximo'] for v in oo]))})
    mercado=RAIZ/freeze['dados']['pasta']
    mani=ler_json(mercado/'manifesto.json');assert sha256(mercado/'markPriceKlines.parquet')==mani['arquivos']['markPriceKlines.parquet']
    marca=pd.read_parquet(mercado/'markPriceKlines.parquet',columns=['open_time','close']).set_index('open_time')['close']
    partes=[]
    for rec in freeze['configuracao']['recortes']:
        inicio,fim=[int(pd.Timestamp(v,tz='UTC').timestamp()*1000) for v in rec['comparacao']];par=[]
        for braco in ('acumulado','movel12'):
            series=[]
            for seed in freeze['configuracao']['seeds']:
                v=next(x for x in base if x['braco']==braco and x['recorte']==rec['id'] and x['unidade']==str(seed))
                r=ler_json(RAIZ/v['pasta']/'resultado.json');equity=diario(r['operacoes'],marca,inicio,fim)
                assert (equity>0).all();np.testing.assert_allclose(equity[-1],r['metricas']['capital_final'],rtol=0,atol=1e-7)
                series.append(np.diff(np.log(equity)))
            par.append(np.array(series))
        partes.append(par)
    resumo=ler_json(pub/'resumo.json')
    for braco in ('acumulado','movel12'):
        for k in ('mse','mae'):
            np.testing.assert_allclose(np.mean([v[k] for v in previsao if v['braco']==braco]),resumo['resumos'][braco][k+'_media_seeds_recortes'],rtol=1e-12)
    documento={'utc':agora(),'situacao':'conferido','execucao':ptr,'arquivos_fechamento':len(fecho['arquivos']),
       'arquivos_preservados':len(freeze['preservacao']),'fontes':len(fontes),'principais':18,'controles':2,'carteiras':456,
       'residuo_contabil_maximo_usdt':residuo,'previsao':previsao,'por_recorte':por_recorte,'por_seed':por_seed,
       'incerteza_delta_retorno_medio_seeds_pp':{str(n):incerteza_retornos(partes,n) for n in (7,14,28)},
       'politica_calibrada_operacoes_S':sum(x['metricas']['operacoes'] for x in sel),
       'novos_treinos':0,'novas_simulacoes':0,'codigo_sha256':sha256(__file__)}
    destino=reg/'conferencias'/agora().replace(':','').replace('+','_');destino.mkdir(parents=True,exist_ok=False)
    salvar_json(destino/'conferencia.json',documento)
    print({'situacao':'conferido','recibo':str((destino/'conferencia.json').relative_to(RAIZ)),
           'incerteza_retornos':documento['incerteza_delta_retorno_medio_seeds_pp'],'residuo':residuo},flush=True)


if __name__=='__main__':executar()
