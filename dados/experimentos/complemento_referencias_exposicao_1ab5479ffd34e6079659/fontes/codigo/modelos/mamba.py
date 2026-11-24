"""Mamba-1 oficial: varredura temporal, projeção multivariada e saída terminal."""
from torch import nn
from .neurais import conferir_tensor


class RedeMamba(nn.Module):
    def __init__(self, especificacao, parametros):
        super().__init__()
        # Exigir extensões oficiais; nunca substituir por aproximação CPU/Python.
        import selective_scan_cuda
        import causal_conv1d_cuda
        from mamba_ssm import Mamba
        if Mamba.__module__ != 'mamba_ssm.modules.mamba_simple':
            raise RuntimeError('Classe Mamba-1 oficial esperada.')
        self.especificacao = especificacao
        p, d = parametros, parametros['largura']
        self.projecao = nn.Linear(especificacao.dimensao_entrada, d)
        self.blocos = nn.ModuleList([Mamba(d_model=d, d_state=p['estado'], d_conv=p['convolucao'],
                                         expand=p['expansao']) for _ in range(p['camadas'])])
        self.normas = nn.ModuleList([nn.LayerNorm(d) for _ in self.blocos])
        self.dropout = nn.Dropout(p['dropout'])
        self.norma_final = nn.LayerNorm(d)
        self.saida = nn.Linear(d, 1)

    def forward(self, x):
        conferir_tensor(x, self.especificacao)
        x = self.projecao(x)
        for bloco, norma in zip(self.blocos, self.normas):
            x = x + bloco(norma(x))
        return self.saida(self.norma_final(self.dropout(x))[:, -1, :]).squeeze(-1)
