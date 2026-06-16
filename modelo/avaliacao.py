import json
import logging

import torch
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
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }


def salvar_metricas(par: str, metricas: dict):
    config.RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)
    path = config.RESULTADOS_DIR / f"{par}_metricas.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)
    logger.info(f"Métricas salvas em {path}")
