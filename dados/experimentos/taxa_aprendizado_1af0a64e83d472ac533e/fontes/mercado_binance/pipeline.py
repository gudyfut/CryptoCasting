"""Orquestra somente fontes de mercado e candles; artefatos sempre versionados."""
from pathlib import Path
from uuid import uuid4
import importlib.metadata
import json
import numpy as np
import pandas as pd
from infraestrutura.artefatos import (RAIZ, agora, abrir_artefato, destino_artefato, fontes,
                                     relativo, salvar_json, sha256, tentativa, ler_json)
from .contratos import Periodo, validar_par, conferir_candles
from .validacao import conferir_checksum, ler_zip, normalizar
from .candles import agregar
from .transporte import ClienteHTTP
from .api import consultar


def _assinatura(parametros):
    return {'contrato':'mercado-binance-1','parametros':parametros,
            'fontes':fontes('infraestrutura','mercado_binance'),
            'bibliotecas':{k:importlib.metadata.version(k) for k in ('numpy','pandas','pyarrow')}}


def _pares(pares):
    if not pares or len(set(pares))!=len(pares):
        raise ValueError('Lista de pares vazia ou duplicada.')
    return sorted(validar_par(p) for p in pares)


def importar_arquivos(raiz_brutos, pares, periodo, base=None):
    """Revalida ZIP+CHECKSUM existentes sem escrever na coleta original."""
    base=Path(base or RAIZ/'dados/mercado/binance_spot')
    brutos=Path(raiz_brutos).resolve()
    inventario=[]
    for par in _pares(pares):
        for mes in periodo.meses():
            nome=f'{par}-1m-{mes.inicio:%Y-%m}.zip';p=brutos/par/nome
            h=conferir_checksum(p,p.with_suffix('.zip.CHECKSUM'))
            inventario.append({'par':par,'periodo':mes.json(),'arquivo':relativo(p),'sha256':h,
                               'checksum':relativo(p.with_suffix('.zip.CHECKSUM')),
                               'checksum_sha256':sha256(p.with_suffix('.zip.CHECKSUM'))})
    assinatura=_assinatura({'fonte':'arquivos_mensais','mercado':'spot','intervalo':'1m',
                            'periodo':periodo.json(),'pares':_pares(pares),'inventario':inventario})
    assinatura['originais']={p:h for r in inventario for p,h in
                             [(r['arquivo'],r['sha256']),(r['checksum'],r['checksum_sha256'])]}
    with tentativa(base,'mercado_minutos',assinatura) as (pasta,existe):
        if not existe:
            resumos=[]
            for item in inventario:
                original=RAIZ/item['arquivo']; mes=Periodo(**item['periodo'])
                if sha256(original)!=item['sha256']:
                    raise ValueError('Arquivo mudou após inventário.')
                unidade='us' if mes.inicio>=pd.Timestamp('2025-01-01',tz='UTC') else 'ms'
                q,r=normalizar(ler_zip(original),mes,unidade)
                destino=pasta/'minutos'/item['par']/f'{mes.inicio:%Y-%m}.parquet'
                destino.parent.mkdir(parents=True,exist_ok=True)
                q.to_parquet(destino,index=False)
                resumos.append({'par':item['par'],'periodo':mes.json(),'arquivo':destino.relative_to(pasta).as_posix(),**r})
                print(f"{item['par']} {mes.inicio:%Y-%m}: {r['completos']} completos; {r['indisponiveis']} indisponíveis",flush=True)
            salvar_json(pasta/'qualidade.json',{'partes':resumos,'politica':'lacunas/velas interrompidas preservadas; sem interpolação',
                        'volume':'unidades do ativo-base; volume_cotacao em unidade de cotação',
                        'tempo':'inicio_utc inclusivo; fim_utc exclusivo e instante de disponibilidade idealizado'})
    return destino_artefato(base,assinatura)


