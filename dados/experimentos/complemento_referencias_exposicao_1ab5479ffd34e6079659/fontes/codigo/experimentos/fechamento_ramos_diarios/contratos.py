"""Receitas fixas; nenhum resultado decide o próximo contraste ou moeda."""
from copy import deepcopy
from infraestrutura.artefatos import RAIZ, ler_json
from experimentos.eixo_temporal_diario.contratos import selecionar_prefixo, organizar

REG = RAIZ / 'registros/fechamento_ramos_diarios'
CFG = RAIZ / 'configuracoes/fechamento_ramos_diarios_001.json'
FASES = ('treino', 'validacao', 'teste')


def configuracao_moeda(c, simbolo):
    r = deepcopy(c['moedas'][simbolo])
    for k in ('seeds', 'bootstrap', 'linear', 'slippage_cenarios', 'observacao_epocas'):
        r[k] = deepcopy(c[k])
    r['simbolo'] = simbolo
    return r


def receita(c, variante):
    r = deepcopy(c)
    fator = r['variantes'][variante]
    r['eixo'] = 'canais'
    r['ramos_mamba'] = fator['ramos_mamba']
    r['treinamento']['weight_decay'] = fator['weight_decay']
    r['treinamento']['politica_penalizacao'] = 'uniforme'
    return r


def ordem_trabalhos(c):
    ordem = []
    for moeda in c['moedas']:
        referencia, nova = ('B', 'L0') if moeda == 'BTCUSDT' else ('A', 'L')
        for variante, seed, controle in [(referencia, 42, True), (nova, 42, False),
                                        (nova, 42, True), (nova, 17, False), (nova, 2026, False)]:
            ordem.append(dict(simbolo=moeda, variante=variante, seed=seed, controle=controle,
                              id=f'{variante}_' + ('controle_' if controle else '') + str(seed)))
    return ordem


def conferir(c, moedas_anteriores):
    assert c['seeds'] == [42, 17, 2026]
    assert list(c['moedas']) == ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT']
    assert c['max_ajustes_cientificos'] == 12
    assert c['slippage_cenarios'] == [.0001, .0002, .0003]
    base = ler_json(RAIZ/'configuracoes/ablacao_linear_diaria_001.json')
    for simbolo, info in moedas_anteriores.items():
        novo = configuracao_moeda(c, simbolo)
        antigo = info['configuracao']
        for campo in ('simbolo', 'mercado', 'periodos', 'contexto_dias', 'canais',
                      'volume_divisor', 'normalizar', 'timestamp', 'alvo', 'arquitetura',
                      'padronizacao', 'codigo_publico_commit', 'execucao_numerica'):
            assert novo[campo] == antigo[campo], (simbolo, campo)
        t = deepcopy(antigo['treinamento']); t['epocas'] = 200
        assert novo['treinamento'] == t
        regras = deepcopy(antigo['operacoes'])
        regras.update(slippage_por_lado=.0001, politica=base['operacoes']['politica'])
        assert novo['operacoes'] == regras
        variantes = {'A': dict(ramos_mamba=True, weight_decay=.001),
                     'L': dict(ramos_mamba=False, weight_decay=.001)}
        if simbolo == 'BTCUSDT':
            variantes.update(B=dict(ramos_mamba=True, weight_decay=0.),
                             L0=dict(ramos_mamba=False, weight_decay=0.))
        assert novo['variantes'] == variantes
        assert novo['carteiras_previstas'] == (108 if simbolo == 'BTCUSDT' else 60)
        for chave in ('linear', 'bootstrap', 'observacao_epocas'):
            assert novo[chave] == base[chave]
    trabalhos = ordem_trabalhos(c)
    assert len(trabalhos) == 20
    assert sum(not j['controle'] for j in trabalhos) == 12
    return True
