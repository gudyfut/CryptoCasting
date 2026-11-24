"""CryptoMamba público com SSM oficial CUDA, seis canais e sem adapter temporal.

Estrutura MIT de Sepehri et al.; licença/original em registros/cryptomamba/fontes_externas/.
O núcleo já conferido é importado sem modificar a adaptação histórica.
"""
import torch
from torch import nn
from experimento_cryptomamba.modelo import NucleoCMamba


class CryptoMambaDiario(nn.Module):
    def __init__(self,c):
        super().__init__()
        if not torch.cuda.is_available():raise RuntimeError('CUDA oficial obrigatória; sem fallback.')
        a=c['arquitetura']
        self.nucleo=NucleoCMamba(6,a['larguras'],a['densidade'],a['estado'],a['convolucao'],a['expansao'],a['eps_layernorm'])

    def forward(self,x):
        if x.ndim!=3 or tuple(x.shape[1:])!=(6,14) or not x.is_cuda or x.dtype!=torch.float32:
            raise ValueError('Contrato obrigatório [lote,6,14], float32 CUDA.')
        return self.nucleo(x).reshape(len(x))


def construir(c):return CryptoMambaDiario(c).cuda().float()
