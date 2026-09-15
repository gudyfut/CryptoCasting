"""Componente Mamba reutilizável; não contém configuração experimental ou treino."""

import logging

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


def _importar_mamba():
    """Usa Mamba oficial quando disponível e mantém o fallback PyTorch."""
    try:
        from mamba_ssm import Mamba

        logger.info("Usando mamba-ssm oficial")
    except ImportError:
        from modelo.mamba_minimal import Mamba

        logger.info("Usando fallback Mamba em PyTorch puro")
    return Mamba


class MambaClassificador(nn.Module):
    """Recebe (batch, sequência, entradas) e devolve logits de duas classes.

    Dimensões e regularização devem ser fornecidas pelo futuro experimento.
    Este componente preservado ainda precisa de validação antes do estudo.
    """

    def __init__(
        self,
        *,
        d_input: int,
        d_model: int,
        n_layers: int,
        d_state: int,
        d_conv: int,
        expand: int,
        dropout: float,
        pooling: str = "last",
    ):
        super().__init__()
        if min(d_input, d_model, n_layers, d_state, d_conv, expand) <= 0:
            raise ValueError("As dimensões do modelo devem ser positivas.")
        if pooling not in ("last", "mean"):
            raise ValueError(f"Pooling desconhecido: {pooling}")
        Mamba = _importar_mamba()
        self.input_proj = nn.Linear(d_input, d_model)
        self.layers = nn.ModuleList([
            Mamba(d_model=d_model, d_state=d_state, d_conv=d_conv, expand=expand)
            for _ in range(n_layers)
        ])
        self.norms = nn.ModuleList([nn.LayerNorm(d_model) for _ in range(n_layers)])
        self.dropout = nn.Dropout(dropout)
        self.norm = nn.LayerNorm(d_model)
        self.pooling = pooling
        self.classifier = nn.Linear(d_model, 2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.input_proj(x)
        for layer, norm in zip(self.layers, self.norms):
            x = norm(x + layer(x))
        x = self.norm(self.dropout(x))
        x = x[:, -1, :] if self.pooling == "last" else x.mean(dim=1)
        return self.classifier(x)
