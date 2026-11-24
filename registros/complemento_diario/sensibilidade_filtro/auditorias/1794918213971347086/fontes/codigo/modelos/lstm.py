"""LSTM temporal unidirecional; canais derivados do contrato de entradas."""
from torch import nn
from .neurais import conferir_tensor


class RedeLSTM(nn.Module):
    def __init__(self, especificacao, parametros):
        super().__init__()
        self.especificacao = especificacao
        p = parametros
        self.recorrente = nn.LSTM(especificacao.dimensao_entrada, p['largura'], num_layers=p['camadas'],
                                 batch_first=True, dropout=p['dropout'] if p['camadas'] > 1 else 0,
                                 bidirectional=False)
        self.saida = nn.Linear(p['largura'], 1)

    def forward(self, x):
        conferir_tensor(x, self.especificacao)
        sequencia, _ = self.recorrente(x)
        return self.saida(sequencia[:, -1, :]).squeeze(-1)
