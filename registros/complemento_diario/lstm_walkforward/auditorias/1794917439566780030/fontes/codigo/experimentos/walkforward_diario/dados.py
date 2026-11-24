"""Contratos das divisões e preparação causal das janelas de cada bloco."""
from copy import deepcopy
import numpy as np
import pandas as pd
from entradas_modelo.padronizacao_diaria import preparar_com_escalas


def configuracao_bloco(base, bloco, inicio):
    c=deepcopy(base)
    c['periodos']={'treino':[inicio,bloco['treino_fim']],
                   'validacao':[bloco['treino_fim'],bloco['validacao_fim']],
                   'teste':[bloco['validacao_fim'],bloco['teste_fim']]}
    c['treinamento']['epocas']=200
    datas=[pd.Timestamp(c['periodos'][fase][0],tz='UTC') for fase in ('treino','validacao','teste')]
    datas.append(pd.Timestamp(c['periodos']['teste'][1],tz='UTC'))
    if datas != sorted(datas) or len(set(datas))!=4:raise ValueError('Fronteiras temporais inválidas.')
    return c


def preparar(diario,c):
    dados,escalas=preparar_com_escalas(diario,c)
    for fase,z in dados.items():
        inicio,fim=[pd.Timestamp(x,tz='UTC').value//1000000 for x in c['periodos'][fase]]
        assert z['x'].shape==(len(z['y']),6,14) and len(z['y'])>28
        assert np.all(z['origens_ms']>=inicio+14*86400000)
        assert np.all(z['fim_alvo_ms']<fim)
        assert np.all(np.diff(z['origens_ms'])==86400000)
        np.testing.assert_array_equal(z['y'],z['preco_alvo']/z['ultimo_close']-1)
    assert escalas['ultimo_candle_ms'] < pd.Timestamp(c['periodos']['treino'][1],tz='UTC').value//1000000
    return dados,escalas
