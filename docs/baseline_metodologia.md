# Pesquisa da baseline para a Entrega 1

**Revisão de 27/09/2026, antes dos experimentos do novo protocolo.** A regra SMA 5/20 proposta na revisão anterior foi retirada como baseline principal após uma pesquisa mais específica sobre *benchmarks de previsão*. Nenhum resultado do projeto foi usado nessa decisão.

**Atualização de 28/09/2026:** este documento preserva a justificativa histórica da escolha do AR(1). Depois de observar o piloto de BTCUSDT em D1–D4, o pesquisador acrescentou **LSTM** como segunda baseline no [protocolo 1.6](protocolo_experimental.md). AR(1) permanece fixo; a LSTM ainda não foi implementada ou avaliada.

## Resposta da pesquisa

Não existe uma única baseline comprovadamente mais usada em **todas** as tarefas financeiras. O comparador depende do alvo e da métrica. As fontes permitem a distinção abaixo, sem comprovar uma contagem bibliométrica ou de uso profissional:

| Tarefa | Referência documentada | Consequência para este TCC |
|---|---|---|
| Preço ou retorno numérico | Passeio aleatório sem deriva (*random walk*), com previsão de preço `Ĉ_(t+H) = C_t`. É a referência clássica em ações, câmbio e Bitcoin. | Convertido para `alta` quando o retorno previsto é `> 0`, prevê sempre `não alta`. Com as duas classes reais presentes, sua **balanced accuracy é exatamente 50%**: não oferece um segundo confronto direcional informativo. |
| Prêmio/retorno numérico de ações | Média histórica dos retornos, referência frequente em estudos do prêmio acionário. | Seu sinal pode ficar constante e a pergunta original é diferente da classificação de candles de cripto. |
| Direção | Artigos usam comparadores distintos, entre eles ARIMA/autorregressão, logit, momentum e palpite aleatório. Estudos de direção de Bitcoin incluem **ARIMA** como comparador estatístico. | Um ARIMA simples dos retornos produz previsões variáveis sem arquitetura neural ou dados externos. É o **comparador algorítmico operacional** escolhido aqui. |
| Rentabilidade de trading | Buy-and-hold e regras técnicas, inclusive médias móveis. Gestores profissionais de carteiras também comparam desempenho com índices de mercado apropriados. | A variável de sucesso deste estudo é acerto direcional, sem posições, custos ou execução. Índice ou buy-and-hold não produz a classe prevista em cada origem. |

Uma revisão sistemática de 52 estudos de classificação da direção de ações encontrou indicadores técnicos e preços como entradas frequentes; isso **não** mostra que o cruzamento SMA 5/20 seja a baseline mais usada. Estudos clássicos de médias móveis examinam regras de compra/venda ou propriedades dos retornos, finalidade distinta de prever `alta`/`não alta` a cada origem. A presença dessas regras na prática profissional também não fornece uma ordenação verificável de uso entre firmas. A escolha anterior extrapolava as fontes.

**Decisão estatística preservada:** apresentar o *random walk* sem deriva como **referência clássica conceitual**, explicando sua equivalência a 50% de BA neste alvo; usar **ARIMA(1,0,0) nos log-retornos**, equivalente a um AR(1) com intercepto, como baseline **estatística simples** de confronto com o Mamba. A baseline neural LSTM foi acrescentada posteriormente, como explica a atualização acima. ARIMA é uma família tradicional e aparece como benchmark em artigos de direção de Bitcoin. A ordem `(1,0,0)` é uma **especificação simples fixada por este projeto**, sem alegar que essa ordem seja a mais usada ou a melhor. Ela permite verificar se uma dependência linear de um período já explica o sinal. Não haverá escolha posterior de ordem pelo desempenho no teste, por AIC ou por grade.

### O que a configuração significa

