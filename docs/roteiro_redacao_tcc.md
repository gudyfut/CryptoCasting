# Roteiro de redação e evidências do TCC

O trabalho investiga a previsão pontual do retorno de criptomoedas em 24 horas, comparando Mamba e LSTM, com Naive e ARIMA como referências, e analisando diferentes tamanhos de contexto. A qualidade da pesquisa depende da pergunta, do controle experimental e da interpretação sustentada pelas evidências; não exige que Mamba vença ou que a estratégia simulada produza lucro.

## Organização científica

O estudo de referência foi definido em 20/10/2026 e concluído em 21/10. A revisão de 24/10 verificou os resultados e identificou uma ressalva no tratamento da penalização do Mamba. Em 26/10, o pesquisador autorizou uma extensão controlada para medir o efeito dessa correção. Essas etapas devem aparecer com sua cronologia real. Não apresentar a extensão como hipótese definida antes de conhecer os resultados originais.

O estudo anterior de barreiras permanece em `arquivo/estudo_barreiras_2026-10-20/`, como histórico. Suas classes, probabilidades, log-loss e Brier não integram os resultados do estudo atual de regressão. Se mencionado na redação, deve servir para explicar a evolução do projeto, com escopo e cronologia claros.

## Estrutura sugerida para o texto

| Parte | Conteúdo e pergunta que precisa responder | Fontes do projeto |
|---|---|---|
| Introdução | Por que avaliar retorno de 24h? Qual o interesse em Mamba versus LSTM e em contexto? Qual a diferença entre previsão e utilidade econômica? | `plano.md`, `docs/decisoes.md` e referências científicas primárias. |
| Fundamentação | Retorno logarítmico; previsão pontual e MSE; persistência/random walk; ARIMA; recorrência LSTM; estados seletivos Mamba; avaliação temporal e sobreajuste na seleção. | Artigos originais e livro de previsão, com citações verificadas. O código do projeto descreve sua implementação, não substitui literatura. |
| Dados | Quatro pares Binance Spot, período, origem dos arquivos, timestamps, lacunas, formação de horas, população comum, exclusões e limitações de representatividade. | `docs/protocolo_experimental.md`, manifesto do dataset e auditorias de coleta. |
| Método de referência | Alvo, entradas, contextos, arquitetura, seeds, escalas, treino/validação/teste, purga, parada, seleção de época e ARIMA. | Configuração, protocolo e fontes congelados de `1e7c5ed662fba55ddd25`. |
| Avaliação | Métrica principal predefinida, métricas secundárias, agregação, pares e bootstrap temporal; política Spot separada e custos. | Protocolo e publicações auditadas das duas fases. |
| Resultados da referência | LSTM versus Mamba, comparação com Naive, efeito de contexto e estabilidade; desenvolvimento e avaliação separados. | `docs/resultados_desenvolvimento.md`, `docs/resultados_avaliacao.md`, CSVs e recibos correspondentes. |
| Extensão controlada | Como a penalização foi identificada, qual a única intervenção, o que ficou constante e a exposição prévia dos períodos. | `docs/protocolo_penalizacao_mamba.md`, `docs/auditoria_configuracao_penalizacao.md` e novo congelamento. |
| Resultados da extensão | Efeito pareado da correção, intervalos, estabilidade, contexto e simulação; conclusões somente após execução completa. | Novo `analises/*/resumo.json`, comparações por ajuste, publicações e relatório gerado. |
| Discussão | O que os resultados sustentam, hipóteses sobre os mecanismos, relevância prática, ameaças à validade e comparação com a literatura. | Evidências anteriores, com distinção entre observação e hipótese causal. |
| Conclusão | Responder às perguntas sem extrapolar as moedas, períodos, entradas e configurações; indicar próximos testes independentes. | Resultados efetivamente auditados. |

## Tabelas e figuras a preparar

1. Uma linha do tempo com datas UTC de treino, validação e teste de DB1–DB4 e B1–B4, indicando a purga de 24h e o treino expansivo.
2. Uma tabela de arquitetura e treinamento, com contagem de parâmetros, argumentos oficiais Mamba, normalização, otimizador, seeds e seleção de época.
3. Uma tabela de cobertura dos dados por moeda, incluindo lacunas e tamanho da população comum. Não apresentar quantidade de janelas sobrepostas como observações independentes.
4. Uma tabela principal de MSE, RMSE, MAE e habilidade contra Naive, separando as duas fases. Identificar média de habilidades por célula e razão de erros agregados como medidas distintas.
5. Gráficos de diferenças pareadas e intervalos temporais, com zero marcado e direção de melhora explícita; não mostrar apenas barras de médias sem incerteza.
6. Gráficos do efeito de contexto e da variação entre seeds, com todos os resultados, sem selecionar uma inicialização favorável.
7. Na extensão, tabela original/corrigido e figura das diferenças por moeda/contexto, identificando análises secundárias como exploratórias.
8. Exemplos de previsões reais com seleção transparente, usados para ilustração e não como prova de superioridade. Previsão de preço transformada não equivale automaticamente à esperança do preço.
9. Resultados da política Spot, custos, exposição e drawdown quando auditável. Distinguir resultados de estratégias individuais de uma carteira combinada e compras diárias de buy-and-hold.

