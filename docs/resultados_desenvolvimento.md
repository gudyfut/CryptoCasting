# Resultados do desenvolvimento — retorno em 24 horas

Registro de 21/10/2026. Execução `1e7c5ed662fba55ddd25`, dataset `d25f6a93a9900725f51e`. Este relatório interpreta exclusivamente DB1–DB4, com testes em 2023. A avaliação predefinida de 2024–2025 é apresentada separadamente em `docs/resultados_avaliacao.md` e não integra estes números.

## O que foi executado

Foram concluídos e auditados 384 ajustes neurais: quatro moedas, quatro contextos, quatro blocos, três seeds e duas redes. Há ainda 16 séries Naive e 16 seleções ARIMA. Todos os 144 candidatos ARIMA foram válidos nesta fase; nenhuma tentativa terminou marcada como falha. Cada bloco neural teve sua cobertura e seus hashes conferidos separadamente.

A auditoria da publicação conferiu 416 resultados, 144 candidatos, 212 cenários financeiros e 2.418 registros de operações. Operações repetidas entre estratégias ou cenários não são observações independentes. A publicação está vinculada pelo manifesto SHA-256 `f7f82286ad4e7112bb721ca133ad77e208c24f5f2cec3f597cce4147758520f6`.

## A frase que resume o resultado preditivo

**Neste desenvolvimento, a LSTM teve menor erro que o Mamba, mas ambas as redes apresentaram erro maior que o Naive na média predefinida. O ARIMA ficou muito próximo do Naive, com pequena melhora descritiva.** Isso vale para as configurações compactas, entradas de retornos horários, quatro moedas e períodos estudados; não demonstra incapacidade universal de uma arquitetura.

| Modelo | MSE médio | RMSE × 100 | Ganho médio por célula frente ao Naive | Acerto direcional | Acerto balanceado |
|---|---:|---:|---:|---:|---:|
| Mamba | 0,000836326 | 2,892 | −1,71% | 48,75% | 50,08% |
| LSTM | 0,000826884 | 2,876 | −0,76% | 50,13% | 50,67% |
| ARIMA | 0,000820478 | 2,864 | +0,07% | 44,71% | 44,95% |
| Naive | 0,000820793 | 2,865 | 0,00% | 0,48% | 0,00% |

Primeiro são promediados os erros das seeds de cada célula; depois as células recebem pesos iguais. Não se faz uma média das previsões para criar um ensemble. A habilidade é a média de `1 − MSE_modelo/MSE_naive` por célula, não a razão das médias globais. ARIMA e Naive são compartilhados entre contextos, sem serem tratados como novas réplicas.

RMSE × 100 está em pontos de log-retorno. Um valor de 2,892 não significa 2,892% de acertos, nem uma margem garantida para cada previsão. O Naive prevê retorno zero: só acerta exatamente o sinal quando o retorno observado também é zero. Por isso pode ter acerto direcional quase nulo e, simultaneamente, ser uma referência forte em erro de magnitude. O ARIMA também escolheu a ordem equivalente ao Naive em duas células de XRP; isso contribui para a leitura de sua métrica direcional.

## Incerteza e contextos

A diferença média de MSE `Mamba − LSTM` foi **0,000009442**. O intervalo de 95% pelo bootstrap pareado de blocos de 14 dias foi **[0,000003654; 0,000015196]**. Como todo o intervalo é positivo, o procedimento favorece a LSTM nesta fase. As sensibilidades de sete e 28 dias mantiveram esse sentido. As comparações de ambas as redes contra o Naive também tiveram intervalos positivos para a diferença de MSE. Não foi calculado aqui um intervalo específico para ARIMA menos Naive; sua pequena vantagem descritiva não basta para declarar superioridade confirmada.

Mais contexto não produziu melhora monotônica. Para Mamba, 14 dias tiveram menor MSE que um dia na comparação exploratória, com intervalo principal positivo para `MSE_curto − MSE_longo`; isso não equivale a superar o Naive. Os contrastes de três e sete dias com um dia incluíram zero. Para LSTM, todos os contrastes de contexto incluíram zero no procedimento principal de 14 dias. Há várias comparações secundárias sem ajuste de multiplicidade, portanto não devem virar seleção retrospectiva de um vencedor.

As três seeds permaneceram na análise. A dispersão do MSE global entre seeds foi maior em Mamba que em LSTM. Esse diagnóstico descreve estabilidade da inicialização e não substitui a incerteza temporal do bootstrap.

## O que aconteceu na simulação Spot

A simulação usa somente decisões diárias às 00:00 UTC, execução às 00:01 e saída 24 horas depois. Compra com todo o capital se a previsão superar o custo predefinido; caso contrário, permanece em caixa. Não representa futuros, posições vendidas, alavancagem ou stop. Os resultados preditivos horários e os resultados financeiros diários respondem a perguntas diferentes.

Nos custos base, cada rede tem 48 estratégias distintas: quatro moedas × quatro contextos × três seeds. Entre as estratégias LSTM, 24 tiveram retorno positivo, 20 negativo e quatro ficaram em caixa; para Mamba, 25 tiveram retorno positivo, 19 negativo e quatro ficaram em caixa. Essas estratégias são correlacionadas e não equivalem a 48 testes independentes. Os resultados não autorizam escolher a combinação lucrativa depois de observar o teste.

Um exemplo ilustra a importância disso: LSTM em BTC, contexto de um dia, seed 17 teve +10,95% com apenas três entradas; na seed 2026, teve −3,42%, também com três entradas. Na seed 42, não houve entrada. Com custos agravados, a seed 2026 manteve as mesmas três decisões e passou a −4,29%. Um caso lucrativo isolado não comprova uma política estável.

Naive e ARIMA ficaram em caixa nas quatro moedas pela regra de entrada. O controle de compra diária teve retorno negativo nas quatro moedas após custos. Suas pontas de execução permitiram calcular o retorno, mas lacunas durante posições impediram atestar o drawdown integral em todas as quatro contas. A interface conserva essa distinção e exibe o risco como não auditável.

## Continuação e rastreabilidade

O congelamento foi registrado em 21/10/2026 às 06:47:38 UTC, após a conclusão e auditoria do desenvolvimento. A avaliação posterior segue a mesma configuração, sem alteração motivada pelos placares acima. A classificação da exposição anterior conserva a declaração do pesquisador; não é uma auditoria universal de toda exposição histórica.

Fontes recalculáveis: `registros/analises/1e7c5ed662fba55ddd25/desenvolvimento/resumo.json`, CSVs, arquivos de operações, `publicacao.json` e `auditoria_publicacao.json`. A interface permite filtrar moedas, contextos e blocos, consultar seeds e ordens ARIMA, comparar custos e visualizar previsões e operações reais. A síntese global e os intervalos continuam referentes à fase completa; o placar filtrado pode ter outra ordenação.