`ARIMA(p,d,q)` descreve: `p` = quantidade de valores passados da série transformada usados na autorregressão; `d` = quantidade de diferenças aplicadas à série antes do ajuste; `q` = quantidade de **erros de previsão passados** incluídos. O “MA” de ARIMA é uma média móvel de **erros**, não a SMA de preços da análise técnica. Também precisam ser definidos: série modelada (preço, log-preço ou retorno), presença de intercepto/deriva, frequência dos candles e horizonte de previsão. `p=1` significa um candle anterior na frequência escolhida, não necessariamente um dia.

Exemplos úteis, **sem afirmar uma ordem mais frequente em todo o setor**: ARIMA(0,1,0) **sem** deriva no log-preço é o *random walk*; com deriva, acrescenta um retorno médio; ARIMA(1,0,0) nos log-retornos é o AR(1) adotado aqui; ARIMA(1,1,0) no log-preço expressa uma dependência semelhante dos retornos, sujeita às convenções de intercepto e estimação; ARIMA(0,1,1) inclui um erro passado após diferenciar o log-preço; ARIMA(1,1,1) combina um retorno e um erro passados. Essas variantes são famílias de especificações, não limiares percentuais.

ARIMA gera uma previsão **numérica**; a classe é derivada depois. Neste protocolo, `alta` significa retorno futuro `> 0`, então o limiar da previsão também é `0`. A pergunta “vai subir **pelo menos 5% em um dia?**” definiria **outro alvo**: `C_(t+1d)/C_t − 1 ≥ 0,05`, equivalente a log-retorno `≥ ln(1,05)`. Seria possível comparar a previsão numérica ou uma probabilidade prevista com esse limiar, mas o novo evento, seu desequilíbrio de classes e sua avaliação exigiriam outra versão do protocolo. Nenhuma escolha de `p,d,q` transforma por si só o ARIMA num classificador de altas de 5%.

## Definição operacional do ARIMA(1,0,0)

Para fechamentos completos `C_t`, calcular o log-retorno `r_t = ln(C_t / C_(t-1))`. Em cada fold, estimar apenas com retornos de **candles consecutivos do treino**, sem pares que atravessem lacunas e sem preços posteriores ao corte de treino:

```text
r_t = alfa + phi * r_(t-1) + erro_t
r_previsto_(t+1|t) = alfa_estimado + phi_estimado * r_t
previsao_AR1(t) = 1 se r_previsto_(t+1|t) > 0; caso contrário, 0
```

Estimar `alfa` e `phi` por mínimos quadrados ordinários, com intercepto; registrar coeficientes, versão da implementação, quantidade de pares e eventuais falhas de ajuste. Ordem e limiar `0` são fixos. Se o ajuste for impossível por histórico insuficiente ou singularidade, marcar o fold indisponível e investigar, sem trocar silenciosamente de regra. O AR(1) em si é um modelo estatístico linear, sem rede neural, dados externos, ajuste de limiar ou seeds; a LSTM é avaliada separadamente.

- **Matriz principal de 24 horas:** usar fechamentos **diários UTC** derivados dos mesmos candles de 15 minutos. Ajustar um AR(1) por moeda e fold com os retornos diários de treino. Em cada origem diária, usar o último retorno diário conhecido e prever o próximo. Para uma moeda, origem e fold, a baseline é idêntica nas quatro colunas de granularidade e nos contextos de 7/14 dias; o alvo também é o mesmo.
- **Matriz complementar de próximo candle:** ajustar um AR(1) por moeda, granularidade e fold com retornos de candles completos do treino daquela granularidade. Em cada origem, prever somente o próximo retorno da mesma granularidade. Reutilizar a célula diária da matriz principal.
- Os **coeficientes ficam congelados dentro do bloco de validação/teste**. O estado de um passo pode usar o último retorno *já realizado* em cada origem, inclusive dentro do bloco: esse preço já seria conhecido em operação. Não usar o candle a prever, rótulos futuros ou reajustar coeficientes no teste. Em novo fold expansivo, reestimar com o respectivo treino.
- Aplicar as mesmas origens elegíveis, timestamps de alvo, lacunas e purga temporal usados na avaliação do Mamba. O AR(1) precisa de dois retornos consecutivos para iniciar a previsão; o contexto de 7/14 dias do Mamba normalmente exige aquecimento maior. Não exigir 20 dias extras da antiga SMA.
- Salvar previsão individual, retorno previsto, coeficientes, corte de treino, origem e término do alvo. A baseline não recebe seeds; não tratar cópias suas em comparações com seeds do Mamba como observações independentes.