As figuras do artigo devem ser geradas dos arquivos auditados e exportadas com unidades, legendas, fonte e resolução adequadas. Evitar captura de tela da interface como única evidência científica.

## Como formular as conclusões

Para a referência, a formulação sustentada é: a configuração LSTM apresentou menor erro que a configuração Mamba nos períodos avaliados, mas não demonstrou vantagem clara sobre a persistência; não houve melhora geral com mais contexto. Isso não prova superioridade universal da LSTM nem ausência de previsibilidade em qualquer mercado ou conjunto de entradas.

Para a extensão, reservar a conclusão até o término da grade e auditoria. A comparação direta com o Mamba anterior responde ao efeito da política de penalização sob o procedimento fixado. A hipótese surgiu após consulta dos resultados; sua repetição nos mesmos períodos não deve ser vendida como nova confirmação independente.

Diferença de MSE é erro de previsão, não retorno financeiro. Acurácia direcional derivada do sinal não transforma o modelo em classificador probabilístico. Um resultado inconclusivo não demonstra igualdade, e uma diferença estatística não garante relevância operacional. Uma seed lucrativa não representa uma política robusta.

## Rastreabilidade e reprodução

Registrar no texto ou material suplementar: identificadores de dataset/execuções, configurações, hashes das fontes, ambiente e GPU, seeds, lista de candidatos ARIMA, regras de exclusão, falhas e retomadas, política de agregação e bootstrap. Os IDs auxiliam a reprodução e pertencem ao material técnico; o texto principal deve explicar seu significado antes de usá-los.

O ciclo de referência tem 768 ajustes neurais, 32 referências Naive e 32 seleções ARIMA, com 288 candidatos internos. Não somar candidatos e seleções como resultados independentes. A extensão planeja 384 ajustes Mamba corrigidos e dois controles de reprodução; referências herdadas não são novos treinamentos. A versão final deve substituir contagens planejadas por contagens verificadas e manter eventuais falhas no inventário.

A declaração humana de exposição anterior foi registrada para o ciclo original. Os resultados B1–B4 foram abertos em 21/10 e discutidos antes da extensão. Conservar essa diferença na seção de ameaças à validade. Arquivamento e manifestos locais não equivalem a backup externo; confirmar a preservação externa antes da entrega acadêmica.

## Referências primárias iniciais

- Gu e Dao. *Mamba: Linear-Time Sequence Modeling with Selective State Spaces*. [Artigo](https://arxiv.org/abs/2312.00752).
- Hochreiter e Schmidhuber. *Long Short-Term Memory*. Neural Computation, 9(8), 1735–1780, 1997. DOI: 10.1162/neco.1997.9.8.1735. [Texto dos autores](https://www.bioinf.jku.at/publications/older/2604.pdf).
- Loshchilov e Hutter. *Decoupled Weight Decay Regularization*. ICLR, 2019. [Artigo do AdamW](https://arxiv.org/abs/1711.05101). Distinguir weight decay desacoplado de acrescentar simplesmente uma penalidade L2 à perda.
- Hyndman e Athanasopoulos. *Forecasting: Principles and Practice*, terceira edição. [Métodos de referência e avaliação](https://otexts.com/fpp3/toolbox.html).
- Cawley e Talbot. *On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation*. JMLR, 2010. [Artigo](https://www.jmlr.org/papers/v11/cawley10a.html).
- Implementação efetivamente utilizada do Mamba: versão e SHA-256 da instalação registrados na qualificação; [repositório oficial](https://github.com/state-spaces/mamba).
- PyTorch 2.6: [opções por grupo de parâmetros](https://docs.pytorch.org/docs/2.6/optim.html#per-parameter-options), correspondentes à versão usada no experimento.
- Binance Public Data: formato, origem e convenções dos arquivos. [Repositório oficial](https://github.com/binance/binance-public-data).

O formato acadêmico exigido pela instituição, extensão do texto, modelo de artigo e prazos de entrega ainda precisam ser confrontados com as orientações atuais do curso e do orientador. A conclusão computacional não substitui esse aceite.
