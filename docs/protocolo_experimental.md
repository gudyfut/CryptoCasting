# Protocolo experimental — Atividade 1 do TCC 2

**Projeto:** CryptoCasting — Previsibilidade de Criptomoedas com a Arquitetura Mamba: um Sistema de Forecasting Temporal  
**Autor:** Murilo R. F. Monferrari  
**Versão:** 1.6 — 28/09/2026; inclusão da LSTM como segunda baseline após o piloto AR(1) de desenvolvimento

**Entrega:** definição do desenho experimental, conforme o [cronograma](Cronograma_Atividades_TCC2_Murilo_Monferrari.pdf).  
**Estado técnico em 13/10/2026:** a coleta e o pré-processamento foram executados pelo pesquisador; o dataset `daeec76f001afb50a8fe` está documentado na [Entrega 3](entregas/03_pre_processamento_amostras/resultados_execucao_oficial.md). AR(1) BTCUSDT/D1–D4 tem resultados na [Entrega 4](entregas/04_infraestrutura_baselines/resultados_desenvolvimento_BTC_D1_D4.md). LSTM e infraestrutura de treino pareado foram validadas no [piloto BTCUSDT/1d/D1 em CPU](entregas/05_mamba_base/resultados_piloto_BTC_D1_cpu.md), executado pelo agente com autorização explícita: BA Mamba 41,46%, LSTM 50,00% e AR(1) 46,34%. A qualificação do backend oficial/CUDA permanece pendente por indisponibilidade do ambiente compatível nesta máquina. A [Entrega 5](entregas/05_mamba_base/README.md) documenta comandos e artefatos. Não existem resultados finais de 2024–2025; as decisões metodológicas da versão 1.6 permanecem vigentes. Esta atualização de estado é posterior ao piloto; a pasta da execução preserva a cópia exata do protocolo que foi utilizado.

## 1. Objetivo e perguntas de pesquisa

### Revisão de tarefas em aberto — 13/10/2026

Por solicitação do pesquisador, estamos examinando **quais tarefas de previsão devem integrar a ampliação do estudo**. O [estudo fundamentado](estudo_tarefas_previsao.md) e a seção visual “O que prever” distinguem direção, retorno/preço, faixas probabilísticas, volatilidade e primeiro toque em barreiras. O explorador combina moeda, candle, prazo, alvo, contexto e agenda. O antigo catálogo A–H foi reorganizado para não confundir alvos com horizontes ou políticas de resposta. Direção diária de 24h e direção do próximo candle já pertencem a este protocolo; somente o piloto neural diário tem execução documentada.

**Contrato executável permanece 1.6.** Este registro abre uma decisão, sem alterar retroativamente alvos, amostras, resultados ou liberar tarefas novas. A escolha deverá produzir uma versão operacional explícita, com baselines, purga, métricas e orçamento adequados. O piloto NVIDIA continua delimitado à Entrega 5; a grade maior aguarda essa definição e a qualificação técnica. Os totais de treinamento deste documento não incluem as novas candidatas, inclusive horizontes de 3/7/14 dias exibidos para discussão. O PT avalia associação direcional, não qualidade/correção do treinamento; alvos sobrepostos ou seleção de origens exigem rever a inferência antes do uso.

Investigar se a arquitetura Mamba consegue prever a direção de retornos de criptomoedas utilizando apenas dados OHLCV e como seu desempenho varia entre moedas e granularidades de candle.

A apresentação central dos resultados será uma **matriz com moedas nas linhas e granularidades nas colunas**. A comparação deve permitir responder:

1. O Mamba supera o AR(1) estatístico e uma LSTM neural com as mesmas entradas, em dados posteriores aos usados no treinamento?
2. Para prever o mesmo período futuro, observar candles menores ou maiores altera o desempenho?
3. Essa diferença se repete em BTC, ETH, BNB e XRP e em diferentes períodos históricos?
4. Como os resultados mudam quando a tarefa passa a ser prever o próximo candle de cada granularidade?
5. Usar 14 dias de contexto, em vez de 7, melhora ou piora a previsão em cada moeda e granularidade?

O objeto principal é a previsibilidade direcional. A expressão “melhor para tradar” não será usada como equivalente a maior F1 ou acurácia: comprovar rentabilidade exigiria outro protocolo, incluindo execução, custos, slippage, posições e risco. Simulações de trading não integram esta entrega nem o critério de sucesso do estudo.

## 2. Decisões principais

