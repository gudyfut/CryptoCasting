"""Persistência explícita: retorno real zero, não zero da escala normalizada."""
import numpy as np
from .contratos import montar_resultado


def prever_naive(pedido):
    return montar_resultado(pedido, np.zeros(len(pedido.origens), dtype=np.float64))
