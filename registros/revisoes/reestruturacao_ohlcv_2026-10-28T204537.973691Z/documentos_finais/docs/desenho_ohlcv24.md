# Desenho do estudo OHLCV em 24 horas

Atualizado em 28/10/2026. **Documento de decisão e proposta metodológica; não é protocolo executado nem configuração congelada.** O pesquisador autorizou reorganizar o projeto e estabelecer uma referência com OHLCV. As escolhas concretas abaixo são a recomendação para fechar essa etapa; não houve autorização de uma busca indefinida, implementação científica nova ou treinamento neste registro.

Este é o documento único de trabalho para refinar o desenho. Atualizar suas seções, em vez de criar um relatório para cada conversa. Decisão de transição: [ADR 0006](adr/0006-reorganizacao-e-desenho-ohlcv.md). Estudos já executados: [arquivo preliminar](../arquivo/estudos_preliminares_2026-10-28/README.md).

## 1. Correspondência com o TCC escrito

Fonte acadêmica: [TCC 1](TCC_1_MuriloRFM.pdf), fornecido pelo pesquisador em 28/10. Foram lidas as seções relevantes completas e inspecionada visualmente a página de posicionamento. O PDF original permanece intacto; hash, extração e evidência estão na [revisão desta organização](../registros/revisoes/reestruturacao_ohlcv_2026-10-28T204537.973691Z/fonte_tcc1.json).

| Compromisso do texto | Situação encontrada | Encaminhamento |
|---|---|---|
| Resumo/introdução: desenvolvimento iterativo do Mamba, sem ranking como finalidade central (páginas PDF 5–6) | Plano operacional de 20/10 passou a priorizar contexto e comparação Mamba–LSTM | Restaurar a investigação das decisões do Mamba como pergunta central; LSTM será referência auxiliar |
| Seção 2.7, página impressa 6 / PDF 10: desenho das entradas, OHLCV versus indicadores | Os três ciclos de retorno24 usaram apenas retornos de fechamento, apesar de coletarem OHLCV | A nova referência deve usar O, H, L, C e V explicitamente; estudos anteriores serão referências preliminares, sem mudança retroativa de sua descrição |
| Resumo, introdução e seção 2.7: avaliação walk-forward | Uma única divisão, discutida para acelerar, não satisfaz sozinha esse compromisso | Usar divisão única somente na exploração; preservar avaliação ampliada com reestimação temporal para a configuração congelada |
| Seção 2.7: normalização estática versus adaptativa dos dados | Experimento concluído mudou a posição da LayerNorm dentro da rede | Não contar pré-LayerNorm como realização de comparação estática/adaptativa das entradas |
| Seção 2.7: erro pontual não basta para utilidade de negociação | Há métricas preditivas e simulação Spot; não há evidência de ganho operacional consistente | Manter os dois eixos, com política e custos definidos antes dos resultados |
| Texto menciona contextos, normalizações, variantes e horizontes | Uma busca irrestrita multiplicaria custo e seleção retrospectiva | Delimitar hipóteses, orçamento e horizonte 24h; mudanças de escopo devem constar da redação e do alinhamento com o orientador |
| Texto fala em “teto de previsibilidade” | Experimentos finitos não identificam um limite fundamental de todo o mercado | Na redação, preferir “desempenho e limites observados sob os dados, métodos e orçamento estudados” |

Não foi verificada nesta revisão toda a bibliografia, nem o aceite formal do orientador. A seção 3 do PDF está por desenvolver. O texto não obriga, nas seções examinadas, uma grade de quatro moedas; BTC como estudo inicial é uma delimitação a explicitar, não prova sobre todo o mercado cripto.

## 2. Pergunta e escopo recomendado

**Pergunta:** como alterações controladas na representação de dados históricos OHLCV e na configuração do Mamba afetam a previsão do retorno do Bitcoin em 24h, sua estabilidade temporal e o desempenho de uma política operacional fixa?

Uma conclusão negativa é válida. Não prometer que OHLCV supera retornos, que Mamba vence LSTM, que existe lucro ou que encontraremos a melhor configuração possível. As ablações identificam efeitos nas condições estudadas, não causas universais do funcionamento interno.

