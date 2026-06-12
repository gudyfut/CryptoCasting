import logging

import numpy as np
import pandas as pd

from pipeline import config

logger = logging.getLogger(__name__)


def sma(df: pd.DataFrame, periodos: list[int]) -> pd.DataFrame:
    df = df.copy()
    close = df["close"]
    for p in periodos:
        df[f"sma_{p}"] = close.rolling(window=p, min_periods=p).mean()
    return df


def rsi(df: pd.DataFrame, periodo: int) -> pd.DataFrame:
    df = df.copy()
    delta = df["close"].diff()

    ganho = delta.where(delta > 0, 0.0)
    perda = (-delta).where(delta < 0, 0.0)

    avg_ganho = ganho.ewm(alpha=1 / periodo, min_periods=periodo).mean()
    avg_perda = perda.ewm(alpha=1 / periodo, min_periods=periodo).mean()

    rs = avg_ganho / avg_perda.replace(0, np.nan)
    df[f"rsi_{periodo}"] = 100.0 - (100.0 / (1.0 + rs))
    return df


def macd(df: pd.DataFrame, rapido: int, lento: int, sinal: int) -> pd.DataFrame:
    df = df.copy()
    ema_rapida = df["close"].ewm(span=rapido, min_periods=rapido).mean()
    ema_lenta = df["close"].ewm(span=lento, min_periods=lento).mean()

    df["macd"] = ema_rapida - ema_lenta
    df["macd_signal"] = df["macd"].ewm(span=sinal, min_periods=sinal).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    return df


def retornos(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["retorno_diario"] = df["close"].pct_change()
    df["retorno_acumulado"] = df["retorno_diario"].cumsum()
    return df


def volatilidade(df: pd.DataFrame, janela: int) -> pd.DataFrame:
    df = df.copy()
    df[f"volatilidade_{janela}"] = df["retorno_diario"].rolling(window=janela).std()
    return df


def gerar_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df = sma(df, config.SMA_PERIODOS)
    df = rsi(df, config.RSI_PERIODO)
    df = macd(df, config.MACD_RAPIDO, config.MACD_LENTO, config.MACD_SINAL)
    df = retornos(df)
    df = volatilidade(df, config.VOLATILIDADE_JANELA)

    df["direcao"] = (df["close"].shift(-1) > df["close"]).astype(int)
    df.loc[df.index[-1], "direcao"] = np.nan

    return df


def executar_feature_engineering(par: str) -> pd.DataFrame:
    logger.info("=" * 60)
    logger.info(f"ETAPA 3 — FEATURE ENGINEERING: {par}")
    logger.info("=" * 60)

    path_processado = config.DADOS_DIR / "processados" / f"{par}.parquet"
    if not path_processado.exists():
        logger.error(f"Arquivo processado não encontrado: {path_processado}")
        return pd.DataFrame()

    df = pd.read_parquet(path_processado)
    logger.info(f"Registros de entrada: {len(df)}")

    df_features = gerar_features(df)

    nan_antes_drop = df_features.isnull().any(axis=1).sum()
    logger.info(f"Linhas com NaN (indicadores iniciais): {nan_antes_drop}")

    feature_cols = [c for c in df_features.columns if c not in ("timestamp", "direcao")]
    logger.info(f"Features geradas: {feature_cols}")

    path_features = config.DADOS_DIR / "features" / f"{par}.parquet"
    path_features.parent.mkdir(parents=True, exist_ok=True)
    df_features.to_parquet(path_features, index=False)
    logger.info(f"Salvo em {path_features.name} ({len(df_features)} registros)")

    return df_features
