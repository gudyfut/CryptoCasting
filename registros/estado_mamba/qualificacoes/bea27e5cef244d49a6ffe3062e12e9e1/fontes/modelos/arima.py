"""ARIMA sem ajuste: recebe parâmetros externos e usa apenas estados filtrados."""
from dataclasses import dataclass
import numpy as np
from .contratos import vetor_finito


@dataclass(frozen=True)
class ParametrosARIMA:
    identidade: str
    ordem: tuple[int, int, int]
    valores: tuple[float, ...]
    nomes: tuple[str, ...]
    base_log_preco: float
    indice_fim_ajuste: int


def criar_sistema(valores, ordem):
    from statsmodels.tsa.arima.model import ARIMA
    if (len(ordem) != 3 or any(type(v) is not int for v in ordem)
            or ordem[1] != 1 or ordem[0] not in range(3) or ordem[2] not in range(3)):
        raise ValueError('Contrato: ARIMA(p,1,q), p/q em 0..2, sem deriva.')
    return ARIMA(valores, order=tuple(ordem), trend='n',
                 enforce_stationarity=True, enforce_invertibility=True)


def prever_arima(historico, parametros):
    if historico.identidade != parametros.identidade:
        raise ValueError('Parâmetros ARIMA pertencem a outro conjunto.')
    i = np.asarray(historico.indices_origens)
    v = np.asarray(historico.log_precos)
    if (i.ndim != 1 or not len(i) or not np.issubdtype(i.dtype, np.integer)
            or (i < 0).any() or (i >= len(v)).any() or len(np.unique(i)) != len(i)
            or v.ndim != 1 or np.isinf(v).any() or not np.isfinite(v[i]).all()):
        raise ValueError('Histórico/origens ARIMA inválidos.')
    if (type(parametros.indice_fim_ajuste) is not int or parametros.indice_fim_ajuste < 0
            or parametros.indice_fim_ajuste > historico.ultimo_indice_ajuste_permitido
            or parametros.indice_fim_ajuste > int(i.min())):
        raise ValueError('Parâmetros ajustados além do passado permitido.')
    if parametros.base_log_preco != historico.base_log_preco or not np.isfinite(parametros.base_log_preco):
        raise ValueError('Centralização ARIMA incompatível.')
    h = historico.horizonte_passos
    if type(h) is not int or h < 1:
        raise ValueError('Horizonte ARIMA inválido.')
    # Mesmo se o chamador fornecer mais linhas, nunca filtrar além da última origem pedida.
    sistema = criar_sistema((v[:int(i.max()) + 1] - parametros.base_log_preco) * 100., parametros.ordem)
    if tuple(sistema.param_names) != tuple(parametros.nomes):
        raise ValueError('Nomes/ordem de parâmetros ARIMA incompatíveis.')
    p = vetor_finito(parametros.valores, len(sistema.param_names), 'Parâmetros ARIMA')
    if p[-1] <= 0:
        raise ValueError('Variância ARIMA deve ser positiva.')
    resultado = sistema.filter(p)  # Sem fit/seleção; parâmetros não são reestimados.
    if (np.abs(resultado.arroots) <= 1).any() or (np.abs(resultado.maroots) <= 1).any():
        raise ValueError('Parâmetros ARIMA não estacionários/invertíveis.')
    s = resultado.model.ssm
    z, t = np.asarray(s['design']), np.asarray(s['transition'])
    if z.ndim != 2 or t.ndim != 2 or np.any(s['obs_intercept']) or np.any(s['state_intercept']):
        raise ValueError('Sistema exige matrizes constantes e interceptos nulos.')
    previsto = (z @ np.linalg.matrix_power(t, h) @ resultado.filter_results.filtered_state).reshape(-1)
    retorno = previsto[i] / 100. + parametros.base_log_preco - v[i]
    if tuple(parametros.ordem) == (0, 1, 0):
        retorno = np.zeros(len(i))  # Persistência exata, sem sinal numérico espúrio.
    return vetor_finito(retorno, len(i), 'Previsão ARIMA')
