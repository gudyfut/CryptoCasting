"""Mesmas operações do treinador instrumentado; construtor privado por eixo.

FunctionType troca apenas o construtor e os marcos de observação no namespace
privado da função; não modifica globals, classes ou fontes de outros ciclos.
"""
from types import FunctionType
import torch
from infraestrutura.artefatos import ler_json, sha256
from experimentos.sem_penalizacao_diaria import treinamento as herdado
from experimentos.cryptomamba_reproducivel.modelo import construir as canais
from modelos.cryptomamba_temporal import construir as temporal

inferir = herdado.inferir


def construir(c):
    if c['eixo'] == 'canais':
        return canais(c)
    if c['eixo'] == 'dias':
        return temporal(c)
    raise ValueError('Eixo desconhecido.')


def ajustar(dados, c, seed, destino, vinculo, epocas=None):
    globais = dict(herdado.ajustar.__globals__)
    globais.update(construir=construir, EPOCAS=tuple(c['observacao_epocas']))
    funcao = FunctionType(herdado.ajustar.__code__, globais, herdado.ajustar.__name__,
                          herdado.ajustar.__defaults__, herdado.ajustar.__closure__)
    return funcao(dados, c, seed, destino, vinculo, epocas)


def carregar_rede(pasta, c):
    selecao = ler_json(pasta/'selecao.json')
    assert sha256(pasta/selecao['checkpoint']) == selecao['sha256']
    checkpoint = torch.load(pasta/selecao['checkpoint'], map_location='cpu', weights_only=True)
    assert checkpoint['epoca'] == selecao['epoca']
    rede = construir(c)
    rede.load_state_dict(checkpoint['pesos'], strict=True)
    return rede.eval()
