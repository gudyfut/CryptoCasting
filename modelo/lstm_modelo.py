"""Baseline sequencial do protocolo 1.6; dimensões fornecidas pelo experimento."""

import torch
from torch import nn


class LSTMClassificador(nn.Module):
    def __init__(self, *, dimensao_entrada: int, largura: int = 32):
        super().__init__()
        if dimensao_entrada not in (5, 8) or largura not in (32, 64):
            raise ValueError("Dimensões LSTM fora do protocolo.")
        self.recorrente = nn.LSTM(
            input_size=dimensao_entrada, hidden_size=largura,
            num_layers=2, dropout=0.1, batch_first=True, bidirectional=False,
        )
        self.classificador = nn.Linear(largura, 2)

    def forward(self, entradas: torch.Tensor) -> torch.Tensor:
        # O estado começa em zero a cada janela; não atravessa batches/folds.
        sequencia, _ = self.recorrente(entradas)
        return self.classificador(sequencia[:, -1, :])
