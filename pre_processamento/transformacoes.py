"""Agregação UTC e três indicadores diários causais do protocolo."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .contrato import DURACOES, FEATURES_AMPLIADAS

PASSO_15M = pd.Timedelta(minutes=15)


def agregar_candles(base: pd.DataFrame, granularidade: str) -> pd.DataFrame:
    """Agrega blocos completos; abertura marca o início e fim_utc marca disponibilidade."""
    if granularidade not in DURACOES:
        raise ValueError(f"Granularidade desconhecida: {granularidade}")
    if granularidade == "15m":
        return base[["abertura_utc", "fim_utc", "open", "high", "low", "close", "volume"]].copy()

    duracao = pd.Timedelta(DURACOES[granularidade])
    esperados = int(duracao / PASSO_15M)
    agrupador = pd.Grouper(
        key="abertura_utc", freq=granularidade, origin="epoch", closed="left", label="left"
    )
    agregados = base.groupby(agrupador).agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        quantidade_base=("close", "size"),
    )
    agregados = agregados.loc[agregados["quantidade_base"] == esperados].drop(columns="quantidade_base")
    agregados = agregados.reset_index()
    agregados.insert(1, "fim_utc", agregados["abertura_utc"] + duracao)
    return agregados


def indicadores_diarios(candles_diarios: pd.DataFrame) -> pd.DataFrame:
    """Exige oito fechamentos diários consecutivos para os três indicadores."""
    diarios = candles_diarios[["fim_utc", "close"]].copy().sort_values("fim_utc")
    if diarios["fim_utc"].duplicated().any():
        raise ValueError("Fechamentos diários duplicados.")
    segmento = diarios["fim_utc"].diff().ne(pd.Timedelta(days=1)).cumsum()
    diarios["segmento"] = segmento
    diarios["retorno_24h"] = diarios.groupby("segmento", sort=False)["close"].transform(
        lambda valores: np.log(valores / valores.shift(1))
    )
    medias = diarios.groupby("segmento", sort=False)["close"].transform(
        lambda valores: valores.rolling(7, min_periods=7).mean()
    )
    diarios["distancia_sma_7d"] = diarios["close"] / medias - 1.0
    diarios["volatilidade_7d"] = diarios.groupby("segmento", sort=False)["retorno_24h"].transform(
        lambda valores: valores.rolling(7, min_periods=7).std(ddof=1)
    )
    return diarios.drop(columns=["segmento", "close"]).rename(columns={"fim_utc": "fim_diario_utc"})


def associar_indicadores(
    candles: pd.DataFrame, indicadores: pd.DataFrame
) -> pd.DataFrame:
    """Usa somente o último dia encerrado, nunca o fechamento de um dia em andamento."""
    if candles["fim_utc"].duplicated().any():
        raise ValueError("Candles com fim_utc duplicado.")
    diario = indicadores.sort_values("fim_diario_utc")
    resultado = pd.merge_asof(
        candles.sort_values("fim_utc"),
        diario,
        left_on="fim_utc",
        right_on="fim_diario_utc",
        direction="backward",
        allow_exact_matches=True,
    )
    obsoleto = (
        resultado["fim_diario_utc"].isna()
        | (resultado["fim_utc"] >= resultado["fim_diario_utc"] + pd.Timedelta(days=1))
    )
    for coluna in FEATURES_AMPLIADAS[5:]:
        resultado.loc[obsoleto, coluna] = np.nan
    return resultado.reset_index(drop=True)
