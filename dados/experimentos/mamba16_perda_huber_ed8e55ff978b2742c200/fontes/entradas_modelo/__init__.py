"""Entradas, alvos e amostras; consome candles de mercado e não acessa a Binance."""
from .pipeline import preparar_entradas, carregar_conjunto
from .receitas import calcular_entradas, CANAIS

__all__ = ['preparar_entradas','carregar_conjunto','calcular_entradas','CANAIS']
