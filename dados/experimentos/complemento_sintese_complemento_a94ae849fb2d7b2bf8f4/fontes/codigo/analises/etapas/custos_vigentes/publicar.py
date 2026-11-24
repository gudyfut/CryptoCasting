"""Publicação vigente separada das identidades históricas, incluindo médias e web."""
from copy import deepcopy
from pathlib import Path
import json
import sqlite3
import zipfile
import zlib
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,agora,identidade
from .executar import PONTEIRO

METADADOS={'seed','contexto','controle','herdado','retorno_original','retorno_posnorm','diferenca_retorno'}
def assinatura(v):
    return identidade({k:x for k,x in v.items() if k not in METADADOS and (x is None or (isinstance(x,(int,float)) and not isinstance(x,bool)))})


def media(esqueleto,linhas):
    novo=deepcopy(esqueleto)
    for k,v in esqueleto.items():
        if k in ('retorno_desvio_seeds','desvio_retorno_seeds'):
            novo[k]=float(np.std([x['retorno_liquido'] for x in linhas],ddof=1)) if len(linhas)>1 else None
        elif k=='seeds_lucrativas':novo[k]=sum(x['retorno_liquido']>0 for x in linhas)
        elif k=='n_seeds':novo[k]=len(linhas)
        elif all(isinstance(x.get(k),(int,float)) and not isinstance(x.get(k),bool) for x in linhas):novo[k]=float(np.mean([x[k] for x in linhas]))
    return novo


def agregar(j):
    """Recompõe apenas agregados financeiros de coortes explicitamente identificadas."""
    carteiras=j.get('carteiras',{})
    for bloco,grupos in j.get('medias_operacionais_por_bloco',{}).items():
        for chave,antigo in grupos.items():
            grupo,politica,cenario=chave.split('/')
            linhas=[v for k,v in carteiras.items() if k.startswith(f'{bloco}/{grupo}/') and k.endswith(f'/{politica}/{cenario}') and k.split('/')[2].isdigit()]
            if not linhas:raise ValueError(f'Coorte financeira ausente: {bloco}/{chave}')
            grupos[chave]=media(antigo,linhas)
    if 'por_simulacao' in j:
        for fase,cenarios in j.get('medias',{}).items():
            for cen,politicas in cenarios.items():
                for politica,grupos in politicas.items():
                    if politica=='benchmarks':
                        for nome in grupos:
                            row=j['por_simulacao'][f'{fase}/{cen}/{nome}/benchmark']
                            grupos[nome]=media(grupos[nome],[row])
                            grupos[nome]['retornos_individuais']={'benchmark':row['retorno_liquido']}
                        continue
                    for nome,antigo in grupos.items():
                        ids=antigo.get('retornos_individuais',{})
                        if not ids:continue
                        rows=[j['por_simulacao'][f'{fase}/{cen}/{politica}/{k}'] for k in ids]
                        novo=media(antigo,rows);novo['retornos_individuais']={k:r['retorno_liquido'] for k,r in zip(ids,rows)};grupos[nome]=novo
    ajustes=j.get('por_ajuste',{})
    for fase,grupos in j.get('medias',{}).items():
        for grupo in grupos.values():
            if not isinstance(grupo,dict) or 'spot' not in grupo:continue
            ids=grupo.get('mse_por_seed',grupo.get('metricas',{}).get('mse_por_seed',{}))
            for cen,antigo in grupo['spot'].items():
                if cen=='bruto_mesmos_sinais':continue # cenário zero não foi alterado
                rows=[ajustes[k]['spot'][cen] for k in ids]
                if rows:grupo['spot'][cen]=media(antigo,rows)
    return j


def conferir_agregacao(a,b):
    if isinstance(a,dict):
        for k,v in a.items():conferir_agregacao(v,b[k])
    elif isinstance(a,list):
        assert len(a)==len(b)
        for x,y in zip(a,b):conferir_agregacao(x,y)
    elif isinstance(a,(int,float)) and not isinstance(a,bool):
        np.testing.assert_allclose(a,b,rtol=1e-10,atol=1e-12)
    else:assert a==b


