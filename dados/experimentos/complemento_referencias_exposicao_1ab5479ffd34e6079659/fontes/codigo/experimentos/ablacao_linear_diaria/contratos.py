"""A única intervenção científica é a remoção estrutural dos ramos."""
from copy import deepcopy
from experimentos.eixo_temporal_diario.contratos import organizar, selecionar_prefixo


def receita(configuracao, variante):
    c = deepcopy(configuracao)
    c['eixo'] = c['variantes'][variante]['eixo']
    c['ramos_mamba'] = c['variantes'][variante]['ramos_mamba']
    c['treinamento']['politica_penalizacao'] = 'uniforme'
    return c


def conferir_configuracao(c, anterior):
    alteraveis = {'ciclo', 'variantes', 'heranca', 'controle', 'contrastes',
                  'penalizacao_seletiva', 'ablacao_linear', 'referencia_seletiva'}
    assert {k:v for k,v in c.items() if k not in alteraveis} == {
        k:v for k,v in anterior.items() if k not in alteraveis}
    assert c['variantes'] == {'A':{'eixo':'canais','ramos_mamba':True},
                             'L':{'eixo':'canais','ramos_mamba':False}}
    assert c['treinamento']['epocas'] == 200 and c['seeds'] == [42,17,2026]
    assert c['treinamento']['weight_decay'] == .001
    assert c['controle'] == {'seed':42,'epocas':200,'referencia_A_nova':True,
                            'repeticao_L_nova':True,'antes_das_demais_seeds':True}
    assert c['contrastes'] == {'L_menos_A':{'L':1,'A':-1}}
    assert c['ablacao_linear'] == {
        'remocao':'12_blocos_CMBlock_incluindo_LayerNorm_substituidos_por_identidades',
        'inicializacao':'construir_A_com_a_mesma_seed_e_remover_antes_de_qualquer_ajuste',
        'parametros_A':136952,'parametros_L':824,'pesos_treinados_herdados':False}
    assert c['referencia_seletiva'] == 'registros/penalizacao_seletiva_diaria/execucao.json'
    return True
