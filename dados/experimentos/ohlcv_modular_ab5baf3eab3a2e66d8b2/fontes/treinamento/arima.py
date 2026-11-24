"""Nove ajustes só no treino; validação escolhe a ordem, sem reestimar no teste."""
from dataclasses import asdict
import warnings
import numpy as np
from infraestrutura.artefatos import salvar_json, ler_json
from modelos.arima import criar_sistema, ParametrosARIMA, prever_arima
from .selecao import escolher_arima


def ajustar(consumo, cfg, destino):
    dados = consumo.dados_ajuste_arima()
    pedido = consumo.solicitar('validacao')
    historico = consumo.historico_arima(pedido)
    y = consumo.alvos_supervisionados(pedido, padronizados=False)
    candidatos = []
    for ordem in cfg['ordens']:
        c = {'ordem': ordem, 'status': 'falhou'}
        avisos = []
        try:
            with warnings.catch_warnings(record=True) as avisos:
                warnings.simplefilter('always')
                ajuste = criar_sistema(dados['endog'], ordem).fit(method_kwargs={'maxiter': cfg['maxiter']})
            if not ajuste.mle_retvals.get('converged', False):
                raise ValueError('ARIMA não convergiu.')
            parametros = ParametrosARIMA(dados['identidade'], tuple(ordem), tuple(float(v) for v in ajuste.params),
                                        tuple(ajuste.param_names), dados['base_log_preco'], dados['indice_fim_ajuste'])
            p = prever_arima(historico, parametros)
            c.update(status='valido', mse_validacao=float(np.mean((p - y)**2)), parametros=asdict(parametros))
        except (ValueError, RuntimeError, np.linalg.LinAlgError) as erro:
            c['erro'] = repr(erro)
        c['avisos'] = [str(a.message) for a in avisos]
        candidatos.append(c)
        salvar_json(destino / 'candidatos.json', candidatos)
    selecionado = escolher_arima(candidatos)
    salvar_json(destino / 'selecao_arima.json', selecionado)
    return carregar(destino)


def carregar(destino):
    p = ler_json(destino / 'selecao_arima.json')['parametros']
    for k in ('ordem', 'valores', 'nomes'):
        p[k] = tuple(p[k])
    return ParametrosARIMA(**p)