| Item | Definição |
|---|---|
| Criptomoedas | Bitcoin (BTC), Ether (ETH), BNB e XRP |
| Pares | BTCUSDT, ETHUSDT, BNBUSDT e XRPUSDT |
| Mercado/fonte | Binance Spot, arquivos históricos públicos de klines |
| Período | 01/01/2021 00:00 UTC até 01/01/2026 00:00 UTC, limite final exclusivo |
| Granularidades | 15 minutos, 1 hora, 4 horas e 1 dia |
| Entradas principais | Open, high, low, close e volume, sem dados externos |
| Alvo | Classe binária do retorno futuro: alta ou não alta |
| Horizonte principal | Próximas 24 horas, igual para todas as granularidades |
| Horizonte complementar | Próximo candle: 15 min, 1 h, 4 h ou 24 h, conforme a coluna |
| Contextos analisados | 7 dias como referência e 14 dias como análise de sensibilidade, reportados separadamente |
| Baseline estatística simples | ARIMA(1,0,0) nos log-retornos, equivalente a AR(1) com intercepto; parâmetros ajustados somente no treino de cada fold |
| Baseline neural sequencial | LSTM unidirecional em PyTorch; mesmas janelas, features, alvo e folds do Mamba; topologia e escolha definidas na seção 7 |
| Referência clássica e matemática | Random walk sem deriva prevê preço inalterado e, neste alvo, sempre não alta: BA de 50% quando ambas as classes reais estão presentes; não é a BA observada do AR(1) |
| Teste direcional | Pesaran–Timmermann (PT), com nível de significância de 5%; não testa a diferença Mamba menos AR(1) ou LSTM |
| Métrica primária | Balanced accuracy; diferenças pareadas Mamba menos AR(1) e Mamba menos LSTM, apresentadas separadamente |
| Métricas secundárias | Accuracy direcional, F1 macro, matriz de confusão e suporte por classe |
| Desenvolvimento | 2021–2023, com divisões cronológicas internas |
| Avaliação final | 2024–2025, oito folds trimestrais com treino expansivo |
| Repetições finais | Seeds 17, 42 e 2026; todas reportadas |
| Arquiteturas | Mamba (objeto do estudo) e LSTM (baseline neural), ambas em PyTorch; um ajuste de cada arquitetura por moeda, granularidade, contexto, horizonte, fold e seed |

Essas escolhas definem o estudo, mas não representam resultados previamente comprovados nem garantia de cobertura integral dos arquivos da fonte. A cobertura será auditada na coleta.

## 3. Justificativa das moedas

Os quatro ativos foram escolhidos por terem **papéis de uso e mecanismos de rede diferentes**, documentados na [justificativa da Entrega 2](entregas/02_pipeline_coleta/justificativa_ativos.md): BTC é o ativo nativo de uma rede de pagamentos baseada em prova de trabalho; ETH paga pelo uso e pela validação de uma plataforma de contratos inteligentes; BNB é nativo da BNB Chain e também oferece usos na corretora Binance; XRP é o ativo nativo de uma rede voltada a pagamentos e liquidação por consenso entre validadores. Essas propriedades motivam a comparação, **sem demonstrar por si mesmas** diferenças de volatilidade ou previsibilidade.

Os quatro pares usam USDT, mercado Spot e a mesma fonte de candles. A escolha é intencional, feita antes dos experimentos. Não representa uma amostra aleatória do mercado e não permite generalizar conclusões para todas as criptomoedas. A ligação de BNB com a Binance e o fato de todos os preços virem da mesma corretora serão explicitados como limites da amostra. Eventos e mudanças nas redes, como a transição do Ethereum para prova de participação em 2022, podem gerar mudanças de regime; este estudo não atribuirá causalmente resultados de previsão a esses eventos.

**A ordem BTC < ETH < BNB < XRP é uma hipótese do projeto, não um ranking verificado de volatilidade.** Na Entrega 3, calcular retornos logarítmicos de fechamentos diários UTC para os quatro ativos nos **mesmos dias válidos**. Reportar, por ativo e ano e no período completo, desvio-padrão diário, sua versão anualizada com `sqrt(365)`, mediana e percentil 95 do retorno absoluto, além de cobertura e quantidade de dias. A comparação anual mostrará se a ordem persiste ou muda com o período. Nenhum ativo será incluído ou excluído depois de ver sua volatilidade ou seus scores preditivos.

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
- Na matriz principal, utilizar a interseção dos dias elegíveis dos quatro ativos e das quatro granularidades, definida pela qualidade dos dados, nunca pelo rótulo ou erro do modelo. Registrar as exclusões e o total efetivo de dias por fold; se BNB tiver falhas relevantes, mostrar o efeito na cobertura antes de qualquer revisão do protocolo.
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

Na análise de contexto, serão comparados **7 e 14 dias**. Com 14 dias, as entradas terão 1.344/336/84/14 candles, respectivamente. Os dois resultados serão reportados separadamente; não será escolhido retrospectivamente um contexto diferente para cada célula. A grade comum de elegibilidade considerará 14 dias e o maior aquecimento entre candidatos, inclusive os retornos consecutivos exigidos pelo AR(1), para que a diferença observada não seja causada por avaliar dias diferentes.

### 5.2. Matriz complementar: próximo candle

Será avaliado também `H = 1` candle: 15m, 1h, 4h e 1d. Nessa análise, origens de treino, validação e teste ocorrem a cada candle completo da própria granularidade. O contexto ficará fixo em 7 dias, para isolar a mudança do horizonte. A coluna de 1d coincide com o horizonte de 24 horas e será reutilizada.

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

## 7. Baseline e decisão de classe

