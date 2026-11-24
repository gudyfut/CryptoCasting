"""Reutiliza exatamente os artefatos de entrada das duas rodadas encerradas."""
from infraestrutura.artefatos import RAIZ, ler_json
from experimentos.entradas_niveis.dados import carregar as carregar_niveis

REG = RAIZ / 'registros/crua_huber'
CONFIG = 'configuracoes/crua_huber_001.json'
VARIANTES = ['relativa_mse', 'relativa_huber', 'crua_mse', 'crua_huber']


def carregar(mapa):
    # O leitor herdado confere hashes, valores OHLCV, escalas, janelas e alvos.
    xs = carregar_niveis(mapa)
    for b, vs in xs.items():
        a, raw = vs['atual'], vs['crua']
        assert a.especificacao.contexto == raw.especificacao.contexto == 168
        assert raw.especificacao.dimensao_entrada == 5
        assert raw._conjunto.escalas['media_entrada'] == [0.] * 5
        assert raw._conjunto.escalas['escala_entrada'] == [1.] * 5
        for n in ('media_alvo', 'escala_alvo'):
            assert a._conjunto.escalas[n] == raw._conjunto.escalas[n]
    return {b: {'relativa': vs['atual'], 'crua': vs['crua']} for b, vs in xs.items()}
