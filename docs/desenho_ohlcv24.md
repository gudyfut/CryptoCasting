# Desenho do estudo OHLCV em 24 horas

Atualizado em29/10/2026. **A referência modular R0 ab5baf3eab3a2e66d8b2 foi concluída e conferida.** A preparação anterior92e3eb82e3f6adf99994 continua preservada. O andamento e os estados distinguem a preparação histórica da execução modular. O pesquisador solicitou fechar as escolhas, limpar o repositório e verificar o fluxo antes dos treinamentos. A preparação histórica usa `estudo_ohlcv/`; a cadeia executada é modular (`modelos/`, `treinamento/`, `avaliacao/`) e as extensões têm executores próprios. A referência de trabalho posterior é identificada na seção11. A cópia deste documento no congelamento identifica o método daquela execução; esta página continua sendo o documento único de trabalho. Não há aprovação acadêmica presumida nem autorização de busca indefinida.

Este é o documento único de trabalho para refinar o desenho. Atualizar suas seções, em vez de criar um relatório para cada conversa. Decisão de transição: [ADR 0006](adr/0006-reorganizacao-e-desenho-ohlcv.md). Estudos já executados: [arquivo preliminar](../arquivo/estudos_preliminares_2026-10-28/README.md).

**Prioridade posterior, ainda em 28/10:** o pesquisador pediu revisar a modularização antes de treinar. A [arquitetura de dados](arquitetura_dados.md) separa mercado e preparação de entradas, preservando as escolhas científicas descritas aqui. A identidade preparada `92e3eb82e3f6adf99994`, inclusive sua cópia de protocolo, continua intacta. O novo caminho de dados ainda não foi ligado ao executor congelado; essa integração pertence à próxima revisão, com nova identidade e qualificação. Conferir [estado dos dados](../registros/dados/estado.json).

## 1. Correspondência com o TCC escrito

Atualização técnica de29/10: o consumo das entradas foi separado em `modelos/`, conforme a [arquitetura](arquitetura_modelos.md). Dimensões derivadas do contrato, alvo separado da previsão e unidades de saída explícitas; arquiteturas/hiperparâmetros e regras dos baselines preservados. Esta revisão realizou somente verificações de dados e inferência sem ajustes. O executor de treinamento ainda precisa ser integrado e qualificado sob nova identidade.

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

Levar a referência OHLCV e no máximo uma candidata selecionada, além das referências necessárias. Atualização autorizada em03/11 (ADR0019): quatro blocos × oito seeds =32ajustes principais por versão Mamba,64nos dois lados, mais2controles reais. Ver [protocolo próprio](protocolo_huber_blocos.md). Não repetir toda a busca em cada bloco. Se escolher uma configuração após consultar2024, avaliá-la em blocos de 2024 é uma verificação **retrospectiva com seleção informada pelo período**: a ordem causal dentro de cada treinamento não elimina esse viés. Relatar sempre essa limitação. Só chamar de confirmação independente uma avaliação que cumpra os requisitos de independência.

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

A cadeia modular de29/10 usa `run_treinamento.py`, conforme [arquitetura de treinamento](arquitetura_treinamento.md). `estudo_ohlcv/`, `run_ohlcv.py` e identidade92e3eb82e3f6adf99994 permanecem preservados como preparação anterior. A migração mantém todas as decisões científicas desta R0, mas exige nova identidade e qualificação; não altera recibos antigos.

No WSL/CUDA qualificado, `qualificar` faz ensaios exclusivamente sintéticos e verifica os dados reais sem treiná-los; `preparar --qualificacao <recibo>` congela a nova execução; `conferir` verifica sua integridade. Somente `executar --autorizacao <recibo>` depois do “Ok” explícito inicia mercado. O recibo vincula o consentimento à identidade e ao orçamento, sem autorizar ciclos futuros.

- `registros/dados/estado.json` e `registros/modelos/estado.json`: evidências das camadas revisadas; dados publicados são reutilizados, sem coleta automática.
- `registros/treinamento/qualificacoes/`: fontes, ambiente, ensaios, falhas, recarga e repetição. Atualização de fonte/configuração exige nova qualificação.
- `registros/treinamento/execucao.json`: ponteiro do congelamento em `dados/experimentos/ohlcv_modular_<id>/`, com fontes, protocolo e hashes de dependências. Estado inicial `aguardando_ok`, sem treino.
- `celulas/<modelo_seed>/tentativa_NNN/`: início, épocas, grupos de AdamW, checkpoints por melhora, seleção, previsões, métricas, recarga e conclusão com hashes. ARIMA conserva os nove candidatos, incluindo falhas, e a escolha. Controles têm chaves próprias.
- `publicacoes/tentativa_NNN/`: conferência independente, médias de perdas e dispersão entre seeds, contrastes temporais, diagnósticos trimestrais e simulação Spot base/agravada/bruta com referências. Publicação interrompida é preservada.
- `progresso.json` e `processo.json`: estado, host, boot, PID e início do processo. Lock exclusivo bloqueia concorrência. Retomada exige investigação e `--retomar`; preserva a tentativa interrompida e reinicia só o ajuste incompleto com a mesma seed. Não retoma otimizador de checkpoint parcial. Uma reprovação de controle bloqueia repetições favoráveis.