O protocolo adotará **duas baselines de confronto com papéis diferentes**. **ARIMA(1,0,0) nos log-retornos**, equivalente a AR(1) com intercepto, verifica se o Mamba supera uma regra estatística simples que usa apenas fechamentos. **LSTM unidirecional** verifica se o Mamba acrescenta desempenho frente a outra arquitetura sequencial recebendo exatamente as mesmas entradas. ARIMA e LSTM aparecem como comparadores em estudos de direção de cripto; isso não demonstra que esta especificação seja universalmente a melhor ou a mais usada. A [pesquisa metodológica](baseline_metodologia.md) distingue também o *random walk* clássico, 50% de BA e regras técnicas como SMA.

### 7.1. Modelo autorregressivo de um passo

Para uma série de fechamentos completos disponíveis até a origem `t`, calcular `r_t = ln(C_t/C_(t-1))`. Estimar, por mínimos quadrados ordinários com intercepto, apenas em pares de retornos consecutivos do treino de cada fold:

```text
r_t = alfa + phi * r_(t-1) + erro_t
r_previsto_(t+1|t) = alfa_estimado + phi_estimado * r_t
previsao_baseline(t) = 1, se r_previsto_(t+1|t) > 0
previsao_baseline(t) = 0, se r_previsto_(t+1|t) <= 0
```

Os parâmetros `alfa` e `phi` são reestimados no treino de cada fold expansivo, sem seleção de ordem, limiar ou hiperparâmetros por desempenho final. A baseline não recebe seeds. Se o ajuste for impossível, registrar a indisponibilidade do fold e investigar, sem substituir silenciosamente o modelo.

Na **matriz principal de 24 horas**, o AR(1) usa retornos de fechamentos **diários UTC** da moeda, derivados dos candles-base 15m. Às 00:00 UTC, o último dia completo já está disponível. Ajustar um modelo por moeda e fold. Em uma mesma moeda e origem, sua previsão é idêntica nas quatro granularidades e nos contextos de 7/14 dias.

Na **tabela complementar de próximo candle**, ajustar um AR(1) por moeda, granularidade e fold aos retornos de candles completos daquela granularidade. Em cada origem, o último retorno já observado prevê o próximo. A célula diária coincide com a principal e será reutilizada. Essas colunas representam tarefas e frequências diferentes.

O *random walk* sem deriva (`Ĉ_(t+H) = C_t`) é a referência clássica para preço. Convertido literalmente pelo limiar do alvo, prevê sempre classe 0; sua BA é 50% quando as duas classes reais aparecem. Por isso será explicado junto da referência de 50%, **sem ser contado como um segundo ganho independente**. A baseline AR(1) poderá ter BA diferente de 50%.

### 7.2. LSTM: baseline neural pareada

A LSTM receberá o mesmo tensor temporal `[amostras, candles_do_contexto, features]` do Mamba para cada configuração. Usará as mesmas cinco entradas OHLCV ou as mesmas oito entradas quando os indicadores forem avaliados, na mesma ordem, com o mesmo scaler ajustado somente ao treino purgado de cada fold. Moeda, granularidade, origem, término do alvo, contexto de 7/14 dias, horizonte, elegibilidade e rótulo também serão idênticos. Comparar essas previsões em pares permite investigar o efeito da arquitetura **sob entradas equivalentes**; não garante igualdade de capacidade ou número de parâmetros.

A topologia inicial será uma LSTM **unidirecional de duas camadas**, `batch_first=True`, `hidden_size=32`, dropout entre camadas de `0,1`, último passo temporal e camada linear para duas classes. A única alternativa arquitetural no desenvolvimento será `hidden_size=64`, mantendo duas camadas e os demais valores. Escolher uma das duas larguras pela mesma regra global de BA do desenvolvimento descrita na seção 8, com empate a favor de 32; congelar essa escolha antes de 2024–2025. A comparação de larguras internas do Mamba continua específica do Mamba: não se deve escolher a largura da LSTM com resultados finais nem trocar sua topologia por célula. Registrar contagem de parâmetros de ambos e custo computacional, sem reivindicar controle perfeito de capacidade.

A LSTM utilizará o mesmo orçamento de treino, otimizador, taxa inicial, batch efetivo, função de perda, regra de early stopping, limiar `p(alta) > 0,5`, folds e três identificadores de seed definidos para o Mamba. Os pesos e estados de otimizador serão novos a cada fold e seed. As escolhas de **dados** (contexto, features e normalização) serão aplicadas a ambos; não se dará a cada baseline um conjunto distinto de indicadores escolhido com base no teste final. A LSTM não substitui o AR(1): ela responde à pergunta de comparação entre arquiteturas, enquanto o AR(1) responde à de superar um modelo simples.

### 7.3. Regras de comparação

