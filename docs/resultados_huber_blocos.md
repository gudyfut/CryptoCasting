# Mamba16: MSE versus Huber em quatro blocos e oito seeds

Execução `10dac17ea9df2c540c57`.64ajustes principais+2controles reais;4Naive e408simulações. [Protocolo](protocolo_huber_blocos.md), [estado](../registros/huber_blocos/estado.json).

2024/2025 já conhecidos: walk-forward retrospectivo com seleção informada por períodos. Cada bloco tem treino/validação anteriores ao teste, pesos e scalers novos. Mais seeds não garantem certeza. Não misturar estas médias com a exploração anterior de divisão única.

## Previsão: média das oito seeds em cada bloco

| Bloco | Parte | MSE referência | MSE Huber | Mudança relativa |
|---|---|---:|---:|---:|
| B1 | validacao | 0.0004902856 | 0.0004840273 | -1.276% |
| B1 | teste | 0.0007282770 | 0.0007292476 | +0.133% |
| B2 | validacao | 0.0005728364 | 0.0005710134 | -0.318% |
| B2 | teste | 0.0007225947 | 0.0007183430 | -0.588% |
| B3 | validacao | 0.0006032542 | 0.0006026933 | -0.093% |
| B3 | teste | 0.0005934036 | 0.0005933060 | -0.016% |
| B4 | validacao | 0.0003938712 | 0.0003912371 | -0.669% |
| B4 | teste | 0.0004299033 | 0.0004261056 | -0.883% |

## Agregação predefinida

Peso igual entre quatro blocos e oito seeds dentro de cada bloco. RMSE/MAE são médias de métricas individuais, não erro de ensemble.

| Parte | Variante | MSE | RMSE×100 | MAE×100 | Habilidade Naive |
|---|---|---:|---:|---:|---:|
| validacao | mse | 0.0005150618 | 2.2621 | 1.6341 | +1.186% |
| validacao | huber | 0.0005122428 | 2.2556 | 1.6295 | +1.727% |
| teste | mse | 0.0006185446 | 2.4739 | 1.7887 | -1.518% |
| teste | huber | 0.0006167505 | 2.4700 | 1.7850 | -1.224% |

Diferença MSE Huber−MSE: -1.794098842e-06; IC95% principal (seeds pareadas e blocos14dias): [-7.176986731503976e-06, 4.926644364805305e-06].
Critério primário: {'media_mse_menor': True, 'ic95_seeds_tempo_14_inteiramente_favoravel': False, 'promocao_automatica': False, 'natureza': 'Avaliação retrospectiva ampliada; não substitui o fechamento da exploração anterior.'}. Sem promoção automática; inconclusivo não demonstra igualdade nem ausência universal de previsibilidade.

## Operação por bloco: custos base

| Bloco | Política | Retorno referência | Retorno Huber | DD referência | DD Huber |
|---|---|---:|---:|---:|---:|
| B1 | smart | +14.19% | +27.72% | 13.65% | 16.47% |
| B1 | diaria24 | +1.70% | +5.75% | 4.58% | 6.98% |
| B2 | smart | +25.11% | +16.46% | 14.52% | 10.49% |
| B2 | diaria24 | +0.38% | +1.43% | 6.82% | 7.05% |
| B3 | smart | +4.62% | +5.13% | 26.02% | 27.11% |
| B3 | diaria24 | +2.13% | +3.72% | 14.90% | 15.55% |
| B4 | smart | -19.87% | -18.11% | 29.93% | 29.05% |
| B4 | diaria24 | -17.66% | -14.51% | 25.34% | 21.39% |

Os cenários ideal/agravado, benchmarks, exposição, taxas, carteiras e diários estão na publicação estruturada. Capital inicial10.000USDT em cada carteira/bloco, long/caixa, sem futuros ou stop. Carteiras não formam um histórico contínuo de dois anos. A comparação usa o mesmo motor, calendário e custos dentro de cada bloco.

Seleção por MSE de validação, fontes, checkpoints/recarga, reprodução real, métricas e lançamentos conferidos. Scalers são de cada treino. Os controles não entram nas médias. As limitações dos períodos escolhidos, reamostragem e seleção adaptativa permanecem. Não alterar configurações ou simulação para obter lucro.
