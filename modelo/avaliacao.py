import json
import logging

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)

from modelo import config

logger = logging.getLogger(__name__)


def avaliar(modelo, loader, device: str | None = None) -> dict:
    device = device or config.DEVICE
    modelo.eval()
    y_true, y_pred = [], []

    with torch.no_grad():
        for X, y in loader:
            X = X.to(device)
            logits = modelo(X)
            preds = logits.argmax(dim=1).cpu()
            y_true.extend(y.numpy())
            y_pred.extend(preds.numpy())

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
    }


def avaliar_seletivo(
    modelo,
    loader,
    device: str | None = None,
    limiares: tuple[float, ...] = (0.50, 0.52, 0.55, 0.58, 0.60, 0.65, 0.70),
) -> list[dict]:
    """Avaliação com abstenção por confiança (previsão seletiva).

    A confiança de cada amostra é max(softmax). O modelo só "opina" quando a
    confiança >= limiar; nos demais casos ele se abstém. Mostra o trade-off
    cobertura x acurácia: conforme o limiar sobe, a cobertura cai e (se houver
    sinal) a acurácia sobe. Se a acurácia cair com o limiar, o modelo está
    "confiantemente errado" — sinal de que não há borda.
    """
    device = device or config.DEVICE
    modelo.eval()
    probs_all, y_all = [], []
    with torch.no_grad():
        for X, y in loader:
            X = X.to(device)
            p = F.softmax(modelo(X), dim=1).cpu()
            probs_all.append(p)
            y_all.append(y)

    probs = torch.cat(probs_all)
    y = torch.cat(y_all)
    conf = probs.max(dim=1).values
    preds = probs.argmax(dim=1)
    n = len(y)

    resultados = []
    for lim in limiares:
        mask = conf >= lim
        n_voto = int(mask.sum())
        if n_voto == 0:
            resultados.append({
                "limiar": round(lim, 2),
                "cobertura": 0.0,
                "n_amostras": 0,
                "accuracy": None,
                "precision": None,
                "recall": None,
                "f1": None,
            })
            continue
        yt = y[mask].numpy()
        yp = preds[mask].numpy()
        resultados.append({
            "limiar": round(lim, 2),
            "cobertura": n_voto / n,
            "n_amostras": n_voto,
            "accuracy": float(accuracy_score(yt, yp)),
            "precision": float(precision_score(yt, yp, average="macro", zero_division=0)),
            "recall": float(recall_score(yt, yp, average="macro", zero_division=0)),
            "f1": float(f1_score(yt, yp, average="macro", zero_division=0)),
        })
    return resultados


