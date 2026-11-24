"""Contrastes pareados; finanças da referência vêm da releitura vigente."""
import json
import sqlite3
from zipfile import ZipFile
import numpy as np
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, sha256
from experimentos.alvo_retorno_diario.metricas import avaliar_precos


def intervalos(erros, logs, blocos=(7,14,28), replicas=2000):
    erros, logs = np.asarray(erros), np.asarray(logs)
    if erros.ndim!=2 or erros.shape!=logs.shape or not np.isfinite(erros).all() or not np.isfinite(logs).all():
        raise ValueError('Contrastes sem pareamento ou não finitos.')
    ns,n=erros.shape; resultado={}
    for bloco in blocos:
        if not 1<=bloco<=n: raise ValueError('Bloco inválido.')
        rng=np.random.default_rng(3105); deltas=[]
        for _ in range(replicas):
            seeds=rng.integers(0,ns,ns)
            ix=(rng.integers(0,n-bloco+1,int(np.ceil(n/bloco)))[:,None]+np.arange(bloco)).ravel()[:n]
            deltas.append([float(erros[seeds][:,ix].mean()),float(logs[seeds][:,ix].mean())])
        resultado[str(bloco)]={'replicas':replicas,'delta_mse_retorno_ic95':np.quantile(np.array(deltas)[:,0],[.025,.975]).tolist(),
                              'delta_crescimento_log_ic95':np.quantile(np.array(deltas)[:,1],[.025,.975]).tolist()}
    return resultado


def carteira_vigente(custos, fonte):
    p=RAIZ/custos['pasta']
    # Somente leitura: uma consulta não cria SQLite ausente.
    with sqlite3.connect((p/'carteiras.sqlite').resolve().as_uri()+'?mode=ro', uri=True) as banco:
        r=banco.execute('SELECT sha256,chave,resumo FROM carteiras WHERE fonte=?',(fonte,)).fetchone()
        if r is None: raise ValueError('Carteira ausente na releitura vigente: '+fonte)
        assert sha256(RAIZ/fonte)==r[0]
        nome=banco.execute('SELECT ledger FROM cache WHERE chave=?',(r[1],)).fetchone()[0]
    with ZipFile(p/'ledgers.zip') as z: ledger=json.loads(z.read(nome))
    return json.loads(r[2]), ledger


def medias(linhas, campo):
    return {k:float(np.mean([l[campo][k] for l in linhas])) for k in linhas[0][campo]
            if all(isinstance(l[campo][k],(int,float)) for l in linhas)}


def executar(p,c):
    f=ler_json(p/'congelamento.json'); ant=RAIZ/f['antecessora']['pasta']; res={}
    for fase in ('validacao','teste'):
        linhas=[]; erros=[]; logs=[]
        for seed in c['seeds']:
            a=np.load(ant/'publicacao/previsoes'/f'{fase}_{seed}.npz')
            b=np.load(p/'publicacao/previsoes'/f'{fase}_{seed}.npz')
            for k in ('y','ultimo_close','origens_ms','fim_alvo_ms','alvo_retorno'):
                np.testing.assert_array_equal(a[k],b[k])
            y=b['y']; u=b['ultimo_close']
            ma=avaliar_precos(y,a['previsoes'],u); mb=avaliar_precos(y,b['previsoes'],u)
            pa=ant/'publicacao/carteiras'/fase/str(seed)/'base/resultado.json'
            oa,ledger=carteira_vigente(f['custos_vigentes'],pa.relative_to(RAIZ).as_posix())
            pb=p/'publicacao/carteiras'/fase/str(seed)/'base'
            ob=ler_json(pb/'resultado.json')['metricas']
            sa=np.asarray(ledger['saldos_diarios']); sb=np.load(pb/'curva.npz')['saldos_diarios']
            assert len(sa)==len(sb)==len(y)+1 and ledger['slippage_por_lado']==f['slippage_avaliacao']
            erros.append(((b['previsoes']-y)/u)**2-((a['previsoes']-y)/u)**2)
            logs.append(np.diff(np.log(sb))-np.diff(np.log(sa)))
            linhas.append({'seed':seed,'referencia':ma,'candidata':mb,'operacao_referencia':oa,'operacao_candidata':ob})
        res[fase]={'seeds_pareadas':linhas,'medias':{campo:medias(linhas,campo) for campo in
                   ('referencia','candidata','operacao_referencia','operacao_candidata')},
                   'delta_mse_retorno':float(np.mean(erros)), 'delta_crescimento_log':float(np.mean(logs)),
                   'incerteza':intervalos(erros,logs)}
        for nome in ('naive','sempre_comprado','sempre_vendido'):
            for cen in c['cenarios']:
                pa=ant/'publicacao/carteiras'/fase/nome/cen/'resultado.json'
                oa,ledger=carteira_vigente(f['custos_vigentes'],pa.relative_to(RAIZ).as_posix())
                pb=p/'publicacao/carteiras'/fase/nome/cen
                np.testing.assert_array_equal(ledger['saldos_diarios'],np.load(pb/'curva.npz')['saldos_diarios'])
                for k,v in oa.items():
                    novo=ler_json(pb/'resultado.json')['metricas'][k]
                    if v is None: assert novo is None
                    else: np.testing.assert_allclose(v,novo,rtol=1e-12,atol=1e-9,err_msg=k)
    salvar_json(p/'publicacao/comparacao.json',{'referencia':f['antecessora'],'custos_vigentes':f['custos_vigentes'],
        'contraste':'Taxa inicial 0.001 menos 0.01; Adam decay zero; demais fatores mantidos',
        'fases':res,'herdados_nao_contam_novos':True,'baselines_operacionais_identicas':True,
        'limites':'Três seeds, um ano retrospectivo por fase; IC exploratório, sem correção da busca histórica.'})
