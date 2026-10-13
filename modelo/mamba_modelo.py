"""Componente Mamba reutilizável; não contém configuração experimental ou treino."""

import logging

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


def _importar_mamba(backend: str = "automatico"):
    """Usa Mamba oficial quando disponível e mantém o fallback PyTorch."""
    if backend not in ("automatico", "oficial", "pytorch"):
        raise ValueError(f"Backend Mamba desconhecido: {backend}")
    if backend == "pytorch":
        from modelo.mamba_minimal import Mamba
        return Mamba
    try:
        from mamba_ssm import Mamba

        logger.info("Usando mamba-ssm oficial")
    except ImportError:
        if backend == "oficial":
            raise ImportError("Backend oficial solicitado, mas mamba_ssm não está disponível.")
        from modelo.mamba_minimal import Mamba

        logger.info("Usando fallback Mamba em PyTorch puro")
    return Mamba


class MambaClassificador(nn.Module):
    """Recebe (batch, sequência, entradas) e devolve logits de duas classes.

    Dimensões e regularização são fornecidas pelo experimento.
    A validação empírica do treinamento cabe ao piloto do pesquisador.
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
        backend: str = "automatico",
    ):
        super().__init__()
        if min(d_input, d_model, n_layers, d_state, d_conv, expand) <= 0:
            raise ValueError("As dimensões do modelo devem ser positivas.")
        if pooling not in ("last", "mean"):
            raise ValueError(f"Pooling desconhecido: {pooling}")
        if not 0 <= dropout < 1:
            raise ValueError("Dropout deve estar entre zero e um (exclusivo).")
        Mamba = _importar_mamba(backend)
        self.backend = "pytorch" if Mamba.__module__ == "modelo.mamba_minimal" else "oficial"
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
