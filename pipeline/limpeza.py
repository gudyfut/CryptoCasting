import logging

import pandas as pd

from pipeline import config

logger = logging.getLogger(__name__)


def limpar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.sort_values("timestamp", inplace=True)
    df.reset_index(drop=True, inplace=True)

    dupes = df.duplicated(subset=["timestamp"], keep="first").sum()
    if dupes > 0:
        logger.info(f"Removendo {dupes} registros duplicados")
        df.drop_duplicates(subset=["timestamp"], keep="first", inplace=True)
        df.reset_index(drop=True, inplace=True)

    nulos = df.isnull().sum()
    if nulos.any():
        logger.info(f"Valores ausentes por coluna:\n{nulos[nulos > 0]}")
        df.dropna(subset=["open", "high", "low", "close", "volume"], inplace=True)
        df.reset_index(drop=True, inplace=True)

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)

    _validar_consistencia(df)

    return df


def _validar_consistencia(df: pd.DataFrame):
    timestamps = df["timestamp"]
    diffs = timestamps.diff().dropna()
    if len(diffs) == 0:
        return

    moda_diff = diffs.mode().iloc[0]
    gaps = diffs[diffs != moda_diff]
    if len(gaps) > 0:
        logger.info(f"Detectados {len(gaps)} gaps temporais no dataset")
        if len(gaps) <= 10:
            for idx in gaps.index:
                logger.info(f"  Gap em {df.loc[idx, 'timestamp']} (delta: {diffs.loc[idx]})")

    assert (df["high"] >= df["low"]).all(), "Inconsistência: High < Low detectado"
    assert (df["high"] >= df["open"]).all(), "Inconsistência: High < Open detectado"
    assert (df["high"] >= df["close"]).all(), "Inconsistência: High < Close detectado"
    assert (df["low"] <= df["open"]).all(), "Inconsistência: Low > Open detectado"
    assert (df["low"] <= df["close"]).all(), "Inconsistência: Low > Close detectado"
    assert (df["volume"] >= 0).all(), "Inconsistência: Volume negativo detectado"


def executar_limpeza(par: str) -> pd.DataFrame:
    logger.info("=" * 60)
    logger.info(f"ETAPA 2 — LIMPEZA: {par}")
    logger.info("=" * 60)

    path_bruto = config.DADOS_DIR / "brutos" / f"{par}.parquet"
    if not path_bruto.exists():
        logger.error(f"Arquivo bruto não encontrado: {path_bruto}")
        return pd.DataFrame()

    df = pd.read_parquet(path_bruto)
    logger.info(f"Registros brutos: {len(df)}")

    df_limpo = limpar(df)
    logger.info(f"Registros após limpeza: {len(df_limpo)}")

    path_limpo = config.DADOS_DIR / "processados" / f"{par}.parquet"
    path_limpo.parent.mkdir(parents=True, exist_ok=True)
    df_limpo.to_parquet(path_limpo, index=False)
    logger.info(f"Salvo em {path_limpo.name}")

    return df_limpo
