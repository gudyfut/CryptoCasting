"""Impede alterações acidentais além do alvo e da unidade de seleção."""
from copy import deepcopy


def conferir_configuracao(nova,anterior):
    a,b=deepcopy(nova),deepcopy(anterior)
    assert a['alvo']=='retorno_simples_fechamento_seguinte_decimal'
    assert a['treinamento']['selecao']=='RMSE_global_validacao_retorno'
    for k in ('ciclo','versao','antecessora','alvo'):
        a.pop(k);b.pop(k)
    a['treinamento'].pop('selecao');b['treinamento'].pop('selecao')
    assert a==b,'Mudança fora do alvo/unidade da seleção.'
    return True
