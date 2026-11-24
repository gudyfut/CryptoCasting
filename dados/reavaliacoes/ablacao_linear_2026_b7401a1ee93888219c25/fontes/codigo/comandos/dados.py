"""CLI de dados: nenhuma ação neste comando treina ou importa redes neurais."""
import argparse
import json
import sys
import traceback
from uuid import uuid4
from pathlib import Path
from infraestrutura.artefatos import RAIZ, abrir_artefato, ler_json, relativo, salvar_json, agora
from mercado_binance import Periodo, importar_arquivos, baixar_arquivos, coletar_api, agregar_mercado
from entradas_modelo import preparar_entradas


def config_mercado(caminho):
    c=ler_json(caminho)
    if set(c)!={'versao','mercado','intervalo_origem','pares','inicio','fim','raiz_brutos_existentes'} or c['versao']!=1 or c['mercado']!='spot' or c['intervalo_origem']!='1m':
        raise ValueError('Configuração de mercado desconhecida; suporte explícito a Spot/1m.')
    return c


def principal():
    p=argparse.ArgumentParser(description=__doc__)
    comandos=p.add_subparsers(dest='acao',required=True)
    for acao in ('importar','baixar'):
        s=comandos.add_parser(acao)
        s.add_argument('--config',type=Path,default=RAIZ/'configuracoes/mercado_binance_001.json')
    s=comandos.add_parser('api')
    s.add_argument('par');s.add_argument('inicio');s.add_argument('fim')
    s.add_argument('--limite',type=int,default=1000);s.add_argument('--max-paginas',type=int,default=100)
    s=comandos.add_parser('agregar');s.add_argument('mercado',type=Path);s.add_argument('--minutos',type=int,default=60)
    s=comandos.add_parser('entradas');s.add_argument('candles',type=Path)
    s.add_argument('--config',type=Path,default=RAIZ/'configuracoes/entradas_ohlcv24_001.json')
    s=comandos.add_parser('conferir');s.add_argument('artefato',type=Path)
    a=p.parse_args()
    if a.acao in ('importar','baixar'):
        c=config_mercado(a.config);periodo=Periodo(c['inicio'],c['fim'])
        if a.acao=='importar':
            saida=importar_arquivos(RAIZ/c['raiz_brutos_existentes'],c['pares'],periodo)
        else:
            saida=baixar_arquivos(c['pares'],periodo)
    elif a.acao=='api':
        saida=coletar_api(a.par,Periodo(a.inicio,a.fim),limite=a.limite,maximo_paginas=a.max_paginas)
    elif a.acao=='agregar':
        saida=agregar_mercado(a.mercado,a.minutos)
    elif a.acao=='entradas':
        saida=preparar_entradas(a.candles,ler_json(a.config))
    else:
        m=abrir_artefato(a.artefato)
        print(json.dumps({'status':'conferido','tipo':m['tipo'],'id':m['id'],'arquivos':len(m['arquivos'])},ensure_ascii=False))
        return
    print(json.dumps({'artefato':relativo(saida),'treinamento':False},ensure_ascii=False))


if __name__=='__main__':
    try:
        principal()
    except (Exception, KeyboardInterrupt):
        salvar_json(RAIZ/'registros/dados/falhas'/f'{uuid4().hex}.json',
                    {'utc':agora(),'argumentos':sys.argv[1:],'erro':traceback.format_exc(),'treinamento':False})
        raise
