import json
import logging

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau

from modelo import config
from modelo.dataset import criar_dataloader
from modelo.mamba_modelo import MambaClassificador

logger = logging.getLogger(__name__)


def treinar(
    par: str,
    nome: str = "mamba",
    epochs: int | None = None,
    learning_rate: float | None = None,
    batch_size: int | None = None,
) -> tuple[MambaClassificador, dict]:
    epochs = epochs or config.EPOCHS
    lr = learning_rate or config.LEARNING_RATE
    batch_size = batch_size or config.BATCH_SIZE
    device = config.DEVICE

    torch.manual_seed(config.SEED)

    logger.info("=" * 60)
    logger.info(f"TREINAMENTO MAMBA — {par} / modelo='{nome}' (device: {device})")
    logger.info("=" * 60)

    train_loader = criar_dataloader(par, "train", batch_size=batch_size, shuffle=True, apenas_direcionais=True)
    val_loader = criar_dataloader(par, "val", batch_size=batch_size, shuffle=False, apenas_direcionais=True)

    modelo = MambaClassificador().to(device)
    otimizador = AdamW(
        modelo.parameters(), lr=lr, weight_decay=config.WEIGHT_DECAY
    )
    scheduler = ReduceLROnPlateau(otimizador, mode="max", factor=0.5, patience=5)
    criterio = nn.CrossEntropyLoss(label_smoothing=0.05)

    historico = {"train_loss": [], "val_loss": [], "val_acc": []}
    melhor_val_acc = 0.0
    paciencia = 0

    for epoch in range(1, epochs + 1):
        modelo.train()
        train_loss = 0.0
        for X, y in train_loader:
            X, y = X.to(device), y.to(device)
            otimizador.zero_grad()
            logits = modelo(X)
            loss = criterio(logits, y)
            if torch.isnan(loss):
                logger.warning(f"Epoch {epoch}: NaN no loss, pulando batch")
                continue
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                modelo.parameters(), config.GRAD_CLIP
            )
            otimizador.step()
            train_loss += loss.item() * X.size(0)
        train_loss /= len(train_loader.dataset)

        val_loss, val_acc = _avaliar_loss_acc(modelo, val_loader, criterio, device)
        scheduler.step(val_acc)

        historico["train_loss"].append(train_loss)
        historico["val_loss"].append(val_loss)
        historico["val_acc"].append(val_acc)

        logger.info(
            f"Epoch {epoch:3d}/{epochs} | "
            f"train_loss={train_loss:.4f} | val_loss={val_loss:.4f} | val_acc={val_acc:.4f}"
        )

        if val_acc > melhor_val_acc:
            melhor_val_acc = val_acc
            paciencia = 0
            _salvar_checkpoint(modelo, par, nome)
        else:
            paciencia += 1
            if paciencia >= config.EARLY_STOP_PATIENCE:
                logger.info(f"Early stopping na epoch {epoch}")
                break

    _carregar_checkpoint(modelo, par, nome)
    return modelo, historico


def _avaliar_loss_acc(modelo, loader, criterio, device) -> tuple[float, float]:
    modelo.eval()
    total_loss, corretos, n = 0.0, 0, 0
    with torch.no_grad():
        for X, y in loader:
            X, y = X.to(device), y.to(device)
            logits = modelo(X)
            total_loss += criterio(logits, y).item() * X.size(0)
            corretos += (logits.argmax(dim=1) == y).sum().item()
            n += X.size(0)
    return total_loss / n, corretos / n


def _salvar_checkpoint(modelo, par: str, nome: str):
    config.RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)
    torch.save(
        modelo.state_dict(), config.RESULTADOS_DIR / f"{par}_{nome}.pt"
    )
    meta = {
        "d_model": config.D_MODEL,
        "n_layers": config.N_LAYERS,
        "d_input": config.D_INPUT,
        "d_state": config.D_STATE,
        "d_conv": config.D_CONV,
        "expand": config.EXPAND,
        "num_classes": config.NUM_CLASSES,
        "pooling": config.POOLING,
        "dropout": config.DROPOUT,
    }
    meta_path = config.RESULTADOS_DIR / f"{par}_{nome}_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def _carregar_checkpoint(modelo, par: str, nome: str):
    path = config.RESULTADOS_DIR / f"{par}_{nome}.pt"
    if not path.exists():
        return
    modelo.load_state_dict(
        torch.load(path, map_location=config.DEVICE)
    )
