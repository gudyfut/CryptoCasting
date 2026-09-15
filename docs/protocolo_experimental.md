# Protocolo experimental — Atividade 1 do TCC 2

**Projeto:** CryptoCasting — Previsibilidade de Criptomoedas com a Arquitetura Mamba: um Sistema de Forecasting Temporal  
**Autor:** Murilo R. F. Monferrari  
**Versão:** 1.1 — 14/09/2026  
**Entrega:** definição do desenho experimental, conforme o [cronograma](Cronograma_Atividades_TCC2_Murilo_Monferrari.pdf).  
**Estado:** decisões metodológicas estabelecidas para orientar o desenvolvimento. A coleta, a implementação e os experimentos deste protocolo ainda serão realizados.

## 1. Objetivo e perguntas de pesquisa

Investigar se a arquitetura Mamba consegue prever a direção de retornos de criptomoedas utilizando apenas dados OHLCV e como seu desempenho varia entre moedas e granularidades de candle.

A apresentação central dos resultados será uma **matriz com moedas nas linhas e granularidades nas colunas**. A comparação deve permitir responder:

1. O Mamba supera um baseline direcional ingênuo em dados posteriores aos usados no treinamento?
2. Para prever o mesmo período futuro, observar candles menores ou maiores altera o desempenho?
3. Essa diferença se repete em BTC, ETH e XRP e em diferentes períodos históricos?
4. Como os resultados mudam quando a tarefa passa a ser prever o próximo candle de cada granularidade?

O objeto principal é a previsibilidade direcional. A expressão “melhor para tradar” não será usada como equivalente a maior F1 ou acurácia: comprovar rentabilidade exigiria outro protocolo, incluindo execução, custos, slippage, posições e risco. Simulações de trading não integram esta entrega nem o critério de sucesso do estudo.

## 2. Decisões principais

| Item | Definição |
|---|---|
| Criptomoedas | Bitcoin (BTC), Ether (ETH) e XRP |
| Pares | BTCUSDT, ETHUSDT e XRPUSDT |
| Mercado/fonte | Binance Spot, arquivos históricos públicos de klines |
| Período | 01/01/2021 00:00 UTC até 01/01/2026 00:00 UTC, limite final exclusivo |
| Granularidades | 15 minutos, 1 hora, 4 horas e 1 dia |
| Entradas principais | Open, high, low, close e volume, sem dados externos |
| Alvo | Classe binária do retorno futuro: alta ou não alta |
| Horizonte principal | Próximas 24 horas, igual para todas as granularidades |
| Horizonte complementar | Próximo candle: 15 min, 1 h, 4 h ou 24 h, conforme a coluna |
| Contexto inicial | Últimos 7 dias completos, igual em duração entre granularidades |
| Baseline principal | Momentum: repetir a direção do retorno passado com a mesma duração do horizonte futuro |
| Outras referências obrigatórias | Random walk/retorno zero, prevalência histórica/classe majoritária e AR(1) do retorno |
| Métrica primária | Balanced accuracy; principal comparação: diferença Mamba menos momentum |
| Métricas secundárias | Accuracy direcional, F1 macro, precision/recall/F1 por classe, Brier score, matriz de confusão e suporte |
| Desenvolvimento | 2021–2023, com divisões cronológicas internas |
| Avaliação final | 2024–2025, oito folds trimestrais com treino expansivo |
| Repetições finais | Seeds 17, 42 e 2026; todas reportadas |
| Arquitetura | Mamba, PyTorch; um modelo por moeda, granularidade, horizonte, fold e seed |

Essas escolhas definem o estudo, mas não representam resultados previamente comprovados nem garantia de cobertura integral dos arquivos da fonte. A cobertura será auditada na coleta.

## 3. Justificativa das moedas

BTC e ETH são as referências escolhidas para o estudo; XRP acrescenta um terceiro ativo, permitindo observar se o comportamento encontrado nas duas referências também aparece em outra criptomoeda. Os três pares usam USDT e a mesma fonte, reduzindo diferenças introduzidas pela moeda de cotação ou pela bolsa utilizada.

A escolha é intencional, feita antes dos experimentos. Não representa uma amostra aleatória do mercado e não permite generalizar conclusões para todas as criptomoedas. SOL e BNB não integram esta versão; três ativos mantêm a matriz e o custo computacional delimitados.

