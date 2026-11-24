# OHLCV cru com Huber: complemento fatorial

Execução `1781f557fdf2b45a3ae2`:32principais novos+1controle;96referências herdadas,128resultados principais.

[Protocolo](protocolo_crua_huber.md), [estado](../registros/crua_huber/estado.json).

## Médias de oito seeds por bloco

| Bloco | Parte | Relativa/MSE | Relativa/Huber | Crua/MSE | Crua/Huber |
|---|---|---:|---:|---:|---:|
| B1 | validacao | 0.0004902856 | 0.0004840273 | 0.0004829695 | 0.0004809259 |
| B1 | teste | 0.0007282770 | 0.0007292476 | 0.0007370560 | 0.0007280996 |
| B2 | validacao | 0.0005728364 | 0.0005710134 | 0.0005695012 | 0.0005712448 |
| B2 | teste | 0.0007225947 | 0.0007183430 | 0.0007265668 | 0.0007227458 |
| B3 | validacao | 0.0006032542 | 0.0006026933 | 0.0006118555 | 0.0006058960 |
| B3 | teste | 0.0005934036 | 0.0005933060 | 0.0005905105 | 0.0005893093 |
| B4 | validacao | 0.0003938712 | 0.0003912371 | 0.0004089005 | 0.0004065480 |
| B4 | teste | 0.0004299033 | 0.0004261056 | 0.0004046596 | 0.0004066375 |

## Agregado com peso igual entre quatro blocos

| Parte | Combinação | MSE | RMSE×100 | MAE×100 | Habilidade Naive |
|---|---|---:|---:|---:|---:|
| validacao | relativa_mse | 0.0005150618 | 2.2621 | 1.6341 | +1.186% |
| validacao | relativa_huber | 0.0005122428 | 2.2556 | 1.6295 | +1.727% |
| validacao | crua_mse | 0.0005183067 | 2.2699 | 1.6351 | +0.564% |
| validacao | crua_huber | 0.0005161537 | 2.2652 | 1.6323 | +0.977% |
| teste | relativa_mse | 0.0006185446 | 2.4739 | 1.7887 | -1.518% |
| teste | relativa_huber | 0.0006167505 | 2.4700 | 1.7850 | -1.224% |
| teste | crua_mse | 0.0006146982 | 2.4630 | 1.7805 | -0.887% |
| teste | crua_huber | 0.0006116980 | 2.4577 | 1.7729 | -0.394% |

## Contrastes fixados antes da execução nova

| Contraste | Diferença MSE de teste | IC98,75% principal | Decisão |
|---|---:|---|---|
| huber_na_crua | -3.000173587e-06 | [-8.22231689648039e-06, 1.411750699616421e-06] | inconclusivo |
| crua_na_huber | -5.052499719e-06 | [-1.604579803269332e-05, 3.883163475965354e-06] | inconclusivo |
| combinacao_menos_referencia | -6.846598561e-06 | [-1.7009288178804837e-05, 1.5802487676428346e-06] | inconclusivo |
| interacao | -1.206074744e-06 | [-1.3102442325438519e-05, 7.142286823638062e-06] | inconclusivo |

A interação é (crua/Huber−crua/MSE)−(relativa/Huber−relativa/MSE). Negativa indica ganho além da soma dos efeitos nesta escala de MSE; não significa lucro ou causalidade universal.

## Spot Smart, custos base

| Bloco | Relativa/MSE | Relativa/Huber | Crua/MSE | Crua/Huber |
|---|---:|---:|---:|---:|
| B1 | +14.19% | +27.72% | +0.73% | +14.00% |
| B2 | +25.11% | +16.46% | +0.00% | +0.00% |
| B3 | +4.62% | +5.13% | +3.91% | +11.24% |
| B4 | -19.87% | -18.11% | -12.02% | -21.96% |

192carteiras novas e600herdadas; diárias24, cenários ideal/agravado, risco, exposição, custos e todas as seeds na publicação estruturada.

Avaliação retrospectiva 2024/2025 já consultados; sem holdout novo ou certeza.
Oito seeds por combinação/bloco, médias individuais; não ensemble.
Pesos iguais entre quatro blocos, histórico expansivo reestimado; não mercados independentes.
Entrada crua sem padronização de X; alvo log-retorno24h continua zscore de treino.
Receita fixa: resultado não demonstra ótimo universal de cada representação/perda.
Carteiras independentes de10.000USDT por bloco; não compor retornos como série contínua.
Sem promoção, nova busca ou repetição automática de resultados ruins.
