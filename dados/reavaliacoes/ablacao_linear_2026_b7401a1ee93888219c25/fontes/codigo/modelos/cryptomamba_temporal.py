"""Variante temporal do CMamba de Sepehri et al. (MIT), Mamba-1 oficial.

Núcleo e atribuição preservados em experimento_cryptomamba.modelo; original e
licença: registros/cryptomamba/fontes_externas/. Esta adaptação acrescenta uma
projeção por dia e altera a dimensão da cabeça; não é mera transposição.
"""
from types import FunctionType, MethodType
import torch
from torch import nn
from experimento_cryptomamba.modelo import NucleoCMamba


class CryptoMambaTemporal(nn.Module):
    def __init__(self, configuracao):
        super().__init__()
        a = configuracao['arquitetura']
        self.projecao_entrada = nn.Linear(6, 14)
        self.nucleo = NucleoCMamba(14, a['larguras'], a['densidade'],
                                  a['estado'], a['convolucao'], a['expansao'],
                                  a['eps_layernorm'])

    def forward(self, x):
        if (x.ndim != 3 or tuple(x.shape[1:]) != (14, 6)
                or not x.is_cuda or x.dtype != torch.float32):
            raise ValueError('Contrato temporal: [lote,14dias,6canais], float32 CUDA.')
        return self.nucleo(self.projecao_entrada(x)).reshape(len(x))


def construir(configuracao):
    from mamba_ssm import Mamba
    from mamba_ssm.ops.selective_scan_interface import selective_scan_ref
    if (configuracao['execucao_numerica'] != 'mamba1_oficial_scan_ref_cuda'
            or not torch.cuda.is_available()):
        raise RuntimeError('Mamba-1 oficial com scan de referência CUDA obrigatório.')
    rede = CryptoMambaTemporal(configuracao).cuda().float()
    torch.use_deterministic_algorithms(True, warn_only=False)
    for camada in rede.modules():
        if isinstance(camada, Mamba):
            assert camada.__class__.__module__ == 'mamba_ssm.modules.mamba_simple'
            camada.use_fast_path = False
            globais = dict(Mamba.forward.__globals__)
            globais['selective_scan_fn'] = selective_scan_ref
            funcao = FunctionType(Mamba.forward.__code__, globais,
                                  Mamba.forward.__name__, Mamba.forward.__defaults__,
                                  Mamba.forward.__closure__)
            funcao.__kwdefaults__ = Mamba.forward.__kwdefaults__
            camada.forward = MethodType(funcao, camada)
    return rede
