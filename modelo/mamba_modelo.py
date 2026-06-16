import logging

import torch
import torch.nn as nn

from modelo import config

logger = logging.getLogger(__name__)


def _importar_mamba():
    """Importa o bloco Mamba oficial; cai para o fallback puro-PyTorch se faltar."""
    try:
        from mamba_ssm import Mamba

        logger.info("Usando mamba-ssm oficial (CUDA)")
        return Mamba
    except ImportError:
        try:
            from modelo.mamba_minimal import Mamba

            logger.info("Usando mamba-minimal (PyTorch puro / fallback)")
            return Mamba
        except ImportError as e:
            raise ImportError(
                "Nenhuma implementação do Mamba encontrada. "
                "Instale `mamba-ssm` ou mantenha `modelo/mamba_minimal.py`."
            ) from e


class MambaClassificador(nn.Module):
    """Mamba empilhado + head de classificação direcional.

    Entrada:  (batch, seq_len, d_input)
    Saída:    (batch, num_classes) logits
    """

    def __init__(
        self,
        d_input: int | None = None,
        d_model: int | None = None,
        n_layers: int | None = None,
        d_state: int | None = None,
        d_conv: int | None = None,
        expand: int | None = None,
        num_classes: int | None = None,
        pooling: str | None = None,
        dropout: float | None = None,
    ):
        super().__init__()
        d_input = d_input or config.D_INPUT
        d_model = d_model or config.D_MODEL
        n_layers = n_layers or config.N_LAYERS
        d_state = d_state or config.D_STATE
        d_conv = d_conv or config.D_CONV
        expand = expand or config.EXPAND
        num_classes = num_classes or config.NUM_CLASSES
        pooling = pooling or config.POOLING
        dropout = 0.0 if dropout is None else dropout

        Mamba = _importar_mamba()

        self.input_proj = nn.Linear(d_input, d_model)
        self.layers = nn.ModuleList(
            [
                Mamba(
                    d_model=d_model,
                    d_state=d_state,
                    d_conv=d_conv,
                    expand=expand,
                )
                for _ in range(n_layers)
            ]
        )
        self.dropout = nn.Dropout(dropout)
        self.norm = nn.LayerNorm(d_model)
        self.pooling = pooling
        self.classifier = nn.Linear(d_model, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.input_proj(x)
        for layer in self.layers:
            x = layer(x)
        x = self.dropout(x)
        x = self.norm(x)

        if self.pooling == "last":
            x = x[:, -1, :]
        elif self.pooling == "mean":
            x = x.mean(dim=1)
        else:
            raise ValueError(f"Pooling desconhecido: {self.pooling}")

        return self.classifier(x)
