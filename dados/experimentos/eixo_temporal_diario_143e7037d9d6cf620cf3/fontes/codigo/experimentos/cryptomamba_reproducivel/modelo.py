"""Mamba-1 oficial com scan de referência oficial em CUDA, sem kernel fused.

Não altera o pacote instalado nem o forward de outras instâncias/ciclos.
O forward oficial recebe um namespace privado com selective_scan_ref, mantendo
os pesos, convolução causal oficial, equações, dimensões e parâmetros públicos.
"""
from types import FunctionType, MethodType
import torch
from mamba_ssm import Mamba
from mamba_ssm.ops.selective_scan_interface import selective_scan_ref
from modelos.cryptomamba_diario import construir as construir_original


def construir(c):
    if c.get('execucao_numerica') != 'mamba1_oficial_scan_ref_cuda':
        raise ValueError('Backend explícito obrigatório; nenhum fallback automático.')
    rede = construir_original(c)
    torch.use_deterministic_algorithms(True, warn_only=False)
    for camada in rede.modules():
        if isinstance(camada, Mamba):
            camada.use_fast_path = False
            globais = dict(Mamba.forward.__globals__)
            globais['selective_scan_fn'] = selective_scan_ref
            funcao = FunctionType(Mamba.forward.__code__, globais, Mamba.forward.__name__,
                                  Mamba.forward.__defaults__, Mamba.forward.__closure__)
            funcao.__kwdefaults__ = Mamba.forward.__kwdefaults__
            camada.forward = MethodType(funcao, camada)
    return rede
