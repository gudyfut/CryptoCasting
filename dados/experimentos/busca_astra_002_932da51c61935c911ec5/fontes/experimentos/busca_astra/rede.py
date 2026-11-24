"""Mamba-1 oficial CUDA; variacoes explicitas, nunca fallback."""
import torch
from torch import nn

class Rede(nn.Module):
    def __init__(self, receita, canais):
        super().__init__()
        import selective_scan_cuda
        import causal_conv1d_cuda
        from mamba_ssm import Mamba
        assert Mamba.__module__ == 'mamba_ssm.modules.mamba_simple'
        self.receita = receita
        self.canais = canais
        d = receita['largura']
        self.projecao = nn.Linear(canais, d)
        self.blocos = nn.ModuleList([Mamba(d_model=d, d_state=receita['estado'], d_conv=4, expand=2)
                                    for _ in range(receita['camadas'])])
        self.normas = nn.ModuleList([nn.LayerNorm(d) for _ in self.blocos])
        self.dropout = nn.Dropout(receita['dropout'])
        self.norma_final = nn.LayerNorm(d)
        self.saida = nn.Linear(d, 1)

    def representar(self, x):
        assert x.ndim == 3 and tuple(x.shape[1:]) == (self.receita['contexto'], self.canais)
        assert x.dtype == torch.float32 and x.device.type == 'cuda' and torch.isfinite(x).all()
        x = self.projecao(x)
        for b, n in zip(self.blocos, self.normas):
            x = x + b(n(x))
        x = self.norma_final(self.dropout(x))
        return x[:, -1] if self.receita['pooling'] == 'ultimo' else x.mean(1)

    def forward(self, x):
        return self.saida(self.representar(x)).squeeze(-1)

def editar_cabeca(rede, ganho, media_alvo, escala_alvo):
    """Edicao deterministica dos pesos: retorno real final = ganho * retorno anterior."""
    with torch.no_grad():
        rede.saida.weight.mul_(ganho)
        rede.saida.bias.mul_(ganho).add_((ganho-1.)*media_alvo/escala_alvo)
