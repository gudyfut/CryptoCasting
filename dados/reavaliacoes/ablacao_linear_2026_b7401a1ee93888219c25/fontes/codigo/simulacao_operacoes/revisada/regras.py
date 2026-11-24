"""Regras de pesquisa explícitas; não substituem exchangeInfo histórico/conta real."""
import math
from decimal import Decimal, ROUND_DOWN


def quantizar(valor, passo):
    if not math.isfinite(valor) or not math.isfinite(passo) or passo <= 0:
        raise ValueError('Quantidade/passo invalido.')
    # Conversão decimal evita arredondar uma venda acima da quantidade disponível.
    v, p = Decimal(str(abs(valor))), Decimal(str(passo))
    return math.copysign(float((v / p).to_integral_value(rounding=ROUND_DOWN) * p), valor)


def filtros(cfg, futuro):
    return cfg['filtros']['futuro' if futuro else 'spot']


def aumenta_risco(anterior, nova):
    return anterior * nova < 0 or abs(nova) > abs(anterior) + 1e-12


def separar_ordem(delta, posicao, futuro):
    """Redução primeiro; abertura na direção contrária é uma segunda ordem."""
    if not delta:
        return [(0., False)]
    if futuro and delta * posicao < 0:
        reducao = math.copysign(min(abs(delta), abs(posicao)), delta)
        resto = delta - reducao
        return [(reducao, True)] + ([(resto, False)] if abs(resto) > 1e-12 else [])
    return [(delta, False)]
