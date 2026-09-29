"""Regressão AR(1) com intercepto e alinhamento causal das amostras."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from pre_processamento.contrato import DURACOES


@dataclass(frozen=True)
class ParametrosAR1:
    alfa: float
    phi: float
    quantidade_pares: int


def _validar_amostras(candles: pd.DataFrame, amostras: pd.DataFrame) -> np.ndarray:
    """Confere identidade, continuidade local e alvo de um candle no mesmo parquet."""
    if amostras.empty:
        raise ValueError("Bloco vazio para o AR(1).")
    if candles.empty or candles[["par", "granularidade"]].drop_duplicates().shape[0] != 1:
        raise ValueError("Parquet de candles sem identidade única.")
    par = str(candles.iloc[0]["par"])
    granularidade = str(candles.iloc[0]["granularidade"])
    if not ((amostras["par"] == par) & (amostras["granularidade"] == granularidade)).all():
        raise ValueError("Amostras de outro par ou granularidade.")
    if not (amostras["horizonte_candles"] == 1).all():
        raise ValueError("O AR(1) deste protocolo prevê exatamente o próximo candle.")
    origens = amostras["indice_contexto_fim"].to_numpy(dtype="int64")
    alvos = amostras["indice_alvo"].to_numpy(dtype="int64")
    if (origens < 1).any() or (alvos >= len(candles)).any() or not np.array_equal(alvos, origens + 1):
        raise ValueError("Índices de origem/alvo inválidos para AR(1).")
    fim = pd.DatetimeIndex(candles["fim_utc"])
    passo = pd.Timedelta(DURACOES[granularidade])
    if not ((fim[origens] - fim[origens - 1] == passo) & (fim[alvos] - fim[origens] == passo)).all():
        raise ValueError("Retornos do AR(1) atravessam lacuna temporal.")
    if (
        not pd.DatetimeIndex(amostras["origem_utc"]).equals(fim[origens])
        or not pd.DatetimeIndex(amostras["alvo_fim_utc"]).equals(fim[alvos])
    ):
        raise ValueError("Timestamps das amostras não correspondem aos candles.")
    fechamentos = candles["close"].to_numpy(dtype="float64")
    if not np.isfinite(fechamentos[np.r_[origens - 1, origens, alvos]]).all():
        raise ValueError("Fechamento não finito no AR(1).")
    if not np.allclose(amostras["preco_origem"], fechamentos[origens], rtol=0, atol=1e-10):
        raise ValueError("Preço de origem divergente.")
    if not np.allclose(amostras["preco_alvo"], fechamentos[alvos], rtol=0, atol=1e-10):
        raise ValueError("Preço-alvo divergente.")
    return origens


def construir_pares_autorregressivos(
    candles: pd.DataFrame, amostras_treino: pd.DataFrame
) -> tuple[np.ndarray, np.ndarray]:
    """Cada origem elegível fornece (retorno observado em t, retorno em t+1)."""
    origens = _validar_amostras(candles, amostras_treino)
    fechamentos = candles["close"].to_numpy(dtype="float64")
    retornos_observados = np.log(fechamentos[origens] / fechamentos[origens - 1])
    retornos_seguintes = np.log(fechamentos[origens + 1] / fechamentos[origens])
    if not np.allclose(retornos_seguintes, amostras_treino["retorno_futuro"], rtol=0, atol=1e-12):
        raise ValueError("Retorno futuro divergente da amostra auditada.")
    return retornos_observados, retornos_seguintes


def ajustar_ar1(retornos_observados: np.ndarray, retornos_seguintes: np.ndarray) -> ParametrosAR1:
    """ARIMA(1,0,0) nos retornos via MQO condicional, com intercepto fixado no protocolo."""
    anteriores = np.asarray(retornos_observados, dtype="float64")
    seguintes = np.asarray(retornos_seguintes, dtype="float64")
    if anteriores.ndim != 1 or seguintes.shape != anteriores.shape or len(anteriores) < 3:
        raise ValueError("São necessários ao menos três pares de retornos alinhados.")
    if not np.isfinite(anteriores).all() or not np.isfinite(seguintes).all():
        raise ValueError("Retornos não finitos no ajuste do AR(1).")
    desenho = np.column_stack((np.ones(len(anteriores)), anteriores))
    coeficientes, _, posto, _ = np.linalg.lstsq(desenho, seguintes, rcond=None)
    if posto != 2 or not np.isfinite(coeficientes).all():
        raise ValueError("Ajuste AR(1) singular ou não finito; fold indisponível.")
    return ParametrosAR1(float(coeficientes[0]), float(coeficientes[1]), len(anteriores))


def prever_amostras(
    candles: pd.DataFrame, amostras: pd.DataFrame, parametros: ParametrosAR1
) -> pd.DataFrame:
    """Atualiza só o último retorno realizado; mantém alfa/phi congelados no bloco."""
    origens = _validar_amostras(candles, amostras)
    fechamentos = candles["close"].to_numpy(dtype="float64")
    ultimo_retorno = np.log(fechamentos[origens] / fechamentos[origens - 1])
    estimados = parametros.alfa + parametros.phi * ultimo_retorno
    if not np.isfinite(estimados).all():
        raise ValueError("Previsão AR(1) não finita.")
    saida = amostras[[
        "par", "granularidade", "tarefa", "contexto_dias", "origem_utc", "alvo_fim_utc",
        "preco_origem", "preco_alvo", "retorno_futuro", "classe_alta", "empate",
    ]].copy()
    saida["ultimo_retorno_observado"] = ultimo_retorno
    saida["retorno_previsto_ar1"] = estimados
    saida["classe_prevista_ar1"] = (estimados > 0).astype("int8")
    return saida
