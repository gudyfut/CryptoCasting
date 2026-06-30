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


def vwap(df: pd.DataFrame, janela: int) -> pd.DataFrame:
    """VWAP rolling — benchmark institucional. Distância normalizada."""
    typical = (df["high"] + df["low"] + df["close"]) / 3
    vol = df["volume"]
    vol_sum = vol.rolling(janela, min_periods=1).sum()
    vwap_val = (typical * vol).rolling(janela, min_periods=1).sum() / vol_sum.replace(0, np.nan)
    df["dist_vwap"] = (df["close"] - vwap_val) / vwap_val.replace(0, np.nan)
    return df


def fair_value_gap(df: pd.DataFrame, lookback: int) -> pd.DataFrame:
    """Fair Value Gap — canais bull/bear SEPARADOS para forcar aprendizado direcional."""
    high, low, close = df["high"], df["low"], df["close"]

    bullish = low > high.shift(2)
    bearish = high < low.shift(2)

    bull_gap = (low - high.shift(2)).where(bullish, 0) / close
    bear_gap = (low.shift(2) - high).where(bearish, 0) / close

    df["fvg_bull"] = bull_gap.clip(lower=0)
    df["fvg_bear"] = bear_gap.clip(lower=0)
    df["fvg_ativo"] = (bullish | bearish).astype(float).rolling(lookback, min_periods=1).sum()
    return df


def order_blocks(df: pd.DataFrame, decay: float) -> pd.DataFrame:
    """Order Blocks — canais bull/bear SEPARADOS com decay independente."""
    bearish = df["close"] < df["open"]
    bullish = df["close"] > df["open"]

    bull_ob = bearish.shift(1) & (df["high"] > df["high"].shift(1))
    bear_ob = bullish.shift(1) & (df["low"] < df["low"].shift(1))

    bull_signed = pd.Series(0.0, index=df.index)
    bull_signed[bull_ob.fillna(False)] = 1.0
    bear_signed = pd.Series(0.0, index=df.index)
    bear_signed[bear_ob.fillna(False)] = 1.0

    df["ob_bull"] = bull_signed.ewm(alpha=decay, min_periods=1).mean()
    df["ob_bear"] = bear_signed.ewm(alpha=decay, min_periods=1).mean()
    return df


def estrutura_mercado(df: pd.DataFrame, janela: int) -> pd.DataFrame:
    """Estrutura de mercado — tendencia e breakout em canais bull/bear SEPARADOS."""
    high, low, close = df["high"], df["low"], df["close"]

    rolling_high = high.rolling(janela).max().shift(1)
    rolling_low = low.rolling(janela).min().shift(1)

    df["dist_resistencia"] = (rolling_high - close) / close
    df["dist_suporte"] = (close - rolling_low) / close

    bos_bull = close > rolling_high
    bos_bear = close < rolling_low

    # Tendencia como dois canais binarios separados
    bull_active = pd.Series(0.0, index=df.index)
    bull_active[bos_bull.fillna(False)] = 1.0
    bear_active = pd.Series(0.0, index=df.index)
    bear_active[bos_bear.fillna(False)] = 1.0
    df["tend_bull"] = bull_active.ewm(alpha=0.05, min_periods=1).mean()
    df["tend_bear"] = bear_active.ewm(alpha=0.05, min_periods=1).mean()

    # Breakout em canais separados
    df["breakout_bull"] = ((close - rolling_high).where(bos_bull.fillna(False), 0) / close).clip(lower=0)
    df["breakout_bear"] = ((rolling_low - close).where(bos_bear.fillna(False), 0) / close).clip(lower=0)

    # Contexto multi-timeframe: SMAs ja calculadas
    df["ctx_bull"] = ((df["sma_7"] - df["sma_50"]) / df["close"]).clip(lower=0)
    df["ctx_bear"] = ((df["sma_50"] - df["sma_7"]) / df["close"]).clip(lower=0)
    return df


def manipulacao(df: pd.DataFrame, vol_janela: int, sweep_janela: int) -> pd.DataFrame:
    """Features de manipulação — wick rejection, volume spike sem follow-through, liquidity sweep."""
    high, low, open_, close, volume = df["high"], df["low"], df["open"], df["close"], df["volume"]

    range_candle = (high - low).replace(0, np.nan)

    df["wick_up"] = (high - np.maximum(open_, close)) / range_candle
    df["wick_down"] = (np.minimum(open_, close) - low) / range_candle

    vol_mean = volume.rolling(vol_janela, min_periods=1).mean().shift(1)
    df["volume_spike"] = (volume / vol_mean.replace(0, np.nan)).fillna(1.0)

    ret_norm = df["retorno_diario"].abs() / (df[f"volatilidade_{vol_janela}"].replace(0, np.nan) + 1e-8)
    df["vol_price_div"] = (df["volume_spike"] * (1.0 - ret_norm).clip(lower=0)).clip(0, 5)

    rolling_high = high.rolling(sweep_janela).max().shift(1)
    rolling_low = low.rolling(sweep_janela).min().shift(1)

    sweep_bull_cond = (low < rolling_low) & (close > rolling_low)
    sweep_bear_cond = (high > rolling_high) & (close < rolling_high)

    sweep_bull = pd.Series(0.0, index=df.index)
    sweep_bull[sweep_bull_cond.fillna(False)] = ((rolling_low - low) / close).clip(lower=0)
    sweep_bear = pd.Series(0.0, index=df.index)
    sweep_bear[sweep_bear_cond.fillna(False)] = ((high - rolling_high) / close).clip(lower=0)

    df["sweep_bull"] = sweep_bull
    df["sweep_bear"] = sweep_bear

    return df