O AR(1) usa o último retorno na **previsão** e todos os pares históricos admissíveis do treino na **estimação**. O Mamba também é ajustado no treino histórico; sua janela de 7/14 dias por amostra não limita o total de dados de ajuste. Mamba recebe OHLCV, AR(1) usa fechamentos; a LSTM recebe as mesmas entradas do Mamba. A primeira comparação mistura arquitetura e representação, enquanto a segunda aproxima uma comparação de arquiteturas sob entradas iguais.

## Quatro verificações separadas

| Pergunta | Cálculo | Interpretação |
|---|---|---|
| **1. Mamba versus comparador estatístico** | `delta_BA = BA_Mamba − BA_AR1`, nos mesmos timestamps, em pontos percentuais. | Diferença **observada** frente ao ARIMA(1,0,0). Valor positivo isolado não prova superioridade estatística nem vence todo algoritmo de mercado. |
| **2. Mamba versus LSTM** | `BA_Mamba − BA_LSTM`, nas mesmas entradas e timestamps, em pontos percentuais. | Diferença **observada** frente à rede sequencial de referência; tamanho e outros aspectos internos podem diferir. |
| **3. Mamba versus 50%** | `BA_Mamba − 0,50`, se ambas as classes reais aparecerem. | 50% é o patamar matemático de um classificador constante em BA. A tradução do *random walk* **sem deriva** para este alvo é exatamente a classe constante 0; não contar isso como duas evidências independentes. A BA das baselines pode diferir de 50%. |
| **4. Teste Pesaran–Timmermann** | Estatística e p-valor PT entre previsões binárias e direções realizadas, por modelo. | Examina falha preditiva direcional sob as condições do teste. Exigir estatística positiva e `p < 0,05` para leitura favorável. **Não** testa diferenças de BA entre modelos; dependência serial limita a inferência clássica. |

**Exemplo didático, sem resultados do projeto:** BA Mamba 54%, BA AR(1) 56%, BA LSTM 52% e PT do Mamba positivo com `p = 0,02`. O Mamba está 4 pontos percentuais acima de 50%, perde 2 pontos para o AR(1) e ganha 2 da LSTM. Isso não autoriza afirmar superioridade às duas baselines.

Publicar BA, suporte por classe, diferenças por fold e seed, previsões individuais e estatísticas PT separadamente. Se uma baseline produzir classe constante num período, sua BA poderá ser 50%; registrar esse comportamento. Para alegar diferença **estatisticamente significativa** entre Mamba e qualquer baseline, seria necessário um teste pareado adicional apropriado à dependência temporal, definido antes de consultar resultados finais. PT sozinho não serve. Autocorrelação também pode distorcer a inferência clássica do PT; registrar diagnósticos e limitar a conclusão quando houver dependência material.

## Fontes e alcance

