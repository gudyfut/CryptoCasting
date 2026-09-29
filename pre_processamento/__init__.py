"""Construção auditável dos dados e índices de amostras da Entrega 3."""

from .contrato import ConfiguracaoProcessamento, carregar_configuracao_processamento
from .pipeline import executar_processamento

__all__ = ["ConfiguracaoProcessamento", "carregar_configuracao_processamento", "executar_processamento"]