def features_derivados(df: pd.DataFrame, regime_janela: int, slope_janela: int) -> pd.DataFrame:
    """Meta-features que amplificam sinais direcionais fracos.

    A analise de anomalias mostrou que RSI e VWAP carregam sinal direcional
    estatisticamente significativo antes de movimentos anormais, mas o sinal
    e fraco e afogado pelo ruido nos valores pontuais. Estas features
    transformam valores pontuais em contexto dinamico:

    - vol_zscore:    volatilidade atual vs sua propria norma rolling
                     (sinaliza "algo esta acontecendo")
    - volume_zscore: volume atual vs sua propria norma rolling
    - rsi_slope:     direcao do momentum (RSI subindo/descendo)
    - vwap_slope:    forca da tendencia (preco divergindo/convergindo do VWAP)
    """
    df = df.copy()

    r_mean = df["volatilidade_21"].rolling(regime_janela, min_periods=20).mean()
    r_std = df["volatilidade_21"].rolling(regime_janela, min_periods=20).std()
    df["vol_zscore"] = (df["volatilidade_21"] - r_mean) / r_std.replace(0, np.nan)

    r_mean = df["volume"].rolling(regime_janela, min_periods=20).mean()
    r_std = df["volume"].rolling(regime_janela, min_periods=20).std()
    df["volume_zscore"] = (df["volume"] - r_mean) / r_std.replace(0, np.nan)

    df["rsi_slope"] = df["rsi_14"].diff(slope_janela) / slope_janela
    df["vwap_slope"] = df["dist_vwap"].diff(slope_janela)

    return df


def gerar_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df = sma(df, config.SMA_PERIODOS)
    df = rsi(df, config.RSI_PERIODO)
    df = macd(df, config.MACD_RAPIDO, config.MACD_LENTO, config.MACD_SINAL)
    df = retornos(df)
    df = volatilidade(df, config.VOLATILIDADE_JANELA)
    df = vwap(df, config.VWAP_JANELA)
    df = fair_value_gap(df, config.FVG_LOOKBACK)
    df = order_blocks(df, config.OB_DECAY)
    df = estrutura_mercado(df, config.ESTRUTURA_JANELA)
    df = manipulacao(df, config.VOLATILIDADE_JANELA, config.SWEEP_JANELA)
    df = features_derivados(df, config.REGIME_JANELA, config.SLOPE_JANELA)

    df["direcao"] = _label_regime(df, config.REGIME_K, config.HORIZONTE)

    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    for col in ["dist_vwap", "fvg_bull", "fvg_bear", "breakout_bull", "breakout_bear",
                 "dist_resistencia", "dist_suporte", "ctx_bull", "ctx_bear",
                 "ob_bull", "ob_bear", "tend_bull", "tend_bear",
                 "sweep_bull", "sweep_bear"]:
        if col in df.columns:
            df[col] = df[col].clip(-1.0, 1.0)

    for col in ["wick_up", "wick_down"]:
        if col in df.columns:
            df[col] = df[col].clip(0, 1)
    if "volume_spike" in df.columns:
        df["volume_spike"] = df["volume_spike"].clip(0, 5)

    for col in ["vol_zscore", "volume_zscore"]:
        if col in df.columns:
            df[col] = df[col].clip(-5, 5)
    for col in ["rsi_slope", "vwap_slope"]:
        if col in df.columns:
            df[col] = df[col].clip(-10, 10)

    return df


def _label_regime(df: pd.DataFrame, k: float, horizonte: int) -> pd.Series:
    """Label 3 classes sobre um horizonte de H candles: 0=baixa, 1=neutro, 2=alta.

    Threshold adaptativo escalado ao horizonte pela regra sqrt-tempo
    (variancia de um passeio aleatorio cresce linearmente com o tempo):
    k * vol_1h * sqrt(H). So movimentos que excedem a volatilidade esperada
    no horizonte sao classificados como direcionais; o resto vira NEUTRO.
    """
    fut_ret = df["close"].shift(-horizonte) / df["close"] - 1
    threshold = k * df["volatilidade_21"] * np.sqrt(horizonte)

    regime = pd.Series(config.REGIME_NEUTRO, index=df.index)
    regime[fut_ret > threshold] = config.REGIME_ALTA
    regime[fut_ret < -threshold] = config.REGIME_BAIXA
    regime.iloc[-horizonte:] = np.nan

    return regime


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
