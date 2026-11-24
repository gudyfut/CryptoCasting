"""Reavalia a execução do estudo arquivado sem alterar barreiras, filtros ou risco."""
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json,sha256,identidade
from .adaptadores import conferir_reproducao
from .executar import limpar

BASE=RAIZ/'arquivo/estudo_barreiras_2026-10-20/projeto'


def motor(fator):
    fonte=(BASE/'barreiras/financeiro.py').read_text(encoding='utf8')
    # Somente o custo no preenchimento: retorno_limite continua fixando filtro/risco histórico.
    antigo='taxa,slip=(.002,.001) if agravado else (.001,.0005)'
    assert fonte.count(antigo)==1
    fonte=fonte.replace(antigo,f'taxa,slip=(.002,{.001*fator!r}) if agravado else (.001,{.0005*fator!r})')
    fonte=fonte.replace('a*1.0005*1.001',f'a*{1+.0005*fator!r}*1.001')
    fonte=fonte.replace('*.9995*.999',f'*{1-.0005*fator!r}*.999')
    ns={};exec(compile(fonte,'<leitor financeiro de barreiras com custo identificado>','exec'),ns)
    return ns,hashlib.sha256(fonte.encode()).hexdigest()


@lru_cache(maxsize=4)
def dados(par):
    p=BASE/'dados/processados/barreiras_9341610dbb329a858784';meta=ler_json(p/'dataset.json')
    nome=par+'/minutos.npy'
    if sha256(p/nome)!=meta['arquivos'][nome]:raise ValueError('Minutos históricos divergentes')
    return np.load(p/nome,mmap_mode='r'),meta['primeiro_minuto']


def recalcular(destino_zip):
    original,_=motor(1.);novo,hash_codigo=motor(.2)
    estat=(BASE/'barreiras/estatistica.py').read_text(encoding='utf8').replace('from .metricas import erros','')
    ns={};exec(compile(estat,'<incerteza histórica de barreiras>','exec'),ns)
    resultados={};pais={};cache={};n=0
    for registro in sorted((BASE/'historico/execucoes').glob('*.json')):
        j=ler_json(registro)
        if not j.get('financeiro'):continue
        pasta=BASE/j['diretorio'];par=j['celula']['par'];limites=None
        for modelo,casos in j['financeiro'].items():
            arq=pasta/modelo/'financeiro.json';pais[arq.relative_to(RAIZ).as_posix()]=sha256(arq)
            previsoes=pasta/modelo/'previsoes_operacional.parquet';q=None;atual={}
            for caso,esperado in casos.items():
                n+=1
                if caso=='caixa' or (esperado.get('status')=='auditavel' and esperado.get('operacoes')==0):atual[caso]=deepcopy(esperado);continue
                if q is None:
                    pais[previsoes.relative_to(RAIZ).as_posix()]=sha256(previsoes);q=pd.read_parquet(previsoes)
                    cv=pd.read_parquet(pasta/modelo/'curva_base.parquet',columns=['minuto_utc']);limites=[pd.to_datetime(int(cv.minuto_utc.iloc[0]),unit='m',utc=True),pd.to_datetime(int(cv.minuto_utc.iloc[-1])+1,unit='m',utc=True)]
                chave=identidade([par,caso,sha256(previsoes)])
                if chave in cache:atual[caso]=deepcopy(cache[chave]);continue
                minutos,primeiro=dados(par)
                if caso=='comprar_manter':
                    r=original['comprar_manter'](q,minutos,primeiro,*limites);conferir_reproducao(esperado,r)
                    r=novo['comprar_manter'](q,minutos,primeiro,*limites)
                else:
                    op={'filtro':caso!='sem_filtro','agravado':caso=='custos_agravados','superior_ambiguo':caso=='ambiguidade_superior'}
                    r,_,_=original['simular'](q,minutos,primeiro,*limites,**op);conferir_reproducao(esperado,r)
                    r,ordens,curva=novo['simular'](q,minutos,primeiro,*limites,**op)
                    r['incerteza']=ns['incerteza_financeira'](curva)
                    # Arquivo compacto preserva ledger e marcos diários sem criar milhares de arquivos.
                    diario=curva.assign(dia=curva.minuto_utc//1440).groupby('dia').last().reset_index()
                    destino_zip.writestr(chave+'.json',json.dumps(limpar({'operacoes':ordens,'diario':diario}),ensure_ascii=False,allow_nan=False))
                cache[chave]=r;atual[caso]=deepcopy(r)
            resultados[arq.relative_to(RAIZ).as_posix()]=atual
    pais[(BASE/'barreiras/financeiro.py').relative_to(RAIZ).as_posix()]=sha256(BASE/'barreiras/financeiro.py')
    pais[(BASE/'barreiras/estatistica.py').relative_to(RAIZ).as_posix()]=sha256(BASE/'barreiras/estatistica.py')
    return resultados,{'carteiras':n,'recalculos_unicos':len(cache),'fonte_adaptada_sha256':hash_codigo,'pais':pais}
