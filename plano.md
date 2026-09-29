# Plano científico do TCC

**Título:** Previsibilidade de Criptomoedas com a Arquitetura Mamba: um Sistema de Forecasting Temporal.

## Objetivo

Investigar se um classificador Mamba consegue prever a direção de retornos futuros de BTC, ETH, BNB e XRP a partir de OHLCV, superar o comparador estatístico ARIMA(1,0,0) e uma LSTM neural pareada, e apresentar diferenças de desempenho entre moedas, granularidades de candle, durações de contexto e horizontes de previsão.

## Escopo

- Arquitetura Mamba, implementada em PyTorch, com fallback PyTorch preservado.
- Dados Binance Spot de pares cotados em USDT; OHLCV e indicadores derivados causalmente.
- Classificação direcional binária, avaliação temporal e resultados separados por moeda, granularidade, contexto e horizonte.
- Sem notícias, redes sociais, sentimento, dados macroeconômicos ou previsão com LLMs.
- Sem outras arquiteturas neurais concorrentes além da LSTM definida como baseline, e sem regressão de preço nesta versão. ARIMA(1,0,0) nos log-retornos é o comparador estatístico simples; LSTM usa as mesmas janelas e features do Mamba para comparar arquiteturas. O random walk sem deriva é a referência clássica de previsão de preço e, convertido para este alvo binário, coincide com 50% de balanced accuracy. O teste de Pesaran–Timmermann é uma verificação distinta; não testa a diferença Mamba menos qualquer baseline.
- Rentabilidade de trading não é a variável de sucesso científico.

## Protocolo de referência

As decisões operacionais, fórmulas, datas e critérios de avaliação estão em [docs/protocolo_experimental.md](docs/protocolo_experimental.md), que substitui as definições do protótipo anterior.

Um resultado sem superioridade do Mamba também responde à pergunta científica. A conclusão deve acompanhar as evidências, inclusive limitações de amostragem e incerteza.