| Elemento | Referência proposta |
|---|---|
| Mercado | BTCUSDT Binance Spot; demais moedas ficam como extensão de generalização |
| Dados | OHLCV de candles completos de 1h, derivados dos minutos auditados |
| Contexto | 168 candles horários; escolha de escopo, não contexto ótimo comprovado |
| Horizonte | 24h, fixo |
| Origem preditiva | A cada hora completa; não significa retreinamento horário |
| Entrada | Cinco canais O/H/L/C/V transformados causalmente, definidos abaixo |
| Saída | Um log-retorno terminal, convertido em variação percentual e preço para apresentação |
| Modelo principal | Mamba-1 oficial CUDA, scan ao longo do tempo |
| Referências | Naive zero, ARIMA e LSTM; não tratar todas como entradas/capacidades idênticas |
| Repetições | Seeds 17/42/2026, sem escolher a vencedora |
| Exploração | Uma divisão cronológica; orçamento limitado |
| Avaliação ampliada | Walk-forward em quatro blocos, após congelar a configuração; natureza retrospectiva explicitada |

## 3. Dados e entrada: o que chegará de fato à rede

OHLCV bruto fica preservado com seus timestamps, origem e unidades. Não basta afirmar que “os dados são OHLCV” se a rede recebe somente C. O contrato deverá registrar campos coletados, transformações e canais efetivos separadamente.

Para cada candle horário completo k, usar inicialmente:

| Canal | Fórmula proposta | Informação |
|---|---|---|
| abertura_relativa | ln(O_k / C_(k−1)) | Abertura em relação ao fechamento anterior |
| maxima_relativa | ln(H_k / C_(k−1)) | Máxima da hora em relação ao fechamento anterior |
| minima_relativa | ln(L_k / C_(k−1)) | Mínima da hora em relação ao fechamento anterior |
| fechamento_relativo | ln(C_k / C_(k−1)) | Retorno horário de fechamento |
| volume_transformado | ln(1 + V_k) | Volume negociado na hora, em unidade do ativo-base conforme a fonte |

Aplicar, depois, média/desvio de treinamento por canal. Sem estatísticas calculadas com validação/teste; sem atualização desses scalers dentro de um bloco. Scalers ficam salvos. Volume zero legítimo é diferente de dado ausente; desvio zero exige tratamento explícito no contrato, não divisão silenciosa por zero.

Uma amostra tem formato **168 × 5**, e um lote, **lote × 168 × 5**. As quatro variáveis de preço permanecem representadas; retirar o nível absoluto do preço é uma escolha de representação relativa, não eliminação de O/H/L. Isso não reproduz literalmente OHLCV bruto em dólares e deve aparecer na metodologia. A transformação requer um fechamento anterior ao primeiro candle, além dos 168 candles. Esse preço de fronteira é conhecido no instante da previsão.

Não usar candle parcial, volume ainda não terminado, máximas futuras, normalização global ou interpolação de lacunas. Elegibilidade usa apenas passado disponível; avaliação preditiva também requer o preço terminal observado. Para simulação, indisponibilidade futura nunca decide retrospectivamente se teria havido entrada.

Os dados atuais já armazenam OHLCV horário e minutos. Primeiro conferir integridade, unidades, lacunas e cobertura de BTC. **Não é necessário recoletar automaticamente**; preparar uma nova versão multivariada com identidade própria, mantendo o dataset anterior. A população do novo BTC não precisa ser restringida por lacunas de ETH/BNB/XRP; isso impede comparar diretamente médias agregadas antigas com novas. O controle de retornos terá exatamente as mesmas origens da nova referência OHLCV.

## 4. Alvo, unidades e interpretação

No instante t, após o último candle encerrar, prever:

`y_t = ln(C_(t+24h) / C_t)`

`variacao_percentual_prevista = 100 * expm1(previsao_log)`

`preco_correspondente = C_t * exp(previsao_log)`

Exemplo:100→102 equivale a+2% e log-retorno aproximadamente0,019803;100→98 equivale a−2% e log-retorno aproximadamente−0,020203. Não armazenar “2” como log-retorno de2%. Treinar com o alvo padronizado no treino e inverter a transformação antes das métricas publicadas.

O alvo é das **próximas**24h. A estimativa não informa trajetória, probabilidade calibrada, intervalo de confiança do preço, stop-loss ou risco de liquidação. MSE aprende uma estimativa da média condicional do log-retorno; exponenciar não garante a média condicional do preço em nível. Previsão terminal e política de operação são componentes distintos.

## 5. Exploração simples, avaliação temporal ampliada

