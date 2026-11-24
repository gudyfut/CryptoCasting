"""Somente a política de penalização distingue A e S."""
from copy import deepcopy
from experimentos.eixo_temporal_diario.contratos import organizar, selecionar_prefixo


def receita(configuracao, variante):
    c = deepcopy(configuracao)
    fator = c['variantes'][variante]
    c['eixo'] = fator['eixo']
    c['treinamento']['politica_penalizacao'] = fator['politica_penalizacao']
    if fator['politica_penalizacao']=='seletiva':
        c['treinamento']['penalizacao']='grupos_seletivos_marcadores_LayerNorm_bias'
    return c


def conferir_configuracao(c, anterior):
    assert c['variantes'] == {
        'A': {'eixo': 'canais', 'politica_penalizacao': 'uniforme'},
        'S': {'eixo': 'canais', 'politica_penalizacao': 'seletiva'}}
    alteraveis = {'ciclo', 'variantes', 'referencias', 'referencia_fatorial',
                  'adaptacao_temporal', 'heranca', 'controle', 'contrastes',
                  'carteiras_previstas', 'penalizacao_seletiva'}
    assert {k:v for k,v in c.items() if k not in alteraveis} == {
        k:v for k,v in anterior.items() if k not in alteraveis}
    assert c['treinamento']['epocas'] == 200 and c['seeds'] == [42,17,2026]
    assert c['treinamento']['weight_decay'] == .001
    assert c['controle'] == {'seed':42, 'epocas':200, 'referencia_A_nova':True,
        'repeticao_S_nova':True, 'antes_das_demais_seeds':True}
    assert c['carteiras_previstas'] == 60
    assert c['contrastes'] == {'S_menos_A': {'S':1, 'A':-1}}
    assert c['penalizacao_seletiva'] == {
        'isentar':['marcador_no_weight_decay','parametros_LayerNorm','bias'],
        'demais':.001, 'otimizador':'Adam', 'parametros':136952}
    return True
