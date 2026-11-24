# Adam → AdamW no CryptoMamba adaptado

Execução `6829c5fa076dc8c0e0ac`: seis ajustes novos, 59 referências herdadas e 54 novas simulações Smart. [Protocolo](protocolo_otimizador_cryptomamba.md), [estado](../registros/otimizador/estado.json).

## Comparação preditiva

Única diferença científica: otimizador. O Mamba16 já usava AdamW e é referência auxiliar; o par controlado é CryptoMamba/AdamW contra CryptoMamba/Adam. Médias individuais, não ensemble.

| Parte | Modelo | Seeds | MSE | RMSE | MAE |
|---|---|---:|---:|---:|---:|
| validacao | adamw_seis | 6 | 0,0007195145 | 0,0268237471 | 0,0194919311 |
| validacao | adam_seis | 6 | 0,0007178306 | 0,0267923582 | 0,0194646021 |
| validacao | mamba16_seis | 6 | 0,0007198378 | 0,0268297860 | 0,0194925884 |
| validacao | adamw_tres | 3 | 0,0007199330 | 0,0268315353 | 0,0194884577 |
| validacao | adam_tres | 3 | 0,0007173895 | 0,0267841275 | 0,0194612436 |
| validacao | mamba16_tres | 3 | 0,0007191640 | 0,0268172294 | 0,0194771574 |
| validacao | lstm_tres | 3 | 0,0007194461 | 0,0268223892 | 0,0194772907 |
| validacao | naive | 1 | 0,0007218625 | 0,0268674985 | 0,0195231734 |
| validacao | arima | 1 | 0,0007215880 | 0,0268623908 | 0,0195147555 |
| teste | adamw_seis | 6 | 0,0004961223 | 0,0222736781 | 0,0158805870 |
| teste | adam_seis | 6 | 0,0004979591 | 0,0223149763 | 0,0158856761 |
| teste | mamba16_seis | 6 | 0,0004965701 | 0,0222836931 | 0,0158939043 |
| teste | adamw_tres | 3 | 0,0004961998 | 0,0222755175 | 0,0158773193 |
| teste | adam_tres | 3 | 0,0004990971 | 0,0223404761 | 0,0159034521 |
| teste | mamba16_tres | 3 | 0,0004958901 | 0,0222683060 | 0,0158891746 |
| teste | lstm_tres | 3 | 0,0004980096 | 0,0223159526 | 0,0159310684 |
| teste | naive | 1 | 0,0004952210 | 0,0222535625 | 0,0158639571 |
| teste | arima | 1 | 0,0004946217 | 0,0222400915 | 0,0158540946 |

## Contraste primário e incerteza

| Parte | Diferença MSE AdamW−Adam | IC95% de 14 dias |
|---|---:|---|
| validacao | 1.683975117e-06 | [-4.665846639213746e-06, 7.861872893789662e-06] |
| teste | -1.836815943e-06 | [-5.366920406319645e-06, 1.647699216795886e-06] |

O critério primário não foi atendido; não há evidência suficiente pelo critério fixado para substituir a versão anterior.
A diferença entre Adam/AdamW inclui regularização efetiva diferente mesmo com decay nominal igual. Nenhuma promoção automática por MSE de teste ou lucro.

## Seeds, constância e operação

| Seed | MSE validação | MSE teste | Previsões distintas teste | Desvio previsão teste | Smart base teste |
|---|---:|---:|---:|---:|---:|
| 17 | 0,0007177793 | 0,0004983451 | 8733 | 0,0006405941 | -9,54% |
| 42 | 0,0007230334 | 0,0004950726 | 8735 | 0,0006755210 | +6,26% |
| 2026 | 0,0007189864 | 0,0004951818 | 8734 | 0,0003177693 | -5,37% |
| 7 | 0,0007205030 | 0,0004928730 | 8735 | 0,0015600411 | -1,51% |
| 123 | 0,0007187584 | 0,0005023192 | 8735 | 0,0014075083 | -10,73% |
| 31415 | 0,0007180267 | 0,0004929419 | 8736 | 0,0016260263 | -0,37% |

## Carteira Smart: médias de seis seeds

| Parte | Cenário | Regra | Retorno | Queda máxima média | Exposição |
|---|---|---|---:|---:|
| validacao | ideal | smart | +75,88% | +24,92% | +70,37% |
| validacao | base | smart | +74,05% | +25,15% | +70,37% |
| validacao | agravado | smart | +72,26% | +25,41% | +70,37% |
| teste | ideal | smart | -2,64% | +26,68% | +70,13% |
| teste | ideal | smart_constante | -6,82% | +29,41% | +72,49% |
| teste | base | smart | -3,54% | +26,80% | +70,13% |
| teste | base | smart_constante | -7,05% | +29,40% | +72,48% |
| teste | agravado | smart | -4,44% | +26,92% | +70,12% |
| teste | agravado | smart_constante | -7,27% | +29,40% | +72,47% |

Comparar aos números preservados do [backtest anterior](resultados_backtest_carteira.md), com os mesmos instantes e regras. Smart 2% não é stop. Não escolher uma seed lucrativa. SpotR0 separado consta dos resultados estruturados; não misturar sua contabilidade com a carteira retida.

## Preservação e limites

Qualificação sintética, recarga exata, checkpoints, seleção por validação, métricas por origem, livro Smart e hashes anteriores foram conferidos. As tentativas e publicações anteriores continuam em seus caminhos. 2024/2025 já conhecidos: exploração retrospectiva, sem novo holdout ou walk-forward. Não há garantia de lucro ou execução real. Mais seeds não corrigem toda seleção adaptativa. [Estado, recibos e publicação](../registros/otimizador/estado.json).