- Ajustar coeficientes apenas com o treino elegível do fold, sem pares que atravessem lacunas ou rótulos que cruzem o corte temporal. Durante validação e teste, manter os coeficientes congelados; atualizar apenas o último retorno **já realizado** e disponível na origem. Não reestimar no bloco de teste.
- Usar somente fechamentos e timestamps até `t`; não consumir candle aberto, interpolar lacunas ou usar o alvo na previsão. Aplicar a mesma população elegível, timestamps, purga e convenção de empate do Mamba e da LSTM. Exigir dois retornos consecutivos para iniciar o AR(1); não há aquecimento de 20 dias da SMA.
- A baseline é determinística dado seu treino e não recebe seeds. Repeti-la por seed duplicaria observações sem acrescentar evidência.
- Salvar previsão, retorno estimado, coeficientes, tamanho e corte do treino, origem e término do alvo ao lado das previsões do Mamba e da LSTM e do valor real.
- Mamba e LSTM preveem alta quando `p(alta) > 0,5`; caso contrário preveem classe 0. Não haverá ajuste de limiar ou abstinência no estudo principal.

## 8. Entradas, normalização e escolha da configuração

O ponto de partida será OHLCV: cinco entradas. O scaler StandardScaler será ajustado separadamente para cada ativo e fold, apenas sobre candles únicos utilizados nas entradas de treino, sem contar várias vezes um candle presente em janelas sobrepostas. Ele será reaplicado, sem novo ajuste, na validação e no teste. Mamba e LSTM reutilizarão **o mesmo scaler de cada célula/fold**. Não haverá clipping automático.

O cronograma prevê comparações posteriores de representação e normalização. Para manter o escopo delimitado:

| Etapa | Comparação permitida no desenvolvimento |
|---|---|
| Experimento 1 | Quatro granularidades com horizonte de 24h; resultados separados para contextos de 7 e 14 dias |
| Experimento 2 | OHLCV versus OHLCV + três indicadores causais |
| Experimento 3 | StandardScaler versus MinMaxScaler para ambos; duas larguras Mamba e duas larguras LSTM, escolhidas separadamente no desenvolvimento |

Os três indicadores adicionais serão definidos por duração física: retorno logarítmico nas últimas 24h, distância relativa do close à SMA dos últimos 7 dias e desvio-padrão dos últimos 7 retornos diários disponíveis, calculados em uma série diária comum em UTC. Antes de 00h, usar somente o último dia encerrado. Os indicadores serão associados causalmente aos candles de cada granularidade. A lista resultará em oito entradas e ficará congelada antes do Experimento 2.

A arquitetura Mamba inicial será compacta: `d_model=32`, duas camadas, `d_state=16`, `d_conv=4`, `expand=2`, pooling no último passo e dropout de 0,1. A única alternativa arquitetural Mamba será `d_model=64`, mantendo os demais valores. A LSTM terá as duas opções de `hidden_size` da seção 7. Esses são pontos de partida explícitos, não configurações selecionadas pelos testes anteriores.

Treinamento planejado **para ambas as redes**: AdamW, taxa inicial `0,0002`, weight decay `0,001`, batch efetivo 32, até 100 épocas, clipping da norma do gradiente em 1 e cross-entropy sem pesos de classe. Early stopping por balanced accuracy de validação, paciência de 10 épocas; empate mantém o checkpoint mais antigo. Sem scheduler ou busca adicional nesta versão. Registrar também loss, épocas e duração. Em limitação de memória, reduzir microbatch e acumular gradientes para preservar batch efetivo, registrando a mudança.

As comparações serão sequenciais, modificando um fator por vez. Os contextos de 7 e 14 dias são objetos de análise e ambos terão seus scores registrados; não será selecionado silenciosamente o melhor contexto de cada célula. Para decisões posteriores de features, normalização e largura, a configuração de referência usará contexto de 7 dias e horizonte de 24 horas. Cada escolha usará a média não ponderada de balanced accuracy nos quatro ativos, quatro granularidades e folds de desenvolvimento, com seed 42. As decisões compartilhadas de **features e normalização** seguirão a BA de desenvolvimento do Mamba, por ser o objeto do estudo, e serão aplicadas igualmente à LSTM; os resultados de ambos para todas as opções serão publicados. A largura da LSTM será selecionada pela própria BA de desenvolvimento, e a do Mamba pela BA do Mamba. Empates favorecem a opção inicial mais simples/menor. Todos os candidatos serão registrados.

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

Em cada fold e seed, criar Mamba, LSTM e seus otimizadores novos; ajustar um scaler de treino por configuração e fold e aplicá-lo a ambas as redes. Não reutilizar pesos de um fold anterior. Treinar no histórico indicado, selecionar a época de cada rede pela validação e prever todo o bloco de teste sem atualizar parâmetros dentro dele. Dados de antigos testes tornam-se passado e podem compor a validação/treino posterior de acordo com a tabela; a regra e os hiperparâmetros permanecem congelados.

Cada configuração possui seu próprio treinamento, mas utiliza as mesmas origens elegíveis da comparação principal. Apenas o DataLoader de treino poderá embaralhar amostras.

### 9.3. Purga dos alvos e contexto passado

Uma amostra só pertence a um bloco se o término do seu alvo ocorrer **estritamente antes do início do bloco seguinte**. Remover as últimas origens que violem essa condição. Na tarefa principal, isso corresponde a uma separação conservadora de 24h; na complementar, à duração de um candle. Para o último teste, o término do alvo deve ser anterior a 01/01/2026 00:00 UTC.

