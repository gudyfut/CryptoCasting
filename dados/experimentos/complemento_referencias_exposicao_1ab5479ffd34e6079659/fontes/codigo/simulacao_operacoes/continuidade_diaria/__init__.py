"""Execução diária por variação líquida, com filtros por ordem e auditoria."""
from .simulador import simular
from .auditoria import conferir

__all__ = ['simular','conferir']