### Exploração recomendada

| Parte | Intervalo UTC semiaberto | Uso |
|---|---|---|
| Treino | [2021-01-01,2024-01-01) | Aprender pesos e scalers |
| Validação | [2024-01-01,2025-01-01) | Escolher época e comparar configurações pelo critério fixo |
| Avaliação retrospectiva | [2025-01-01,2026-01-01) | Comparação após congelamento das candidatas, sem dirigir a rodada de busca |

Purga: o destino do alvo de cada exemplo precisa ser estritamente anterior ao fim da sua partição. Contextos podem usar passado anterior à fronteira; nenhum cálculo pode acessar o futuro da origem. A regra de validação é a mesma nas seeds; selecionar pela média de MSE das três seeds, com empates resolvidos em favor da referência/menor complexidade, não por lucro de teste. Usar a validação também para época e configuração aumenta seleção; limitar a rodada e declarar essa dependência.

**2023–2025 já foram consultados.** As novas datas não restauram um holdout intocado. O PDF também apresenta uma figura histórica até junho de 2026; não presumir que2026 inteiro está desconhecido. Eventual confirmação nova exige declaração específica sobre uso de resultados e preços e definição prévia do período, ou avaliação prospectiva. Não anunciar aprovação do orientador ou acesso intocado sem evidência.

### Avaliação ampliada proposta

Reaplicar o procedimento congelado em quatro blocos B1–B4 de 2024–2025 com treino expansivo e validação anterior a cada teste, conforme as datas históricas do [protocolo de referência](protocolo_experimental.md). Treinar do zero a cada bloco; reestimar scalers só no treino desse bloco. Nunca aplicar retrospectivamente um checkpoint treinado com dados posteriores.

Levar a referência OHLCV e no máximo uma candidata selecionada, além das referências necessárias. Quatro blocos × três seeds = 12 ajustes por configuração Mamba. Não repetir toda a busca em cada bloco. Se escolher uma configuração após consultar2024, avaliá-la em blocos de 2024 é uma verificação **retrospectiva com seleção informada pelo período**: a ordem causal dentro de cada treinamento não elimina esse viés. Relatar sempre essa limitação. Só chamar de confirmação independente uma avaliação que cumpra os requisitos de independência.

A divisão única de exploração é avaliação temporal fixa. A etapa de reestimações sucessivas é walk-forward em blocos. Fatiar previsões de um checkpoint único em quatro tabelas não equivale a esse procedimento.

## 6. Referência de treinamento e verificações

Recomendação inicial: conservar o núcleo Mamba oficial, duas camadas, largura 32, estado 16, convolução 4, expansão 2, dropout 0,1, pré-LayerNorm residual e normalização final. A projeção passa de 1 para 5 entradas. A pré-normalização é escolhida como referência tecnicamente motivada e já examinada, não como vencedora confirmada. Não transportar checkpoints anteriores para o novo estudo.

AdamW lr 0,0002, weight_decay 0,001 nos parâmetros não marcados; respeitar `_no_weight_decay` em A_log/D. Batch efetivo 64, microbatch 32, clipping 1, máximo100 épocas, paciência 10, MSE padronizado de treino, melhor MSE de validação na escala original. Seeds 17/42/2026, FP32 e ambiente qualificado. Esses números são referência reproduzível, não “padrão ótimo para cripto”. Recontar parâmetros; não copiar 20.129 do modelo de entrada escalar.

LSTM auxiliar com os mesmos cinco canais, datas, scalers, seeds e critérios, largura 32 e duas camadas como ponto de partida. Naive prevê log-retorno zero. ARIMA(p,1,q), p/q0..2, sem deriva, selecionado na validação; univariado e explicitamente diferente em informação disponível. Não denominar a comparação prova de superioridade arquitetural com informação/orçamento distintos.

Antes de treinar: testar indexação, causalidade por perturbação do futuro, uso efetivo dos cinco canais, unidades, purga, lacunas, população, transformações/inversão, máscaras de ablação, recarga e contabilidade financeira. Qualificar forward/backward/atualização e repetição CUDA no formato real. Não desativar auditorias para acelerar. Medir desempenho em benchmark próprio, mantendo mudanças de engenharia separadas das científicas.

## 7. Sequência limitada de experimentos