Essa regra impede que rótulos de treino dependam de preços do bloco de validação e que rótulos de validação dependam de preços do teste. O scaler também permanece restrito às entradas de treino efetivamente elegíveis.

O contexto de uma amostra de validação/teste pode utilizar candles anteriores ao início daquele bloco: esse passado já estava disponível na previsão. Não é necessário apagar todo o contexto de `W` candles nas fronteiras. A restrição essencial está na disponibilidade temporal das entradas, dos rótulos usados no ajuste e das estatísticas de transformação.

## 10. Métricas, agregação e interpretação

### 10.1. Métricas obrigatórias

Balanced accuracy será a métrica primária. Ela é a média do recall de alta e do recall de não alta; quando as duas classes reais aparecem, qualquer regra que sempre escolha a mesma classe obtém 0,5. **50% é uma referência matemática**, equivalente à BA da tradução binária do *random walk* sem deriva neste alvo; não é a BA observada do AR(1) nem um teste de significância. Isso oferece uma escala de ausência de discriminação mais estável diante de desequilíbrio que a accuracy bruta ou o F1 macro. Se faltar uma classe real, a leitura de BA contra 50% fica indisponível e o suporte será registrado.

F1 macro continuará obrigatório: é a média do F1 das duas classes. Usar sempre a lista de classes `[0, 1]` e definir F1/precision/recall indefinidos como zero, registrando suportes; isso evita que a métrica mude de definição quando uma classe estiver ausente. [Definição e opções: documentação do F1](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html).

Para cada modelo, moeda, granularidade, contexto, horizonte, fold e seed, registrar:

- Balanced accuracy de Mamba, AR(1) e LSTM; `BA_Mamba - BA_AR1`, `BA_Mamba - BA_LSTM` e `BA_Mamba - 50%` em pontos percentuais, mantidos como três cálculos distintos.
- Accuracy direcional, também denominada taxa de acerto ou mean directional accuracy, e F1 macro.
- Precision, recall e F1 por classe, matriz de confusão e quantidade de amostras por classe.
- Previsões individuais dos três métodos, probabilidades de Mamba e LSTM, alvo e timestamps para auditoria e recálculo.
- Tempo de treinamento, número de épocas, contagem de parâmetros e backend utilizado para cada rede.

Fold vazio deve ser marcado como indisponível, com motivo; não preencher com zero nem inventar observações. Ausência de classes ou perda material de cobertura deverá aparecer na discussão e na tabela de qualidade.

### 10.2. Agregação

Cada célula principal mostrará balanced accuracy média de Mamba e LSTM nos oito folds e três seeds, balanced accuracy do AR(1) nos oito folds e as duas diferenças médias pareadas Mamba menos cada baseline. A média dará o mesmo peso a cada fold e seed; não juntar mais candles de 15m para dominar a média. O AR(1), ajustado ao treino do fold, será calculado uma única vez por fold e pareado a cada seed apenas para a diferença, sem tratá-lo como três ajustes independentes. Mostrar `BA_Mamba - 50%` em coluna separada; 50% não entra no cálculo de ganho sobre qualquer baseline.

Separar duas fontes de variabilidade: desvio-padrão entre seeds dentro de cada fold e variação entre folds após média das seeds. Seeds não são três novos históricos de mercado. Reportar também quantos folds tiveram diferença positiva e a diferença por ativo, sem transformar um percentual arbitrário de vitórias em prova estatística.

Reportar quantos folds tiveram cada diferença pareada positiva. Isso mostra estabilidade temporal sem acrescentar, nesta entrega, um procedimento de reamostragem complexo.

### 10.3. O que contará como evidência

Há **quatro perguntas separadas**:

1. **Mamba versus AR(1):** `BA_Mamba - BA_AR1` mostra o ganho observado sobre o comparador estatístico simples nos mesmos timestamps. Entradas diferentes impedem atribuir a diferença somente à arquitetura.
2. **Mamba versus LSTM:** `BA_Mamba - BA_LSTM` mostra o ganho observado sobre a baseline neural com as mesmas entradas, rótulos e períodos. Hiperparâmetros internos e capacidade podem diferir. Nenhuma das duas diferenças de BA, isoladamente, é prova de superioridade estatística; PT não testa diferenças entre modelos.
3. **Comparação com 50%:** `BA_Mamba - 50%` mostra a distância ao patamar de um classificador constante ou de palpites independentes, quando as duas classes reais aparecem. O *random walk* sem deriva traduzido para este alvo é uma previsão constante de classe 0 e cai nesse mesmo patamar, não constituindo evidência adicional. Valor positivo não fornece p-valor e não implica vencer as baselines.
4. **Teste PT:** avalia se o acerto direcional observado difere do esperado pelas frequências marginais de altas reais e previstas sob a hipótese de falha preditiva. A independência direcional implica essa hipótese, mas não deve ser usada como sinônimo exato dela. Exigir estatística **positiva** e `p < 0,05` no teste bicaudal para alegar associação direcional favorável. PT significativo com estatística negativa não é evidência favorável.

