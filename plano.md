# TCC - Previsibilidade de Criptomoedas com a Arquitetura Mamba

## Contexto do Projeto

Este projeto corresponde ao Trabalho de Conclusão de Curso (TCC) de Ciência da Computação.

Título do trabalho:

**"Previsibilidade de Criptomoedas com a Arquitetura Mamba: Desenvolvimento e Avaliação de um Sistema de Forecasting Temporal"**

O objetivo principal não é construir um sistema de trading nem maximizar lucro financeiro.

O foco científico do trabalho é investigar se a arquitetura Mamba é capaz de identificar padrões temporais úteis em séries históricas de criptomoedas, produzindo previsões superiores a um modelo de referência ingênuo.

A hipótese principal é que o Mamba consegue extrair informação relevante dos dados históricos de mercado e superar consistentemente um baseline simples.

A hipótese alternativa é que o mercado de criptomoedas apresenta volatilidade, ruído e não-estacionaridade suficientes para impedir ganhos significativos de previsão, mesmo utilizando arquiteturas modernas.

Ambos os resultados são cientificamente válidos.

---

# Objetivos do Sistema

O sistema deve ser capaz de:

1. Coletar dados históricos de criptomoedas.
2. Realizar pré-processamento dos dados.
3. Gerar indicadores técnicos.
4. Construir janelas temporais para treinamento.
5. Treinar um modelo baseado em Mamba.
6. Avaliar o desempenho do modelo.
7. Comparar os resultados com um modelo de referência ingênuo.
8. Gerar visualizações e métricas para análise dos resultados.

---

# Escopo

O projeto NÃO deve:

* Utilizar notícias.
* Utilizar redes sociais.
* Utilizar dados macroeconômicos.
* Utilizar análise de sentimento.
* Utilizar LLMs para previsão.
* Utilizar múltiplas arquiteturas concorrentes.

O foco está exclusivamente na arquitetura Mamba.

O trabalho não pretende descobrir qual arquitetura é melhor.

O trabalho pretende investigar a capacidade preditiva do Mamba em dados históricos de criptomoedas.

---

# Arquitetura Geral do Sistema

O sistema deve seguir o pipeline:

Dados Brutos
↓
Pré-processamento
↓
Feature Engineering
↓
Construção de Janelas Temporais
↓
Treinamento Mamba
↓
Avaliação
↓
Visualização dos Resultados

---

# Fonte de Dados

Utilizar APIs públicas.

Prioridade:

1. Binance API
2. Yahoo Finance (fallback)

Ativos inicialmente previstos:

* BTCUSDT

Posteriormente o sistema deve permitir expansão para:

* ETHUSDT
* SOLUSDT
* BNBUSDT

Sem alterações significativas na arquitetura.

---

# Dados Coletados

Os dados mínimos esperados são:

* Open
* High
* Low
* Close
* Volume

(OHLCV)

Cada registro deve possuir timestamp.

---

# Pipeline de Dados

## Etapa 1 — Coleta

Responsabilidades:

* Baixar dados históricos.
* Armazenar localmente.
* Evitar downloads repetidos.
* Permitir atualização incremental.

Saída:

dataset bruto em CSV ou Parquet.

---

## Etapa 2 — Limpeza

Responsabilidades:

* Ordenar registros por data.
* Verificar duplicidades.
* Tratar valores ausentes.
* Garantir consistência temporal.

Saída:

dataset limpo.

---

## Etapa 3 — Feature Engineering

Além dos dados OHLCV, gerar indicadores técnicos.

Indicadores inicialmente previstos:

### Médias móveis

* SMA 7
* SMA 21
* SMA 50

### RSI

* RSI 14

### MACD

* MACD
* Signal
* Histogram

### Retornos

* Retorno diário
* Retorno acumulado

### Volatilidade

* Volatilidade móvel

Todos os indicadores devem ser calculados apenas com informações disponíveis até aquele instante.

Nunca utilizar dados futuros.

---

## Etapa 4 — Normalização

Aplicar normalização apenas utilizando informações do conjunto de treinamento.

Evitar data leakage.

Possíveis estratégias:

* StandardScaler
* MinMaxScaler

A implementação deve permitir troca futura do método.

---

## Etapa 5 — Construção de Janelas Temporais

O sistema utilizará sliding windows.

Exemplo:

Janela = 60 dias

Entrada:

Dia 1
...
Dia 60

Saída:

Dia 61

O tamanho da janela deve ser parametrizável.

Não utilizar valores fixos espalhados pelo código.

---

# Definição do Problema

Prioridade:

Classificação direcional.

Objetivo:

Prever se o próximo fechamento será:

* Alta
* Baixa

Representação:

0 = Baixa

1 = Alta

Opcionalmente o sistema pode futuramente suportar regressão de preço.

Porém a classificação direcional é o objetivo principal do TCC.

---

# Arquitetura do Modelo

O modelo principal deve utilizar Mamba.

Biblioteca preferencial:

mamba-ssm

Framework:

PyTorch

Não utilizar TensorFlow.

Toda a implementação deve ser compatível com GPU CUDA.

---

# Treinamento

O treinamento deve ser modular.

Componentes separados:

* Dataset
* DataLoader
* Modelo
* Treinamento
* Avaliação

Evitar scripts monolíticos.

---

# Avaliação

Métricas desejadas:

## Classificação

* Accuracy
* Precision
* Recall
* F1 Score

## Regressão (caso implementada)

* MAE
* RMSE
* MAPE

---

# Baseline

Implementar obrigatoriamente um modelo de referência ingênuo.

Exemplo:

Previsão da direção do próximo dia igual à direção observada no dia atual.

O Mamba deve ser comparado contra esse baseline.

A pergunta científica central do trabalho é:

"O Mamba consegue superar consistentemente um modelo ingênuo utilizando apenas dados históricos de mercado?"

---

# Validação

Utilizar Walk-Forward Validation.

Não utilizar validação aleatória.

Não utilizar shuffle.

A ordem temporal deve ser preservada.

O objetivo é simular condições reais de utilização.

---

# Visualizações

Gerar gráficos para análise.

Exemplos:

* Curvas de treinamento.
* Accuracy ao longo do tempo.
* Comparação Mamba vs Baseline.
* Predições corretas e incorretas.
* Evolução temporal dos erros.

---

# Requisitos de Código

Sempre priorizar:

* Legibilidade.
* Modularidade.
* Reutilização.
* Tipagem quando possível.
* Comentários apenas quando necessários.

Evitar:

* Código duplicado.
* Valores hardcoded.
* Dependências desnecessárias.

Toda implementação deve ser compatível com Python 3.11+.

---

# Objetivo Científico Final

O foco principal do projeto é responder à seguinte questão:

"Existem padrões previsíveis em séries históricas de criptomoedas que possam ser explorados pela arquitetura Mamba para produzir previsões direcionais superiores a um modelo de referência ingênuo?"

Todas as decisões de desenvolvimento devem contribuir para responder essa pergunta de forma experimental, reproduzível e cientificamente defensável.
