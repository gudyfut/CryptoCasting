from copy import deepcopy
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json

REG = RAIZ / 'registros/historico_treino'
CONFIG = RAIZ / 'configuracoes/historico_treino_001.json'
BRACOS = ('acumulado', 'movel12')
FASES = ('validacao', 'calibracao', 'comparacao')


def configuracao():
    return ler_json(CONFIG)


def calendario(recorte, braco):
    if braco not in BRACOS:
        raise ValueError('Braço desconhecido.')
    r = deepcopy(recorte)
    if braco == 'movel12':
        r['treino'][0] = (pd.Timestamp(r['treino'][1]) - pd.DateOffset(months=12)).strftime('%Y-%m-%d')
    return r


def grade(c):
    saida = []
    # Ambos os controles reais precedem todas as demais células.
    for b in BRACOS:
        for controle in (False, True):
            saida.append(dict(braco=b, recorte=c['recortes'][0], seed=42, controle=controle))
    for r in c['recortes']:
        for s in c['seeds']:
            for b in BRACOS:
                if r['id'] == 'D1' and s == 42:
                    continue
                saida.append(dict(braco=b, recorte=r, seed=s, controle=False))
    for i, j in enumerate(saida):
        j['id'] = f"{i+1:02d}_{j['braco']}_{j['recorte']['id']}_{j['seed']}" + ('_controle' if j['controle'] else '')
    if len(saida) != 20:
        raise ValueError('Cobertura diferente de 18 principais e dois controles.')
    return saida
