# Backtest de carteiras Spot com previsões já treinadas

Execução `8ec8a66648313caa48e3`.369simulações, zero novos treinamentos,17séries de previsão preservadas. [Protocolo](protocolo_backtest_carteira.md), [decisão](adr/0015-backtest-carteira.md), [estado/recibos](../registros/backtest_carteira/estado.json).

## Resultado principal e interpretação

Smart2% no Mamba16 terminou o teste com retorno líquido médio de **-8,79%**, drawdown médio por minuto-close de +34,43%, exposição média de 89,40% e 254,17 ordens. 0/6seeds terminaram com lucro. Com custos agravados: -9,49%.

Este cenário não produziu lucro médio. Uma regra mais cuidadosa não cria sinal preditivo automaticamente.

O controle Smart com previsão constante calibrada em2024 retornou -8,66%. Comparar com esse controle ajuda a investigar se a variação das previsões acrescentou algo ao viés médio. As exposições diferem: não é isolamento causal perfeito. Comprar/manter e caixa completam a comparação.

## Como a estratégia usa o modelo

A previsão continua sendo do retorno em24h. Smart transforma a alta prevista numa fração do caixa a comprar, e a queda numa fração do BTC a vender. Repete a decisão no próximo dia, mantendo o restante da posição. Uma previsão positiva pequena repetida pode acumular BTC até quase investir todo o caixa. Isso é diferente de manter uma pequena porcentagem fixa investida.

Vanilla1% compra/vende tudo apenas quando a variação prevista ultrapassa1%; caso contrário mantém a carteira. O controle diária24 vende a cada dia e decide se recompra. Nenhuma dessas regras foi ajustada para obter lucro em2025. Os2% da Smart são parâmetro de alocação, não stop-loss, garantia de risco ou intervalo calibrado.

O código público do CryptoMamba utiliza o fechamento anterior como execução e não debita custos explicitamente. Aqui há atraso de1min, preços de minutos Binance, comissão,slippage,filtros e risco até o saldo terminal. É adaptação da política, não reprodução dos lucros publicados. Short exige dados de financiamento/margem que não fazem parte deste estudo Spot.

## Calendário e custos

- validacao: 2024-01-01T00:01:00+00:00 → 2024-12-31T00:01:00+00:00; 365 decisões diárias, mesmas origens em todos os modelos.
- teste: 2025-01-01T00:01:00+00:00 → 2025-12-31T00:01:00+00:00; 364 decisões diárias, mesmas origens em todos os modelos.

Base: comissão0,10% e slippage0,05% por lado; agravado0,20%/0,10%; ideal0/0. Quantidades arredondadas para baixo em0,00001BTC e mínimo5USDT assumido. Filtros e taxas históricas reais da conta não foram certificados. Comissões de compra debitadas no BTC recebido e de venda noUSDT recebido. Resíduo sem tamanho de ordem permanece marcado e é mostrado nos arquivos de cada simulação.

## Médias por modelo, regra e período

Seis seeds no Mamba16/CryptoMamba; três na LSTM. Para comparação pareada com LSTM usar os grupos de três da tabela seguinte. Médias individuais, não carteira formada por ensemble.

| Período | Regra | Modelo | N | Retorno base | Drawdown médio | Exposição média | Ordens médias |
|---|---|---|---:|---:|---:|---:|---:|
| validacao | diaria24 | mamba16_seis | 6 | +17,89% | +20,14% | 9,41% | 68,67 |
| validacao | diaria24 | lstm_tres | 3 | +1,72% | +12,56% | 5,57% | 40,67 |
| validacao | diaria24 | cryptomamba_seis | 6 | +0,00% | +0,00% | 0,00% | 0,00 |
| validacao | diaria24 | naive | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| validacao | diaria24 | arima | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| validacao | vanilla | mamba16_seis | 6 | +52,62% | +16,79% | 39,31% | 1,67 |
| validacao | vanilla | lstm_tres | 3 | +30,14% | +20,96% | 44,66% | 2,00 |
| validacao | vanilla | cryptomamba_seis | 6 | +0,00% | +0,00% | 0,00% | 0,00 |
| validacao | vanilla | naive | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| validacao | vanilla | arima | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| validacao | smart | mamba16_seis | 6 | +81,45% | +29,70% | 75,92% | 325,50 |
| validacao | smart | lstm_tres | 3 | +28,83% | +17,50% | 37,62% | 303,67 |
| validacao | smart | cryptomamba_seis | 6 | +109,41% | +32,96% | 95,93% | 73,83 |
| validacao | smart | naive | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| validacao | smart | arima | 1 | +32,67% | +12,11% | 34,78% | 295,00 |
| validacao | benchmark | caixa | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| validacao | benchmark | comprar_manter | 1 | +118,69% | +33,12% | 100,00% | 2,00 |
| teste | diaria24 | mamba16_seis | 6 | -18,47% | +28,33% | 15,94% | 116,00 |
| teste | diaria24 | lstm_tres | 3 | -15,52% | +20,97% | 20,42% | 148,67 |
| teste | diaria24 | cryptomamba_seis | 6 | +0,00% | +0,00% | 0,00% | 0,00 |
| teste | diaria24 | naive | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| teste | diaria24 | arima | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| teste | vanilla | mamba16_seis | 6 | -0,80% | +12,00% | 29,30% | 0,67 |
| teste | vanilla | lstm_tres | 3 | +1,58% | +23,99% | 55,31% | 1,33 |
| teste | vanilla | cryptomamba_seis | 6 | +0,00% | +0,00% | 0,00% | 0,00 |
| teste | vanilla | naive | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| teste | vanilla | arima | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| teste | smart | mamba16_seis | 6 | -8,79% | +34,43% | 89,40% | 254,17 |
| teste | smart | lstm_tres | 3 | -5,20% | +23,00% | 60,33% | 247,00 |
| teste | smart | cryptomamba_seis | 6 | -9,47% | +35,80% | 95,72% | 72,67 |
| teste | smart | naive | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| teste | smart | arima | 1 | -2,32% | +15,91% | 31,90% | 299,00 |
| teste | benchmark | caixa | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| teste | benchmark | comprar_manter | 1 | -5,80% | +35,99% | 100,00% | 2,00 |

