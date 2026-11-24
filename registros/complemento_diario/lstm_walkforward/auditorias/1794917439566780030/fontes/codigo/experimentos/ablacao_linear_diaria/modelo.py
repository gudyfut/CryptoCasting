"""Preserva as projeções e seu RNG; remove os 12 blocos antes do treinamento.

Derivado do núcleo CryptoMamba de Sepehri et al. Não é Ridge nem arquitetura
SSM nova: restam quatro transformações afins, sem não linearidade.
"""
import torch
from torch import nn
from mamba_ssm import Mamba
from experimentos.cryptomamba_reproducivel.modelo import construir as construir_completo


def remover_ramos(rede):
    """Intervenção estrutural sem sorteio, atualização ou recarga de pesos."""
    assert len(rede.nucleo.blocks) == 3
    assert sum(isinstance(m, Mamba) for m in rede.modules()) == 12
    for bloco in rede.nucleo.blocks:
        assert len(bloco) == 5 and isinstance(bloco[4], nn.Linear)
        for indice in range(4):
            bloco[indice] = nn.Identity()
    assert sum(p.numel() for p in rede.parameters()) == 824
    assert not any(isinstance(m, Mamba) for m in rede.modules())
    assert not any(isinstance(m, nn.LayerNorm) for m in rede.modules())
    return rede


def construir(c):
    # Construir A primeiro consome exatamente o mesmo RNG e mantém os nomes e
    # pesos iniciais das projeções. Nenhum checkpoint de mercado é lido aqui.
    rede = construir_completo(c)
    if not c['ramos_mamba']:
        remover_ramos(rede)
    return rede


def coeficientes_afins(rede):
    """Decomposição em float64 das projeções; não ajusta coeficientes aos dados."""
    peso = torch.eye(14, dtype=torch.float64)
    vies = torch.zeros(14, dtype=torch.float64)
    for bloco in rede.nucleo.blocks:
        camada = bloco[4]
        a = camada.weight.detach().cpu().double()
        b = camada.bias.detach().cpu().double()
        peso, vies = a @ peso, a @ vies + b
    cabeca = rede.nucleo.post_process[1]
    canais = cabeca.weight.detach().cpu().double().reshape(6)
    coeficientes = canais[:, None] * peso.reshape(1, 14)
    intercepto = canais.sum() * vies[0] + cabeca.bias.detach().cpu().double()[0]
    return coeficientes.numpy(), float(intercepto)
