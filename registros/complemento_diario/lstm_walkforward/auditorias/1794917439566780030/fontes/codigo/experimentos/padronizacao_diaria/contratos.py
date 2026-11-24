"""A única mudança científica permitida é a padronização das entradas."""
from copy import deepcopy
from entradas_modelo.padronizacao_diaria import RECEITA


def conferir_configuracao(nova,anterior):
    a,b=deepcopy(nova),deepcopy(anterior)
    assert a['normalizar'] is True and b['normalizar'] is False
    assert a.pop('padronizacao')==RECEITA
    assert a['antecessora']=='de09c2193737c2581261'
    for k in ('ciclo','versao','antecessora','normalizar'):a.pop(k);b.pop(k)
    assert a==b,'Mudança adicional à padronização.'
    return True
