"""Dados Binance Spot: coleta, validação e candles; sem alvos ou normalização de modelos."""
from .contratos import Periodo
from .pipeline import importar_arquivos, coletar_api, baixar_arquivos, agregar_mercado, carregar_candles

__all__ = ['Periodo', 'importar_arquivos', 'coletar_api', 'baixar_arquivos', 'agregar_mercado', 'carregar_candles']