O cache das janelas de treino em GPU usa os mesmos valores do consumidor. Teste/operacional não entram no gradiente nem na seleção de época ou de ordem ARIMA. Cada checkpoint escolhido é recarregado antes de testar; uma segunda instância deve reproduzir exatamente suas previsões. Na execução sintética integral também se verifica a publicação e a retomada sem alteração dos ajustes já concluídos.

Scalers e matrizes têm manifesto próprio. Os resultados só são declarados concluídos depois das verificações; inferência e recarga de rede não são novos ajustes. O ambiente congela versões de Python, PyTorch, Mamba, causal-conv1d, NumPy, pandas, statsmodels e PyArrow, além de GPU/host. Não há fallback CPU para Mamba nem compra de computação.

A incerteza publicada usa blocos de dias corridos; considera dependência temporal das perdas e é condicional aos modelos ajustados. Não transforma três seeds ou janelas sobrepostas em observações independentes nem corrige toda a seleção adaptativa de experimentos. A simulação é uma hipótese operacional Spot, não prova de execução real ou de lucro futuro.

A seção 3 do TCC ainda precisa ser escrita e a delimitação BTC/24h alinhada ao orientador. O PDF original permanece intacto. O portal atual é do estudo preliminar; integração dos resultados OHLCV ocorre somente quando existirem. Fontes e artefatos antigos não foram editados para aceitar o novo desenho.

## 11. Referência adotada e próxima hipótese proposta

### Investigação de capacidade encerrada

Em29/10/2026, o pesquisador adotou16estados para as próximas hipóteses (ADR0012). O [bloco fechado de estados8/16/32/64](../registros/investigacoes/estados_internos_001/fechamento.json) agrega índices, não move resultados. O [relatório](resultados_estados32_64.md) mantém as médias comparáveis em três/seis seeds. A [referência de trabalho](../registros/referencias/mamba16_ohlcv24_001.json) identifica as seis tentativas16, contratos e hashes; é uma seleção de resultados existentes, não nova execução nem ensemble. R0 e as extensões ficam preservadas.

Esta atualização sucede as descrições históricas de preparação/migração acima: R0 e a investigação de estados já foram executadas e conferidas. Para próximos contrastes usar seis seeds17/42/2026/7/123/31415. A referência tem taxa0,0002; não substituí-la silenciosamente pelo valor candidato. Estado16 é uma escolha de continuidade e menor erro médio observado, não ótimo universal ou vencedor operacional.2024/2025 já conhecidos permanecem retrospectivos.

### Contraste de taxa ampliado e autorizado nos quatro estados

A proposta inicial era0,0002→0,0001 em16/seis seeds. O pesquisador autorizou posteriormente a mesma redução **também em8/32/64**, conforme [ADR0013](adr/0013-taxa-aprendizado-quatro-estados.md). A delimitação vigente está no [protocolo da taxa](protocolo_taxa_aprendizado.md), com **24ajustes novos** e29referências herdadas, sem repetir as referências. O estado16 escolhido continua referência de trabalho; a nova grade investiga se o efeito da taxa depende do estado, sem promoção automática por ranking de teste.

| Fator | Referências existentes | Grade autorizada |
|---|---|---|
| Taxa constante AdamW | 0,0002 | 0,0001 |
| Estados e seeds | 8/16/32/64, seis seeds cada | Mesmos estados/seis seeds, do zero |
| Dados/entradas/contexto/alvo | BTC/1h, cinco canais,168h→24h | Iguais |
| Datas,origens,purga e scalers | Treino2021–23/val2024/teste2025 | Iguais |
| Largura/camadas/d_conv/expand/dropout | 32/2/4/2/0,1 | Iguais dentro de cada estado |
| Penalização/lote/clipping/épocas/paciência | 0,001 com isenções /64(32)/1/100/10 | Iguais |
| Simulação Spot | R0 preservada | Igual; sem unir mudança operacional |
| Orçamento | Nenhum ajuste repetido | 24novos; sem baselines/repetição real extra |