def avaliar_trade(
    par: str,
    modelo,
    device: str | None = None,
    horizonte: int | None = None,
    atr_janela: int = 14,
    rrs: tuple[float, ...] = (1.0, 2.0),
    limiar_confianca: float | None = None,
    n_amostras_debug: int = 0,
) -> dict:
    """Avalia expectancy (em R) via simulação de TP/SL no conjunto de teste direcional.

    Convenções:
    - Entrada: close[t] onde t é o candle previsto (fim da janela).
    - Stop: 1×ATR(14); TP: RR×stop.
    - Percurso: candles t+1..t+H.
    - TP antes de SL = +RR; SL antes de TP = -1.
    - Ambos no mesmo candle = -1 (conservador).
    - Sem hit em H candles = resolve por close[t+H] (R fracionário).

    Mapeamento de índices: o NPZ guarda window-index (posição da janela, não
    do dataframe). entry_pos = window_index + tamanho_janela dá a posição no
    normalizados pós-dropna+reset. O timestamp dessa linha é usado para
    localizar o candle correspondente no features parquet (OHLCV cru).
    """
    from pipeline import config as pipe_config

    device = device or config.DEVICE
    horizonte = horizonte or pipe_config.HORIZONTE

    # --- Carregar dados ---
    path_features = pipe_config.DADOS_DIR / "features" / f"{par}.parquet"
    path_norm = pipe_config.DADOS_DIR / "normalizados" / f"{par}.parquet"
    path_test = config.DADOS_DIR / "janelas" / par / "test.npz"

    for p in (path_features, path_norm, path_test):
        if not p.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {p}")

    df_raw = pd.read_parquet(path_features)
    df_norm = pd.read_parquet(path_norm).dropna().reset_index(drop=True)
    data = np.load(path_test)

    X_test = torch.from_numpy(data["features"]).float()
    y_test = torch.from_numpy(data["targets"]).long()
    indices_test = data["indices"]
    tamanho_janela = X_test.shape[1]

    # --- Filtrar direcionais (mesmo espaço 2-class do treino) ---
    mask_dir = (y_test != 1).numpy()
    X_dir = X_test[mask_dir]
    indices_dir = indices_test[mask_dir]

    # --- Previsões do modelo ---
    modelo.eval()
    with torch.no_grad():
        logits = modelo(X_dir.to(device))
        probs = F.softmax(logits, dim=1).cpu()
        preds = probs.argmax(dim=1).numpy()
        confianca = probs.max(dim=1).values.numpy()

    # --- Filtrar por confiança ---
    if limiar_confianca is not None:
        mask_conf = confianca >= limiar_confianca
        preds = preds[mask_conf]
        indices_dir = indices_dir[mask_conf]
        confianca = confianca[mask_conf]

    # --- Preparar arrays de preço (acesso numpy é muito mais rápido) ---
    highs = df_raw["high"].values
    lows = df_raw["low"].values
    closes = df_raw["close"].values

    prev_close = pd.Series(closes).shift(1)
    tr = np.maximum.reduce([
        highs - lows,
        np.abs(highs - prev_close.values),
        np.abs(lows - prev_close.values),
    ])
    atr_arr = pd.Series(tr).rolling(atr_janela, min_periods=atr_janela).mean().values

    ts_map = {ts: i for i, ts in enumerate(df_raw["timestamp"])}
    n_raw = len(df_raw)

    # --- Simular trades ---
    resultados_por_rr = {}

    for rr in rrs:
        rs = []
        debug_trades = []

        for j in range(len(preds)):
            entry_pos_norm = int(indices_dir[j]) + tamanho_janela
            if entry_pos_norm >= len(df_norm):
                continue

            entry_ts = df_norm.iloc[entry_pos_norm]["timestamp"]
            if entry_ts not in ts_map:
                continue
            entry_pos = ts_map[entry_ts]

            atr = atr_arr[entry_pos]
            if np.isnan(atr) or atr <= 0:
                continue

            entry_close = closes[entry_pos]
            stop_dist = float(atr)
            direcao = 1 if preds[j] == 1 else -1

            if direcao == 1:
                tp_price = entry_close + rr * stop_dist
                sl_price = entry_close - stop_dist
            else:
                tp_price = entry_close - rr * stop_dist
                sl_price = entry_close + stop_dist

            r = None
            for h in range(1, horizonte + 1):
                pos = entry_pos + h
                if pos >= n_raw:
                    break
                hit_tp = (highs[pos] >= tp_price) if direcao == 1 else (lows[pos] <= tp_price)
                hit_sl = (lows[pos] <= sl_price) if direcao == 1 else (highs[pos] >= sl_price)

                if hit_sl:
                    r = -1.0
                    break
                if hit_tp:
                    r = rr
                    break

            if r is None:
                pos_exit = min(entry_pos + horizonte, n_raw - 1)
                exit_close = closes[pos_exit]
                if direcao == 1:
                    r = (exit_close - entry_close) / stop_dist
                else:
                    r = (entry_close - exit_close) / stop_dist

            rs.append(r)

            if len(debug_trades) < n_amostras_debug:
                debug_trades.append({
                    "direcao": "long" if direcao == 1 else "short",
                    "entry": round(float(entry_close), 2),
                    "tp": round(float(tp_price), 2),
                    "sl": round(float(sl_price), 2),
                    "atr": round(stop_dist, 2),
                    "conf": round(float(confianca[j]), 3),
                    "r": round(r, 4),
                })

        arr = np.array(rs) if rs else np.array([])
        n = len(arr)

        chave = f"rr_{rr:.0f}"
        if n > 0:
            resultados_por_rr[chave] = {
                "rr": rr,
                "n_trades": n,
                "win_rate": float((arr > 0).mean()),
                "expectancy_r": float(arr.mean()),
                "std_r": float(arr.std()),
                "soma_r": float(arr.sum()),
            }
        else:
            resultados_por_rr[chave] = {
                "rr": rr, "n_trades": 0, "win_rate": None,
                "expectancy_r": None, "std_r": None, "soma_r": None,
            }

        if debug_trades:
            resultados_por_rr[chave]["debug"] = debug_trades

    return resultados_por_rr


