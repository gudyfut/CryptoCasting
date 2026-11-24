"""Diferença científica única, antes de qualquer ajuste de mercado."""
from copy import deepcopy


def conferir_configuracao(nova, anterior):
    a, b = deepcopy(nova), deepcopy(anterior)
    assert a['antecessora'] == '8a0aeee4d78503b7f50d'
    assert a['treinamento']['taxa'] == .001 and b['treinamento']['taxa'] == .01
    assert a['treinamento']['weight_decay'] == b['treinamento']['weight_decay'] == 0
    a['treinamento']['taxa'] = b['treinamento']['taxa']
    for k in ('ciclo', 'versao', 'antecessora'):
        a.pop(k); b.pop(k)
    assert a == b, 'Alteração adicional à taxa inicial.'
    assert nova['seeds'] == [42, 17, 2026] and nova['controle_seed'] == 42
    return True