OHLCV é a referência principal desde o início. Volume não precisa “merecer inclusão” para cumprir esse desenho; retirar informação servirá como ablação, sem presumir que ela obrigatoriamente melhora a previsão.

| Versão | Entrada efetiva | Objetivo |
|---|---|---|
| R0 | O/H/L/C/V transformados | Estabelecer a referência multivariada |
| A1 | O/H/L/C; V mascarado | Medir contribuição do volume |
| A2 | Somente C relativo; O/H/L/V mascarados | Medir contribuição da informação adicional ao fechamento |

Manter cinco canais e a mesma projeção nas três versões: canais removidos ficam em zero **depois da padronização**. Isso preserva dimensões e contagem de parâmetros na ablação; a capacidade efetivamente exercida pode diferir. Todas as variantes são treinadas do zero, com origens comuns; não apenas zerar um canal na inferência de uma rede treinada com todos. Comparações principais R0−A1 e R0−A2; não ordenar os resultados antigos de outra divisão como controle deste experimento.

Primeira rodada proposta: três configurações × três seeds Mamba = 9 ajustes; uma LSTM OHLCV auxiliar × três seeds = 3. **12 ajustes neurais principais**, uma série Naive e nove candidatos ARIMA/uma seleção. Pilotos que integrarem a grade não são duplicados. Acrescentar dois controles de reprodução, um R0 Mamba e um LSTM, seed 42: 14 tentativas neurais concluídas previstas, além de eventuais falhas preservadas. Testes sintéticos não contam como treinos de mercado. Não executado.

Segunda rodada: no máximo duas hipóteses adicionais Mamba (até 6 ajustes principais), definidas antes de executá-las. Prioridades possíveis: representação por indicadores causalmente definidos, normalização de entrada e depois configuração do otimizador/capacidade, orientada por curvas de aprendizagem. Não abrir esses três eixos simultaneamente. Médias/indicadores não criam informação nova se derivados do mesmo passado; qualquer histórico adicional precisa ser declarado. Pré-LayerNorm não é normalização adaptativa dos dados. Adam e AdamW têm regularizações diferentes; troca requer contrato explícito.

Encerrar a rodada pelo orçamento, não quando aparecer lucro. Selecionar pela validação e publicar também fracassos. Uma nova ideia após a avaliação ampliada abre nova rodada, identificada como posterior à consulta. Se a finalidade passar a ser ranking Mamba–LSTM, será necessário orçamento comparável de ajuste; esse não é o objetivo principal do TCC 1.

## 8. Como medir previsão

- Primária: MSE de log-retorno, fora do treino, com diferença pareada contra R0 e Naive e habilidade `1 − MSE_modelo/MSE_naive` na mesma população.
- Secundárias: RMSE e MAE para interpretação de magnitude, viés médio, direção derivada do sinal e acerto balanceado, sempre com regra explícita para zero. Não usar MAPE de retornos próximos de zero.
- Mostrar cada seed e sua média; não selecionar a melhor nem formar ensemble silenciosamente.
- Mostrar resultado agregado e por trimestre, volatilidade e ano como diagnósticos previamente definidos; não remover trechos difíceis. Faixas de volatilidade, se usadas, devem ter limites derivados do treino.
- Incerteza pareada com blocos temporais, preservando dependência das previsões horárias de 24h; referência 14 dias/2.000 réplicas e sensibilidades 7/28. Documentar limites e multiplicidade; um IC que inclui zero é inconclusivo, não prova de igualdade.

“Deu certo como previsão” exige magnitude de redução de erro relevante, estabilidade e evidência temporal, não apenas a melhor média entre muitas tentativas. Não haverá limiar inventado depois dos resultados. A primeira rodada é exploratória; seu desempenho não demonstra um teto absoluto de previsibilidade.

## 9. Como medir utilidade operacional

Propor uma política Spot comprado/caixa, sem alavancagem, para avaliar o sinal com baixo número de decisões livres. Não confundir com futuros. Os dados atuais permitem essa análise; futuros exigiriam fonte e regras próprias, funding, margem e liquidação.

