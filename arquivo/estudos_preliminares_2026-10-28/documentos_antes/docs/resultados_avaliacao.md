# Resultados da avaliação — retorno em 24 horas

Registro de 21/10/2026. Execução `1e7c5ed662fba55ddd25`, dataset `d25f6a93a9900725f51e`. Este relatório interpreta B1–B4, com testes em 2024–2025. Os resultados de desenvolvimento em 2023 permanecem em `docs/resultados_desenvolvimento.md`.

## O que foi concluído

A avaliação terminou às 18:25:01 UTC, com 384 ajustes neurais auditados: quatro moedas × quatro contextos × quatro blocos × três seeds × duas redes. Há 16 séries Naive e 16 seleções ARIMA, com todos os 144 candidatos ARIMA válidos. Os quatro blocos neurais tiveram cobertura exata e integridade conferidas separadamente. No inventário das duas fases, há 832 resultados únicos auditados: 768 neurais e 64 referências.

A auditoria da publicação foi aprovada às 18:28:46 UTC. Conferiu os 416 resultados desta fase, 144 candidatos, 212 cenários financeiros e 13.866 registros de operações. O manifesto da publicação tem SHA-256 `5d14debd500b4bb03e697d8a5a1b35f2cda004edbc9141052ab13f23d41c2ee1`.

A interrupção operacional ocorrida após o ajuste 220 e sua retomada permanecem documentadas em `registros/incidentes/`. Os 220 ajustes anteriores foram preservados e reutilizados após verificação; a retomada não é um novo treinamento. Não houve revisão da configuração científica durante a avaliação.

## A frase que responde à comparação principal

**Nesta avaliação, a LSTM previu o retorno de 24h com menor erro que o Mamba. A LSTM ficou muito próxima do Naive, sem redução de erro demonstrada frente à persistência. O Mamba apresentou erro maior que LSTM, Naive e ARIMA no procedimento predefinido.**

Essa conclusão vale para as configurações compactas, a entrada de retornos horários, as quatro moedas e os períodos estudados. O experimento não estima a melhor configuração possível de cada arquitetura.

| Modelo | MSE médio | RMSE × 100 | Ganho médio por célula frente ao Naive | Acerto direcional | Acerto balanceado |
|---|---:|---:|---:|---:|---:|
| Mamba | 0,001190714 | 3,451 | −1,55% | 50,51% | 50,51% |
| LSTM | 0,001176416 | 3,430 | +0,04% | 50,78% | 50,64% |
| ARIMA | 0,001176143 | 3,429 | +0,04% | 44,62% | 44,77% |
| Naive | 0,001176354 | 3,430 | 0,00% | 0,08% | 0,00% |

Primeiro se calcula a média dos erros das seeds em cada célula; depois as células recebem pesos iguais. As previsões das seeds não foram combinadas em um ensemble. RMSE × 100 está em pontos de log-retorno: 3,430 descreve a escala do erro quadrático, sem representar acertos ou uma margem garantida por previsão.

O Naive prevê retorno exatamente zero. Seu acerto direcional baixo decorre dessa saída neutra, que só coincide com o sinal observado quando o retorno real também é zero. Isso é compatível com ser uma referência forte para o erro de magnitude. As redes foram treinadas para MSE; o sinal é um diagnóstico secundário, e a saída numérica não é uma probabilidade de alta.

## Por que a LSTM tem ganho médio positivo e MSE global ligeiramente maior?

Os dois indicadores fazem contas diferentes. O MSE global da LSTM foi `0,0011764163725050832`, contra `0,0011763537707533199` do Naive: uma diferença muito pequena, desfavorável à LSTM. Já a habilidade faz primeiro `1 − MSE_modelo/MSE_naive` em cada célula e depois tira a média. Cada redução absoluta é dividida por um erro de referência diferente.

Um exemplo aritmético ajuda: reduzir 10% de um erro de 1 e aumentar 2% de um erro de 100 produz ganho percentual médio de 4%, mas eleva o erro médio de 50,5 para 51,45. Portanto, uma média de ganhos positiva pode coexistir com um erro global maior. A comparação principal e seus intervalos usam diferenças pareadas de MSE. O pequeno +0,04% da tabela, isoladamente, não demonstra superioridade da LSTM.

## O que a incerteza permite afirmar

O bootstrap pareado por blocos móveis preservou a dependência temporal e a comparação conjunta entre modelos e moedas. Foram 2.000 réplicas, com 14 dias como procedimento principal e sensibilidades de sete e 28 dias.

| Diferença de MSE | Estimativa | Intervalo de 95%, blocos de 14 dias | Interpretação |
|---|---:|---:|---|
| Mamba − LSTM | 0,000014297 | [0,000003536; 0,000032574] | Favorece LSTM |
| Mamba − Naive | 0,000014360 | [0,000003084; 0,000034406] | Mamba com erro maior |
| Mamba − ARIMA | 0,000014571 | [0,000003264; 0,000034679] | Mamba com erro maior |
| LSTM − Naive | 0,000000063 | [−0,000005263; 0,000005524] | Diferença inconclusiva |

