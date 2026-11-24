"""Espaco experimental fechado e validacao de propostas do agente."""
from copy import deepcopy
from infraestrutura.artefatos import identidade

SEEDS = [42, 17, 2026, 7, 123, 31415, 271828, 161803]
ESPACO = {
    'representacao': ['relativa', 'crua', 'niveis', 'log_niveis', 'janela_relativa'],
    'indicadores': [False, True], 'contexto': [24, 72, 168],
    'largura': [16, 32, 64], 'camadas': [1, 2, 3], 'estado': [8, 16, 32, 64],
    'dropout': [0., .1, .2], 'pooling': ['ultimo', 'media'],
    'taxa': [.00005, .0001, .0002, .0005, .001],
    'decay': [0., .0001, .001, .01], 'otimizador': ['AdamW', 'Adam'],
    'perda': ['mse', 'huber'], 'scheduler': ['constante', 'plateau'],
    'ganho_saida': [.25, .5, .75, 1.],
}
REFERENCIA = dict(representacao='relativa', indicadores=False, contexto=168,
    largura=32, camadas=2, estado=16, dropout=.1, pooling='ultimo', taxa=.0002,
    decay=.001, otimizador='AdamW', perda='mse', scheduler='constante', ganho_saida=1.)
DESENVOLVIMENTO = {
    'D1': ['2023-01-01', '2023-07-01'],
    'D2': ['2023-07-01', '2024-01-01'],
}
FINAIS = {
    'B1': ['2023-10-01', '2024-01-01', '2024-07-01'],
    'B2': ['2024-04-01', '2024-07-01', '2025-01-01'],
    'B3': ['2024-10-01', '2025-01-01', '2025-07-01'],
    'B4': ['2025-04-01', '2025-07-01', '2026-01-01'],
}

def validar_receita(r):
    if set(r) != set(ESPACO):
        raise ValueError('Receita incompleta ou com campos externos ao espaco autorizado.')
    for k, valores in ESPACO.items():
        if not any(type(r[k]) is type(v) and r[k] == v for v in valores):
            # JSON admite numeros inteiros onde a receita permite ponto flutuante.
            if not (type(r[k]) in (int, float) and type(valores[0]) is float and r[k] in valores):
                raise ValueError(f'Valor nao autorizado: {k}={r[k]!r}')
    return deepcopy(r)

def chave_receita(r):
    r = validar_receita(r)
    for k in ['dropout', 'taxa', 'decay', 'ganho_saida']:
        r[k] = float(r[k])
    return identidade(r)[:20]

def esquema():
    props = {}
    for k, vs in ESPACO.items():
        tipo = 'boolean' if type(vs[0]) is bool else 'string' if type(vs[0]) is str else 'integer' if type(vs[0]) is int else 'number'
        props[k] = {'type': tipo, 'enum': vs}
    return {'type': 'object', 'properties': {
        'acao': {'type': 'string', 'enum': ['experimentar', 'encerrar']},
        'hipotese': {'type': 'string'}, 'justificativa': {'type': 'string'},
        'diagnostico': {'type': 'string'}, 'riscos': {'type': 'string'},
        'receita': {'type': 'object', 'properties': props, 'required': list(props), 'additionalProperties': False}},
        'required': ['acao', 'hipotese', 'justificativa', 'diagnostico', 'riscos', 'receita'], 'additionalProperties': False}

def pontuar(resultados):
    """Menor media MSE/Naive; nao usa teste nem lucro."""
    import numpy as np
    valores = [r['validacao']['mse'] / r['validacao']['mse_naive'] for r in resultados]
    return float(np.mean(valores)), float(np.std(valores)), float(max(valores))

def elegivel(candidata, referencia):
    """Melhora media >=0,1%, melhor em ambos os recortes e >=4/6 pares."""
    if len(candidata) != 6 or len(referencia) != 6:
        return False
    import numpy as np
    c = np.array([x['validacao']['mse'] for x in candidata]).reshape(2, 3)
    r = np.array([x['validacao']['mse'] for x in referencia]).reshape(2, 3)
    return bool(pontuar(candidata)[0] <= .999*pontuar(referencia)[0]
                and (c.mean(1) < r.mean(1)).all() and (c < r).sum() >= 4)

def ambiente_cuda():
    import sys
    import importlib.metadata as md
    import torch
    return {'python':sys.version.split()[0], 'torch':str(torch.__version__), 'cuda':torch.version.cuda,
            'gpu':torch.cuda.get_device_name(0),
            'pacotes':{n:md.version(n) for n in ['mamba-ssm','causal-conv1d','numpy','pandas','pyarrow']}}
