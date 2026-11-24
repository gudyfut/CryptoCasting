"""LSTM causal sobre os 14 candles da representação diária preservada."""
import torch
from torch import nn


class LSTMDiaria(nn.Module):
    def __init__(self, largura=32, camadas=2):
        super().__init__()
        self.recorrente = nn.LSTM(6, largura, num_layers=camadas, batch_first=True,
                                  dropout=0.0, bidirectional=False)
        self.saida = nn.Linear(largura, 1)

    def forward(self, x):
        if x.ndim != 3 or x.shape[1:] != (6, 14):
            raise ValueError('Esperado tensor [lote, 6 canais, 14 dias].')
        z, _ = self.recorrente(x.transpose(1, 2).contiguous())
        return self.saida(z[:, -1, :]).squeeze(-1)