def publicar():
    from .historico import instalar
    instalar()
    ptr=ler_json(PONTEIRO);p=RAIZ/ptr['pasta'];progresso=ler_json(p/'progresso.json')
    if progresso['situacao']!='recalculado_conferido':raise ValueError('Reavaliação ainda não conferida')
    f=ler_json(p/'congelamento.json');jobs=f['inventario']['jobs'];db=sqlite3.connect(p/'carteiras.sqlite')
    posterior=ler_json(p/'conferencia_posterior.json')
    if posterior['situacao']!='conferido' or posterior['carteiras']!=len(jobs):raise ValueError('Conferência posterior ausente/incompleta')
    por_fonte={r[0]:json.loads(r[1]) for r in db.execute('SELECT fonte,resumo FROM carteiras')}
    if len(por_fonte)!=len(jobs):raise ValueError('Cobertura incompleta')
    mapa={};ambiguos=set()
    for antigo,novo in db.execute('SELECT antigo,novo FROM cache'):
        a=json.loads(zlib.decompress(antigo));b=json.loads(zlib.decompress(novo));k=assinatura(a)
        numeric={c:v for c,v in b.items() if c not in ('seed','contexto','controle') and (isinstance(v,(float,int,bool)) or v is None)}
        if k in mapa and mapa[k]!=numeric:ambiguos.add(k)
        else:mapa[k]=numeric
    for k in ambiguos:mapa.pop(k,None)
    ledgers_zip=zipfile.ZipFile(p/'ledgers.zip')
    chaves_ledger=dict(db.execute('SELECT fonte,chave FROM carteiras'))
    def revisar(v):
        if isinstance(v,list):return [revisar(x) for x in v]
        if not isinstance(v,dict):return v
        if 'retorno_liquido' in v and 'capital_final' in v:
            k=assinatura(v)
            if k in mapa:
                r={**v,**{c:x for c,x in mapa[k].items() if c in v}}
                for campo in ('retorno_original','retorno_posnorm','diferenca_retorno'):r.pop(campo,None)
                return r
            if k in ambiguos:raise ValueError('Resumo financeiro ambíguo exige vínculo explícito')
        if 'pasta' in v and 'metricas' in v:
            q=str(v['pasta']).replace('\\','/');prefix=RAIZ.as_posix()+'/'
            if q.startswith(prefix):q=q[len(prefix):]
            if q+'/resultado.json' in por_fonte:return {**v,'metricas':por_fonte[q+'/resultado.json']}
        return {k:revisar(x) for k,x in v.items()}
    panor=ler_json(RAIZ/'dataview/src/data/panorama.json');publicacoes={};pais={}
    for pub in panor['publicacoes'].values():
        fonte=pub['fonte']
        if fonte.endswith('custos_resultados.json'):continue
        original=ler_json(RAIZ/fonte)
        conferir_agregacao(original,agregar(deepcopy(original)))
        atual=agregar(revisar(original));publicacoes[fonte]=atual;pais[fonte]=sha256(RAIZ/fonte)
        if 'por_simulacao' in original and 'smart_mamba16_menos_caixa' in original.get('contrastes',{}):
            from backtest_carteira.relatorio import bootstrap as bootstrap_spot
            base=Path(fonte).parent
            ids=list(original['medias']['teste']['base']['smart']['mamba16_seis']['retornos_individuais'])
            cfg={'dias':14,'replicas':2000,'seed':20261030}
            def diarios(chave,novo):
                if novo:
                    key=chaves_ledger[(base/chave/'sinais.json').as_posix()]
                    return np.array([d['retorno_log'] for d in json.loads(ledgers_zip.read(key+'.json'))['diarios']])
                return pd.read_parquet(RAIZ/base/chave/'diarios.parquet').retorno_log.to_numpy()
            for novo in (False,True):
                principal=np.mean([diarios('teste/base/smart/'+s,novo) for s in ids],axis=0)
                constante=np.mean([diarios('teste/base/smart_constante/'+s,novo) for s in ids],axis=0)
                bh=diarios('teste/base/comprar_manter/benchmark',novo)
                cc={k:bootstrap_spot(principal,b,cfg) for k,b in [('smart_mamba16_menos_vies_validacao',constante),('smart_mamba16_menos_comprar_manter',bh),('smart_mamba16_menos_caixa',np.zeros_like(principal))]}
                if not novo:conferir_agregacao(original['contrastes'],cc)
                else:atual['contrastes']=cc
        for k in list(pub):
            if k in atual:pub[k]=atual[k]
        if 'benchmarks_blocos' in pub:pub['benchmarks_blocos']={k:v for k,v in atual['carteiras'].items() if '/benchmark/' in k}
        # Compilação da superfície publicada, sem copiar agregados editoriais não recompostos.
        publicacoes[fonte]=deepcopy(pub)
        if 'por_simulacao' in original:publicacoes[fonte]['contrastes_operacionais']=atual['contrastes']
    diarias={}
    bases=sorted({j['base'] for j in jobs if j['tipo']=='diaria'})
    from experimentos.generalizacao_moedas.avaliacao import bootstrap
    for base in bases:
        resumo=ler_json(RAIZ/base/'publicacao/resumo.json');carteiras=ler_json(RAIZ/base/'publicacao/carteiras.json')
        for r in carteiras:r['metricas']=por_fonte[r['pasta']+'/resultado.json']
        for fase,v in resumo['resumos'].items():
            linhas=[r['metricas'] for r in carteiras if r['fase']==fase and r['cenario']=='base' and str(r['unidade']).isdigit()]
            v['operacao_media_seeds_base']={k:float(np.mean([r[k] for r in linhas])) for k in linhas[0] if all(r[k] is not None for r in linhas)}
            seeds=resumo['seeds'];zs=[dict(np.load(RAIZ/base/f'publicacao/previsoes/{fase}_{s}.npz')) for s in seeds]
            alvo=zs[0].get('preco_alvo',zs[0].get('y'));previsoes=np.array([z['previsoes'] for z in zs]);ultimo=zs[0]['ultimo_close']
            registros=[next(r for r in carteiras if r['fase']==fase and r['cenario']=='base' and str(r['unidade'])==str(s)) for s in seeds]
            novos_saldos=np.array([json.loads(ledgers_zip.read(chaves_ledger[r['pasta']+'/resultado.json']+'.json'))['saldos_diarios'] for r in registros])
            saldos_originais=np.array([np.load(RAIZ/r['pasta']/'curva.npz')['saldos_diarios'] for r in registros])
            for bloco,intervalo in v['incerteza'].items():
                prova=bootstrap(alvo,previsoes,ultimo,saldos_originais,int(bloco))
                conferir_agregacao(intervalo,prova)
                atual=bootstrap(alvo,previsoes,ultimo,novos_saldos,int(bloco))
                np.testing.assert_array_equal(atual['ic95_delta_mse_vs_naive_usdt2'],intervalo['ic95_delta_mse_vs_naive_usdt2'])
                intervalo['ic95_crescimento_log_diario']=atual['ic95_crescimento_log_diario']
        resumo['custos_vigentes']={'slippage_por_lado':.0001,'natureza':'Provisorio; estresses proporcionais; politica e previsoes historicas mantidas.'}
        diarias[base]={'resumo':resumo,'carteiras':carteiras}
        for nome in ('resumo','carteiras'):pais[f'{base}/publicacao/{nome}.json']=sha256(RAIZ/base/f'publicacao/{nome}.json')
    ledgers_zip.close()
    from .publico import recalcular
    publico,ledgers,recibo=recalcular();fonte='registros/diagnosticos_previsoes/cryptomamba_custos_20261103/custos_resultados.json'
    publicacoes[fonte]=publico;pais.update(recibo['fontes']);panor['publicacoes']['custos_publicos']['series']=publico['series']
    with zipfile.ZipFile(p/'publico_ledgers.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
        for k,v in ledgers.items():z.writestr(k+'.json',json.dumps(v,ensure_ascii=False,allow_nan=False))
    barreiras=ler_json(p/'barreiras_recalculo.json')
    publicacoes.update(barreiras['resultados']);pais.update(barreiras['conferencia']['pais'])
    publicacao=p/'publicacao';publicacao.mkdir(exist_ok=False)
    cfg=f['configuracao'];meta={'situacao':'concluido_conferido','slippage_por_lado':cfg['slippage_por_lado'],'natureza':'Cenário intermediário provisório; não custo histórico certificado','base_fator':.2,'carteiras':len(jobs)+recibo['carteiras']+barreiras['conferencia']['carteiras'],'novos_treinamentos':0,'selecao_historica_preservada':True}
    meta['fonte']=ptr['pasta']+'/publicacao/resumo.json'
    panor['custos_vigentes']=meta
    panor['natureza']='Reavaliação financeira identificada com previsões históricas preservadas; zero novos treinamentos.'
    salvar_json(publicacao/'panorama.json',panor);salvar_json(publicacao/'diarias.json',diarias);salvar_json(publicacao/'publicacoes.json',publicacoes)
    salvar_json(publicacao/'carteiras.json',por_fonte)
    salvar_json(publicacao/'resumo.json',{**meta,'utc':agora(),'pais':pais,'publico':recibo,'barreiras':barreiras['conferencia'],'historico_preservado':True,'limites':['Taxas, funding, filtros e decisões de seleção mantidos.','Alvos que incorporavam custo histórico não foram retreinados.','Cenários sem custo permanecem sem custo.','Publicações e narrativas congeladas são históricas e não foram reescritas.']})
    arquivos={q.relative_to(p).as_posix():sha256(q) for q in publicacao.glob('*.json')}
    for nome in ('congelamento.json','conferencia.json','conferencia_posterior.json','carteiras.sqlite','ledgers.zip','barreiras_ledgers.zip','barreiras_recalculo.json','publico_ledgers.zip','editoriais_antes.zip','editoriais_antes.json'):
        arquivos[nome]=sha256(p/nome)
    salvar_json(p/'publicacao_manifesto.json',{'id':ptr['id'],'utc':agora(),'arquivos':arquivos,'fontes_publicador':{q.relative_to(RAIZ).as_posix():sha256(q) for q in Path(__file__).parent.glob('*.py')},'pais':pais})
    salvar_json(RAIZ/'registros/custos_vigentes/vigente.json',{'id':ptr['id'],'pasta':ptr['pasta'],'manifesto_sha256':sha256(p/'publicacao_manifesto.json')})
    print(json.dumps(meta,ensure_ascii=False))


if __name__=='__main__':publicar()
