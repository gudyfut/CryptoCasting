import logging

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

from modelo import config

logger = logging.getLogger(__name__)


def carregar_split(par: str, split: str) -> tuple[torch.Tensor, torch.Tensor]:
    path = config.DADOS_DIR / "janelas" / par / f"{split}.npz"
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset não encontrado: {path}\n"
            "Execute a pipeline primeiro: python run_pipeline.py"
        )
    data = np.load(path)
    X = torch.from_numpy(data["features"]).float()
    y = torch.from_numpy(data["targets"]).long()
    logger.info(f"{par}/{split}: X={tuple(X.shape)}, y={tuple(y.shape)}")
    return X, y


def carregar_split_direcional(par: str, split: str) -> tuple[torch.Tensor, torch.Tensor]:
    """Carrega apenas amostras UP/DOWN (exclui NEUTRO) e remapeia para 0/1."""
    X, y = carregar_split(par, split)
    mask = y != 1  # remove NEUTRO
    X_dir = X[mask]
    y_dir = (y[mask] == 2).long()  # UP(2)->1, DOWN(0)->0
    logger.info(f"{par}/{split} direcional: X={tuple(X_dir.shape)} ({int(mask.sum())}/{len(y)})")
    return X_dir, y_dir


def criar_dataloader(
    par: str,
    split: str,
    batch_size: int | None = None,
    shuffle: bool = False,
    apenas_direcionais: bool = False,
) -> DataLoader:
    batch_size = batch_size or config.BATCH_SIZE
    if apenas_direcionais:
        X, y = carregar_split_direcional(par, split)
    else:
        X, y = carregar_split(par, split)
    dataset = TensorDataset(X, y)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=0,
        pin_memory=(config.DEVICE == "cuda"),
    )
