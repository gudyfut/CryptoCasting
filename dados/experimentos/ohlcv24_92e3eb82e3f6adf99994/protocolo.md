# Desenho do estudo OHLCV em 24 horas

Atualizado em 28/10/2026. **Contrato técnico da referência inicial OHLCV, implementado para preparação e qualificação; ainda sem treinamento de mercado.** O pesquisador solicitou fechar as escolhas, limpar o repositório e verificar o fluxo antes dos treinamentos. A implementação é `estudo_ohlcv/`, com configuração `configuracoes/ohlcv24_001.json`. A cópia deste documento no congelamento identifica o método daquela execução; esta página continua sendo o documento único de trabalho. Não há aprovação acadêmica presumida nem autorização de busca indefinida.

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

| Elemento | Referência inicial |
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

| Canal | Fórmula inicial | Informação |
|---|---|---|
| abertura_relativa | ln(O_k / C_(k−1)) | Abertura em relação ao fechamento anterior |
| maxima_relativa | ln(H_k / C_(k−1)) | Máxima da hora em relação ao fechamento anterior |
| minima_relativa | ln(L_k / C_(k−1)) | Mínima da hora em relação ao fechamento anterior |
| fechamento_relativo | ln(C_k / C_(k−1)) | Retorno horário de fechamento |
| volume_transformado | ln(1 + V_k) | Volume negociado na hora, em unidade do ativo-base conforme a fonte |

Aplicar, depois, média/desvio de treinamento por canal. Sem estatísticas calculadas com validação/teste; sem atualização desses scalers dentro de um bloco. Scalers ficam salvos. Volume zero legítimo é diferente de dado ausente; desvio zero exige tratamento explícito no contrato, não divisão silenciosa por zero.

Uma amostra tem formato **168 × 5**, e um lote, **lote × 168 × 5**. As quatro variáveis de preço permanecem representadas; retirar o nível absoluto do preço é uma escolha de representação relativa, não eliminação de O/H/L. Isso não reproduz literalmente OHLCV bruto em dólares e deve aparecer na metodologia. A transformação requer um fechamento anterior ao primeiro candle, além dos 168 candles. Esse preço de fronteira é conhecido no instante da previsão.

Não usar candle parcial, volume ainda não terminado, máximas futuras, normalização global ou interpolação de lacunas. Elegibilidade usa apenas passado disponível; avaliação preditiva também requer o preço terminal observado. Para simulação, indisponibilidade futura nunca decide retrospectivamente se teria havido entrada.

Os dados atuais já armazenam OHLCV horário e minutos. Primeiro conferir integridade, unidades, lacunas e cobertura de BTC. **Não é necessário recoletar automaticamente**; preparar uma nova versão multivariada com identidade própria, mantendo o dataset anterior. A população do novo BTC não precisa ser restringida por lacunas de ETH/BNB/XRP; isso impede comparar diretamente médias agregadas antigas com novas. Uma futura ablação de retornos deverá ter exatamente as mesmas origens da referência OHLCV. Ela não integra a primeira execução.

### Justificativa da representação e relação com CryptoMamba

Essas transformações **não são essenciais, nem têm superioridade demonstrada**. Uma rede pode receber preços em nível com escalas ajustadas no treino. Escolhemos a forma relativa porque nosso alvo é retorno, o nível nominal do Bitcoin varia muito entre anos e a escala do candle fica comparável. As razões H/O, L/O, C/O e a geometria do candle continuam recuperáveis a partir dos quatro canais. O nível absoluto foi deliberadamente retirado; uma futura comparação de representações poderá investigar se faz falta.

Em mercado contínuo, O costuma ser muito próximo de C anterior: abertura relativa pode carregar pouca informação e ruído de microestrutura. Padronização por canal dá escala semelhante a todas as entradas, mas não torna todas igualmente informativas. Não substituir desvio pequeno por um número escolhido depois dos resultados; apenas desvio exatamente zero recebe escala 1, registrado no dataset. Não há clipping ou remoção de observações extremas nesta referência.

Volume usa unidades BTC, conforme a coluna `volume` da Binance. `ln(1+V)` reduz a influência da cauda e aceita volume zero; não garante estacionariedade ou sinal preditivo. Trocar para volume em USDT, volume relativo a uma média ou OHLCV em nível é outro fator e outra versão. Adicionar informação pode aumentar ruído/sobreajuste: OHLCV é compromisso de escopo, não garantia de ganho.