O PT será calculado **separadamente para Mamba e LSTM**, por seed, concatenando as previsões fora da amostra dos oito folds sem duplicar timestamps. Publicar os três p-valores e estatísticas de cada rede; a célula exibirá o maior p-valor por rede. Uma alegação favorável pelo PT para uma rede exige suas três estatísticas positivas e seus três p-valores abaixo de 0,05. Para o AR(1) determinístico, calcular uma vez por célula. Quando o teste for degenerado, registrar indisponibilidade, sem fabricar p-valor. Registrar autocorrelação descritiva de previsões e rótulos dentro dos folds. O PT clássico pressupõe independência serial para a inferência; se houver dependência material, seu p-valor será tratado como condicional/exploratório, sem alegação confirmatória de previsibilidade pelo PT isolado. As muitas células examinadas também limitam a interpretação.

As diferenças entre candles serão apresentadas por moeda e também agregadas, usando 1h como referência previamente definida. Os intervalos por célula e contraste serão tratados como descritivos, sem alegar significância simultânea em dezenas de comparações. Uma conclusão de superioridade consistente exige discutir direção, tamanho e estabilidade dos ganhos por período e ativo; uma única célula favorável não basta.

As antigas faixas únicas de "ruim" a "excelente" misturavam perguntas diferentes e foram retiradas antes dos experimentos. A conclusão apresentará **separadamente**: magnitude e sinal das duas diferenças frente às baselines; posição em relação a 50%; estatística/p-valor PT; estabilidade entre folds, seeds e moedas. Pode-se descrever uma célula como favorável neste protocolo se `BA_Mamba > 50%`, ambas as diferenças de BA forem positivas e PT do Mamba for positivo com `p < 0,05` nas três seeds, sempre informando magnitudes e limitações. Isso não equivale a demonstrar estatisticamente que Mamba supera as baselines, nem estabelece rentabilidade de trading.

## 11. Forma das tabelas finais

### Tabela principal — direção das próximas 24 horas, contexto de 7 dias

Mesmas origens diárias, mesmo contexto em dias e mesma população de dias elegíveis. **Quatro tabelas separadas** usarão as mesmas linhas (moedas) e colunas (granularidades):

1. **Comparação estatística:** `BA Mamba / BA AR(1) / BA Mamba − BA AR(1) em p.p.` por célula.
2. **Comparação neural:** `BA Mamba / BA LSTM / BA Mamba − BA LSTM em p.p.` por célula.
3. **Referência de 50%:** `BA Mamba / BA Mamba − 50% em p.p.`, com suporte das classes.
4. **Teste PT:** estatísticas e p-valores de cada rede por seed, indicando o maior p-valor por célula e qualquer indisponibilidade; AR(1) uma vez por célula.

| Moeda / candle de entrada | 15 minutos | 1 hora | 4 horas | 1 dia |
|---|---|---|---|---|
| BTC | A calcular | A calcular | A calcular | A calcular |
| ETH | A calcular | A calcular | A calcular | A calcular |
| BNB | A calcular | A calcular | A calcular | A calcular |
| XRP | A calcular | A calcular | A calcular | A calcular |

### Tabela complementar — direção do próximo candle, contexto de 7 dias

| Moeda / candle | 15 min → +15 min | 1 h → +1 h | 4 h → +4 h | 1 d → +24 h |
|---|---|---|---|---|
| BTC | A calcular | A calcular | A calcular | Reutilizar principal |
| ETH | A calcular | A calcular | A calcular | Reutilizar principal |
| BNB | A calcular | A calcular | A calcular | Reutilizar principal |
| XRP | A calcular | A calcular | A calcular | Reutilizar principal |

Apresentar separadamente suporte, proporção de classes, scores por fold/seed e caracterização dos ativos. Se for utilizado um mapa de calor, destacar `delta_BA` em uma escala comum, sem mascarar células desfavoráveis. Essas tabelas são modelos de apresentação; o piloto AR(1) de desenvolvimento não preenche as tabelas finais.

### Tabelas de contexto e horizonte

A análise de contexto repetirá a matriz principal duas vezes: uma para 7 dias e outra para 14 dias, além de uma tabela de contraste `BA_14d - BA_7d`. A análise de horizonte manterá contexto de 7 dias e apresentará lado a lado próximo candle e próximas 24 horas. Não agregar essas tarefas em um único score antes de mostrar seus resultados individuais.

Essas separações permitem que uma moeda apresente resultado favorável apenas em previsão curta, apenas em previsão longa ou apenas com determinada quantidade de contexto. Qualquer conclusão ficará limitada à configuração efetivamente avaliada.

## 12. Viabilidade e sequência de implementação

A matriz principal com contexto de 7 dias terá `4 moedas × 4 granularidades × 8 folds × 3 seeds = 384` treinamentos **por rede**. Repeti-la com contexto de 14 dias adiciona 384 por rede. A análise de próximo candle adiciona `4 × 3 granularidades não diárias × 8 folds × 3 seeds = 288` por rede; a coluna diária é reutilizada. O escopo completo chega a **1.056 treinamentos Mamba + 1.056 treinamentos LSTM = 2.112 treinamentos neurais finais**, além do desenvolvimento e dos ajustes determinísticos AR(1). Isso será medido por um piloto de tempo/memória somente no desenvolvimento; o tempo total não está estimado por execução real nesta entrega.