## Smart no teste: comparação pareada nas três seeds comuns

| Modelo | Seeds | Retorno base | Desvio entre seeds |
|---|---:|---:|---:|
| mamba16_tres | 3 | -8,29% | +2,21% |
| lstm_tres | 3 | -5,20% | +4,14% |
| cryptomamba_tres | 3 | -9,49% | +0,11% |

## Sensibilidade a custos no teste

| Regra | Modelo | Ideal | Base | Agravado |
|---|---|---:|---:|---:|
| diaria24 | mamba16_seis | -3,34% | -18,47% | -30,15% |
| diaria24 | lstm_tres | +4,60% | -15,52% | -28,50% |
| diaria24 | cryptomamba_seis | +0,00% | +0,00% | +0,00% |
| vanilla | mamba16_seis | -0,70% | -0,80% | -0,90% |
| vanilla | lstm_tres | +1,79% | +1,58% | +1,38% |
| vanilla | cryptomamba_seis | +0,00% | +0,00% | +0,00% |
| smart | mamba16_seis | -8,10% | -8,79% | -9,49% |
| smart | lstm_tres | -4,47% | -5,20% | -5,93% |
| smart | cryptomamba_seis | -9,20% | -9,47% | -9,74% |
| smart_constante | mamba16_seis | -8,39% | -8,66% | -8,93% |
| smart_constante | lstm_tres | -2,46% | -2,55% | -2,64% |
| smart_constante | cryptomamba_seis | -9,19% | -9,46% | -9,72% |

## Cada seed do Mamba16 no teste

| Seed | Diária24 | Vanilla | Smart | Smart com viés fixo |
|---|---:|---:|---:|---:|
| 17 | -15,25% | +9,06% | -9,84% | -9,67% |
| 42 | -7,99% | -13,84% | -5,77% | -7,30% |
| 2026 | -33,33% | +0,00% | -9,27% | -9,68% |
| 7 | -24,49% | +0,00% | -9,43% | -9,64% |
| 123 | -22,30% | +0,00% | -8,53% | -7,70% |
| 31415 | -7,43% | +0,00% | -9,94% | -7,95% |

## Incerteza temporal do contraste principal

Média entre seeds de retornos log diários; bootstrap circular14dias,2000réplicas. O intervalo é condicional aos checkpoints e ao histórico. Não corrige a escolha retrospectiva das políticas ou toda investigação anterior.

| Contraste Smart/Mamba16 | Diferença log diária | IC95% |
|---|---:|---|
| smart_mamba16_menos_vies_validacao | -4.294261e-06 | [-0.00013410088;0.00012129836] |
| smart_mamba16_menos_comprar_manter | -8.9050685e-05 | [-0.00039125451;0.00015170307] |
| smart_mamba16_menos_caixa | -0.00025323331 | [-0.0019741496;0.0014906069] |

Intervalo que inclui zero é inconclusivo quanto ao efeito. Um saldo positivo isolado não demonstra vantagem futura. Os controles de viés usam apenas previsões de2024 e nunca média futura de2025.

![Curvas e comparações](figuras/backtest_carteira_8ec8a66648313caa48e3/carteiras.png)

## Auditoria e limites

Todas as369simulações têm ordens,recusas,saldos,curva horária,retornos diários e verificador independente. Caixa,BTC,comissão,slippage,quantidades e drawdown foram reconstituídos do livro de lançamentos. O drawdown considera closes de todos os minutos, saldos de execução e liquidação final; a curva ilustrada é amostrada. Não há stop-loss ou garantia de execução real. Dados/previsões/modelos anteriores não foram alterados.

2024participou da seleção dos checkpoints.2025já foi consultado antes desta decisão. Trata-se de backtest retrospectivo, sem novo holdout ou walk-forward. A receita do modelo, parâmetros das políticas e todas as seeds foram preservados; nenhum vencedor foi escolhido automaticamente e não houve busca até lucrar. Resultados devem ser confirmados por outros períodos e condições antes de qualquer alegação operacional.

[CryptoMamba](https://arxiv.org/html/2501.01010v2), [código público das políticas](https://github.com/MShahabSepehri/CryptoMamba/blob/fef42727861a9c3a32241283ab981ef21a49e291/utils/trade.py), [comissões Binance](https://developers.binance.com/en/docs/products/spot/faqs/commission_faq).

[Resultados estruturados](../dados/experimentos/backtest_carteira_8ec8a66648313caa48e3/resultados/comparacao.json) e [estado verificável](../registros/backtest_carteira/estado.json).