Uma diferença positiva indica erro maior do primeiro modelo. Na comparação Mamba–LSTM, todo o intervalo ficou acima de zero. Na comparação LSTM–Naive, o intervalo atravessa zero: o procedimento não separou os dois de maneira clara. As sensibilidades de sete e 28 dias mantiveram essas leituras.

O ARIMA apresentou pequena vantagem descritiva frente ao Naive, mas não foi calculado um intervalo específico ARIMA−Naive neste protocolo. Isso impede transformar a pequena diferença observada em uma afirmação confirmada de superioridade.

## Contexto e inicialização

Mais contexto não produziu uma melhora geral. Para Mamba, as comparações exploratórias de um dia contra três e 14 dias favoreceram o contexto de um dia: os intervalos de `MSE_curto − MSE_longo` ficaram negativos. A comparação contra sete dias incluiu zero. Para LSTM, todos os contrastes de contexto incluíram zero no procedimento principal.

O desenvolvimento havia favorecido 14 dias contra um dia para Mamba; a avaliação apresentou o sentido oposto. Essa mudança mostra por que observar um período e escolher retrospectivamente seu contexto vencedor não garante generalização. Os contrastes secundários são exploratórios, sem correção por multiplicidade. Todos os contextos permanecem reportados.

As três seeds foram mantidas. O desvio padrão das médias de MSE entre seeds foi `0,000001432` na LSTM e `0,000010484` no Mamba. A variação descritiva entre seeds foi maior no Mamba. A seed controla a inicialização e outras fontes aleatórias do treinamento; essa medida complementa a incerteza temporal, pois três execuções não representam todas as condições futuras do mercado.

## Como a previsão se comportou na simulação Spot

A política predefinida decide uma vez ao dia, às 00:00 UTC, compra às 00:01 se a previsão superar os custos e encerra exatamente 24h depois. Caso contrário, fica em caixa. Cada estratégia tem sua própria conta inicial de 10.000 USDT e mantém capital entre os blocos da fase. Usa posição comprada, sem alavancagem ou stop. O placar preditivo usa origens horárias; a política financeira usa decisões diárias.

Nos custos base:

| Família | Estratégias | Retorno positivo | Retorno negativo | Sem entradas | Mediana dos retornos |
|---|---:|---:|---:|---:|---:|
| LSTM | 48 | 24 | 24 | 0 | −0,16% |
| Mamba | 48 | 21 | 27 | 0 | −10,48% |

Essas são 48 combinações de moeda, contexto e seed por rede. São estratégias correlacionadas, e sua mediana não representa o retorno de uma carteira ou de um modelo combinado. Nenhuma combinação é selecionada como política vencedora após observar o teste.

O mesmo exemplo de BTC/LSTM/contexto de um dia usado no desenvolvimento ilustra a sensibilidade entre seeds na avaliação: seed 17 terminou com +14,90% e oito entradas; seed 42, com −2,48% e 12 entradas; seed 2026, com −7,39% e sete entradas. Com custos agravados e as mesmas decisões, os resultados passaram a +12,17%, −5,92% e −9,32%, respectivamente. O resultado lucrativo de uma seed não estabelece rentabilidade consistente.

Naive e ARIMA ficaram em caixa nas quatro moedas pela regra de entrada. O controle de compra diária perdeu nas quatro moedas após custos. Esse controle compra e vende diariamente, pagando custos em cada ciclo; seu resultado não representa uma compra mantida por dois anos.

Nesta fase, as pontas de execução e o percurso de minuto das operações permitiram auditar retorno e risco de todas as estratégias publicadas. No desenvolvimento, lacunas impediram atestar o drawdown de alguns controles, e esses desconhecidos permanecem preservados. O drawdown utiliza fechamentos de minuto e não certifica cada movimento intraminuto ou execução real.

## Conclusão e continuidade científica

O desenho respondeu à comparação principal e à pergunta sobre contexto, mesmo sem vantagem do Mamba. A LSTM apresentou menor MSE que o Mamba, mas não demonstrou redução de erro frente ao Naive. A simulação também não estabeleceu uma política com rentabilidade consistente entre as combinações e inicializações.

O congelamento ocorreu após o desenvolvimento, às 06:47:38 UTC de 21/10. A classificação da exposição anterior conserva a declaração do pesquisador de que não usou resultados de 2024–2025 para decidir o estudo; essa declaração não é uma auditoria universal do histórico. Os resultados parciais foram consultados para verificar a publicação, com a configuração científica preservada. Após esta abertura, novas experiências nesses mesmos períodos devem ser tratadas como desenvolvimento, com confirmação independente para novas conclusões.

Fontes recalculáveis: `registros/analises/1e7c5ed662fba55ddd25/avaliacao/resumo.json`, CSVs, arquivos de operações, `publicacao.json` e `auditoria_publicacao.json`. A exportação e o aceite visual da interface são registrados separadamente em `registros/interface/`; a conclusão da análise não substitui essa conferência.
