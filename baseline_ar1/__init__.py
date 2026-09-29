"""Baseline ARIMA(1,0,0) nos log-retornos, estimada como AR(1) por MQO."""

from .modelo import ajustar_ar1, construir_pares_autorregressivos, prever_amostras

__all__ = ["ajustar_ar1", "construir_pares_autorregressivos", "prever_amostras"]
