"""Treinador e construtor da ablação qualificada, sem alterar o módulo congelado."""
from experimentos.ablacao_linear_diaria.treinamento import ajustar, carregar_rede, inferir
from experimentos.ablacao_linear_diaria.modelo import construir, coeficientes_afins

# A função herdada constrói a rede pelo campo ramos_mamba e recebe weight_decay
# da receita efetiva. Não há monkeypatch, nova perda, precisão ou ordem de lotes.