Para o desenvolvimento, cada configuração global custa `4 × 4 × 4 × 1 = 64` treinamentos **por rede**. A sequência admite no máximo cinco configurações distintas por rede: inicial, contexto alternativo, entradas alternativas, normalizador alternativo e largura alternativa, reaproveitando resultados já existentes quando a configuração não mudou. Limite planejado: **320 Mamba + 320 LSTM = 640 treinamentos de desenvolvimento**. O conjunto diário tem poucos exemplos, enquanto a tarefa complementar intradiária pode ser substancialmente mais cara.

Se o orçamento medido não couber no cronograma, a ordem de prioridade será: matriz principal de 7 dias e 24 horas **com as duas baselines**; comparação de contexto com 14 dias; análise de próximo candle; demais alternativas de desenvolvimento. Qualquer redução será registrada **antes de consultar resultados finais**, preservando a comparação pareada Mamba–LSTM em toda célula mantida. Não remover seletivamente moedas, granularidades, contextos, horizontes ou seeds por apresentarem desempenho baixo.

| Etapa do cronograma | Implementação/entrega orientada por este protocolo |
|---|---|
| Atividade 1 | Este documento: decisões, fórmulas, matriz, folds e regras de avaliação |
| Coleta | Download do período fechado, manifesto, checksums e auditoria dos quatro pares |
| Pré-processamento | Agregações UTC, janelas com timestamps, alvo binário, elegibilidade, purga e scaler por fold |
| Infraestrutura e baselines | Preservar ARIMA(1,0,0) já implementado; implementar LSTM e infraestrutura compartilhada de dados, treino, avaliação e alinhamento |
| Mamba base | Validar os componentes preservados, construir treino, checkpoint, seeds e registro de backend; verificar a comparação pareada com LSTM |
| Experimentos 1–3 | Comparações delimitadas em 2021–2023 para ambas as redes e congelamento das escolhas compartilhadas e das larguras próprias |
| Robustez | Oito folds finais, três seeds para cada rede, matriz principal e análise complementar conforme orçamento registrado |
| Análise e escrita | Consolidar scores, incerteza, cobertura, limitações e responder às perguntas de pesquisa |

O novo `run_pipeline.py` foi construído na Entrega 3. `run_treino.py`, implementado nas Entregas 4/5, executa as duas redes no desenvolvimento e mantém F1–F8 bloqueados; `run_avaliacao.py` consolida execuções por configuração e fold. O usuário realiza coleta, processamento integral e treinamentos.

## 13. Reprodutibilidade e critérios de conclusão da Atividade 1

Cada experimento deverá identificar protocolo, commit, versão dos dados, par, granularidade, contexto, horizonte, lista/ordem das features, scaler, fronteiras temporais, modelo, seed quando aplicável, hiperparâmetros, backend Mamba quando aplicável, versões de dependências e hardware. Salvar estado do scaler, checkpoints neurais e previsões. Não sobrescrever resultados de outro modelo, célula ou fold.

O estudo final usará um backend Mamba registrado e consistente entre células. O fallback PyTorch permanece disponível para desenvolvimento, mas sua compatibilidade de interface não comprova equivalência numérica ao backend oficial. Trocas não podem ocorrer silenciosamente na matriz científica.

A Atividade 1 estabelece:

- [x] Criptomoedas e justificativa de seleção.
- [x] Fonte, datas históricas e granularidades.
- [x] Variável-alvo, instante de previsão e horizontes.
- [x] Duas baselines, referência de 50%, teste PT e população de avaliação.
- [x] Métricas, agregação e interpretação.
- [x] Walk-forward por datas, seleção interna e proteção contra vazamento.
- [x] Tabelas separadas por moeda, candle, contexto e horizonte, modificando um fator por vez.
- [x] Escopo dos experimentos posteriores e orçamento de execuções.

Antes da implementação experimental, registrar o histórico de exposição a dados/resultados dos testes anteriores. Na coleta, comprovar cobertura. Na infraestrutura, comprovar viabilidade computacional. Esses registros verificam pressupostos explícitos do protocolo; não autorizam escolher decisões a partir do teste final.

## 14. Referências e registro da fundação

