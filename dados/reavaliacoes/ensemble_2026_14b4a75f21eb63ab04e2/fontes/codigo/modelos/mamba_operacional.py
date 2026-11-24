"""Adaptador do Mamba oficial: uma saída terminal ou dois payoffs por origem.

Mantém o núcleo histórico por herança, sem alterar suas fontes/fábrica.
Não recebe alvos observados, scalers ou instruções de operação.
"""
from dataclasses import dataclass
import torch
from torch import nn
from .mamba import RedeMamba


@dataclass(frozen=True)
class EspecificacaoOperacional:
    identidade: str
    canais: tuple[str, ...]
    contexto: int
    saidas: tuple[str, ...]

    def __post_init__(self):
        if not self.identidade or type(self.contexto) is not int or self.contexto <= 0:
            raise ValueError('Identidade/contexto inválidos.')
        if not isinstance(self.canais, tuple) or not self.canais or len(set(self.canais)) != len(self.canais):
            raise ValueError('Canais inválidos.')
        if any(not isinstance(c, str) or not c for c in self.canais):
            raise ValueError('Nome de canal inválido.')
        if self.saidas not in [('log_retorno_24h',), ('payoff_compra', 'payoff_venda')]:
            raise ValueError('Contrato de saída desconhecido.')

    @property
    def dimensao_entrada(self):
        return len(self.canais)


class RedeMambaOperacional(RedeMamba):
    def __init__(self, especificacao: EspecificacaoOperacional, parametros):
        if not isinstance(especificacao, EspecificacaoOperacional):
            raise TypeError('Especificação operacional obrigatória.')
        chaves = {'largura', 'estado', 'camadas', 'convolucao', 'expansao', 'dropout'}
        if set(parametros) != chaves:
            raise ValueError('Parâmetros completos e exclusivos obrigatórios.')
        for nome in chaves - {'dropout'}:
            if type(parametros[nome]) is not int or parametros[nome] <= 0:
                raise ValueError('Dimensão deve ser inteiro positivo.')
        if parametros['convolucao'] != 4 or parametros['expansao'] != 2:
            raise ValueError('Esta linha fixa d_conv4 e expand2.')
        if type(parametros['dropout']) not in [int,float] or not 0 <= parametros['dropout'] < 1:
            raise ValueError('Dropout inválido.')
        super().__init__(especificacao, parametros)
        if len(especificacao.saidas) == 2:
            self.saida = nn.Linear(parametros['largura'], 2)

    def forward(self, x):
        y = super().forward(x)
        if len(self.especificacao.saidas) == 1:
            y = y.unsqueeze(-1)
        if y.shape != (len(x), len(self.especificacao.saidas)) or not torch.isfinite(y).all():
            raise ValueError('Saída exige [lote, canais_alvo] finitos, sem broadcasting.')
        return y
