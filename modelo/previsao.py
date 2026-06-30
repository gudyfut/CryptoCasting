import json
import logging

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

from modelo import config
from modelo.mamba_modelo import carregar_modelo

logger = logging.getLogger(__name__)


def gerar_previsoes(par: str, nome: str = "mamba") -> dict:
    """Gera previsões 2-class (direcionais) para o conjunto de teste.

    Saída: apenas amostras UP/DOWN (NEUTRO excluído), com labels 0/1
    compatíveis com o modelo e o frontend. Timestamps e closes são
    resolvidos via join por timestamp entre normalizados e features
    (OHLCV cru) — não por posição de linha, que seria imprecisa.
    """
    model = carregar_modelo(par, nome)

    # --- Carregar dados ---
    df_raw = pd.read_parquet(config.DADOS_DIR / "features" / f"{par}.parquet")
    df_norm = pd.read_parquet(config.DADOS_DIR / "normalizados" / f"{par}.parquet")
    df_norm = df_norm.dropna().reset_index(drop=True)
    data = np.load(config.DADOS_DIR / "janelas" / par / "test.npz")

    X_all = torch.from_numpy(data["features"]).float()
    y_all = torch.from_numpy(data["targets"]).long()
    indices_all = data["indices"]
    tamanho_janela = X_all.shape[1]

    # --- Filtrar direcionais (2-class: 0=DOWN, 1=UP) ---
    mask_dir = (y_all != 1).numpy()
    X_dir = X_all[mask_dir]
    y_dir = (y_all[mask_dir] == 2).long()
    indices_dir = indices_all[mask_dir]

    # --- Mapear índices → timestamp + close via timestamp join ---
    ts_map = {ts: i for i, ts in enumerate(df_raw["timestamp"])}
    closes_raw = df_raw["close"].values

    ts_dir = []
    close_dir = []
    for j in range(len(indices_dir)):
        entry_pos_norm = int(indices_dir[j]) + tamanho_janela
        entry_ts = df_norm.iloc[entry_pos_norm]["timestamp"]
        entry_pos_raw = ts_map[entry_ts]
        ts_dir.append(str(entry_ts))
        close_dir.append(float(closes_raw[entry_pos_raw]))

    # --- Previsões em batches ---
    previsoes = []
    with torch.no_grad():
        batch = 256
        for start in range(0, len(X_dir), batch):
            end = min(start + batch, len(X_dir))
            X_batch = X_dir[start:end].to(config.DEVICE)
            logits = model(X_batch)
            probs = F.softmax(logits, dim=1)
            preds = logits.argmax(dim=1)

            for j in range(end - start):
                idx_local = start + j
                actual = int(y_dir[idx_local].item())
                predicted = int(preds[j].item())
                prob_alta = float(probs[j][1].item())

                previsoes.append({
                    "timestamp": ts_dir[idx_local],
                    "close": round(close_dir[idx_local], 2),
                    "atual": actual,
                    "previsto": predicted,
                    "correto": actual == predicted,
                    "probabilidade_alta": round(prob_alta, 4),
                })

    # --- Resumo ---
    metricas_path = config.RESULTADOS_DIR / f"{par}_{nome}_metricas.json"
    metricas = json.loads(metricas_path.read_text(encoding="utf-8")) if metricas_path.exists() else {}

    corretos = sum(1 for p in previsoes if p["correto"])
    resultado = {
        "par": par,
        "intervalo": "1h",
        "janela": tamanho_janela,
        "total_amostras": len(previsoes),
        "resumo": {
            "accuracy": corretos / len(previsoes) if previsoes else 0,
            "baseline_accuracy": metricas.get("baseline", {}).get("test", {}).get("accuracy", 0),
        },
        "previsoes": previsoes,
        "walk_forward": metricas.get("walk_forward", []),
        "historico": metricas.get("historico", {}),
        "metricas_modelo": {
            k: v for k, v in metricas.items()
            if k not in ("baseline", "historico", "walk_forward")
        },
        "metricas_baseline": metricas.get("baseline", {}),
    }

    saida = config.RESULTADOS_DIR / f"{par}_{nome}_previsoes.json"
    config.RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Previsoes salvas em {saida} ({len(previsoes)} amostras)")

    return resultado