1. Às 00:00UTC usar apenas candles já completos. Decisão diária, embora existam previsões horárias.
2. Entrar às 00:01 no open do minuto disponível se a previsão superar o limiar de custos. Uma posição por vez, saída 24h após a entrada; saída anterior à nova entrada na fronteira diária. Capital ilustrativo 10.000USDT, posição 100% comprado ou caixa, sem reiniciar capital a cada operação.
3. Custos base assumidos por lado: taxa 0,001 e slippage 0,0005. Limiar de log-retorno `ln((1+s)*(1+f)/((1-s)*(1-f)))`. Quantidade `capital/[open_entrada*(1+s)*(1+f)]`; valor de saída `quantidade*open_saida*(1-s)*(1-f)`. Essas são hipóteses de simulação, não taxas verificadas da conta do pesquisador. O horizonte executado tem defasagem de 1min em relação ao alvo terminal; publicar essa diferença.
4. Cenário agravado: taxa 0,002 e slippage 0,001, preservando os sinais base para isolar custos. Não procurar o limiar/horário que melhor ficou no teste.
5. Referências econômicas: caixa; comprar e manter com custos de entrada/saída nas fronteiras predefinidas; compra diária sistemática com o mesmo calendário de entrada/saída da política. O Naive de retornozero fica em caixa nesta regra, não equivale a comprar e manter.
6. Publicar retorno líquido/grosso, custos, drawdown marcado por minuto, exposição, número de entradas e distribuição de ganhos/perdas, por seed e período. Sem operações: retorno zero e métricas condicionais não aplicáveis, nunca “100% de acerto”. Preços ausentes geram indisponibilidade auditável, não remoção vantajosa.

O limiar usa uma previsão pontual do log-retorno; não garante esperança de lucro positiva após custos. O open do minuto é uma aproximação de execução, sem livro de ofertas. Sem stop/take-profit, não há promessa de controle intraposição. Um experimento de stops/futuros seria outra política e novo ciclo; não adaptar essa política depois para salvar o resultado.

| Resultado observado | Conclusão permitida |
|---|---|
| MSE menor e resultado líquido pior | Previsão melhor naquela métrica; política operacional pior |
| Lucro, mas abaixo de comprar e manter, com exposição diferente | Lucro histórico; vantagem do modelo ainda não demonstrada |
| Resultado favorável em uma seed, negativo nas demais | Instabilidade; não selecionar a seed vencedora |
| Melhoria líquida consistente após custos, referência e análise temporal | Evidência para essa política e amostra, ainda sem garantia futura |

MSE e simulação são eixos separados; não criar um escore composto ajustável para declarar vitória. Na seleção inicial, MSE de validação é o critério fixo; lucro de teste não seleciona a configuração. Se a seleção econômica se tornar objetivo principal, registrar uma política de seleção própria antes da nova rodada.

## 10. Entregas e registros antes da execução

1. Fechar esta proposta e a correspondência acadêmica com o pesquisador/orientador, sem inventar aprovação.
2. Criar implementação/configuração multivariada novas, sem editar fontes dos ciclos encerrados; reusar dados brutos íntegros.
3. Congelar entradas, alvo, splits, origens, métricas, política, variantes e orçamento; atribuir identidade real somente na preparação.
4. Qualificar, executar a referência e os controles, depois as ablações autorizadas. Guardar tentativas, previsões, épocas, scalers, checkpoints e falhas.
5. Publicar resultados e decidir a rodada seguinte no mesmo documento de acompanhamento. Só as decisões materiais ganham ADR; logs/recibos ficam em registros, não viram páginas explicativas em docs.

Esta reorganização não altera o PDF, não confirma aceite acadêmico e não inicia treinamento. O portal atual ainda exibe o estudo preliminar; não deve ser apresentado como resultado OHLCV. A interface futura precisa declarar canais efetivos e identidade do ciclo, além da fonte OHLCV.

## Referências metodológicas

- [CryptoMamba](https://arxiv.org/html/2501.01010v2): referência de estudo com OHLCV diário; não prova a superioridade da nossa formulação nem equivale a reproduzi-lo.
- [Cawley e Talbot](https://www.jmlr.org/papers/v11/cawley10a.html): seleção de configurações também pode sobreajustar o conjunto usado para escolhê-las.
- [Forecasting: Principles and Practice](https://otexts.com/fpp3/toolbox.html#time-series-cross-validation): avaliação temporal com origens móveis e separação cronológica.

## Revisões deste documento

- 28/10/2026: desenho inicial após leitura do TCC1 e revisão dos estudos preliminares. OHLCV adotado como direção pelo pesquisador; detalhes propostos, sem execução. Atualizações posteriores devem registrar aqui o motivo e a situação, evitando documentos concorrentes.
