"""Elegibilidade causal e índices de amostras sem duplicar tensores de janelas."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .contrato import (
    DURACOES,
    FEATURES_AMPLIADAS,
    candles_por_contexto,
    candles_por_horizonte_24h,
)


def origens_elegiveis(
    candles: pd.DataFrame,
    granularidade: str,
    contexto_maximo_dias: int,
    horizonte_candles: int,
    somente_meia_noite: bool,
) -> np.ndarray:
    """Exige contexto, indicadores e alvo contínuos, sem consultar valor do rótulo."""
    tamanho = len(candles)
    largura = candles_por_contexto(granularidade, contexto_maximo_dias)
    if tamanho < largura + horizonte_candles:
        return np.empty(0, dtype="int64")
    tempos = candles["fim_utc"].astype("int64").to_numpy()
    passo_ns = int(pd.Timedelta(DURACOES[granularidade]).value)
    segmentos = np.cumsum(np.r_[True, np.diff(tempos) != passo_ns])
    valores = candles[list(FEATURES_AMPLIADAS)].to_numpy(dtype="float64")
    ruins = ~np.isfinite(valores).all(axis=1)
    prefixo_ruins = np.r_[0, np.cumsum(ruins)]

    origens = np.arange(largura - 1, tamanho - horizonte_candles, dtype="int64")
    inicio = origens - largura + 1
    fim_alvo = origens + horizonte_candles
    validas = (
        (segmentos[inicio] == segmentos[origens])
        & (segmentos[origens] == segmentos[fim_alvo])
        & (prefixo_ruins[origens + 1] == prefixo_ruins[inicio])
    )
    if somente_meia_noite:
        horas = candles["fim_utc"].dt.hour.to_numpy()
        minutos = candles["fim_utc"].dt.minute.to_numpy()
        validas &= (horas[origens] == 0) & (minutos[origens] == 0)
    return origens[validas]


def construir_amostras(
    candles: pd.DataFrame,
    origens: np.ndarray,
    par: str,
    granularidade: str,
    contexto_dias: int,
    horizonte_candles: int,
    tarefa: str,
) -> pd.DataFrame:
    """Persiste posições *do mesmo parquet* e timestamps para verificações futuras."""
    largura = candles_por_contexto(granularidade, contexto_dias)
    if len(origens) and (origens.min() - largura + 1 < 0 or origens.max() + horizonte_candles >= len(candles)):
        raise ValueError("Índices de origem incompatíveis com contexto ou alvo.")
    inicio = origens - largura + 1
    fim_alvo = origens + horizonte_candles
    referencia = candles["close"].to_numpy(dtype="float64")[origens]
    alvo = candles["close"].to_numpy(dtype="float64")[fim_alvo]
    retornos = np.log(alvo / referencia)
    tempos_abertura = candles["abertura_utc"]
    tempos_fim = candles["fim_utc"]

    return pd.DataFrame(
        {
            "par": par,
            "granularidade": granularidade,
            "tarefa": tarefa,
            "contexto_dias": contexto_dias,
            "horizonte_candles": horizonte_candles,
            "indice_contexto_inicio": inicio,
            "indice_contexto_fim": origens,
            "indice_alvo": fim_alvo,
            "contexto_inicio_utc": tempos_abertura.iloc[inicio].reset_index(drop=True),
            "contexto_fim_utc": tempos_fim.iloc[origens].reset_index(drop=True),
            "origem_utc": tempos_fim.iloc[origens].reset_index(drop=True),
            "alvo_fim_utc": tempos_fim.iloc[fim_alvo].reset_index(drop=True),
            "preco_origem": referencia,
            "preco_alvo": alvo,
            "retorno_futuro": retornos,
            "classe_alta": (retornos > 0).astype("int8"),
            "empate": (alvo == referencia),
        }
    )


def origens_da_tarefa_principal(candles: pd.DataFrame, granularidade: str) -> np.ndarray:
    return origens_elegiveis(
        candles,
        granularidade,
        contexto_maximo_dias=14,
        horizonte_candles=candles_por_horizonte_24h(granularidade),
        somente_meia_noite=True,
    )


def origens_da_tarefa_complementar(candles: pd.DataFrame, granularidade: str) -> np.ndarray:
    return origens_elegiveis(
        candles,
        granularidade,
        contexto_maximo_dias=7,
        horizonte_candles=1,
        somente_meia_noite=False,
    )