Todas as quatro receitas são congeladas antes do primeiro ajuste, ordem8→16→32→64 e seeds42/17/2026/7/123/31415 por estado. Qualificação sintética de todas as arquiteturas e recarga exata antes de mercado. Identidade,progresso,autorização e pós-conferência em [registros próprios](../registros/taxa_aprendizado/estado.json). A preparação nunca autoriza por si só treino; esta grade tem a autorização explícita citada na ADR0013, vinculada depois à identidade concreta.

Motivação e limitações permanecem: curvas16 selecionam épocas9–13 e depois o erro online cai enquanto a validação piora. Isso não prova taxa alta ou garante ganho. Treino online padronizado e validação em retorno real usam escalas/modos distintos. AdamW aplica decay dependente da taxa por passo; a hipótese mede o efeito total de trocar a taxa sob receita fixa, não um mecanismo isolado. Não ampliar100épocas automaticamente se a candidata aprender mais devagar.

Critério primário: quatro diferenças pareadas de MSE médio de validação (nova taxa menos antiga), mesmas seis seeds, bootstrap circular em dias7/14/28,principal14,2.000réplicas. IC95% descritivo e IC98,75% por Bonferroni para os quatro efeitos; comparação favorável requer média menor e IC98,75%14dias inteiramente negativo. Inconclusivo mantém referência. Esse ajuste não corrige toda seleção histórica ou de checkpoints. Teste2025/Spot e diagnóstico00UTC são secundários retrospectivos; não escolhem taxa,seed,época. RMSE médio por seed, não ensemble.

**Fechamento em29/10/2026:**24ajustes concluídos e conferidos. A média de validação piorou nos quatro estados e nenhum efeito satisfez o critério primário; referências anteriores mantidas. [Resultados e interpretação](resultados_taxa_aprendizado.md). A referência de trabalho permanece16/lr0,0002, sem inferir ótimo universal ou lucro a partir da menor dispersão/menor prejuízo.

As alterações de política Spot,normalização,indicadores ou AdamW→Adam ficam para hipóteses separadas. Nenhum ciclo posterior é iniciado automaticamente. O [relatório anterior](resultados_estados32_64.md) e todos os pesos/fontes/publicações encerrados são preservados.

## Referências metodológicas

