"""Detecção e caracterização de anomalias de preço em dados de crypto.

Uma anomalia é um movimento de preço que excede o esperado pela volatilidade
recente, numa janela de 1-3 candles de 1H. O z-score normaliza o retorno
pela regra √-tempo: z = retorno_H / (σ_1h × √H). Sob random walk, |z| > 3
ocorre em ~0.3% das amostras; em crypto (caudas pesadas) é mais frequente.
"""

import numpy as np
import pandas as pd


def carregar_dados(par: str, ano_inicio: int = 2023) -> pd.DataFrame:
    """Carrega features parquet, filtra por ano."""
    df = pd.read_parquet(f"dados/features/{par}.parquet")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df[df["timestamp"].dt.year >= ano_inicio].copy()
    df.reset_index(drop=True, inplace=True)
    return df


def detectar(
    df: pd.DataFrame,
    horizontes: tuple[int, ...] = (1, 2, 3),
    vol_janela: int = 168,
    threshold: float = 3.0,
) -> pd.DataFrame:
    """Marca candles anômalos baseado no z-score do forward return.

    Para cada candle t e horizonte H:
        z_H(t) = (close[t+H]/close[t] - 1) / (σ_1h_rolling × √H)

    Candle é anômalo se max|z_H| > threshold em qualquer horizonte.
    """
    close = df["close"]
    ret_1h = close.pct_change()
    sigma_1h = ret_1h.rolling(vol_janela, min_periods=21).std()

    z_abs_max = pd.Series(0.0, index=df.index)
    z_signed = pd.Series(0.0, index=df.index)

    for H in horizontes:
        ret_h = close.shift(-H) / close - 1
        esperado = sigma_1h * np.sqrt(H)
        z_h = (ret_h / esperado).replace([np.inf, -np.inf], np.nan)

        mask = z_h.abs() > z_abs_max
        z_abs_max = z_abs_max.where(~mask, z_h.abs())
        z_signed = z_signed.where(~mask, z_h)

    df["z_score"] = z_signed
    df["z_abs"] = z_abs_max
    df["anomalia"] = z_abs_max > threshold
    return df


def agrupar_eventos(
    df: pd.DataFrame,
    min_gap: int = 3,
) -> list[dict]:
    """Agrupa candles anômalos consecutos em eventos.

    Eventos separados por ≥ min_gap candles normais são distintos.
    Retorna lista de dicts com índices, timestamps, z_peak, direção, move.
    """
    eventos_idx: list[tuple[int, int]] = []
    in_event = False

    for i in range(len(df)):
        if df.iloc[i]["anomalia"]:
            if not in_event:
                start = i
                in_event = True
            end = i
        else:
            if in_event and (i - end) >= min_gap:
                eventos_idx.append((start, end))
                in_event = False

    if in_event:
        eventos_idx.append((start, end))

    resultado = []
    for start, end in eventos_idx:
        seg = df.iloc[start : end + 1]
        closes = seg["close"].values
        z_vals = seg["z_score"].values

        max_up = (np.max(closes) / closes[0] - 1) * 100
        max_down = (np.min(closes) / closes[0] - 1) * 100

        if abs(max_up) >= abs(max_down):
            move_pct = float(max_up)
            direcao = "up"
        else:
            move_pct = float(max_down)
            direcao = "down"

        resultado.append({
            "start_idx": start,
            "end_idx": end,
            "onset": str(df.iloc[start]["timestamp"]),
            "fim": str(df.iloc[end]["timestamp"]),
            "duration": end - start + 1,
            "z_peak": float(np.max(np.abs(z_vals))),
            "direcao": direcao,
            "move_pct": move_pct,
        })

    return resultado


def extrair_janelas(
    df: pd.DataFrame,
    eventos: list[dict],
    contexto: int = 24,
    features: tuple[str, ...] | None = None,
) -> tuple[np.ndarray, list[str]]:
    """Extrai arrays (n_eventos, contexto, n_features) dos candles ANTES de cada evento.

    Linha i do array = candle [onset - contexto + i] até [onset - 1].
    Ignora eventos muito próximos do início dos dados.
    """
    if features is None:
        features = (
            "retorno_diario", "volatilidade_21", "volume", "rsi_14",
            "macd_hist", "dist_vwap", "wick_up", "wick_down",
            "volume_spike", "sweep_bull", "sweep_bear",
            "vol_zscore", "volume_zscore", "rsi_slope", "vwap_slope",
        )

    features_validos = [f for f in features if f in df.columns]

    janelas = []
    for ev in eventos:
        onset = ev["start_idx"]
        if onset - contexto < 0:
            continue
        window = df.iloc[onset - contexto : onset]
        janelas.append(window[features_validos].values)

    if not janelas:
        return np.array([]), features_validos

    return np.stack(janelas), features_validos


def amostrar_normais(
    df: pd.DataFrame,
    eventos: list[dict],
    contexto: int = 24,
    margem: int = 6,
    n: int | None = None,
    features: tuple[str, ...] | None = None,
    seed: int = 42,
) -> tuple[np.ndarray, list[str]]:
    """Amostra janelas de períodos normais (longe de qualquer anomalia).

    Exclui uma zona de margem ao redor de cada evento. Retorna o mesmo
    formato que extrair_janelas.
    """
    if features is None:
        features = (
            "retorno_diario", "volatilidade_21", "volume", "rsi_14",
            "macd_hist", "dist_vwap", "wick_up", "wick_down",
            "volume_spike", "sweep_bull", "sweep_bear",
            "vol_zscore", "volume_zscore", "rsi_slope", "vwap_slope",
        )

    features_validos = [f for f in features if f in df.columns]

    is_near = np.zeros(len(df), dtype=bool)
    for ev in eventos:
        s = max(0, ev["start_idx"] - contexto - margem)
        e = min(len(df), ev["end_idx"] + margem + 1)
        is_near[s:e] = True

    starts_validos = []
    for i in range(len(df) - contexto):
        if not is_near[i : i + contexto].any():
            starts_validos.append(i)

    if n is None:
        n = len(eventos)
    n = min(n, len(starts_validos))

    rng = np.random.RandomState(seed)
    starts = rng.choice(starts_validos, size=n, replace=False)

    janelas = []
    for s in starts:
        window = df.iloc[s : s + contexto]
        janelas.append(window[features_validos].values)

    return np.stack(janelas), features_validos
