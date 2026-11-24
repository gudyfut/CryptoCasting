"""Paginação de /klines em milissegundos, UTC e limite final exclusivo."""
import json
from urllib.parse import urlencode
import numpy as np
import pandas as pd
from infraestrutura.artefatos import salvar_json
from .contratos import Periodo, validar_par
from .validacao import normalizar

BASE = 'https://data-api.binance.vision'


def consultar(cliente, par, periodo: Periodo, pasta, limite=1000, maximo_paginas=100):
    validar_par(par)
    if not isinstance(limite,int) or isinstance(limite,bool) or not 1<=limite<=1000:
        raise ValueError('Limite de página deve estar entre 1 e 1000.')
    if not isinstance(maximo_paginas,int) or isinstance(maximo_paginas,bool) or maximo_paginas<1:
        raise ValueError('Orçamento de páginas inválido.')
    pasta.mkdir(parents=True,exist_ok=True)
    corpo,_=cliente.obter(BASE+'/api/v3/time')
    (pasta/'relogio.json').write_bytes(corpo)
    servidor=json.loads(corpo)['serverTime']
    if not isinstance(servidor,int) or servidor<0:
        raise ValueError('Relógio do servidor inválido.')
    final=int(periodo.fim.timestamp()*1000)
    if final>(servidor//60000)*60000:
        raise ValueError('Período inclui candle ainda aberto; solicitar somente minutos encerrados.')
    cursor=int(periodo.inicio.timestamp()*1000)
    linhas=[];paginas=[]
    while cursor<final:
        if len(paginas)>=maximo_paginas:
            salvar_json(pasta/'orcamento_esgotado.json',{'paginas':paginas,'proximo_cursor_ms':cursor})
            raise RuntimeError('Orçamento de páginas esgotado; dados parciais preservados, sem publicação.')
        parametros={'symbol':par,'interval':'1m','startTime':cursor,'endTime':final-1,'timeZone':'0','limit':limite}
        corpo,recibo=cliente.obter(BASE+'/api/v3/klines?'+urlencode(parametros))
        numero=len(paginas)+1
        nome=f'pagina_{numero:06d}.json'
        (pasta/nome).write_bytes(corpo)
        pagina=json.loads(corpo)
        if not isinstance(pagina,list) or len(pagina)>limite:
            raise ValueError('API devolveu erro ou formato/tamanho de página inválido.')
        paginas.append({'arquivo':nome,'parametros':parametros,'resposta_sha256':recibo['sha256'],'linhas':len(pagina)})
        if not pagina:
            break
        if any(not isinstance(l,list) or len(l)!=12 or not isinstance(l[0],int) for l in pagina):
            raise ValueError('Kline da API não tem os 12 campos esperados.')
        tempos=np.array([l[0] for l in pagina],dtype=np.int64)
        if (np.diff(tempos)<=0).any() or tempos[0]<cursor or tempos[-1]>=final or (tempos%60000).any():
            raise ValueError('Paginação duplicada, regressiva, desalinhada ou fora do período.')
        linhas.extend(pagina)
        cursor=int(tempos[-1])+60000
        # Página curta não encerra automaticamente: pode haver lacunas na fonte.
    q,resumo=normalizar(linhas,periodo,'ms')
    salvar_json(pasta/'paginas.json',{'paginas':paginas,'servidor_ms':servidor,'resumo':resumo})
    return q,resumo
