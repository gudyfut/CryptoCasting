"""Ablação de um único coeficiente; escala, receita e orçamento herdados."""
from copy import deepcopy


def conferir_configuracao(nova, anterior):
    a,b=deepcopy(nova),deepcopy(anterior)
    assert a['antecessora']=='f3f8772670f244779ad7'
    assert a['treinamento']['weight_decay']==0.0
    assert b['treinamento']['weight_decay']==0.001
    a['treinamento']['weight_decay']=b['treinamento']['weight_decay']
    for k in ('ciclo','versao','antecessora'):a.pop(k);b.pop(k)
    assert a==b, 'Mudança adicional à retirada da penalização.'
    return True