- [CryptoMamba](https://arxiv.org/html/2501.01010v2): referência de estudo com OHLCV diário; não prova a superioridade da nossa formulação nem equivale a reproduzi-lo.
- [Cawley e Talbot](https://www.jmlr.org/papers/v11/cawley10a.html): seleção de configurações também pode sobreajustar o conjunto usado para escolhê-las.
- [Forecasting: Principles and Practice](https://otexts.com/fpp3/toolbox.html#time-series-cross-validation): avaliação temporal com origens móveis e separação cronológica.

## Revisões deste documento

- 28/10/2026: desenho inicial após leitura do TCC1 e revisão dos estudos preliminares. OHLCV adotado como direção pelo pesquisador; detalhes propostos, sem execução. Atualizações posteriores devem registrar aqui o motivo e a situação, evitando documentos concorrentes.

- 28/10/2026, refinamento após pedido de limpeza e preparação: R0 reduzida a 6 ajustes principais e 2 controles; representação justificada sem alegação de ótima; implementação multivariada separada e verificações executáveis. Treinos de mercado ainda não iniciados. Evidências atuais nos ponteiros `registros/ohlcv/` e na cronologia.

- 29/10/2026: integração modular (ADR0009), sem mudança científica de R0. Nova identidade/qualificação, checkpoints por melhora, autorização explícita e proteção de retomada. Preparação antiga preservada; sem treinamento de mercado nesta revisão.

## Revisão de representação e execução em29/10/2026

A [auditoria posterior](../registros/treinamento/auditoria_representacao_atual.json) refez independentemente fórmulas, matrizfloat32, scalers e alvos. A matriz é idêntica; scalers de treino foram reproduzidos exatamente. Geometria H/O,L/O,C/O é preservada (erro numérico máximo2,22×10⁻¹⁶). Oito candles horários nativos da Binance em quatro datas coincidiram com a agregação dos minutos. A auditoria é amostral em relação à API horária e não elimina outras limitações de mercado.

A abertura relativa tem extremos de aproximadamente−50/+26 desvios no treino; seu desvio cai para0,062/0,077 unidades padronizadas em validação/teste. O volume transformado desloca sua média de0 no treino para−0,89/−1,43 na validação/teste. Isso evidencia mudança de distribuição; pode dificultar aprendizado, mas não demonstra erro na transformação nem prova efeito causal sobre desempenho. Não reajustar scaler pelo teste, remover extremos ou alterar os canais dentro da execução encerrada.

A taxa base0,10% por lado coincide com a tabela pública atual de usuário comum Spot; desconto BNB aplicável0,075%. Slippage0,05% por lado é cenário assumido. A fórmula de compra original reserva taxa no caixa (`B/[P*(1+s)*(1+f)]`); o caso sem BNB com taxa no BTC recebido usa `B/[P*(1+s)]*(1−f)`. A auditoria com os mesmos sinais mostra diferença pequena na rentabilidade e todas as redes que operaram continuam negativas mesmo com taxa0,075% e slippagezero. Esse último cenário é custo equivalente, não carteira BNB nem execução garantida. Livro, fills, lotes, filtros históricos e taxas particulares não foram certificados; o snapshot atual da exchange não é dado2025.

A extensão [estado interno16→8](protocolo_estado_mamba.md) mantém as entradas e política R0 para isolar uma mudança de capacidade. O pesquisador escolheu seis ajustes novos da candidata, com comparação pareada restrita às três seeds já disponíveis de R0. Não somar uma repetição real adicional ao orçamento. Controle sintético e recarga exata são documentados, com ausência de controle completo de mercado explicitada.

- 29/10/2026: investigação de estados encerrada;16adotado como referência em seis seeds pela ADR0012. Próximo contraste0,0002→0,0001 apenas proposto na seção11, sem treino; versões anteriores e evidências preservadas.

- 29/10/2026: pesquisador ampliou e autorizou taxa0,0001 em8/16/32/64, seis seeds por estado (ADR0013).24ajustes novos; proposta anterior16/seis preservada em snapshot e ADR0012.

## CryptoMamba adaptado: comparação de abordagem

Após o fechamento da taxa, o pesquisador autorizou uma candidata CryptoMamba adaptada, seis seeds (ADR0014). O [protocolo próprio](protocolo_cryptomamba_adaptado.md) fixa fontes públicas, diferenças, núcleo12blocos/estado64, projeção168→14,Adam/RMSE e orçamento100épocas; dados/alvo/divisão/Spot permanecem. Não é ablação de um fator nem reprodução dos números do artigo. Comparação primária contra16/lr0,0002 por validação; teste/Spot retrospectivos e métricas de preço para todas as séries. O [estado verificável](../registros/cryptomamba/estado.json) separa preparação de execução e auditoria; não promover automaticamente.


## Ablação posterior do otimizador da adaptação

Em30/10/2026 o pesquisador autorizou escolher a próxima hipótese delimitada e prosseguir. A ADR0016 fixa **Adam→AdamW somente no CryptoMamba adaptado**, seis seeds pareadas com a versão Adam preservada; taxa0,01,estado64,arquitetura,entradas,perda,scheduler e população permanecem iguais. O Mamba16 já usa AdamW e segue como referência auxiliar, sem retreinamento. [Protocolo](protocolo_otimizador_cryptomamba.md) e [estado](../registros/otimizador/estado.json). Comparação primária por validação, teste e54carteiras Smart secundários retrospectivos; não buscar lucro até acertar. A preparação/qualificação não comprova ajuste de mercado; conferir identidade, processo e progresso.


## Retorno ao Mamba16: taxa dinâmica

A linha CryptoMamba/otimizador foi encerrada e preservada. Em30/10/2026 o pesquisador autorizou seguir a recomendação com organização e execução. A ADR0017 delimita seis Mamba16, mantendo a referência0,0002 e todos os fatores, com apenas ReduceLROnPlateau como política nova. [Protocolo](protocolo_taxa_dinamica.md), [estado](../registros/taxa_dinamica/estado.json). Métricas adicionais descrevem informação/erros/estabilidade sem mudar o primário por MSE de validação. [Diagnóstico anterior](diagnostico_previsoes.md). Novos códigos ficam em `experimentos/` e `analises/`, preservando caminhos congelados.

## Ablação da perda supervisionada: Huber

Autorização posterior em 02/11/2026 (ADR0018): seis ajustes com2×Huber(delta1 no alvo padronizado), mantendo referência16/AdamW/taxa constante0,0002 e demais fatores. A seleção de checkpoint, parada e comparação principal continuam pelo MSE global de validação em retorno real. A rodada de taxa dinâmica foi encerrada e preservada, sem promoção. [Protocolo próprio](protocolo_perda_huber.md), [estado verificável](../registros/perda_huber/estado.json). A perda Huber não precisa estimar a média condicional; melhorar métricas secundárias não redefine sucesso no MSE. Qualificação/identidade precedem mercado; nenhuma grade de delta ou hipótese adicional é automática.

## Complemento fatorial de entrada e perda

A ADR0021 completa OHLCV cru×Huber:três combinações já existentes são herdadas e somente a quarta é treinada,em quatro blocos/oito seeds. [Protocolo](protocolo_crua_huber.md). Não altera o alvo24h ou o sentido histórico das rodadas anteriores. Avalia interação,sem presumir que melhorias individuais se somam;32principais novos+1controle e96herdados,com exposição retrospectiva conhecida.
