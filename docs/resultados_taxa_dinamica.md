# Mamba16: taxa constante versus redução automática

Execução `99884456ac71fedfd9b0`: seis novos ajustes,53referências herdadas e54carteiras Smart secundárias. [Protocolo](protocolo_taxa_dinamica.md), [estado](../registros/taxa_dinamica/estado.json).

## Comparação preditiva

Médias aritméticas de métricas de modelos individuais, não ensemble. A referência é Mamba16/AdamW com taxa constante0,0002. Dados,arquitetura,perda e critério de parada iguais; somente a política da taxa mudou.

| Parte | Modelo | Seeds | MSE | RMSE×100 | MAE×100 | Habilidade Naive |
|---|---|---:|---:|---:|---:|---:|
| validacao | scheduler_seis | 6 | 0.0007219386 | 2.6869 | 1.9537 | -0.011% |
| validacao | mamba16_seis | 6 | 0.0007198378 | 2.6830 | 1.9493 | +0.280% |
| validacao | scheduler_tres | 3 | 0.0007209551 | 2.6851 | 1.9528 | +0.126% |
| validacao | mamba16_tres | 3 | 0.0007191640 | 2.6817 | 1.9477 | +0.374% |
| validacao | lstm_tres | 3 | 0.0007194461 | 2.6822 | 1.9477 | +0.335% |
| validacao | naive | 1 | 0.0007218625 | 2.6867 | 1.9523 | +0.000% |
| validacao | arima | 1 | 0.0007215880 | 2.6862 | 1.9515 | +0.038% |
| teste | scheduler_seis | 6 | 0.0004976927 | 2.2309 | 1.5906 | -0.499% |
| teste | mamba16_seis | 6 | 0.0004965701 | 2.2284 | 1.5894 | -0.272% |
| teste | scheduler_tres | 3 | 0.0004988807 | 2.2336 | 1.5928 | -0.739% |
| teste | mamba16_tres | 3 | 0.0004958901 | 2.2268 | 1.5889 | -0.135% |
| teste | lstm_tres | 3 | 0.0004980096 | 2.2316 | 1.5931 | -0.563% |
| teste | naive | 1 | 0.0004952210 | 2.2254 | 1.5864 | +0.000% |
| teste | arima | 1 | 0.0004946217 | 2.2240 | 1.5854 | +0.121% |

## Critério primário e incerteza

| Parte | Diferença MSE scheduler−constante | IC95%14dias |
|---|---:|---|
| validacao | 2.100811347e-06 | [-1.566785319436224e-06, 6.279515936232661e-06] |
| teste | 1.122652191e-06 | [-3.073162218867244e-06, 5.700744486656315e-06] |

O critério primário não foi atendido: não há evidência suficiente pelo critério fixado para substituir a referência.
Não selecionar variante/seed/época pelo teste ou pelo lucro. A comparação inclui a alteração do decay efetivo por passo de AdamW ao reduzir a taxa; não isola um mecanismo interno.

## Todas as seeds e diagnóstico diário

| Seed | MSE validação | MSE teste | P95 erro×100 | Vitórias vs Naive | Spearman00UTC | Smart base teste |
|---|---:|---:|---:|---:|---:|---:|
| 17 | 0.0007187754 | 0.0004975988 | 4.6345 | 47.80% | -0.0800 | -10.54% |
| 42 | 0.0007220989 | 0.0005001229 | 4.4900 | 47.25% | 0.0431 | -8.36% |
| 2026 | 0.0007219910 | 0.0004989204 | 4.5956 | 47.25% | 0.0271 | -9.76% |
| 7 | 0.0007243567 | 0.0004961377 | 4.6454 | 48.08% | -0.0723 | -5.80% |
| 123 | 0.0007224509 | 0.0004973759 | 4.4522 | 47.53% | 0.0340 | -7.51% |
| 31415 | 0.0007219584 | 0.0004960006 | 4.5520 | 46.70% | -0.0390 | -9.00% |

## Carteira Smart: média de seis modelos

| Parte | Custos | Política | Retorno | Queda máxima média | Exposição |
|---|---|---|---:|---:|
| validacao | ideal | smart | +62.46% | 28.64% | 69.56% |
| validacao | base | smart | +61.01% | 28.66% | 69.56% |
| validacao | agravado | smart | +59.58% | 28.68% | 69.56% |
| teste | ideal | smart | -7.98% | 34.60% | 90.00% |
| teste | ideal | smart_constante | -6.95% | 29.57% | 74.79% |
| teste | base | smart | -8.49% | 34.63% | 90.00% |
| teste | base | smart_constante | -7.17% | 29.57% | 74.78% |
| teste | agravado | smart | -9.00% | 34.66% | 90.00% |
| teste | agravado | smart_constante | -7.40% | 29.57% | 74.78% |

Comparar com o [backtest anterior](resultados_backtest_carteira.md), no mesmo calendário e regras. Smart2% não é stop. Os resultados SpotR0, com contabilidade histórica própria, estão na publicação estruturada e não substituem as carteiras retidas.

## Evidências e limitações

As taxas de todas as épocas foram reconstruídas independentemente, assim como seleção,métricas e lançamentos das54carteiras. Recarga exata e capacidade20.257 verificadas; nenhum resultado anterior foi sobrescrito. Os diagnósticos descritivos não alteram o primário: [diagnóstico das previsões anteriores](diagnostico_previsoes.md). Resultados por trimestre, faixas causais de previsão, correlações e erros estão na publicação.

