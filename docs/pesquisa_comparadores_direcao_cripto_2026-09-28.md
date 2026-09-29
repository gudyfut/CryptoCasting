# Comparadores para previsão da direção de criptomoedas — revisão de 28/09/2026

## Pergunta e critério

Qual comparador usar contra o Mamba que prevê **alta versus não alta** com dados OHLCV? A resposta depende da variável prevista. Estudos de preço numérico, direção e retorno de estratégia não fornecem baselines intercambiáveis. Esta revisão consultou trabalhos originais de previsão de criptomoedas e uma revisão que tabula explicitamente as baselines de estudos selecionados. Não é uma contagem bibliométrica exaustiva nem uma pesquisa de uso interno de mesas profissionais; portanto, não atribui a nenhum método o título de “mais usado” em todo o setor.

## Evidência direta da literatura

| Estudo | Tarefa | Comparador declarado | O que sustenta aqui |
|---|---|---|---|
| [Ibrahim, Kashef e Corrigan (2021)](https://www.sciencedirect.com/science/article/pii/S0045790620307576) | Direção do BTC em 5 minutos | Palpite aleatório, estratégia de momentum e ARIMA entre os modelos comparados | Momentum é uma referência operacional para **direção**; ARIMA também aparece, mas a frequência é diferente da nossa. |
| [Omole e Enke (2024)](https://link.springer.com/article/10.1186/s40854-024-00643-1) | Direção do BTC e estratégia de negociação | ARIMA para previsão; MACD para a estratégia | ARIMA é um benchmark publicado de direção, sem garantir bom desempenho. Estratégia de trading responde a outra pergunta. |
| [Catania, Grassi e Ravazzolo (2019)](https://pure.au.dk/ws/files/211915634/CataniaGrassiRavazzolo_2019_IJF_AM.pdf) | Retornos e densidades de BTC, ETH, XRP e LTC | AR(1) com volatilidade EWMA | Autorregressão simples é comparador estabelecido em cripto, embora este modelo não seja idêntico ao AR(1) do TCC. |
| [Gradojevic et al. (2023)](https://www.sciencedirect.com/science/article/pii/S0169207021001230) | Retorno de BTC diário e horário | Random walk e ARMAX | Random walk é referência clássica para retornos; modelos lineares também são usados. |
| [Bouteska et al. (2024)](https://dk.upce.cz/bitstreams/03b91573-a6e2-40f1-a463-83793d0fcef7/download) | Preço, direção e medidas de estratégia em BTC, ETH, LTC e XRP | Random walk, ruído branco, compra/venda e ARIMA, entre outros | Um mesmo estudo usa comparadores diferentes para perguntas diferentes. |
| [Basher e Sadorsky (2022)](https://mpra.ub.uni-muenchen.de/113293/1/MPRA_paper_113293.pdf) | Direção do BTC | Regressão logística (*logit*) frente a árvores | Um classificador estatístico direto do alvo binário também é benchmark legítimo. Os autores usaram variáveis que não pertencem ao escopo deste TCC. |
| [Pabuçcu et al. (2020)](https://arxiv.org/abs/2303.04642) | Movimento do BTC | Regressão logística frente a SVM, ANN, Naive Bayes e RF | Mais um exemplo de logit como benchmark de direção; conferir diferenças de dados e horizonte antes de transferir resultados. |
| [Amirzadeh, Nazari e Thiruvady (2022)](https://www.mdpi.com/1999-4893/15/11/428) | Revisão de estudos de preço, direção e trading | A tabela de estudos inclui ARIMA, SMA de trading, modelos neurais e trabalhos sem baseline explícita | A literatura é heterogênea. A tabela não demonstra uma baseline dominante para a nossa tarefa. |
| [Dynamic Bayesian Networks for Predicting Cryptocurrency Price Directions (2025)](https://link.springer.com/article/10.1007/s40745-025-00637-5) | Direção diária de seis criptomoedas | ARIMA, SVR, RF, SVM, LSTM e outros | O artigo observa que seu ARIMA usa somente fechamento, enquanto outros comparadores usam OHLV; comparar nos mesmos dias não iguala automaticamente as entradas. |

O [manual *Forecasting: Principles and Practice*](https://otexts.com/fpp3/simple-methods.html) trata a previsão ingênua ou *random walk* como benchmark básico de séries temporais, inclusive financeiras. No **nosso** alvo, preço previsto igual ao preço atual vira sempre “não alta”, dando 50% de balanced accuracy quando as duas classes reais existem. Isso é uma referência matemática útil, mas não uma regra que discrimina os dias de alta.

## Opções para este projeto

| Método | O que recebe | Adequação à direção | Limite principal |
|---|---|---|---|
| Random walk sem deriva | Último fechamento | Vira sempre classe “não alta”; referência de 50% de BA | Não distingue os dias. |
| Momentum direcional simples | Sinal do último retorno completo: se subiu, prevê alta; caso contrário, não alta | Prevê as duas classes e se relaciona diretamente ao alvo | É uma regra simples, sem aprender parâmetros; pode falhar em regimes de reversão. Janela e tratamento de empate devem ser fixados antes do teste. |
| AR(1) atual / ARIMA(1,0,0) nos retornos | Retorno do último dia e parâmetros ajustados no treino | Comparador estatístico publicado e reprodutível | Só usa fechamentos; o piloto BTC 2023 quase nunca previu alta. Não representa toda a família ARIMA. |
| Outras ordens ARIMA | Histórico de retornos e erros anteriores | Pode ser escolhida por validação temporal no desenvolvimento | A busca aumenta graus de liberdade e não garante BA melhor; continua sem receber OHLCV completo. |
| Regressão logística regularizada | Variáveis causais definidas antes do teste, como retornos, OHLCV e indicadores | Prevê diretamente a probabilidade de alta; permite estudar parte das mesmas entradas do Mamba | É aprendizado estatístico supervisionado, embora não neural; exige uma representação tabular e regras de regularização. |
| SMA/MACD | Histórico de preços | Mais natural como regra de tendência/negociação | Janelas, cruzamentos e estados precisam ser convertidos em uma classe por origem; uma estratégia de lucro não é automaticamente um classificador comparável. |
| GARCH | Histórico de retornos e volatilidade | Útil sobretudo para prever risco/volatilidade | Volatilidade alta ou baixa não determina por si só o sinal da próxima variação. |

### Consulta adicional: ARMA–GARCH

O **ARMA** modela o retorno médio previsto; o **GARCH** acrescenta uma previsão de variância condicional, isto é, do tamanho provável das oscilações. A [documentação do pacote `arch`](https://arch.readthedocs.io/en/latest/univariate/forecasting.html) separa essas saídas. O [estudo de Berger et al. (2024)](https://onlinelibrary.wiley.com/doi/10.1002/for.3165) usa ARMA–GARCH como comparador para **retornos numéricos** do Bitcoin, avaliados por erro de previsão. Um [estudo com BTC, ETH e BNB](https://doaj.org/article/802e4dc2b7a349f18db0aacb6ebd3372) usa ARMA–GARCH–VaR para **risco**. Esses precedentes sustentam o método em cripto, mas não demonstram ganho de balanced accuracy na nossa tarefa binária.

Se a classe é definida por `retorno > 0` e a distribuição dos erros é simétrica em torno da média prevista, a regra `probabilidade de alta > 50%` tem o **mesmo sinal da média ARMA**; aumentar a variância GARCH deixa a previsão menos segura, mas não muda, por si, qual classe supera 50%. Isso é uma **dedução das equações do modelo**, não um resultado empírico para nossos dados. O ajuste conjunto pode alterar coeficientes da média e, portanto, algumas previsões; não afirmamos igualdade exata com o AR(1). Modelos [GARCH-in-mean](https://arch.readthedocs.io/en/latest/univariate/mean.html) são uma extensão distinta em que a volatilidade entra na média.

**Decisão recomendada para o objetivo declarado pelo pesquisador — uma baseline simples que sirva de piso:** não substituir o AR(1) por ARMA–GARCH. O componente adicional resolve prioritariamente uma pergunta de volatilidade/risco, aumenta escolhas de ordem/distribuição e não é uma melhora direcionada ao alvo alta versus não alta. Mantê-lo como possibilidade de trabalho futuro se o estudo passar a prever risco, probabilidade calibrada ou retorno numérico.

## Implicação para as comparações de entradas

Quando o Mamba muda de OHLCV para OHLCV mais indicadores, o AR(1) continua o **mesmo comparador fixo**, porque sua definição recebe só fechamentos. Isso permite perguntar se cada Mamba supera uma regra estatística simples no mesmo alvo e nos mesmos timestamps. **Não permite atribuir uma eventual vantagem apenas à arquitetura Mamba**: as entradas também diferem. A LSTM, incorporada ao protocolo após esta revisão, pode receber literalmente a mesma sequência bruta e os mesmos indicadores do Mamba, fornecendo um confronto mais direto entre arquiteturas. A antiga proposta de logit tabular permanece apenas como alternativa histórica não adotada.

## Recomendação para decisão com o orientador

1. **Preservar o AR(1) já predefinido e seus resultados**, inclusive os desfavoráveis. O resultado de BTC/D1–D4 não aponta, por si, erro de implementação nem invalida ARIMA como família.
2. Se a preferência por comparadores **sem aprendizado supervisionado** permanecer rígida, acrescentar **uma única regra de momentum direcional de um período**, congelada antes de avaliar outros ativos e os folds finais. Reportar Mamba versus AR(1), versus momentum e versus 50% separadamente. Isso oferece um comparador que pode prever ambas as classes, sem busca de janelas.
3. Se o objetivo inclui perguntar quanto o **Mamba acrescenta usando OHLCV e indicadores**, considerar também **regressão logística regularizada** como comparador não neural. Isso exige autorização metodológica para um método de aprendizado supervisionado e especificação prévia da representação das entradas.
4. Não priorizar uma grande busca de ordens ARIMA para “melhorar o score” visto em BTC. Se o orientador preferir um ARIMA selecionado, definir uma grade pequena e escolher apenas com avaliação cronológica de desenvolvimento de **todos os ativos**, antes de consultar 2024–2025. [Validação temporal](https://otexts.com/fpp3/tscv.html).

**Estado da revisão no momento da pesquisa:** as opções acima eram propostas, antes da decisão posterior do pesquisador. O [protocolo 1.6](protocolo_experimental.md) registra a decisão atual: preservar ARIMA(1,0,0) e acrescentar LSTM como segunda baseline. Os scores de BTC em 2023 já vistos integram a motivação declarada; 2024–2025 permanecem reservados. Momentum, logit, GARCH e buscas de ordens ARIMA continuam fora do protocolo.

### Decisão posterior: duas perguntas experimentais

O AR(1) fornece o confronto com um método estatístico simples que usa fechamentos. A LSTM fornece o confronto com uma arquitetura neural sequencial que recebe **as mesmas janelas, features e transformações** do Mamba, nas mesmas origens e folds. Uma eventual vantagem sobre AR(1) pode refletir tanto arquitetura quanto entradas; a comparação com LSTM controla as entradas, mas não iguala automaticamente número de parâmetros ou custo. Ambas as diferenças de BA serão publicadas separadamente, assim como a referência de 50% e o teste PT. A inclusão da LSTM não recalibra os resultados já observados do AR(1).
