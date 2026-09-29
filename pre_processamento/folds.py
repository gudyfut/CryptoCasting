"""Blocos cronológicos, purga e transformação ajustada apenas no treino."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from .contrato import FEATURES_AMPLIADAS, FEATURES_OHLCV, candles_por_contexto


@dataclass(frozen=True)
class Fold:
    nome: str
    tipo: str
    fim_treino: str
    fim_validacao: str
    fim_teste: str


FOLDS = (
    Fold("D1", "desenvolvimento", "2022-10-01", "2023-01-01", "2023-04-01"),
    Fold("D2", "desenvolvimento", "2023-01-01", "2023-04-01", "2023-07-01"),
    Fold("D3", "desenvolvimento", "2023-04-01", "2023-07-01", "2023-10-01"),
    Fold("D4", "desenvolvimento", "2023-07-01", "2023-10-01", "2024-01-01"),
    Fold("F1", "final", "2023-10-01", "2024-01-01", "2024-04-01"),
    Fold("F2", "final", "2024-01-01", "2024-04-01", "2024-07-01"),
    Fold("F3", "final", "2024-04-01", "2024-07-01", "2024-10-01"),
    Fold("F4", "final", "2024-07-01", "2024-10-01", "2025-01-01"),
    Fold("F5", "final", "2024-10-01", "2025-01-01", "2025-04-01"),
    Fold("F6", "final", "2025-01-01", "2025-04-01", "2025-07-01"),
    Fold("F7", "final", "2025-04-01", "2025-07-01", "2025-10-01"),
    Fold("F8", "final", "2025-07-01", "2025-10-01", "2026-01-01"),
)


def separar_fold(amostras: pd.DataFrame, fold: Fold) -> dict[str, pd.DataFrame]:
    """Filtra pela origem e exige término do alvo estritamente antes da fronteira."""
    origem = amostras["origem_utc"]
    alvo = amostras["alvo_fim_utc"]
    inicio = pd.Timestamp("2021-01-01", tz="UTC")
    fim_treino = pd.Timestamp(fold.fim_treino, tz="UTC")
    fim_validacao = pd.Timestamp(fold.fim_validacao, tz="UTC")
    fim_teste = pd.Timestamp(fold.fim_teste, tz="UTC")
    mascara = {
        "treino": (origem >= inicio) & (origem < fim_treino) & (alvo < fim_treino),
        "validacao": (origem >= fim_treino) & (origem < fim_validacao) & (alvo < fim_validacao),
        "teste": (origem >= fim_validacao) & (origem < fim_teste) & (alvo < fim_teste),
    }
    return {nome: amostras.loc[selecao].copy().reset_index(drop=True) for nome, selecao in mascara.items()}


def indices_candles_unicos(amostras_treino: pd.DataFrame, quantidade_candles: int) -> np.ndarray:
    """União dos intervalos de entrada, sem repetir candles de janelas sobrepostas."""
    if amostras_treino.empty:
        raise ValueError("Fold de treino vazio: não é possível ajustar scaler.")
    inicios = amostras_treino["indice_contexto_inicio"].to_numpy(dtype="int64")
    fins = amostras_treino["indice_contexto_fim"].to_numpy(dtype="int64")
    if (inicios < 0).any() or (fins >= quantidade_candles).any() or (fins < inicios).any():
        raise ValueError("Intervalos de contexto fora do parquet de candles.")
    diferencas = np.zeros(quantidade_candles + 1, dtype="int64")
    np.add.at(diferencas, inicios, 1)
    np.add.at(diferencas, fins + 1, -1)
    return np.flatnonzero(np.cumsum(diferencas[:-1]) > 0)


def ajustar_normalizador(
    candles: pd.DataFrame,
    amostras_treino: pd.DataFrame,
    features: tuple[str, ...] = FEATURES_OHLCV,
) -> tuple[StandardScaler, np.ndarray]:
    """Retorna scaler e índices usados; chamar novamente em cada fold/célula."""
    if features not in (FEATURES_OHLCV, FEATURES_AMPLIADAS):
        raise ValueError("A lista e ordem das features devem seguir o protocolo.")
    indices = indices_candles_unicos(amostras_treino, len(candles))
    valores = candles.iloc[indices][list(features)].to_numpy(dtype="float64")
    if not np.isfinite(valores).all():
        raise ValueError("Feature ausente/não finita em candle de treino.")
    normalizador = StandardScaler().fit(valores)
    return normalizador, indices


def montar_janela(
    candles: pd.DataFrame,
    amostra: pd.Series,
    features: tuple[str, ...],
    normalizador: StandardScaler | None = None,
) -> np.ndarray:
    """Confere timestamps e posições contra o mesmo parquet antes de montar a entrada."""
    inicio = int(amostra["indice_contexto_inicio"])
    fim = int(amostra["indice_contexto_fim"])
    alvo = int(amostra["indice_alvo"])
    if candles.empty or "par" not in candles or "granularidade" not in candles:
        raise ValueError("Parquet de candles sem identidade da célula.")
    if (
        candles.iloc[0]["par"] != amostra["par"]
        or candles.iloc[0]["granularidade"] != amostra["granularidade"]
    ):
        raise ValueError("Amostra de outro par ou outra granularidade.")
    if inicio < 0 or fim < inicio or alvo <= fim or alvo >= len(candles):
        raise ValueError("Índices de amostra inválidos.")
    if (
        fim - inicio + 1 != candles_por_contexto(str(amostra["granularidade"]), int(amostra["contexto_dias"]))
        or alvo - fim != int(amostra["horizonte_candles"])
    ):
        raise ValueError("Dimensão da janela ou horizonte divergente do metadado.")
    if (
        candles.iloc[inicio]["abertura_utc"] != amostra["contexto_inicio_utc"]
        or candles.iloc[fim]["fim_utc"] != amostra["origem_utc"]
        or candles.iloc[alvo]["fim_utc"] != amostra["alvo_fim_utc"]
    ):
        raise ValueError("Amostra não pertence a este parquet de candles.")
    valores = candles.iloc[inicio : fim + 1][list(features)].to_numpy(dtype="float64")
    if not np.isfinite(valores).all():
        raise ValueError("Janela contém feature não finita.")
    return normalizador.transform(valores) if normalizador is not None else valores