2024 participou da seleção de checkpoints;2025 já foi consultado. Estudo exploratório retrospectivo, sem novo holdout ou walk-forward. Mais seeds não eliminam seleção adaptativa. Sem garantia de lucro/fills reais/backup externo; nenhuma promoção ou hipótese seguinte é automática. [Registros e publicação](../registros/taxa_dinamica/estado.json).

## Interpretação e conferência posterior — 02/11/2026

A publicação terminou em 30/10/2026 às 06h44 de Brasília, cerca de 25 minutos após o lançamento. O treinamento das seis seeds encerrou às 06h38; os minutos seguintes foram de publicação e conferência. Nenhum novo treinamento foi iniciado nesta revisão. O relatório automático anterior a esta interpretação foi preservado em `registros/taxa_dinamica/entrega/20261102/antes/`.

A taxa dinâmica não melhorou o critério principal: o MSE médio aumentou **0,292% na validação** e **0,226% no teste**, em relação às seis seeds da referência. As seis seeds pioraram na validação; no teste, três melhoraram e três pioraram. Os intervalos temporais de 7, 14 e 28 dias incluem zero. Isso sustenta manter a referência por falta de evidência favorável, sem demonstrar que qualquer política de taxa dinâmica seja inferior. Os intervalos são condicionais aos modelos ajustados; não incorporam toda a variação de treinamentos futuros ou a seleção adaptativa entre rodadas.

| Seed | Variação MSE validação | Variação MSE teste | Época selecionada | Taxa nessa época |
|---|---:|---:|---:|---:|
| 17 | +0,082% | +0,268% | 8 | 0,0002 |
| 42 | +0,363% | +2,153% | 4 | 0,0002 |
| 2026 | +0,302% | −0,578% | 9 | 0,0001 |
| 7 | +0,666% | −0,407% | 12 | 0,00005 |
| 123 | +0,145% | −0,198% | 2 | 0,0002 |
| 31415 | +0,193% | +0,158% | 7 | 0,0001 |

Valores positivos indicam erro maior que na seed correspondente da referência. Todas as execuções passaram pelas três reduções previstas, até 0,000025. A parada permaneceu em dez épocas sem melhora, sem reiniciar a contagem ao reduzir. Três checkpoints selecionados foram anteriores à primeira redução; nos outros três, uma taxa reduzida produziu o melhor checkpoint da própria trajetória. Mesmo assim, nenhum venceu sua referência em validação. As seis execuções somaram 102 épocas, entre 12 e 22 por seed. Seeds iguais controlam a inicialização e a ordem dos dados, mas não garantem trajetórias CUDA idênticas bit a bit; esta rodada não incluiu uma repetição real adicional da referência.

### População horária e decisões diárias

A tabela principal usa todas as 8.736 origens horárias do teste, cada uma prevendo 24 horas. No subconjunto de 364 origens às 00UTC, o MSE caiu de 0,000482273 para 0,000479823 (**−0,508%**). Ambos permaneceram piores que o Naive desse mesmo subconjunto (0,000475584). Não há contradição: são populações de avaliação diferentes. A melhora diária é secundária e não troca retrospectivamente o critério principal.

Nas decisões diárias, a candidata teve erro absoluto menor que o Naive em média em **47,44%** dos casos; Spearman médio **−0,0145**, próximo de zero. Vitórias de erro não são acerto direcional, e correlação próxima de zero é diagnóstico descritivo, não prova de ausência universal de previsibilidade.

### Simulação operacional

| Política, teste e custos base | Referência constante, seis seeds | Taxa dinâmica, seis seeds |
|---|---:|---:|
| SpotR0: encerra a operação após 24h | −18,46% | −8,77% |
| Smart: mantém/reduz/aumenta posição | −8,79% | −8,49% |
| Comprar e manter no motor Smart | −5,80% | −5,80% |
| Caixa | 0% | 0% |

São médias de seis carteiras individuais, sem combinar previsões. A mudança reduziu as entradas planejadas do SpotR0 de 58 para 27 por seed, em média, e os custos observados de aproximadamente 1.677 para 795 USDT por carteira inicial de 10.000 USDT. O giro menor ajuda a explicar a melhora financeira mesmo com MSE horário pior; isso não demonstra melhor previsão. Uma seed SpotR0 foi lucrativa, enquanto **nenhuma das seis Smart** foi. Na Smart, a diferença média de cerca de **+0,31 ponto percentual** manteve a perda e não comprova vantagem operacional. O controle de previsão constante da própria candidata perdeu 7,17%, menos que os 8,49% da previsão variável.

As simulações mantêm as hipóteses anteriores de custos, latência, filtros aproximados e execução Spot. Não são operações reais, futuros ou estimativas de liquidação. O horizonte do alvo continua sendo 24h; a política Smart pode manter exposição por mais de 24h. O calendário operacional vai de 01/01/2025 00:01 a 31/12/2025 00:01 UTC, sem a última sessão completa do ano.

**Decisão sustentada pela rodada:** manter Mamba16/AdamW com taxa constante 0,0002 como referência de trabalho. A hipótese de redução por estagnação, nesta receita específica, não mostrou benefício preditivo convincente. Isso é um resultado válido para o TCC; não equivale a falha da implementação ou demonstração de lucro futuro. Nenhuma hipótese seguinte foi executada automaticamente.

A [conferência independente posterior](../registros/taxa_dinamica/entrega/20261102/conferencia.json) recalcula métricas de 59 séries, médias, contrastes e intervalos, reconstrói as taxas e a seleção, e verifica fontes, publicações e preservação. Não sobrescreve os recibos congelados nem repete treinamento. Seu [código de leitura](../registros/taxa_dinamica/entrega/20261102/conferir.py) está junto do recibo.