def baixar_arquivos(pares,periodo,base=None):
    """Download novo e explícito. Nunca substitui ZIPs já usados por um estudo."""
    pasta=Path(base or RAIZ/'dados/coletas_binance')/uuid4().hex
    pasta.mkdir(parents=True)
    cliente=ClienteHTTP(pasta/'http')
    salvar_json(pasta/'solicitacao.json',{'utc':agora(),'pares':_pares(pares),'periodo':periodo.json(),'tipo':'mensal'})
    try:
        for par in _pares(pares):
            for mes in periodo.meses():
                nome=f'{par}-1m-{mes.inicio:%Y-%m}.zip'
                url=f'https://data.binance.vision/data/spot/monthly/klines/{par}/1m/{nome}'
                destino=pasta/'brutos'/par/nome;destino.parent.mkdir(parents=True,exist_ok=True)
                for sufixo in ('.CHECKSUM',''):
                    corpo,_=cliente.obter(url+sufixo)
                    Path(str(destino)+sufixo).write_bytes(corpo)
                conferir_checksum(destino,Path(str(destino)+'.CHECKSUM'))
        salvar_json(pasta/'conclusao.json',{'utc':agora(),'status':'baixado_checksum_conferido','proxima_etapa':'importar_arquivos'})
    except BaseException:
        import traceback
        salvar_json(pasta/'falha.json',{'utc':agora(),'erro':traceback.format_exc()})
        raise
    return pasta/'brutos'


def coletar_api(par,periodo,base=None,base_coletas=None,limite=1000,maximo_paginas=100):
    base=Path(base or RAIZ/'dados/mercado/binance_spot')
    coleta=Path(base_coletas or RAIZ/'dados/coletas_binance')/uuid4().hex
    coleta.mkdir(parents=True)
    salvar_json(coleta/'solicitacao.json',{'utc':agora(),'par':validar_par(par),'periodo':periodo.json(),'tipo':'api','limite':limite})
    try:
        q,resumo=consultar(ClienteHTTP(coleta/'http'),par,periodo,coleta/'respostas',limite,maximo_paginas)
        arquivos={p.relative_to(coleta).as_posix():sha256(p) for p in sorted(coleta.rglob('*')) if p.is_file()}
        assinatura=_assinatura({'fonte':'api','mercado':'spot','intervalo':'1m','pares':[par],
                                'periodo':periodo.json(),'coleta':relativo(coleta),'arquivos_coleta':arquivos})
        assinatura['originais']={relativo(coleta/p):h for p,h in arquivos.items()}
        with tentativa(base,'mercado_minutos',assinatura) as (pasta,existe):
            if not existe:
                saida=pasta/'minutos'/par/'api.parquet';saida.parent.mkdir(parents=True)
                q.to_parquet(saida,index=False)
                salvar_json(pasta/'qualidade.json',{'partes':[{'par':par,'periodo':periodo.json(),
                            'arquivo':saida.relative_to(pasta).as_posix(),**resumo}], 'tempo':'UTC, fim exclusivo',
                            'integridade':'hash local da resposta; API não fornece CHECKSUM oficial'})
        salvar_json(coleta/'conclusao.json',{'utc':agora(),'status':'concluido','artefato':relativo(destino_artefato(base,assinatura))})
    except BaseException:
        import traceback
        salvar_json(coleta/'falha.json',{'utc':agora(),'erro':traceback.format_exc()})
        raise
    return destino_artefato(base,assinatura)


def agregar_mercado(mercado,intervalo=60,base=None):
    mercado=Path(mercado).resolve(); m=abrir_artefato(mercado,'mercado_minutos')
    base=Path(base or RAIZ/'dados/mercado/candles')
    assinatura=_assinatura({'mercado':relativo(mercado),'manifesto_sha256':sha256(mercado/'manifesto.json'),
                            'intervalo_minutos':intervalo,'pares':m['assinatura']['parametros']['pares']})
    assinatura['dependencias']=[{'pasta':relativo(mercado),'manifesto_sha256':sha256(mercado/'manifesto.json')}]
    partes=ler_json(mercado/'qualidade.json')['partes']
    with tentativa(base,'mercado_candles',assinatura) as (pasta,existe):
        if not existe:
            resumo={}
            for par in assinatura['parametros']['pares']:
                quadros=[agregar(pd.read_parquet(mercado/r['arquivo']),intervalo) for r in partes if r['par']==par]
                q=pd.concat(quadros,ignore_index=True)
                conferir_candles(q,intervalo)
                q.to_parquet(pasta/f'{par}.parquet',index=False)
                resumo[par]={'candles':len(q),'completos':int(q['completo'].sum()),'incompletos':int((~q['completo']).sum())}
            salvar_json(pasta/'qualidade.json',resumo)
    return destino_artefato(base,assinatura)


def carregar_candles(pasta,par):
    validar_par(par); pasta=Path(pasta).resolve();m=abrir_artefato(pasta,'mercado_candles')
    if par not in m['assinatura']['parametros']['pares']:
        raise ValueError('Par indisponível no artefato.')
    q=pd.read_parquet(pasta/f'{par}.parquet')
    conferir_candles(q,m['assinatura']['parametros']['intervalo_minutos'])
    return q,m
