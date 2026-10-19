"""Configurações versionadas; nenhum resultado escolhe parâmetros em silêncio."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from itertools import product
import math

import pandas as pd

from .arquivos import ler_json

PARES = ('BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT')
CONTEXTOS = (24, 168)
HORIZONTES = (1, 24, 168)
COLUNAS = ('abertura_relativa', 'maxima_relativa', 'minima_relativa',
           'retorno', 'volume_log')
VERSAO = 'barreiras-2.1'


@dataclass(frozen=True)
class Fold:
    nome: str
    inicio_validacao: str
    inicio_teste: str
    fim_teste: str

    def limites(self):
        return tuple(pd.Timestamp(x, tz='UTC') for x in
                     ('2021-01-01', self.inicio_validacao, self.inicio_teste, self.fim_teste))


FOLDS = {f.nome: f for f in (
    Fold('DB1', '2022-10-01', '2023-01-01', '2023-04-01'),
    Fold('DB2', '2023-01-01', '2023-04-01', '2023-07-01'),
    Fold('DB3', '2023-04-01', '2023-07-01', '2023-10-01'),
    Fold('DB4', '2023-07-01', '2023-10-01', '2024-01-01'),
    Fold('B1', '2023-10-01', '2024-01-01', '2024-07-01'),
    Fold('B2', '2024-04-01', '2024-07-01', '2025-01-01'),
    Fold('B3', '2024-10-01', '2025-01-01', '2025-07-01'),
    Fold('B4', '2025-04-01', '2025-07-01', '2026-01-01'),
)}


def carregar(caminho: Path) -> dict:
    c = ler_json(caminho)
    obrigatorias = {'versao', 'ciclo', 'hipotese', 'pares', 'contextos', 'horizontes',
                    'folds', 'seeds', 'mamba', 'lstm', 'treino', 'dispositivo', 'backend', 'ar1'}
    if set(c) != obrigatorias or c['versao'] != VERSAO:
        raise ValueError('Contrato de configuração desconhecido ou campos divergentes.')
    for chave, permitidos in [('pares', PARES), ('contextos', CONTEXTOS),
                             ('horizontes', HORIZONTES), ('folds', FOLDS)]:
        if not c[chave] or len(set(c[chave])) != len(c[chave]) or not set(c[chave]) <= set(permitidos):
            raise ValueError(f'Valores inválidos em {chave}.')
    if any(not f.startswith('DB') for f in c['folds']):
        raise ValueError('Avaliação final bloqueada: requer congelamento e autorização de abertura registrados.')
    if c['backend'] != 'oficial' or c['dispositivo'] != 'cuda':
        raise ValueError('Este contrato científico exige Mamba oficial/CUDA; fallback só em testes sintéticos.')
    if not c['ciclo'] or not c['hipotese'] or not c['seeds'] or len(set(c['seeds'])) != len(c['seeds']):
        raise ValueError('Ciclo, hipótese e seeds precisam ser definidos antes do treino.')
    for s in c['seeds']:
        if not isinstance(s, int) or s < 0:
            raise ValueError('Seed inválida.')
    for bloco, chaves in [('mamba', ('largura', 'camadas', 'estado', 'convolucao', 'expansao')),
                          ('lstm', ('largura', 'camadas'))]:
        if set(c[bloco]) != set(chaves) | {'dropout'}:
            raise ValueError(f'Campos divergentes em {bloco}.')
        if any(not isinstance(c[bloco][k], int) or c[bloco][k] <= 0 for k in chaves):
            raise ValueError(f'Dimensões inválidas em {bloco}.')
        if not 0 <= c[bloco]['dropout'] < 1:
            raise ValueError('Dropout inválido.')
    t = c['treino']
    if set(t) != {'epocas', 'paciencia', 'batch', 'microbatch', 'taxa_aprendizado', 'weight_decay', 'clipping'}:
        raise ValueError('Contrato de treinamento divergente.')
    if any(not isinstance(t[k], int) or t[k] <= 0 for k in ('epocas', 'paciencia', 'batch', 'microbatch')):
        raise ValueError('Inteiros de treinamento inválidos.')
    if t['batch'] % t['microbatch'] or not 0 < t['taxa_aprendizado'] < 1 or t['weight_decay'] < 0 or t['clipping'] <= 0:
        raise ValueError('Otimização inválida.')
    if any(not math.isfinite(t[k]) for k in ('taxa_aprendizado','weight_decay','clipping')):
        raise ValueError('Parâmetro numérico não finito.')
    if c['ar1'] != {'trajetorias': 4096, 'semente': 20261018}:
        raise ValueError('A alteração do orçamento AR(1) exige nova qualificação numérica.')
    return c


def celulas(c):
    return [dict(par=p, contexto=w, horizonte=h, fold=f, seed=s)
            for f, p, h, w, s in product(c['folds'], c['pares'], c['horizontes'], c['contextos'], c['seeds'])]
