"""Avaliação direcional descritiva da baseline, sem Mamba nem teste PT."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)


def calcular_metricas(previsoes: pd.DataFrame) -> dict[str, object]:
    reais = previsoes["classe_alta"].to_numpy(dtype="int8")
    estimadas = previsoes["classe_prevista_ar1"].to_numpy(dtype="int8")
    if len(reais) == 0 or not np.isin(reais, [0, 1]).all() or not np.isin(estimadas, [0, 1]).all():
        raise ValueError("Classes vazias ou diferentes de 0/1.")
    suporte = np.bincount(reais, minlength=2)
    precisao, revocacao, f1, _ = precision_recall_fscore_support(
        reais, estimadas, labels=[0, 1], zero_division=0,
    )
    ambas_presentes = bool((suporte > 0).all())
    return {
        "amostras": len(reais),
        "suporte_nao_alta": int(suporte[0]),
        "suporte_alta": int(suporte[1]),
        "empates": int(previsoes["empate"].sum()),
        "predicoes_nao_alta": int((estimadas == 0).sum()),
        "predicoes_alta": int((estimadas == 1).sum()),
        "balanced_accuracy": float(balanced_accuracy_score(reais, estimadas)) if ambas_presentes else None,
        "accuracy": float(accuracy_score(reais, estimadas)),
        "f1_macro": float(np.mean(f1)),
        "por_classe": {
            str(classe): {
                "precision": float(precisao[classe]),
                "recall": float(revocacao[classe]),
                "f1": float(f1[classe]),
                "suporte": int(suporte[classe]),
            }
            for classe in (0, 1)
        },
        "matriz_confusao_linhas_reais_colunas_previstas": confusion_matrix(
            reais, estimadas, labels=[0, 1],
        ).tolist(),
    }
