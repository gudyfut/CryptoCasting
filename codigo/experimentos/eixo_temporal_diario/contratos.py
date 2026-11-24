"""Receitas efetivas, população e eixos; sem ajuste de parâmetros."""
from copy import deepcopy
import numpy as np


def receita(configuracao, variante):
    c = deepcopy(configuracao)
    fator = c['variantes'][variante]
    c['eixo'] = fator['eixo']
    c['treinamento']['weight_decay'] = fator['weight_decay']
    return c


def organizar(dados, eixo):
    if eixo not in ('canais', 'dias'):
        raise ValueError('Eixo desconhecido.')
    resultado = {}
    for fase, valores in dados.items():
        x = valores['x']
        assert x.dtype == np.float32 and x.shape[1:] == (6, 14)
        resultado[fase] = dict(valores, x=x if eixo == 'canais'
                               else np.ascontiguousarray(x.transpose(0, 2, 1)))
    return resultado


def conferir_configuracao(c, anterior):
    assert c['variantes'] == {'A': {'eixo':'canais','weight_decay':.001},
                            'B': {'eixo':'canais','weight_decay':0.},
                            'C': {'eixo':'dias','weight_decay':.001},
                            'D': {'eixo':'dias','weight_decay':0.}}
    assert c['seeds'] == [42, 17, 2026] and c['treinamento']['epocas'] == 200
    for campo in ('simbolo','periodos','contexto_dias','canais','volume_divisor',
                  'normalizar','timestamp','alvo','arquitetura','padronizacao',
                  'execucao_numerica','codigo_publico_commit'):
        assert c[campo] == anterior[campo], campo
    novo = deepcopy(c['treinamento']); novo['epocas'] = anterior['treinamento']['epocas']
    novo['weight_decay'] = anterior['treinamento']['weight_decay']
    assert novo == anterior['treinamento']
    assert c['controle']['epocas'] == 200 and c['controle']['seed'] == 42
    return True


def selecionar_prefixo(historico, limite=200):
    prefixo = historico[:limite]
    assert len(prefixo) == limite
    assert [r['epoca'] for r in prefixo] == list(range(1, limite+1))
    for r in prefixo:
        assert np.isfinite(r['rmse_global_validacao_retorno'])
        assert r['taxa'] == .01 * .5 ** ((r['epoca']-1)//100)
    return min(prefixo, key=lambda r: r['rmse_global_validacao_retorno'])
