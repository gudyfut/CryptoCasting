# Resultados do experimento de pré-normalização do Mamba

Execução `9e03af2150cbb7b1068d`. Referência preservada `7868a4d847c1410fc681`. Relatório gerado em 2026-10-28T19:37:49.607390+00:00 (UTC).

Estudo retrospectivo pareado em períodos já consultados. A única intervenção é mover LayerNorm para antes do Mamba, mantendo a penalização corrigida. Foram 384 ajustes pré-normalizados; LSTM, ARIMA, Naive e os Mamba pós-normalização corrigidos são referências herdadas. Dois controles pós-normalização corrigidos foram reexecutados para conferência de reprodução e não contam como novos pares independentes.

A confirmação de preservação antes/depois fica em `preservacao_depois.json` na pasta desta execução; o estado global está em `progresso.json`. A existência deste relatório indica consolidação das duas fases, não substitui o recibo de fechamento.

Protocolo: [experimento controlado](../../../docs/protocolo_normalizacao_mamba.md). A mudança não garante melhora nem rentabilidade.

## Desenvolvimento de 2023

| Modelo | MSE médio | RMSE × 100 | MAE × 100 |
|---|---:|---:|---:|
| mamba_posnorm | 0.0008362688 | 2.8918 | 1.7754 |
| mamba_prenorm | 0.0008320328 | 2.8845 | 1.7713 |
| lstm | 0.0008268839 | 2.8756 | 1.7624 |
| arima | 0.0008204785 | 2.8644 | 1.7558 |
| naive | 0.0008207934 | 2.8649 | 1.7570 |

MSE menor indica menor erro quadrático. RMSE/MAE ×100 estão em pontos de log-retorno, não em acurácia. As seeds são médias de escores, não um ensemble.

| Comparação do pré-normalizado com | Diferença MSE | Variação relativa | IC 95% de 14 dias |
|---|---:|---:|---|
| mamba_posnorm | -4.235943755e-06 | -0.5065% | [-8.041414659e-06; -5.282247517e-07] |
| lstm | 5.148994683e-06 | +0.6227% | [1.704786594e-06; 9.059820162e-06] |
| naive | 1.123944637e-05 | +1.3693% | [5.417646153e-06; 1.746324811e-05] |
| arima | 1.155437492e-05 | +1.4082% | [5.677104831e-06; 1.7788261e-05] |

O intervalo principal favorece a pré-normalização. A diferença é pré-normalizado menos referência: negativa favorece o pré-normalizado. Os contrastes com outras famílias são secundários. Intervalos condicionais aos modelos e períodos, com 2.000 reamostragens de blocos; sensibilidades de sete e 28 dias constam do JSON.

Na simulação Spot com custos base, 48 estratégias tiveram retorno auditável. Mediana pré-normalizada: 0.22%; mediana dos pares pós-normalizados corrigidos: 0.40%. Estratégias correlacionadas, sem carteira combinada e sem escolha retrospectiva da vencedora.

Evidências: `dados/experimentos/normalizacao_9e03af2150cbb7b1068d/analises/desenvolvimento/resumo.json`, `comparacoes_pareadas.csv`, `metricas_por_ajuste.csv`, `financeiro.csv`, `publicacao.json` e `auditoria.json`.

## Avaliação retrospectiva de 2024–2025

| Modelo | MSE médio | RMSE × 100 | MAE × 100 |
|---|---:|---:|---:|
| mamba_posnorm | 0.0011913154 | 3.4515 | 2.3212 |
| mamba_prenorm | 0.0011817236 | 3.4376 | 2.3113 |
| lstm | 0.0011764164 | 3.4299 | 2.3057 |
| arima | 0.0011761429 | 3.4295 | 2.3053 |
| naive | 0.0011763538 | 3.4298 | 2.3061 |

MSE menor indica menor erro quadrático. RMSE/MAE ×100 estão em pontos de log-retorno, não em acurácia. As seeds são médias de escores, não um ensemble.

| Comparação do pré-normalizado com | Diferença MSE | Variação relativa | IC 95% de 14 dias |
|---|---:|---:|---|
| mamba_posnorm | -9.591841265e-06 | -0.8051% | [-2.668146481e-05; 2.734873961e-06] |
| lstm | 5.307228751e-06 | +0.4511% | [-9.430435952e-08; 1.258428335e-05] |
| naive | 5.369830503e-06 | +0.4565% | [-2.064176924e-06; 1.608932842e-05] |
| arima | 5.580694267e-06 | +0.4745% | [-1.791246602e-06; 1.594229924e-05] |

O intervalo principal inclui zero e não distingue claramente as duas posições da normalização. A diferença é pré-normalizado menos referência: negativa favorece o pré-normalizado. Os contrastes com outras famílias são secundários. Intervalos condicionais aos modelos e períodos, com 2.000 reamostragens de blocos; sensibilidades de sete e 28 dias constam do JSON.

Na simulação Spot com custos base, 48 estratégias tiveram retorno auditável. Mediana pré-normalizada: -11.03%; mediana dos pares pós-normalizados corrigidos: -10.48%. Estratégias correlacionadas, sem carteira combinada e sem escolha retrospectiva da vencedora.

Evidências: `dados/experimentos/normalizacao_9e03af2150cbb7b1068d/analises/avaliacao/resumo.json`, `comparacoes_pareadas.csv`, `metricas_por_ajuste.csv`, `financeiro.csv`, `publicacao.json` e `auditoria.json`.

## Limites da conclusão

A intervenção altera somente a posição da LayerNorm e mantém capacidade, entrada, dados, partições, seeds, penalização e regra de seleção de época. A época selecionada pode mudar como consequência do tratamento. Não houve busca adicional. Comparações por moeda, contexto e seed são exploratórias e estão integralmente reportadas nos arquivos, sem seleção de subconjuntos favoráveis.

Os resultados de 2024–2025 já haviam sido vistos quando esta hipótese foi definida. Congelar a extensão não desfaz essa exposição; uma nova alegação confirmatória requer dados não usados nas decisões. Este experimento não mede a melhor configuração possível de Mamba/LSTM nem certifica execução financeira real.
