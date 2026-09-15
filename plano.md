# Plano científico do TCC

**Título:** Previsibilidade de Criptomoedas com a Arquitetura Mamba: um Sistema de Forecasting Temporal.

## Objetivo

Investigar se um classificador Mamba consegue prever a direção de retornos futuros de BTC, ETH e XRP a partir de OHLCV, superar um baseline ingênuo e apresentar diferenças de desempenho entre granularidades de candle.

## Escopo

- Arquitetura Mamba, implementada em PyTorch, com fallback PyTorch preservado.
- Dados Binance Spot de pares cotados em USDT; OHLCV e indicadores derivados causalmente.
- Classificação direcional binária, avaliação temporal e resultados por moeda × granularidade.
- Sem notícias, redes sociais, sentimento, dados macroeconômicos ou previsão com LLMs.
- Sem comparação com arquiteturas neurais concorrentes e sem regressão de preço nesta versão. Random walk, prevalência, momentum e AR(1) são referências metodológicas obrigatórias.
- Rentabilidade de trading não é a variável de sucesso científico.

## Protocolo de referência

As decisões operacionais, fórmulas, datas e critérios de avaliação estão em [docs/protocolo_experimental.md](docs/protocolo_experimental.md), que substitui as definições do protótipo anterior.

Um resultado sem superioridade do Mamba também responde à pergunta científica. A conclusão deve acompanhar as evidências, inclusive limitações de amostragem e incerteza.