O [código público do CryptoMamba](https://github.com/MShahabSepehri/CryptoMamba/blob/fef42727861a9c3a32241283ab981ef21a49e291/data_utils/data_transforms.py) usa preços em nível e divide volume por 1e9. Nas [configurações do modelo](https://github.com/MShahabSepehri/CryptoMamba/blob/fef42727861a9c3a32241283ab981ef21a49e291/configs/models/CryptoMamba/v1.yaml), a normalização opcional está desativada. Usa dados diários, contexto de 14 dias e previsão do próximo fechamento, diferentemente desta referência horária de retorno24. As variantes com/sem volume também alteram épocas/penalização; não isolam o efeito de volume. Não copiamos seus hiperparâmetros nem alegamos replicação. Os arquivos consultados e hashes estão na revisão técnica já existente, acessível pelo arquivo preliminar.

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

Referência implementada: conservar o núcleo Mamba oficial, duas camadas, largura 32, estado 16, convolução 4, expansão 2, dropout 0,1, pré-LayerNorm residual e normalização final. A projeção passa de 1 para 5 entradas. A pré-normalização é escolhida como referência tecnicamente motivada e já examinada, não como vencedora confirmada. Não transportar checkpoints anteriores para o novo estudo.

AdamW lr 0,0002, weight_decay 0,001 nos parâmetros não marcados; respeitar `_no_weight_decay` em A_log/D. Batch efetivo 64, microbatch 32, clipping 1, máximo100 épocas, paciência 10, MSE padronizado de treino, melhor MSE de validação na escala original. Seeds 17/42/2026, FP32 e ambiente qualificado. Esses números são referência reproduzível, não “padrão ótimo para cripto”. Recontar parâmetros; não copiar 20.129 do modelo de entrada escalar.

LSTM auxiliar com os mesmos cinco canais, datas, scalers, seeds e critérios, largura 32 e duas camadas como ponto de partida. Naive prevê log-retorno zero. ARIMA(p,1,q), p/q0..2, sem deriva, selecionado na validação; univariado e explicitamente diferente em informação disponível. Não denominar a comparação prova de superioridade arquitetural com informação/orçamento distintos.

Antes de treinar: testar indexação, causalidade por perturbação do futuro, uso efetivo dos cinco canais, unidades, purga, lacunas, população, transformações/inversão, máscaras de ablação, recarga e contabilidade financeira. Qualificar forward/backward/atualização e repetição CUDA no formato real. Não desativar auditorias para acelerar. Medir desempenho em benchmark próprio, mantendo mudanças de engenharia separadas das científicas.

## 7. Sequência limitada de experimentos

**Primeiro fechar R0, sem ablações simultâneas.** São três seeds Mamba OHLCV e três seeds LSTM OHLCV: **6 ajustes neurais principais**. Há uma referência Naive e nove candidatos ARIMA/uma seleção. Dois controles repetem os ajustes de seed42, um por rede: **8 ajustes neurais previstos ao todo**, além de falhas/interrupções preservadas. Os controles não entram como observações adicionais nas médias. Não existem resultados de mercado desta referência ainda.

Ordem: Mamba42, LSTM42, os dois controles; depois seeds17/2026 das duas redes, Naive e ARIMA. Pilotos reais completos integram a grade; não duplicá-los. Os controles precisam selecionar a mesma época, diferença absoluta máxima de previsões ≤1e−5 de log-retorno e diferença relativa de MSE de validação ≤1e−4. São os limites dos ciclos preliminares, não limites escolhidos por resultado financeiro. A recarga do mesmo checkpoint continua exigindo igualdade exata das previsões. Pequenas diferenças na repetição do treino CUDA são distintas de instabilidade entre seeds.

As futuras alterações serão uma por ciclo, com hipótese e referência antes de treinar. Ordem sugerida após examinar R0: (1) retirar volume, mantendo os demais canais e condições; (2) contraste com fechamento apenas; (3) representação de entradas/indicadores ou normalização; (4) otimizador/capacidade quando curvas de aprendizagem sustentarem essa hipótese. Não executar essa lista automaticamente. Uma ablação usa cinco canais, mascarando em zero após padronização os canais retirados, mesmas origens e treinamento do zero; capacidade exercida pode diferir apesar da mesma contagem de parâmetros.

Cada ciclo posterior registra o antecessor, o único fator alterado, expectativa, orçamento e regra de seleção. A transição dos estudos preliminares para R0 muda entradas, contexto/população e divisão: **não é ablação isolada de OHLCV**, nem pode atribuir eventual melhora só ao volume. R0 inaugura a referência comparável para as próximas mudanças.

Encerrar pelo orçamento, sem procurar indefinidamente até surgir lucro. Selecionar pela média do MSE de validação das três seeds e publicar também falhas e resultados negativos. Médias móveis não criam informação nova quando derivadas do mesmo passado; histórico adicional deve ser declarado. A avaliação walk-forward posterior leva apenas R0 e, no máximo, uma candidata escolhida; períodos já consultados continuam retrospectivos.

## 8. Como medir previsão

- Primária: MSE de log-retorno, fora do treino, com diferença pareada contra Naive e LSTM nesta referência; futuras candidatas também contra R0 e habilidade `1 − MSE_modelo/MSE_naive` na mesma população.
- Secundárias: RMSE e MAE para interpretação de magnitude, viés médio, direção derivada do sinal e acerto balanceado, sempre com regra explícita para zero. Não usar MAPE de retornos próximos de zero.
- Mostrar cada seed e sua média; não selecionar a melhor nem formar ensemble silenciosamente.
- Mostrar resultado agregado e por trimestre do teste; não remover trechos difíceis. Diagnóstico por faixas de volatilidade fica para análise posterior identificada, com limites derivados do treino, sem seleção de configuração por esse resultado.
- Incerteza pareada com blocos temporais, preservando dependência das previsões horárias de 24h; referência 14 dias/2.000 réplicas e sensibilidades 7/28. Documentar limites e multiplicidade; um IC que inclui zero é inconclusivo, não prova de igualdade.

“Deu certo como previsão” exige magnitude de redução de erro relevante, estabilidade e evidência temporal, não apenas a melhor média entre muitas tentativas. Não haverá limiar inventado depois dos resultados. A primeira rodada é exploratória; seu desempenho não demonstra um teto absoluto de previsibilidade.

## 9. Como medir utilidade operacional

Propor uma política Spot comprado/caixa, sem alavancagem, para avaliar o sinal com baixo número de decisões livres. Não confundir com futuros. Os dados atuais permitem essa análise; futuros exigiriam fonte e regras próprias, funding, margem e liquidação.

1. Às 00:00UTC usar apenas candles já completos. Decisão diária, embora existam previsões horárias.
2. Entrar às 00:01 no open do minuto disponível se a previsão superar o limiar de custos. Uma posição por vez, saída 24h após a entrada; saída anterior à nova entrada na fronteira diária. Capital ilustrativo 10.000USDT, posição 100% comprado ou caixa, sem reiniciar capital a cada operação.
3. Custos base assumidos por lado: taxa 0,001 e slippage 0,0005. Limiar de log-retorno `ln((1+s)*(1+f)/((1-s)*(1-f)))`. Quantidade `capital/[open_entrada*(1+s)*(1+f)]`; valor de saída `quantidade*open_saida*(1-s)*(1-f)`. Essas são hipóteses de simulação, não taxas verificadas da conta do pesquisador. O horizonte executado tem defasagem de 1min em relação ao alvo terminal; publicar essa diferença.
4. Cenário agravado: taxa 0,002 e slippage 0,001, preservando os sinais base para isolar custos. Não procurar o limiar/horário que melhor ficou no teste.
5. Referências econômicas: caixa; comprar e manter com custos de entrada/saída nas fronteiras predefinidas; compra diária sistemática com o mesmo calendário de entrada/saída da política. O Naive de retornozero fica em caixa nesta regra, não equivale a comprar e manter.
6. Publicar retorno líquido/grosso, custos, drawdown marcado pelo fechamento de cada minuto (não o pior preço intraminuto), exposição, número de entradas e distribuição de ganhos/perdas, por seed e período. Sem operações: retorno zero e métricas condicionais não aplicáveis, nunca “100% de acerto”. Preços ausentes geram indisponibilidade auditável, não remoção vantajosa.

O limiar usa uma previsão pontual do log-retorno; não garante esperança de lucro positiva após custos. O open do minuto é uma aproximação de execução, sem livro de ofertas. Sem stop/take-profit, não há promessa de controle intraposição. Um experimento de stops/futuros seria outra política e novo ciclo; não adaptar essa política depois para salvar o resultado.

| Resultado observado | Conclusão permitida |
|---|---|
| MSE menor e resultado líquido pior | Previsão melhor naquela métrica; política operacional pior |
| Lucro, mas abaixo de comprar e manter, com exposição diferente | Lucro histórico; vantagem do modelo ainda não demonstrada |
| Resultado favorável em uma seed, negativo nas demais | Instabilidade; não selecionar a seed vencedora |
| Melhoria líquida consistente após custos, referência e análise temporal | Evidência para essa política e amostra, ainda sem garantia futura |

MSE e simulação são eixos separados; não criar um escore composto ajustável para declarar vitória. Na seleção inicial, MSE de validação é o critério fixo; lucro de teste não seleciona a configuração. Se a seleção econômica se tornar objetivo principal, registrar uma política de seleção própria antes da nova rodada.

## 10. Implementação, execução e rastreabilidade

O ponto de entrada separado é `run_ohlcv.py`; não usar os executores encerrados. No WSL e ambiente qualificado, a sequência explícita é `preparar`, `qualificar`, `congelar`, `executar`. Os três primeiros não treinam nos dados de mercado. Qualificação faz testes sintéticos, incluindo treino curto, gradientes, atualização, influência dos cinco canais, recarga, repetição, ARIMA e publicação. Resultados/contagens de mercado só existem depois de `executar` terminar e conferir a cobertura.

- `registros/ohlcv/dataset.json`: ponteiro da preparação, distinta do dataset anterior. Dados horários/minutos auditados são reutilizados; não há nova coleta automática.
- `registros/ohlcv/qualificacao.json`: aponta recibo com fontes, versões, hardware, testes e limites; qualquer alteração nas fontes/configuração exige qualificação nova. Ensaios falhos permanecem guardados.
- `registros/ohlcv/execucao.json`: identidade do congelamento; pasta própria em `dados/experimentos/ohlcv24_<id>/`, com cópias de fontes, configuração, protocolo e hashes dos dados. Ter esse ponteiro não significa que o treino começou.
- `celulas/<modelo_seed>/tentativa_NNN/`: início, épocas, grupos do otimizador, melhor checkpoint, previsões por origem, métricas, recarga e manifesto. Controles identificados separadamente. ARIMA conserva todos os candidatos e a seleção.
- `publicacoes/tentativa_NNN/`: conferência independente das métricas sobre as previsões salvas, médias de perdas entre seeds (não ensemble), intervalos temporais pareados e simulação base/agravada/bruta, com referências econômicas. Publicação interrompida não é sobrescrita.
- `progresso.json` e `processo.json`: estado local e processo; lock impede concorrência. O executor recusa ciclo concluído. Retomada requer processo encerrado, integridade e `--retomar` explícito após investigação; uma tentativa interrompida é preservada e o ajuste recomeça com a mesma seed, não continua de checkpoint parcial.

Scalers e matrizes têm manifesto próprio. Os resultados só são declarados concluídos depois das verificações; inferência e recarga de rede não são novos ajustes. O ambiente congela versões de Python, PyTorch, Mamba, causal-conv1d, NumPy, pandas, statsmodels e PyArrow, além de GPU/host. Não há fallback CPU para Mamba nem compra de computação.

A incerteza publicada usa blocos de dias corridos; considera dependência temporal das perdas e é condicional aos modelos ajustados. Não transforma três seeds ou janelas sobrepostas em observações independentes nem corrige toda a seleção adaptativa de experimentos. A simulação é uma hipótese operacional Spot, não prova de execução real ou de lucro futuro.

A seção 3 do TCC ainda precisa ser escrita e a delimitação BTC/24h alinhada ao orientador. O PDF original permanece intacto. O portal atual é do estudo preliminar; integração dos resultados OHLCV ocorre somente quando existirem. Fontes e artefatos antigos não foram editados para aceitar o novo desenho.

## Referências metodológicas

- [CryptoMamba](https://arxiv.org/html/2501.01010v2): referência de estudo com OHLCV diário; não prova a superioridade da nossa formulação nem equivale a reproduzi-lo.
- [Cawley e Talbot](https://www.jmlr.org/papers/v11/cawley10a.html): seleção de configurações também pode sobreajustar o conjunto usado para escolhê-las.
- [Forecasting: Principles and Practice](https://otexts.com/fpp3/toolbox.html#time-series-cross-validation): avaliação temporal com origens móveis e separação cronológica.

## Revisões deste documento

- 28/10/2026: desenho inicial após leitura do TCC1 e revisão dos estudos preliminares. OHLCV adotado como direção pelo pesquisador; detalhes propostos, sem execução. Atualizações posteriores devem registrar aqui o motivo e a situação, evitando documentos concorrentes.

- 28/10/2026, refinamento após pedido de limpeza e preparação: R0 reduzida a 6 ajustes principais e 2 controles; representação justificada sem alegação de ótima; implementação multivariada separada e verificações executáveis. Treinos de mercado ainda não iniciados. Evidências atuais nos ponteiros `registros/ohlcv/` e na cronologia.
