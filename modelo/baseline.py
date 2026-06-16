import logging

import torch
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)

from modelo.dataset import carregar_split

logger = logging.getLogger(__name__)

CLOSE_IDX = 3


def _metricas(y_true, y_pred) -> dict:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }


def baseline_ingenuo(par: str) -> dict:
    """Prediz: direção do próximo dia = direção do dia atual (momentum).

    'Hoje' é o último candle da janela; compara close[-1] vs close[-2].
    A normalização (Standard/MinMax) é monótona, então o sinal é preservado.
    """
    metricas_por_split = {}
    for split in ("train", "val", "test"):
        X, y = carregar_split(par, split)
        ultimo_close = X[:, -1, CLOSE_IDX]
        penult_close = X[:, -2, CLOSE_IDX]
        pred = (ultimo_close > penult_close).long().numpy()
        y_np = y.numpy()

        metricas_por_split[split] = _metricas(y_np, pred)
        logger.info(
            f"Baseline {par}/{split}: acc={metricas_por_split[split]['accuracy']:.4f}"
        )
    return metricas_por_split
