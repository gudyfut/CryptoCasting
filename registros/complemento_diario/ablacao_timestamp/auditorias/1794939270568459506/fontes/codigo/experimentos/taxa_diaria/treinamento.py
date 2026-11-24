"""Treinador herdado; cache de validação é uma opção técnica a qualificar."""
from types import FunctionType
import numpy as np
import torch
from experimentos.sem_penalizacao_diaria import treinamento as herdado


def construir_ajustador(cache_validacao=False):
    if not cache_validacao:
        return herdado.ajustar
    cache = {}

    def inferir(rede, x, lote=32):
        # Referência forte impede reutilização de id para outra matriz.
        chave = id(x)
        if chave not in cache:
            cache[chave] = (x, torch.as_tensor(x, device='cuda'))
        original, tensor = cache[chave]
        assert original is x
        rede.eval()
        with torch.inference_mode():
            partes = [rede(tensor[i:i+lote]) for i in range(0, len(x), lote)]
            return torch.cat(partes).cpu().numpy().astype(np.float64)

    globais = dict(herdado.ajustar.__globals__)
    globais['inferir'] = inferir
    funcao = FunctionType(herdado.ajustar.__code__, globais, herdado.ajustar.__name__,
                          herdado.ajustar.__defaults__, herdado.ajustar.__closure__)

    def ajustar(*args, **kwargs):
        try:
            return funcao(*args, **kwargs)
        finally:
            cache.clear()
            torch.cuda.empty_cache()
    return ajustar