- [Fama (1965), *The Behavior of Stock-Market Prices*](https://doi.org/10.1086/294743): origem histórica do passeio aleatório em ações.
- [Gradojevic et al., *Forecasting Bitcoin with technical analysis: A not-so-random forest?*](https://www.sciencedirect.com/science/article/pii/S0169207021001230): **random walk e ARMAX** como benchmarks de retornos de Bitcoin em frequências diária e horária.
- [*Non-fundamental, non-parametric Bitcoin forecasting*](https://www.sciencedirect.com/science/article/pii/S0378437119309859): compara erro de previsão e acerto direcional com *random walk*.
- [*Predicting market movement direction for bitcoin: A comparison of time series modeling methods* (2021)](https://doi.org/10.1016/j.compeleceng.2020.106905): tarefa binária de 5 minutos; inclui ARIMA, momentum e palpite aleatório.
- [*Deep learning for Bitcoin price direction prediction: models and trading strategies empirically compared* (2024)](https://doi.org/10.1186/s40854-024-00643-1): chama ARIMA de **benchmark** estatístico em comparação de direção de Bitcoin. Seus dados on-chain e resultados não são transferidos para este TCC.
- [*Dynamic Bayesian Networks for Predicting Cryptocurrency Price Directions* (2025)](https://link.springer.com/article/10.1007/s40745-025-00637-5): inclui ARIMA e LSTM entre os comparadores de direção; usa condições experimentais diferentes das deste TCC e não estabelece uma arquitetura universalmente superior.
- [Catania, Grassi e Ravazzolo (2019), *Forecasting cryptocurrencies under model and parameter instability*](https://doi.org/10.1016/j.ijforecast.2018.09.005): usa **AR(1) com volatilidade EWMA** como benchmark para retornos de BTC, ETH e XRP (entre outras moedas). Sustenta o uso de autorregressão simples como comparador, sem exigir que este projeto adote o componente EWMA de volatilidade.
- [*Forecasting Bitcoin price direction with random forests* (2022)](https://doi.org/10.1016/j.mlwa.2022.100355): usa logit como benchmark; não existe um único comparador obrigatório para direção. Logit não foi adotado por ser outro classificador, enquanto aqui se preferiu um modelo estatístico de série temporal.
- [Welch e Goyal (2008), *A Comprehensive Look at the Empirical Performance of Equity Premium Prediction*](https://doi.org/10.1093/rfs/hhm014): média histórica como referência para o prêmio de ações.
- [Bustos e Pomares-Quimbaya (2020), *Stock market movement forecast: A Systematic review*](https://doi.org/10.1016/j.eswa.2020.113464): revisão de 52 estudos de direção de ações; indicadores técnicos aparecem como **entradas** comuns, sem estabelecer SMA 5/20 como baseline dominante.
- [Brock, Lakonishok e LeBaron (1992), *Simple Technical Trading Rules and the Stochastic Properties of Stock Returns*](https://doi.org/10.1111/j.1540-6261.1992.tb04681.x): médias móveis como regras de negociação, não como escolha necessária para este alvo binário.
- [CFA Institute, *Security Market Indexes*](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/security-market-indexes) e [estudo da SEC sobre benchmarks de fundos](https://www.sec.gov/file/performance-benchmarks-2022-01): no uso profissional de gestão, benchmark costuma significar índice para avaliar **retorno de carteira**; não deve ser confundido com baseline de classificação direcional.
- [Pesaran e Timmermann (1992)](https://doi.org/10.1080/07350015.1992.10509922) e [Blaskowitz e Herwartz (2014)](https://doi.org/10.1016/j.ijforecast.2013.06.001): significado e limitação do teste PT.
- [Hyndman e Athanasopoulos, *Forecasting: Principles and Practice*, capítulo ARIMA](https://otexts.com/fpp3/non-seasonal-arima.html): definição formal de `(p,d,q)` e dos casos especiais, inclusive *random walk* e AR(1).

**Limite:** essas fontes documentam exemplos fortes e o uso de cada método; não fornecem um censo de artigos nem um levantamento representativo de mesas profissionais. Portanto, não afirmamos que ARIMA, SMA ou qualquer ordem particular seja numericamente “a mais usada” por toda a indústria. O [piloto AR(1) de desenvolvimento](entregas/04_infraestrutura_baselines/resultados_piloto_BTC_D1.md) não altera essa justificativa prévia nem constitui avaliação final.

Uma [revisão complementar de 28/09/2026](pesquisa_comparadores_direcao_cripto_2026-09-28.md), feita **após** os resultados de BTC/D1–D4, examina também momentum direcional e regressão logística como possíveis comparadores adicionais. Ela apresenta propostas para decisão metodológica e não altera retroativamente a escolha predefinida acima.