def avaliar_regime(
    par: str,
    modelo,
    device: str | None = None,
    horizonte: int | None = None,
    atr_janela: int = 14,
    rrs: tuple[float, ...] = (1.0, 2.0),
) -> list[dict]:
    """Acuracia direcional + expectancy de TP/SL por regime de volatilidade.

    Divide o teste direcional em buckets de vol_zscore e reporta, para cada:
    - n amostras
    - acuracia direcional (acertou up/down?)
    - win_rate e expectancy em R para cada nivel de RR

    Responde duas perguntas de uma vez:
    1. O modelo sabe direcao em periodos volateis?
    2. O modelo faz dinheiro onde?
    """
    from pipeline import config as pipe_config

    device = device or config.DEVICE
    horizonte = horizonte or pipe_config.HORIZONTE

    path_features = pipe_config.DADOS_DIR / "features" / f"{par}.parquet"
    path_norm = pipe_config.DADOS_DIR / "normalizados" / f"{par}.parquet"
    path_test = config.DADOS_DIR / "janelas" / par / "test.npz"

    for p in (path_features, path_norm, path_test):
        if not p.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {p}")

    df_raw = pd.read_parquet(path_features)
    df_norm = pd.read_parquet(path_norm).dropna().reset_index(drop=True)
    data = np.load(path_test)

    X_test = torch.from_numpy(data["features"]).float()
    y_test = torch.from_numpy(data["targets"]).long()
    indices_test = data["indices"]
    tamanho_janela = X_test.shape[1]

    mask_dir = (y_test != 1).numpy()
    X_dir = X_test[mask_dir]
    y_dir = (y_test[mask_dir] == 2).long().numpy()
    indices_dir = indices_test[mask_dir]

    modelo.eval()
    with torch.no_grad():
        logits = modelo(X_dir.to(device))
        preds = logits.argmax(dim=1).cpu().numpy()

    highs = df_raw["high"].values
    lows = df_raw["low"].values
    closes = df_raw["close"].values

    prev_close = pd.Series(closes).shift(1)
    tr = np.maximum.reduce([
        highs - lows,
        np.abs(highs - prev_close.values),
        np.abs(lows - prev_close.values),
    ])
    atr_arr = pd.Series(tr).rolling(atr_janela, min_periods=atr_janela).mean().values

    if "vol_zscore" in df_raw.columns:
        vol_z = df_raw["vol_zscore"].values
    else:
        vol = df_raw["volatilidade_21"]
        vol_m = vol.rolling(50, min_periods=20).mean()
        vol_s = vol.rolling(50, min_periods=20).std()
        vol_z = ((vol - vol_m) / vol_s.replace(0, np.nan)).fillna(0).values

    ts_map = {ts: i for i, ts in enumerate(df_raw["timestamp"])}
    n_raw = len(df_raw)

    trades = []
    for j in range(len(preds)):
        entry_pos_norm = int(indices_dir[j]) + tamanho_janela
        if entry_pos_norm >= len(df_norm):
            continue
        entry_ts = df_norm.iloc[entry_pos_norm]["timestamp"]
        if entry_ts not in ts_map:
            continue
        entry_pos = ts_map[entry_ts]

        atr = atr_arr[entry_pos]
        if np.isnan(atr) or atr <= 0:
            continue

        entry_close = closes[entry_pos]
        stop_dist = float(atr)
        direcao = 1 if preds[j] == 1 else -1
        z = float(vol_z[entry_pos]) if not np.isnan(vol_z[entry_pos]) else 0.0

        r_por_rr = {}
        for rr in rrs:
            if direcao == 1:
                tp_price = entry_close + rr * stop_dist
                sl_price = entry_close - stop_dist
            else:
                tp_price = entry_close - rr * stop_dist
                sl_price = entry_close + stop_dist

            r = None
            for h in range(1, horizonte + 1):
                pos = entry_pos + h
                if pos >= n_raw:
                    break
                hit_tp = (highs[pos] >= tp_price) if direcao == 1 else (lows[pos] <= tp_price)
                hit_sl = (lows[pos] <= sl_price) if direcao == 1 else (highs[pos] >= sl_price)
                if hit_sl:
                    r = -1.0
                    break
                if hit_tp:
                    r = rr
                    break

            if r is None:
                pos_exit = min(entry_pos + horizonte, n_raw - 1)
                exit_close = closes[pos_exit]
                if direcao == 1:
                    r = (exit_close - entry_close) / stop_dist
                else:
                    r = (entry_close - exit_close) / stop_dist

            r_por_rr[rr] = r

        trades.append({
            "correct": bool(preds[j] == y_dir[j]),
            "vol_zscore": z,
            **{f"rr_{rr:.0f}": r_por_rr[rr] for rr in rrs},
        })

    buckets = [
        ("calmo", "z < 0", lambda z: z < 0),
        ("normal", "0 <= z < 1", lambda z: 0 <= z < 1),
        ("ativo", "z >= 1", lambda z: z >= 1),
    ]

    resultado = []
    for nome, faixa, fn in buckets:
        grupo = [t for t in trades if fn(t["vol_zscore"])]
        n = len(grupo)
        if n == 0:
            resultado.append({"regime": nome, "faixa": faixa, "n": 0, "accuracy": None})
            continue

        entry = {
            "regime": nome,
            "faixa": faixa,
            "n": n,
            "accuracy": float(np.mean([t["correct"] for t in grupo])),
        }
        for rr in rrs:
            chave = f"rr_{rr:.0f}"
            rs = np.array([t[chave] for t in grupo])
            entry[f"win_rate_{chave}"] = float((rs > 0).mean())
            entry[f"expectancy_{chave}"] = float(rs.mean())

        resultado.append(entry)

    return resultado


def salvar_metricas(par: str, metricas: dict, nome: str = "mamba"):
    config.RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)
    path = config.RESULTADOS_DIR / f"{par}_{nome}_metricas.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)
    logger.info(f"Métricas salvas em {path}")
