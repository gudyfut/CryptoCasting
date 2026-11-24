"""Ponto único de acesso a teste, somente após seleção e recarga."""
import numpy as np
from infraestrutura.artefatos import salvar_json
from modelos.neurais import criar_rede, prever_neural
from modelos.naive import prever_naive
from modelos.arima import prever_arima
from modelos.contratos import montar_resultado
from avaliacao.metricas import calcular
from avaliacao.publicacao import conferir_previsoes
from . import checkpoints, arima


def avaliar(consumo, partes, modelo, cfg, destino, vinculo, rede=None, ajuste=None):
    resultado = dict(ajuste or {'modelo': modelo}, metricas={})
    if modelo in ('mamba', 'lstm'):
        if rede is None:
            raise ValueError('Rede selecionada ausente.')
        checkpoints.carregar(destino, rede, vinculo)
        recarga = criar_rede(modelo, consumo.especificacao, cfg['configuracao_modelos'])
        checkpoints.carregar(destino, recarga, vinculo)
    elif modelo == 'arima':
        parametros = arima.carregar(destino)
    for parte in ('validacao', 'teste', 'operacional'):
        pedido = consumo.solicitar(parte)
        if modelo in ('mamba', 'lstm'):
            q = prever_neural(rede, consumo, pedido, cfg['treino']['batch'])
            repetida = prever_neural(recarga, consumo, pedido, cfg['treino']['batch'])
        elif modelo == 'arima':
            h = consumo.historico_arima(pedido)
            q = montar_resultado(pedido, prever_arima(h, parametros))
            repetida = montar_resultado(pedido, prever_arima(h, arima.carregar(destino)))
        elif modelo == 'naive':
            q = prever_naive(pedido)
            repetida = prever_naive(pedido)
        else:
            raise ValueError('Modelo desconhecido.')
        if not np.array_equal(q.previsao.to_numpy(), repetida.previsao.to_numpy()):
            raise ValueError(f'Recarga não exata: {parte}.')
        # O avaliador junta verdade somente após prever. Operacional pode conter NaN.
        esperado = partes[parte].copy()
        q = esperado.merge(q[['indice_candle', 'previsao']], on='indice_candle', how='left', validate='one_to_one')
        if parte != 'operacional':
            resultado['metricas'][parte] = calcular(q.alvo, q.previsao)
        conferir_previsoes(q, esperado, resultado['metricas'].get(parte))
        q.to_parquet(destino / f'previsoes_{parte}.parquet', index=False)
    resultado['recarga_exata'] = True
    salvar_json(destino / 'resultado.json', resultado)
    return resultado