- [Cronograma de Atividades TCC 2](Cronograma_Atividades_TCC2_Murilo_Monferrari.pdf), documento do projeto.
- [Binance Public Data](https://github.com/binance/binance-public-data): origem dos candles, arquivos e integridade.
- [Hyndman e Athanasopoulos — Time series cross-validation](https://otexts.com/fpp3/tscv.html): validação por origens temporais.
- [Fama — The Behavior of Stock-Market Prices](https://doi.org/10.1086/294743): passeio aleatório como referência histórica em ações.
- [Gradojevic et al. — Forecasting Bitcoin with technical analysis](https://www.sciencedirect.com/science/article/pii/S0169207021001230): passeio aleatório e ARMAX como benchmarks de retornos de Bitcoin.
- [Predicting market movement direction for bitcoin: A comparison of time series modeling methods](https://doi.org/10.1016/j.compeleceng.2020.106905): ARIMA e outros comparadores na tarefa binária de direção.
- [Deep learning for Bitcoin price direction prediction: models and trading strategies empirically compared](https://doi.org/10.1186/s40854-024-00643-1): ARIMA como benchmark estatístico de direção.
- [Dynamic Bayesian Networks for Predicting Cryptocurrency Price Directions](https://link.springer.com/article/10.1007/s40745-025-00637-5): exemplo de estudo de direção de cripto que inclui ARIMA e LSTM entre os comparadores; sua configuração não define a deste TCC.
- [Bustos e Pomares-Quimbaya — Stock market movement forecast: A Systematic review](https://doi.org/10.1016/j.eswa.2020.113464): indicadores técnicos como entradas comuns, sem estabelecer SMA como baseline dominante.
- [Brock, Lakonishok e LeBaron — Simple Technical Trading Rules and the Stochastic Properties of Stock Returns](https://doi.org/10.1111/j.1540-6261.1992.tb04681.x): médias móveis como regras de negociação em ações, tarefa diferente da classificação deste TCC.
- [Welch e Goyal — A Comprehensive Look at the Empirical Performance of Equity Premium Prediction](https://doi.org/10.1093/rfs/hhm014): média histórica como benchmark de retornos de ações.
- [Pesaran e Timmermann — A Simple Nonparametric Test of Predictive Performance](https://doi.org/10.1080/07350015.1992.10509922): teste de acurácia direcional, distinto da diferença Mamba menos baseline.
- [Blaskowitz e Herwartz — Testing the value of directional forecasts in the presence of serial correlation](https://doi.org/10.1016/j.ijforecast.2013.06.001): limitação do PT clássico sob dependência serial.
- [Documentação de balanced accuracy](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.balanced_accuracy_score.html): média dos recalls e referência de 50% no caso binário com ambas as classes.
- [Documentação de F1](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html): definição e convenções da métrica.
- [Documentação PyTorch LSTM](https://docs.pytorch.org/docs/stable/generated/torch.nn.LSTM.html): parâmetros e comportamento da arquitetura de comparação.

As datas, moedas, granularidades, grades e regras de comparação são decisões deste protocolo; não foram determinadas pelas referências como configurações universalmente ótimas.

**Revisão 1.6, 28/09/2026:** por decisão do pesquisador, LSTM foi acrescentada à baseline ARIMA(1,0,0) para comparar arquiteturas com as mesmas entradas. Esta revisão ocorreu **depois** da observação dos scores AR(1) de BTCUSDT nos folds de desenvolvimento D1–D4 (BA média 49,11%). Preservam-se esses resultados, sem recalibrar retroativamente o AR(1). A LSTM e o Mamba ainda não foram executados neste protocolo; a comparação final de 2024–2025 permanece reservada, sujeita ao registro de exposições anteriores previsto na seção 9.1. Foram atualizados os critérios de confronto, as tabelas e o orçamento de execução.

**Revisão 1.5, 27/09/2026:** inclusão de BNBUSDT como quarto par, a pedido do pesquisador, antes de coleta e resultados oficiais. A justificativa dos quatro ativos e a hipótese não verificada de ordem de volatilidade foram documentadas. Matriz, elegibilidade comum, inventário e orçamento de execução foram atualizados; baseline AR(1), alvo e avaliação temporal foram mantidos.

**Revisão 1.4, 27/09/2026:** a pesquisa aprofundada distinguiu a referência canônica de preço (*random walk*) de um comparador útil para o alvo binário. O *random walk* sem deriva, convertido pelo limiar deste estudo, prevê sempre classe 0 e coincide com 50% de BA; ARIMA(1,0,0) nos retornos foi fixado como baseline algorítmica de confronto. A SMA 5/20 da revisão 1.3 foi retirada desse papel por faltar evidência de que seja o benchmark padrão de previsão direcional. Nenhuma mudança foi motivada por resultados deste protocolo.

**Revisão 1.3, 27/09/2026, superada pela 1.4:** separou explicitamente ganho sobre baseline, distância da BA a 50% e teste PT e removeu antigas faixas compostas de qualidade. Propôs SMA 5/20 no lugar da persistência direcional; essa escolha de baseline não é mais vigente. Nenhuma janela foi selecionada por resultados de 2024–2025.

Em 14/09/2026, foram removidos os módulos de análise de anomalias, pipeline e treino exploratórios, baselines/avaliações/previsões antigos, CSVs de teste, metadado do checkpoint e documentação técnica desatualizada. O frontend deixou de apresentar previsões e parâmetros experimentais antigos. Foram preservados o cronograma, os componentes genéricos Mamba, a infraestrutura de ambiente e os componentes genéricos de gráficos. Arquivos anteriormente versionados podem ser recuperados pelo histórico Git; nenhum teste anterior integra a evidência científica deste protocolo.
