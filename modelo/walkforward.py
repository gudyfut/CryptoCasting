import logging

import torch
from torch.utils.data import DataLoader, TensorDataset

from modelo import config
from modelo.avaliacao import avaliar
from modelo.dataset import carregar_split_direcional
from modelo.mamba_modelo import carregar_modelo

logger = logging.getLogger(__name__)


def walk_forward(par: str, nome: str = "mamba", n_folds: int = 5) -> list[dict]:
    """Avalia o modelo treinado em fatias temporais sucessivas do conjunto de teste.

    Mostra se a performance se mantém estável ou degrada ao longo do tempo
    (crítico para séries financeiras não-estacionárias).
    """
    X_test, y_test = carregar_split_direcional(par, "test")
    device = config.DEVICE

    modelo = carregar_modelo(par, nome)

    fold_size = max(1, len(y_test) // n_folds)
    resultados = []

    for k in range(n_folds):
        start = k * fold_size
        end = (k + 1) * fold_size if k < n_folds - 1 else len(y_test)
        if start >= end:
            break

        idx = torch.arange(start, end)
        X_fold = X_test[idx]
        y_fold = y_test[idx]

        loader = DataLoader(TensorDataset(X_fold, y_fold), batch_size=config.BATCH_SIZE)
        m = avaliar(modelo, loader)
        m["fold"] = k
        m["periodo"] = f"{start}-{end}"
        m["n_amostras"] = int(end - start)
        resultados.append(m)
        logger.info(
            f"Walk-forward fold {k} ({m['periodo']}): "
            f"acc={m['accuracy']:.4f} f1={m['f1']:.4f}"
        )

    return resultados
