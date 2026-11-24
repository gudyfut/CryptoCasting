"""Conferência de consumo real, sem construir/ajustar redes ou estimar ARIMA."""
from pathlib import Path
import numpy as np
from infraestrutura.artefatos import agora, fontes, relativo, sha256
from .consumo import carregar_consumo
from .naive import prever_naive


def conferir_consumo(pasta):
    pasta = Path(pasta)
    consumo = carregar_consumo(pasta)
    e = consumo.especificacao
    contagens = {}
    for nome in ('treino', 'validacao', 'teste', 'operacional'):
        pedido = consumo.solicitar(nome)
        for a in range(0, len(pedido.origens), 256):
            p = consumo.solicitar(nome, np.arange(a, min(a + 256, len(pedido.origens))))
            lote = consumo.lote_neural(p)
            if lote.entradas.shape != (len(p.origens), e.contexto, e.dimensao_entrada):
                raise ValueError('Lote real incompatível.')
            if nome != 'operacional':
                z = consumo.alvos_supervisionados(p)
                np.testing.assert_allclose(consumo.decodificar_saida_neural(p, z), consumo.alvos_supervisionados(p, False),
                                           rtol=1e-6, atol=1e-8)
        naive = prever_naive(pedido)
        np.testing.assert_array_equal(naive.previsao, np.zeros(len(pedido.origens)))
        hist = consumo.historico_arima(pedido)
        np.testing.assert_array_equal(hist.indices_origens, pedido.origens.indice_candle)
        contagens[nome] = {'origens': len(pedido.origens), 'janelas_conferidas': len(pedido.origens),
                           'primeira': pedido.origens.origem_utc.iloc[0].isoformat(),
                           'ultima': pedido.origens.origem_utc.iloc[-1].isoformat(),
                           'comprimento_prefixo_arima': len(hist.log_precos)}
    ajuste = consumo.dados_ajuste_arima()
    return {'utc': agora(), 'status': 'aprovado', 'treinamento': False, 'fit_arima': False,
            'inferencia_neural_mercado': False, 'avaliacao_desempenho': False,
            'dados': relativo(pasta), 'manifesto_dados_sha256': sha256(pasta / 'manifesto.json'),
            'identidade_contrato_modelos': e.identidade, 'canais': list(e.canais),
            'janela': [e.contexto, e.dimensao_entrada], 'horizonte_passos': e.horizonte_passos,
            'populacoes': contagens, 'indice_fim_ajuste_arima_permitido': ajuste['indice_fim_ajuste'],
            'lacunas_prefixo_ajuste_arima': int(np.isnan(ajuste['endog']).sum()),
            'fontes': fontes('modelos'),
            'limite': 'Contratos reais conferidos; nenhuma rede aplicada ao mercado, nenhum ajuste ARIMA ou seleção de ordem.'}
