# Plano científico do TCC

## Objetivo

Investigar como moeda, contexto, prazo e configuração do Mamba afetam a previsão de primeiro toque em barreiras e sua utilidade econômica após custos. Comparar com LSTM e AR(1), documentando toda a sequência de hipóteses e tentativas.

O [protocolo 2.1](docs/protocolo_experimental.md) é a referência metodológica. O projeto é iterativo: a primeira grade estabelece a referência; os ciclos seguintes procuram melhorias no desenvolvimento. O teste final fica separado dessa seleção.

## Ciclo inicial

| Fator | Valores |
|---|---|
| Moedas | BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT |
| Candle de entrada | 1h |
| Contextos | 24 e 168 candles |
| Prazos máximos | 1h, 24h, 168h |
| Alvo | Inferior primeiro, prazo esgotado, superior primeiro |
| Distância | Desvio padrão dos últimos 168 retornos horários × raiz do prazo |
| Execução/rótulo | OHLCV 1m, com ordem ambígua sinalizada |
| Redes | Mamba e LSTM, largura 32, duas camadas |
| Operação | Spot comprado/caixa, sem alavancagem, custos e risco explícitos |

Desenvolvimento em quatro folds de 2023, seed 42: 192 ajustes neurais. AR(1) é ajustado uma vez por moeda/fold e reutilizado entre contextos. A grade final predefinida em 2024–2025 fica bloqueada enquanto a busca estiver em andamento.

## Ciclos seguintes

Após analisar a referência, registrar outra hipótese e configuração antes de executar. Podem ser estudados contexto/prazo, largura, camadas, estado interno, convolução, expansão, dropout e otimização do Mamba. Evitar mudar tudo ao mesmo tempo; comparar cada ciclo com uma referência explícita e custo medido.

Log-loss média nos folds de desenvolvimento é o critério preditivo inicial. Risco, retorno líquido, exposição e custo computacional compõem a análise de utilidade. Não trocar a métrica depois de ver um resultado nem escolher apenas seeds favoráveis. Testes de desenvolvimento consultados repetidamente são parte da busca, não confirmação independente.

## Primeiro ciclo concluído em 18/10/2026

1. Concluído: implementação e verificação de rótulos, entradas causais, purgas, scalers e operação.
2. Concluído: coleta de 144 meses somados entre moedas e dataset `9341610dbb329a858784`, sem interpolação.
3. Concluído: ambiente CUDA, Mamba oficial e qualificação Monte Carlo do AR(1).
4. Concluído: duas células iniciais integradas à grade; recargas exatas em todas as células.
5. Concluído: DB1–DB4, 96 células auditadas, 192 ajustes neurais, 16 ajustes únicos AR(1); identidade `4e232a796fcda0ea34c3`.
6. Concluído: [análise completa](historico/analises/ciclo_001_resultados.md), tabelas e [proposta delimitada do ciclo 002](historico/ciclos/ciclo_002_proposto.md).

O próximo ciclo foi apenas proposto: estado Mamba 16→8 no prazo semanal, quatro moedas e ambos os contextos, 64 ajustes neurais no executor pareado. Sua qualificação específica e comparação entre ciclos precisam ser preparadas antes da execução. Não é uma configuração final escolhida. B1–B4 seguem bloqueados até congelamento e declaração de exposição prévia.

O pesquisador autorizou execução autônoma de coleta, pipeline, treino e testes nesta sessão. O [andamento](docs/andamento.md) registra o que realmente foi comprovado; a existência de código não significa que a grade foi executada.
