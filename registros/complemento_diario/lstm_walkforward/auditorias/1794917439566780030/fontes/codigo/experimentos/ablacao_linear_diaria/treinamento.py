"""Reutiliza o treinador aprovado, trocando somente o construtor em cópia privada."""
from types import FunctionType
import torch
from infraestrutura.artefatos import ler_json, sha256
from experimentos.penalizacao_seletiva_diaria import treinamento as herdado
from .modelo import construir

inferir = herdado.inferir


def ajustar(dados, c, seed, destino, vinculo, epocas=None):
    globais = dict(herdado.ajustar.__globals__)
    globais['construir'] = construir
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
