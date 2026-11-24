"""Consumo e inferência; não contém treinamento, coleta ou seleção de modelos."""
from .consumo import ConsumoModelos, carregar_consumo
from .naive import prever_naive

__all__ = ['ConsumoModelos', 'carregar_consumo', 'prever_naive']
