"""Configuração delimitada de R0; alterações científicas exigem novo ciclo."""
from pathlib import Path
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json
from modelos.neurais import carregar_configuracao

CAMINHO = 'configuracoes/treinamento_ohlcv24_001.json'


def carregar():
    c = ler_json(RAIZ / CAMINHO)
    referencia = ler_json(RAIZ / 'configuracoes/ohlcv24_001.json')
    antigos = set(referencia) - {'versao', 'ciclo', 'dataset_origem'}
    if set(c) != antigos | {'versao', 'ciclo', 'entradas_pasta', 'mercado_pasta', 'configuracao_modelos'}:
        raise ValueError('Configuração incompleta ou com campos ignorados.')
    for chave in antigos:
        if c[chave] != referencia[chave]:
            raise ValueError(f'R0 modular deve preservar decisão científica: {chave}')
    arquitetura = carregar_configuracao(RAIZ / c['configuracao_modelos'])
    for chave in ('mamba', 'lstm', 'backend', 'dispositivo', 'normalizacao_bloco'):
        if c[chave] != arquitetura[chave]:
            raise ValueError('Configurações de modelo e execução divergentes.')
    for chave in ('entradas_pasta', 'mercado_pasta', 'configuracao_modelos'):
        if not (RAIZ / c[chave]).resolve().is_relative_to(RAIZ):
            raise ValueError('Dependências devem pertencer ao repositório.')
    d = ler_json(RAIZ / c['entradas_pasta'] / 'contrato.json')
    if (d['par'] != c['par'] or d['canais'] != c['entradas'] or d['contexto_passos'] != c['contexto']
            or d['horizonte_minutos'] != c['horizonte'] * 60 or d['intervalo_minutos'] != c['candle_minutos']
            or d['passo_origens'] * d['intervalo_minutos'] != c['origem_minutos']):
        raise ValueError('Entradas e desenho incompatíveis.')
    for parte in c['divisao']:
        for a, b in zip(c['divisao'][parte], d['divisao'][parte], strict=True):
            if pd.Timestamp(a, tz='UTC') != pd.Timestamp(b):
                raise ValueError('Divisão temporal incompatível.')
    return c


def grade(c):
    principais = [{'chave': f'{m}_{s}', 'modelo': m, 'seed': s, 'controle': False}
                  for m in ('mamba', 'lstm') for s in c['seeds']]
    controles = [dict(chave=f"controle_{q['modelo']}_{q['seed']}", controle=True, **q)
                 for q in c['controles_reproducao']]
    return ([p for p in principais if p['seed'] == 42] + controles
            + [p for p in principais if p['seed'] != 42] + [{'chave': m, 'modelo': m} for m in ('naive', 'arima')])