**BTC e ETH não serão classificados antecipadamente como “estáveis”, nem XRP como necessariamente mais volátil.** A motivação do estudo é investigar diferenças. A caracterização descritiva usará retornos diários calculados na mesma escala: desvio-padrão, mediana e percentil 95 do retorno absoluto, por ativo e ano. As relações observadas serão relatadas, inclusive se contrariarem a expectativa inicial. Essa análise não servirá para trocar ativos depois de consultar seu desempenho preditivo.

## 4. Dados, período e qualidade

### 4.1. Fonte e recorte

Serão coletados arquivos mensais de candles de **15 minutos** do Binance Public Data, preservando arquivos originais e checksums. A fonte disponibiliza klines Spot, arquivos por dia/mês e verificação de integridade; também documenta a mudança dos timestamps Spot para microssegundos a partir de 2025. O leitor deverá tratar explicitamente a unidade temporal. [Fonte: Binance Public Data](https://github.com/binance/binance-public-data).

Os cinco anos completos oferecem mais de um período de avaliação e evitam uma coleta relativa, como “últimos 365 dias”, cujo conteúdo muda com a data de execução. A análise permanece restrita a esse recorte retrospectivo. Não se pressupõe que ele represente todos os regimes futuros.

Não haverá mistura automática com Yahoo Finance, outras exchanges ou futuros. Se faltar um arquivo, registrar a falha e tentar recuperar os mesmos candles na fonte Binance Spot, documentando a procedência. Se a cobertura inviabilizar uma comparação, revisar o protocolo por motivo de qualidade de dados antes dos experimentos e registrar a mudança; não substituir ativos com base em scores.

### 4.2. Agregação dos candles

Os candles de 1h, 4h e 1d serão derivados dos mesmos candles-base de 15m: primeira abertura, máxima das máximas, mínima das mínimas, último fechamento e soma do volume.

Os blocos serão alinhados em UTC: horas cheias, 00/04/08/12/16/20h para 4h e 00h para 1d. Somente blocos completos serão válidos. A referência temporal de previsão será o instante em que o candle terminou e seu fechamento ficou disponível, distinguindo-o do timestamp de abertura armazenado na fonte.

### 4.3. Regras de qualidade e rastreabilidade

- Ordenar timestamps, verificar frequência esperada e detectar duplicatas. Duplicatas conflitantes devem ser investigadas, sem escolher um valor silenciosamente.
- Exigir preços positivos, volume não negativo e consistência entre abertura, máxima, mínima e fechamento.
- Não interpolar preços com informação futura nem preencher candles ausentes automaticamente.
- Rejeitar amostras cujo contexto, cálculo de indicador ou intervalo do alvo atravesse lacunas. Indicadores reiniciam após uma lacuna e respeitam novo aquecimento.
- Na matriz principal, utilizar a interseção dos dias elegíveis dos três ativos e das quatro granularidades, definida pela qualidade dos dados, nunca pelo rótulo ou erro do modelo. Registrar as exclusões e o total efetivo de dias por fold.
- Registrar fonte, URL, par, intervalo, datas solicitadas/observadas, unidade temporal, data da coleta, quantidade de registros e SHA-256 dos arquivos.
- Preservar os dados brutos. Dados transformados recebem versão e manifestos próprios.

## 5. Comparação justa entre candles

### 5.1. Matriz principal: mesmo futuro, mesmo passado e mesmas origens

Em todos os casos, a previsão principal será produzida **uma vez por dia, às 00:00 UTC**, imediatamente após o término dos candles anteriores, para a direção das próximas 24 horas. Treino, validação e teste principais também terão uma amostra por dia elegível, nas mesmas origens temporais.

| Candle | Contexto inicial de 7 dias | Horizonte de 24 horas |
|---|---:|---:|
| 15 minutos | 672 candles | 96 candles |
| 1 hora | 168 candles | 24 candles |
| 4 horas | 42 candles | 6 candles |
| 1 dia | 7 candles | 1 candle |

Assim, uma linha da comparação usa o mesmo preço de referência, o mesmo desfecho futuro e a mesma duração de histórico. A variável que muda entre colunas é a resolução com que esse histórico é representado. Também não se concede ao modelo de 15m mais exemplos de treinamento apenas por existir maior quantidade de candles.

Essa escolha responde precisamente se **maior detalhe intradiário ajuda a prever o dia seguinte**. Não responde, por si só, se negociar a cada 15 minutos seria melhor. A quantidade de exemplos independentes continua limitada: aproximadamente 1.826 origens diárias no período completo, antes de contexto, purga e exclusões. Os 672 candles de uma entrada de 15m não são 672 exemplos independentes. O possível sobreajuste, especialmente com poucos dias de treino, deve ser discutido.

No experimento de contexto, a alternativa será **14 dias**: 1.344/336/84/14 candles, respectivamente. A escolha entre 7 e 14 dias será única para toda a matriz, feita no desenvolvimento; não haverá escolha retrospectiva por célula. A grade comum de elegibilidade deve considerar o maior contexto e o maior aquecimento entre candidatos para mantê-los comparáveis.

### 5.2. Matriz complementar: próximo candle

Será avaliado também `H = 1` candle: 15m, 1h, 4h e 1d. Nessa análise, origens de treino, validação e teste ocorrem a cada candle completo da própria granularidade. O contexto em dias e a configuração escolhida no desenvolvimento permanecem fixos.

Essa tabela representa tarefas e frequências diferentes. Diferenças de desempenho podem decorrer da granularidade, do horizonte e da quantidade de amostras. Portanto, ela será identificada como **comparação operacional de tarefas distintas**, sem atribuir todas as diferenças ao tamanho do candle. A célula de 1d coincide com a tarefa principal e seus resultados serão reutilizados.

## 6. Variável-alvo e alinhamento temporal

Seja `t` o instante da previsão, `C_t` o último fechamento disponível e `H` o número de candles futuros. O retorno logarítmico futuro é:

```text
r(t, H) = ln(C_(t+H) / C_t)
y(t, H) = 1, se r(t, H) > 0       (alta)
y(t, H) = 0, se r(t, H) <= 0      (não alta: baixa ou empate)
```

O empate fica na classe 0 e sua frequência será reportada. Não será criada classe neutra nem serão excluídos retornos pequenos: excluir amostras pela magnitude futura mudaria a população avaliada usando informação indisponível na previsão.

Para contexto de `W` candles, a entrada será `[x_(t-W+1), ..., x_t]`. O alvo compara `C_t` com `C_(t+H)`. O último candle da entrada e o preço de referência do alvo correspondem ao mesmo instante; não haverá deslocamento adicional de uma linha.

Cada amostra armazenará início/fim do contexto, origem `t`, término do alvo, par, granularidade e horizonte. Alinhamentos serão feitos por timestamps, sem depender da posição relativa de linhas em parquets diferentes.

## 7. Baselines e decisão de classe

Não existe uma única baseline exclusiva do mercado cripto. A prática encontrada na literatura combina referências que respondem perguntas diferentes. Estudos de retorno de Bitcoin usam random walk e modelos autorregressivos como benchmarks; uma comparação ampla de BTC, ETH e XRP utiliza explicitamente a previsão de retorno zero. A síntese e as fontes estão em [nota metodológica sobre baselines](baseline_metodologia.md).

O protocolo adotará quatro referências. Elas serão executadas em todas as moedas, granularidades, horizontes e folds, sobre exatamente as mesmas observações do Mamba.

### 7.1. B0 — random walk sem drift / retorno zero

Sob o benchmark random walk, o melhor palpite pontual para o preço futuro é o preço atual, equivalente a retorno futuro previsto igual a zero:

```text
retorno_previsto_RW(t, H) = 0
probabilidade_RW(alta) = 0,5
```

Para classificação dura, a regra de desempate do alvo transforma zero em classe 0. Essa previsão constante será registrada, mas não será confundida com “jogar uma moeda”: simular classes aleatórias acrescentaria ruído ao benchmark. A probabilidade fixa 0,5 será comparada às probabilidades do Mamba por Brier score.

O random walk é o benchmark teórico de ausência de previsibilidade de retorno. Ele não é sinônimo da regra de momentum descrita abaixo.

### 7.2. B1 — prevalência histórica e classe majoritária

Em cada fold, calcular somente nos rótulos de treino:

```text
p_treino = (numero_de_altas + 1) / (numero_de_amostras + 2)
classe_majoritaria = 1, se p_treino > 0,5; caso contrário, 0
```

A suavização de Laplace evita probabilidades exatamente 0 ou 1. `p_treino` é a referência probabilística sem informação das entradas; a classe majoritária é sua decisão dura. Esse controle revela ganhos aparentes causados apenas pelo desequilíbrio entre altas e não altas. Validação e teste nunca recalculam essa proporção.

### 7.3. B2 — momentum/persistência direcional, baseline principal

O baseline principal repetirá a direção observada durante um intervalo passado da mesma duração do horizonte previsto:

```text
previsao_momentum(t, H) = 1, se C_t > C_(t-H)
previsao_momentum(t, H) = 0, caso contrário
```

Na matriz principal, o intervalo passado será sempre 24 horas. Para uma mesma moeda e dia, a previsão será idêntica nas quatro colunas; isso também verificará o alinhamento. Na tabela complementar, será a direção do último candle da granularidade.

Essa regra é chamada aqui de momentum ou persistência direcional. Ela é uma heurística ingênua operacional: se o Mamba não a superar fora da amostra, sua complexidade não produziu ganho sobre a informação direcional mais simples disponível.

### 7.4. B3 — AR(1), baseline estatística clássica

Em cada fold será estimada, por mínimos quadrados e somente no treino, uma regressão autorregressiva de primeira ordem sobre retornos com a mesma duração de `H`:

```text
retorno_futuro(t, H) = alfa + phi * retorno_passado(t, H) + erro
retorno_passado(t, H) = ln(C_t / C_(t-H))
previsao_AR1(t, H) = 1, se retorno_estimado > 0; caso contrário, 0
```

Intercepto e coeficiente serão reestimados em cada fold; não haverá regularização ou escolha de defasagens. Essa referência verifica se o Mamba supera uma relação linear elementar, mantendo o escopo Mamba como única arquitetura neural investigada. Na matriz de 24 horas, AR(1), momentum e prevalência usam a mesma série diária de origens nas quatro colunas.

### 7.5. Regras comuns

- Usar preços brutos e timestamps, sem scaler, clipping ou indicadores técnicos nas baselines B0–B2.
- AR(1) usa apenas o retorno passado definido acima; qualquer transformação é ajustada no treino do fold.
- Aplicar a mesma purga temporal, população elegível e convenção de empate do Mamba.
- Baselines são determinísticas e não recebem seeds. Repeti-las por seed duplicaria observações sem acrescentar evidência.
- Salvar as previsões individuais de todas as referências para comparação pareada.
- O Mamba prevê alta quando `p(alta) > 0,5`; caso contrário prevê classe 0. Não haverá ajuste de limiar ou abstinência no estudo principal.

## 8. Entradas, normalização e escolha da configuração

O ponto de partida será OHLCV: cinco entradas. O scaler StandardScaler será ajustado separadamente para cada ativo e fold, apenas sobre candles únicos utilizados nas entradas de treino, sem contar várias vezes um candle presente em janelas sobrepostas. Ele será reaplicado, sem novo ajuste, na validação e no teste. Não haverá clipping automático.

O cronograma prevê comparações posteriores de representação e normalização. Para manter o escopo delimitado:

| Etapa | Comparação permitida no desenvolvimento |
|---|---|
| Experimento 1 | Quatro granularidades e contexto de 7 versus 14 dias |
| Experimento 2 | OHLCV versus OHLCV + três indicadores causais |
| Experimento 3 | StandardScaler versus MinMaxScaler; configuração Mamba base versus uma alternativa |

Os três indicadores adicionais serão definidos por duração física: retorno logarítmico nas últimas 24h, distância relativa do close à SMA dos últimos 7 dias e desvio-padrão dos últimos 7 retornos diários disponíveis, calculados em uma série diária comum em UTC. Antes de 00h, usar somente o último dia encerrado. Os indicadores serão associados causalmente aos candles de cada granularidade. A lista resultará em oito entradas e ficará congelada antes do Experimento 2.

A arquitetura inicial será compacta: `d_model=32`, duas camadas, `d_state=16`, `d_conv=4`, `expand=2`, pooling no último passo e dropout de 0,1. A única alternativa arquitetural será `d_model=64`, mantendo os demais valores. Esses são pontos de partida explícitos, não configurações selecionadas pelos testes anteriores.

Treinamento planejado: AdamW, taxa inicial `0,0002`, weight decay `0,001`, batch efetivo 32, até 100 épocas, clipping da norma do gradiente em 1 e cross-entropy sem pesos de classe. Early stopping por balanced accuracy de validação, paciência de 10 épocas; empate mantém o checkpoint mais antigo. Sem scheduler ou busca adicional nesta versão. Registrar também loss, épocas e duração. Em limitação de memória, reduzir microbatch e acumular gradientes para preservar batch efetivo, registrando a mudança.

As comparações serão sequenciais, modificando um fator por vez. Cada escolha usará a média não ponderada de balanced accuracy nos três ativos, quatro granularidades e folds de desenvolvimento, com seed 42. Empates favorecem a opção inicial mais simples/menor. Todos os candidatos e seus scores serão registrados; não selecionar uma configuração diferente para cada célula da matriz.

O teste final não escolherá o melhor candle, ativo ou modelo para então ocultar as demais células. Todas as combinações definidas serão apresentadas.

## 9. Desenho walk-forward

Walk-forward será implementado como avaliação em blocos posteriores com reestimação do modelo e expansão do histórico. A validação por origens móveis usa apenas observações anteriores à origem avaliada e pode considerar horizontes de vários passos. [Referência metodológica: Hyndman e Athanasopoulos, seção 5.10](https://otexts.com/fpp3/tscv.html).

### 9.1. Desenvolvimento e congelamento

Todas as decisões de contexto, entradas, normalização e configuração interna usarão somente **2021–2023**. Os quatro folds de desenvolvimento serão:

| Fold | Treino expansivo a partir de 01/01/2021 | Validação para early stopping | Avaliação de desenvolvimento |
|---|---|---|---|
| D1 | Até 30/09/2022 | 2022-T4 | 2023-T1 |
| D2 | Até 31/12/2022 | 2023-T1 | 2023-T2 |
| D3 | Até 31/03/2023 | 2023-T2 | 2023-T3 |
| D4 | Até 30/06/2023 | 2023-T3 | 2023-T4 |

A coluna de avaliação de desenvolvimento pode orientar escolhas e, por isso, não é teste final. Antes de abrir scores de 2024–2025, salvar versão do protocolo, código, grade de candidatos, configuração selecionada e manifesto dos dados.

O registro de reinício deverá informar quais períodos e métricas foram consultados nos testes antigos. Se 2024–2025 já tiverem orientado escolhas anteriores, sua avaliação não poderá ser descrita como completamente intocada: declarar a exposição e a limitação, ou definir outra reserva temporal em nova versão antes das execuções. Remover arquivos não apaga exposição prévia a resultados.

### 9.2. Avaliação final

| Fold | Treino expansivo a partir de 01/01/2021 | Validação para early stopping | Teste |
|---|---|---|---|
| F1 | Até 30/09/2023 | 2023-T4 | 2024-T1 |
| F2 | Até 31/12/2023 | 2024-T1 | 2024-T2 |
| F3 | Até 31/03/2024 | 2024-T2 | 2024-T3 |
| F4 | Até 30/06/2024 | 2024-T3 | 2024-T4 |
| F5 | Até 30/09/2024 | 2024-T4 | 2025-T1 |
| F6 | Até 31/12/2024 | 2025-T1 | 2025-T2 |
| F7 | Até 31/03/2025 | 2025-T2 | 2025-T3 |
| F8 | Até 30/06/2025 | 2025-T3 | 2025-T4 |

As datas da tabela representam blocos de calendário. Na implementação, usar intervalos `[início, início_do_bloco_seguinte)`, em UTC. Primeiro aplicar a separação por origem; depois a purga abaixo. Contexto e aquecimento reduzem as amostras iniciais de 2021.

Em cada fold e seed, criar modelo, otimizador e scaler novos. Não reutilizar pesos de um fold anterior. Treinar no histórico indicado, selecionar a época pela validação e prever todo o bloco de teste sem atualizar parâmetros dentro dele. Dados de antigos testes tornam-se passado e podem compor a validação/treino posterior de acordo com a tabela; a regra e os hiperparâmetros permanecem congelados.

Cada configuração possui seu próprio treinamento, mas utiliza as mesmas origens elegíveis da comparação principal. Apenas o DataLoader de treino poderá embaralhar amostras.

### 9.3. Purga dos alvos e contexto passado

Uma amostra só pertence a um bloco se o término do seu alvo ocorrer **estritamente antes do início do bloco seguinte**. Remover as últimas origens que violem essa condição. Na tarefa principal, isso corresponde a uma separação conservadora de 24h; na complementar, à duração de um candle. Para o último teste, o término do alvo deve ser anterior a 01/01/2026 00:00 UTC.

Essa regra impede que rótulos de treino dependam de preços do bloco de validação e que rótulos de validação dependam de preços do teste. O scaler também permanece restrito às entradas de treino efetivamente elegíveis.

O contexto de uma amostra de validação/teste pode utilizar candles anteriores ao início daquele bloco: esse passado já estava disponível na previsão. Não é necessário apagar todo o contexto de `W` candles nas fronteiras. A restrição essencial está na disponibilidade temporal das entradas, dos rótulos usados no ajuste e das estatísticas de transformação.

## 10. Métricas, agregação e interpretação

### 10.1. Métricas obrigatórias

Balanced accuracy será a métrica primária. Ela é a média do recall de alta e do recall de não alta; quando as duas classes aparecem, qualquer regra que sempre escolha a mesma classe obtém 0,5. Isso oferece uma escala de ausência de discriminação mais estável diante de desequilíbrio que a accuracy bruta ou o F1 macro.

F1 macro continuará obrigatório: é a média do F1 das duas classes. Usar sempre a lista de classes `[0, 1]` e definir F1/precision/recall indefinidos como zero, registrando suportes; isso evita que a métrica mude de definição quando uma classe estiver ausente. [Definição e opções: documentação do F1](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html).

Para cada modelo, moeda, granularidade, horizonte, fold e seed, registrar:

- Balanced accuracy e `delta_BA = BA_Mamba - BA_momentum` em pontos percentuais; registrar também os deltas contra classe majoritária e AR(1).
- Accuracy direcional, também denominada taxa de acerto ou mean directional accuracy, e F1 macro.
- Precision, recall e F1 por classe, matriz de confusão e quantidade de amostras por classe.
- Brier score das probabilidades do Mamba, do random walk (`p=0,5`) e da prevalência de treino. Reportar `BSS = 1 - BS_Mamba / BS_prevalencia`; BSS positivo indica ganho probabilístico sobre a referência, zero indica empate e negativo indica piora.
- Previsões individuais, probabilidades, alvo e timestamps para auditoria e recálculo.
- Tempo de treinamento, número de épocas, parâmetros e backend utilizado.

Fold vazio deve ser marcado como indisponível, com motivo; não preencher com zero nem inventar observações. Ausência de classes ou perda material de cobertura deverá aparecer na discussão e na tabela de qualidade.

### 10.2. Agregação

Cada célula principal mostrará balanced accuracy média do Mamba nos oito folds e três seeds, balanced accuracy das baselines nos oito folds e diferenças médias pareadas. A média dará o mesmo peso a cada fold e seed; não juntar mais candles de 15m para dominar a média. Cada baseline determinística será calculada uma única vez por fold.

Separar duas fontes de variabilidade: desvio-padrão entre seeds dentro de cada fold e variação entre folds após média das seeds. Seeds não são três novos históricos de mercado. Reportar também quantos folds tiveram diferença positiva e a diferença por ativo, sem transformar um percentual arbitrário de vitórias em prova estatística.

Como análise de incerteza, usar bootstrap circular pareado de blocos temporais de 7 dias, 2.000 reamostragens, com sensibilidade a 14 e 28 dias e seed de reamostragem 42. Sortear inícios de blocos no calendário de cada fold, com retorno circular ao início desse mesmo fold; concatenar até atingir sua duração original e truncar o excesso. Dias sem observações elegíveis permanecem vazios. Reamostrar os mesmos blocos para Mamba, baseline, granularidades e moedas; recalcular as métricas por seed e a média definida acima. Para a tabela complementar, blocos continuam em dias de calendário e incluem todas as origens daquele período. Reportar intervalos percentis de 95% e explicitar que a estimativa depende da escolha de blocos e do histórico observado; ela não incorpora todas as fontes de incerteza do treinamento. A documentação de [bootstrap temporal do projeto arch](https://arch.readthedocs.io/en/latest/bootstrap/timeseries-bootstraps.html) descreve os blocos circulares de comprimento fixo; os comprimentos e a quantidade de reamostragens são escolhas deste protocolo.

### 10.3. O que contará como evidência

A hipótese nula principal é ausência de ganho preditivo médio do Mamba sobre momentum. O contraste global será a média de `delta_BA` com pesos iguais nas 12 células. Um intervalo inteiramente acima de zero apoia ganho médio neste recorte; intervalo incluindo zero indica evidência insuficiente para estabelecer ganho, e não prova de equivalência.

O teste de Pesaran–Timmermann será aplicado como diagnóstico global da associação entre o sinal previsto pelo Mamba e o realizado. Sua hipótese nula é independência direcional; ele não substitui a comparação pareada com as baselines. A comparação com momentum e AR(1) será sustentada pelos deltas e pelo bootstrap temporal definido acima.

As diferenças entre candles serão apresentadas por moeda e também agregadas, usando 1h como referência previamente definida. Os intervalos por célula e contraste serão tratados como descritivos, sem alegar significância simultânea em dezenas de comparações. Uma conclusão de superioridade consistente exige discutir direção, tamanho e estabilidade dos ganhos por período e ativo; uma única célula favorável não basta.

Os resultados receberão uma interpretação previamente definida:

| Classificação | Evidência observada fora da amostra |
|---|---|
| Ruim | `delta_BA` global contra momentum menor ou igual a zero, ou BSS menor ou igual a zero contra prevalência |
| Promissor, mas inconclusivo | `delta_BA` positivo, porém o intervalo de 95% inclui zero |
| Bom | `delta_BA` global contra momentum positivo com intervalo de 95% acima de zero, BSS positivo e desempenho acima da classe majoritária |
| Muito forte/robusto | Critério “bom”, ganho também sobre AR(1), delta positivo em cada moeda e em pelo menos 75% dos folds após média das seeds |

Essas categorias qualificam a evidência do experimento, não estabelecem percentuais universais de acurácia nem garantem lucro. Os valores exatos e todas as células serão publicados, inclusive quando critérios diferentes divergirem.

## 11. Forma das tabelas finais

### Tabela principal — direção das próximas 24 horas

Mesmas origens diárias, mesmo contexto em dias e mesma população de dias elegíveis. Cada célula conterá `BA Mamba / BA momentum / delta em p.p.`, acompanhada das demais baselines e da incerteza na tabela detalhada.

| Moeda / candle de entrada | 15 minutos | 1 hora | 4 horas | 1 dia |
|---|---|---|---|---|
| BTC | A calcular | A calcular | A calcular | A calcular |
| ETH | A calcular | A calcular | A calcular | A calcular |
| XRP | A calcular | A calcular | A calcular | A calcular |

### Tabela complementar — direção do próximo candle

| Moeda / candle | 15 min → +15 min | 1 h → +1 h | 4 h → +4 h | 1 d → +24 h |
|---|---|---|---|---|
| BTC | A calcular | A calcular | A calcular | Reutilizar principal |
| ETH | A calcular | A calcular | A calcular | Reutilizar principal |
| XRP | A calcular | A calcular | A calcular | Reutilizar principal |

Apresentar separadamente suporte, proporção de classes, scores por fold/seed e caracterização dos ativos. Se for utilizado um mapa de calor, destacar `delta_BA` em uma escala comum, sem mascarar células desfavoráveis. Essas tabelas são modelos de apresentação; nenhum valor foi produzido ainda.

## 12. Viabilidade e sequência de implementação

A matriz final principal terá `3 moedas × 4 granularidades × 8 folds × 3 seeds = 288` treinamentos. A complementar adiciona `3 × 3 × 8 × 3 = 216`; a coluna diária é reutilizada. Total: **504 treinamentos finais**, além do desenvolvimento. Isso será medido por um piloto de tempo/memória somente no desenvolvimento; o tempo total não está estimado por execução real nesta entrega.

Para o desenvolvimento, cada configuração global custa `3 × 4 × 4 × 1 = 48` treinamentos. A sequência admite no máximo cinco configurações distintas: inicial, contexto alternativo, entradas alternativas, normalizador alternativo e largura alternativa, reaproveitando resultados já existentes quando a configuração não mudou. Limite planejado: 240 treinamentos de desenvolvimento. O conjunto diário tem poucos exemplos, enquanto a tarefa complementar intradiária pode ser substancialmente mais cara.

Se o orçamento medido não couber no cronograma, reduzir primeiro a tabela complementar e depois as alternativas de desenvolvimento, em uma revisão registrada **antes de consultar resultados finais**. Não remover seletivamente moedas, granularidades ou seeds por apresentarem desempenho baixo. A matriz principal de 12 células é a prioridade do trabalho.

| Etapa do cronograma | Implementação/entrega orientada por este protocolo |
|---|---|
| Atividade 1 | Este documento: decisões, fórmulas, matriz, folds e regras de avaliação |
| Coleta | Download do período fechado, manifesto, checksums e auditoria dos três pares |
| Pré-processamento | Agregações UTC, janelas com timestamps, alvo binário, elegibilidade, purga e scaler por fold |
| Infraestrutura e baseline | Implementar B0–B3 antes do Mamba; validar igualdade das referências entre colunas principais e produzir seus primeiros resultados |
| Mamba base | Validar os componentes preservados, construir treino, checkpoint, seeds e registro de backend |
| Experimentos 1–3 | Comparações delimitadas em 2021–2023 e congelamento da configuração |
| Robustez | Oito folds finais, três seeds, matriz principal e análise complementar conforme orçamento registrado |
| Análise e escrita | Consolidar scores, incerteza, cobertura, limitações e responder às perguntas de pesquisa |

Os novos `run_pipeline.py` e `run_treino.py` serão construídos nas respectivas etapas. Nesta fundação não há execução desses orquestradores. O usuário realizará as futuras coletas e execuções de treinamento.

## 13. Reprodutibilidade e critérios de conclusão da Atividade 1

Cada experimento deverá identificar protocolo, commit, versão dos dados, par, granularidade, contexto, horizonte, lista/ordem das features, scaler, fronteiras temporais, seed, hiperparâmetros, backend Mamba, versões de dependências e hardware. Salvar estado do scaler, checkpoint e previsões. Não sobrescrever resultados de outra célula ou fold.

O estudo final usará um backend Mamba registrado e consistente entre células. O fallback PyTorch permanece disponível para desenvolvimento, mas sua compatibilidade de interface não comprova equivalência numérica ao backend oficial. Trocas não podem ocorrer silenciosamente na matriz científica.

A Atividade 1 estabelece:

- [x] Criptomoedas e justificativa de seleção.
- [x] Fonte, datas históricas e granularidades.
- [x] Variável-alvo, instante de previsão e horizontes.
- [x] Baselines e população de avaliação.
- [x] Métricas, agregação e interpretação.
- [x] Walk-forward por datas, seleção interna e proteção contra vazamento.
- [x] Tabela moedas × candles e distinção entre horizonte fixo e próximo candle.
- [x] Escopo dos experimentos posteriores e orçamento de execuções.

Antes da implementação experimental, registrar o histórico de exposição a dados/resultados dos testes anteriores. Na coleta, comprovar cobertura. Na infraestrutura, comprovar viabilidade computacional. Esses registros verificam pressupostos explícitos do protocolo; não autorizam escolher decisões a partir do teste final.

## 14. Referências e registro da fundação

- [Cronograma de Atividades TCC 2](Cronograma_Atividades_TCC2_Murilo_Monferrari.pdf), documento do projeto.
- [Binance Public Data](https://github.com/binance/binance-public-data): origem dos candles, arquivos e integridade.
- [Hyndman e Athanasopoulos — Time series cross-validation](https://otexts.com/fpp3/tscv.html): validação por origens temporais.
- [Gradojevic et al. — Forecasting Bitcoin with technical analysis](https://doi.org/10.1016/j.ijforecast.2021.08.001): benchmarks random walk e ARMAX em horizontes horário e diário.
- [Liu, Zhang e Zhao — Out-of-sample forecasting of cryptocurrency returns](https://doi.org/10.1016/j.physa.2022.127379): benchmark de retorno zero em BTC, ETH e XRP.
- [Pesaran e Timmermann — A Simple Nonparametric Test of Predictive Performance](https://doi.org/10.1080/07350015.1992.10509922): teste de acurácia direcional.
- [Gneiting e Raftery — Strictly Proper Scoring Rules](https://doi.org/10.1198/016214506000001437): avaliação de previsões probabilísticas e Brier score.
- [Documentação de F1](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html): definição e convenções da métrica.
- [Bootstrap para séries temporais — arch](https://arch.readthedocs.io/en/latest/bootstrap/timeseries-bootstraps.html): reamostragem em blocos circulares.

As datas, moedas, granularidades, grades e regras de comparação são decisões deste protocolo; não foram determinadas pelas referências como configurações universalmente ótimas.

Em 14/09/2026, foram removidos os módulos de análise de anomalias, pipeline e treino exploratórios, baselines/avaliações/previsões antigos, CSVs de teste, metadado do checkpoint e documentação técnica desatualizada. O frontend deixou de apresentar previsões e parâmetros experimentais antigos. Foram preservados o cronograma, os componentes genéricos Mamba, a infraestrutura de ambiente e os componentes genéricos de gráficos. Arquivos anteriormente versionados podem ser recuperados pelo histórico Git; nenhum teste anterior integra a evidência científica deste protocolo.
