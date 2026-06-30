import logging
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler

from pipeline import config

logger = logging.getLogger(__name__)

SCALERS = {
    "standard": StandardScaler,
    "minmax": MinMaxScaler,
}


def normalizar(
    df: pd.DataFrame,
    metodo: Literal["standard", "minmax"] = "standard",
    train_ratio: float | None = None,
) -> tuple[pd.DataFrame, object]:
    train_ratio = train_ratio or config.TRAIN_RATIO

    df = df.copy()

    feature_cols = [c for c in df.columns if c not in ("timestamp", "direcao")]
    target_col = "direcao"

    scaler_cls = SCALERS.get(metodo)
    if scaler_cls is None:
        raise ValueError(f"Método de normalização desconhecido: {metodo}. Opções: {list(SCALERS)}")

    scaler = scaler_cls()

    split_idx = int(len(df) * train_ratio)
    df_train = df.iloc[:split_idx]

    scaler.fit(df_train[feature_cols])

    df[feature_cols] = scaler.transform(df[feature_cols])
    df[feature_cols] = df[feature_cols].clip(-5, 5)

    return df, scaler


def executar_normalizacao(
    par: str,
    metodo: str | None = None,
    train_ratio: float | None = None,
) -> tuple[pd.DataFrame, object]:
    metodo = metodo or config.NORMALIZADOR

    logger.info("=" * 60)
    logger.info(f"ETAPA 4 — NORMALIZAÇÃO: {par} (método: {metodo})")
    logger.info("=" * 60)

    path_features = config.DADOS_DIR / "features" / f"{par}.parquet"
    if not path_features.exists():
        logger.error(f"Arquivo de features não encontrado: {path_features}")
        return pd.DataFrame(), None

    df = pd.read_parquet(path_features)

    df_valid = df.dropna(subset=["direcao"]).copy()
    df_valid.reset_index(drop=True, inplace=True)
    logger.info(f"Registros válidos (direção definida): {len(df_valid)}")

    df_norm, scaler = normalizar(df_valid, metodo=metodo, train_ratio=train_ratio)

    path_norm = config.DADOS_DIR / "normalizados" / f"{par}.parquet"
    path_norm.parent.mkdir(parents=True, exist_ok=True)
    df_norm.to_parquet(path_norm, index=False)
    logger.info(f"Salvo em {path_norm.name} ({len(df_norm)} registros)")

    return df_norm, scaler
