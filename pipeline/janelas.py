import logging

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

from pipeline import config

logger = logging.getLogger(__name__)


class JanelaDataset(Dataset):
    def __init__(
        self,
        features: np.ndarray,
        targets: np.ndarray,
        indices: np.ndarray,
    ):
        self.features = torch.from_numpy(features).float()
        self.targets = torch.from_numpy(targets).long()
        self.indices = indices

    def __len__(self) -> int:
        return len(self.targets)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.features[idx], self.targets[idx]


def criar_janelas(
    df: pd.DataFrame,
    tamanho_janela: int | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    tamanho_janela = tamanho_janela or config.TAMANHO_JANELA

    df = df.dropna().copy()
    df.reset_index(drop=True, inplace=True)

    feature_cols = [c for c in df.columns if c not in ("timestamp", "direcao")]
    target_col = "direcao"

    features_array = df[feature_cols].values.astype(np.float32)
    targets_array = df[target_col].values.astype(np.int64)

    n_amostras = len(df) - tamanho_janela
    if n_amostras <= 0:
        raise ValueError(
            f"Dados insuficientes: {len(df)} registros para janela de {tamanho_janela}"
        )

    X = np.zeros((n_amostras, tamanho_janela, len(feature_cols)), dtype=np.float32)
    y = np.zeros(n_amostras, dtype=np.int64)
    indices = np.zeros(n_amostras, dtype=np.int64)

    for i in range(n_amostras):
        X[i] = features_array[i : i + tamanho_janela]
        y[i] = targets_array[i + tamanho_janela]
        indices[i] = i + tamanho_janela

    return X, y, indices


def split_temporal(
    X: np.ndarray,
    y: np.ndarray,
    indices: np.ndarray,
    train_ratio: float | None = None,
    val_ratio: float | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    train_ratio = train_ratio or config.TRAIN_RATIO
    val_ratio = val_ratio or config.VAL_RATIO

    n = len(y)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    return (
        X[:train_end], y[:train_end],
        X[train_end:val_end], y[train_end:val_end],
        X[val_end:], y[val_end:],
    )


def executar_janelas(
    par: str,
    tamanho_janela: int | None = None,
) -> dict[str, JanelaDataset] | None:
    tamanho_janela = tamanho_janela or config.TAMANHO_JANELA

    logger.info("=" * 60)
    logger.info(f"ETAPA 5 — JANELAS TEMPORAIS: {par} (janela: {tamanho_janela})")
    logger.info("=" * 60)

    path_norm = config.DADOS_DIR / "normalizados" / f"{par}.parquet"
    if not path_norm.exists():
        logger.error(f"Arquivo normalizado não encontrado: {path_norm}")
        return None

    df = pd.read_parquet(path_norm)
    logger.info(f"Registros carregados: {len(df)}")

    X, y, indices = criar_janelas(df, tamanho_janela)
    logger.info(f"Janelas criadas: {len(y)} (shape X: {X.shape})")

    X_train, y_train, X_val, y_val, X_test, y_test = split_temporal(X, y, indices)

    logger.info(f"Treino: {len(y_train)} | Val: {len(y_val)} | Teste: {len(y_test)}")

    datasets = {
        "train": JanelaDataset(X_train, y_train, np.arange(len(y_train))),
        "val": JanelaDataset(X_val, y_val, np.arange(len(y_val)) + len(y_train)),
        "test": JanelaDataset(X_test, y_test, np.arange(len(y_test)) + len(y_train) + len(y_val)),
    }

    path_saida = config.DADOS_DIR / "janelas" / par
    path_saida.mkdir(parents=True, exist_ok=True)
    for split_name, dataset in datasets.items():
        path_npz = path_saida / f"{split_name}.npz"
        np.savez(
            path_npz,
            features=dataset.features.numpy(),
            targets=dataset.targets.numpy(),
            indices=dataset.indices,
        )

    logger.info(f"Datasets salvos em {path_saida}")

    return datasets
