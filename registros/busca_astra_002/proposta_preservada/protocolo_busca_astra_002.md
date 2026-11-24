# Busca Astra 002 — proposta de pesquisa, ainda sem execução

Situação em 04/11/2026: **planejamento solicitado; treinamentos, consultas ao Astra e execução deste ciclo ainda não autorizados/iniciados**. Este documento é a proposta canônica, não um protocolo já congelado. Configuração legível por máquina: `configuracoes/busca_astra_002_proposta.json`. Não existe identidade de execução nova. A busca001, a comparação Astra/crua e a revisão operacional F03 permanecem encerradas e imutáveis.

## 1. Pergunta e diagnóstico

Pergunta: uma busca local, orientada por diagnósticos e com separação entre parada e seleção, encontra uma receita Mamba com erro menor que referências fortes, estabilidade temporal e evidência operacional sob políticas previamente fixadas?

Não há método que garanta modelo perfeito, ótimo global ou lucro. A investigação é compatível com o desenvolvimento iterativo, entradas OHLCV/indicadores e avaliação walk-forward do TCC1. O recorte continua BTC/1h/retorno24h, sem pretensão sobre quatro moedas ou todas as arquiteturas. Não avaliar superioridade do agente Astra sobre outros métodos de busca sem um experimento próprio com orçamento comparável.

Achados da leitura do código e dos artefatos:

- Na busca001, o mesmo trecho de validação escolhia a época e pontuava a receita. Isso não é vazamento automático do teste final, mas acumula seleção sobre uma mesma amostra.
- A triagem usava uma seed e dois recortes; receitas descartadas podiam estar em desvantagem por acaso de inicialização.
- O espaço permitia mudar muitos fatores juntos. A contração de saída podia aproximar o modelo do Naive sem acrescentar informação. Essa regularização pode ser legítima, mas não prova discriminação temporal.
- C05 melhorou a antiga referência, mas não superou claramente o Naive. A comparação posterior com crua+Huber também foi inconclusiva em precisão. São ambas referências obrigatórias nesta proposta.
- F03 mostrou grande sensibilidade da operação à política, ao lado vendido e aos custos. Escolher pelo maior backtest seria outro problema de seleção; as políticas não podem ser editadas pelo proponente.
- Os 106 ajustes da busca001 consumiram aproximadamente3,70h dentro da rotina de treino, excluindo chamadas Astra, preparação, transferência, verificação e publicação. As durações não comprovam quanto demorará a busca002. Evidência em `registros/busca_astra_002/base_planejamento.json`.

## 2. Dados e separação temporal

Reutilizar candles auditados BTCUSDT Spot1h, dataset `93509a1b06b19103ac1c`, e manter saída `ln(C[t+24]/C[t])`. Treinar com origens horárias. Calcular métricas horárias e, separadamente, nas origens00:00UTC usadas pela operação. Não mudar a frequência de treinamento nesta busca.

Cada ajuste de desenvolvimento contém **treino T → parada V → comparação S**. Pesos e scalers aprendem somente em T; V escolhe a época por MSE real e comanda a parada; S é calculado somente após escolher/recarregar o checkpoint. Astra recebe resultados de S para propor receitas, portanto S é desenvolvimento adaptativo, nunca teste intocado.

| Recorte | Treino T | Parada V | Comparação de receitas S |
|---|---|---|---|
| S1 | 2021-01-01 a 2023-01-01 | 2023-01-01 a 2023-04-01 | 2023-04-01 a 2023-07-01 |
| S2 | 2021-01-01 a 2023-04-01 | 2023-04-01 a 2023-07-01 | 2023-07-01 a 2023-10-01 |
| S3 | 2021-01-01 a 2023-07-01 | 2023-07-01 a 2023-10-01 | 2023-10-01 a 2024-01-01 |

Limites direitos exclusivos. Em cada parte, o destino do alvo deve ser estritamente anterior ao limite direito: purga24h. Contexto pode conter passado anterior ao começo da parte, nunca futuro. Mesmo conjunto de origens para todas as receitas, aquecimento composto336h e exclusão comum de janelas com lacunas, sem interpolação. Indicadores podem ampliar a história efetiva além do comprimento da sequência; registrar alcance efetivo, não chamar esse contraste de simples aumento do número de canais.

Final B1–B4 mantém o calendário já usado: treino desde2021 até2023-10/2024-04/2024-10/2025-04; validações trimestrais seguintes; avaliações nos quatro semestres2024–2025. Reestimar cada modelo por bloco usando apenas passado permitido. Nunca aplicar um checkpoint treinado no futuro a um bloco anterior.

**2023 e 2024–2025 já foram consultados neste projeto.** A separação agora limita adaptação adicional, mas não torna os dados inéditos. Agente recebe apenas T/V/S; final2024–2025 fica inacessível até congelar uma única candidata. Nenhum retorno à busca após abri-lo.2026 também não será declarado intocado sem auditoria de exposição. Confirmação independente exigirá avaliação prospectiva ou conjunto comprovadamente não consultado, fora deste orçamento.

## 3. Referências e espaço de procura

Âncoras: A0=C05 da busca001 (janela relativa, contexto72, Huber) e R0=OHLCV cru+Huber/contexto168 da comparação posterior. Nas duas: Mamba-1 oficial CUDA, estado16, largura32, duas camadas, dropout0,1, poolingúltimo, AdamW0,0002, decay0,001 com isenções oficiais, scheduler constante e ganho de saída1. Novos recortes T/V/S exigem novos ajustes de ambas.

Controles baratos: retorno zero; constante média do alvo de T; constante mediana de T; direção majoritária de T somente para interpretar acurácia. Não aprender constantes em V/S/teste. Zero não possui direção operacional; não atribuir 50% de acerto a uma previsão que se abstém. A média favorece MSE e a mediana favorece MAE: documentar as funções diferentes.

Manter Huber2×delta1 no alvo padronizado, estado16, duas camadas, AdamW, decay0,001, d_conv4, expand2, batch64/micro32, clipping1, máximo100épocas e paciência10. Checkpoint pelo menor MSE real de V; primeiro empate. Nenhum mínimo artificial de épocas para impedir a seleção de um checkpoint inicial. Registrar aprendizado, gradientes/clipping, variância das previsões e época selecionada para diagnosticar problemas; não declarar subtreino apenas porque a época escolhida é baixa.

Espaço limitado:

| Fator permitido | Valores |
|---|---|
| Representação dos cinco canais OHLCV | janela relativa / relativa ao fechamento anterior / logníveis; crua permanece âncora fixa |
| Contexto sequencial | 24 / 72 / 168 horas |
| Momentum adicional | desligado / logretornos passados24 e168 |
| Volatilidade adicional | desligada / desvio dos retornos horários passados24 e168,ddof0 |
| Volume relativo adicional | desligado / ln1p(volume) menos média móvel168 de ln1p(volume) |
| Pooling | último / média temporal |
| Largura | 32 / 64 |
| Dropout | 0 / 0,1 / 0,2 |
| Taxa constante | 0,0001 / 0,0002 / 0,0005 |

Os indicadores são transformações dos dados disponíveis, não garantias de informação adicional ou de melhora. Escalas dos canais adicionais somente em T. Sem novas fontes externas, moedas, candles, alvo, estados, otimizadores ou parâmetros de trading. Não editar pesos diretamente, nem contrair a cabeça nesta rodada; os pesos são aprendidos pelo otimizador.

Máximo12receitas novas, cada uma com um pai conhecido e **um fator alterado**. Identificadores N01–N12, distintos de C05 histórica. Quatro primeiras ablações predefinidas de A0: momentum; volatilidade; volume relativo; poolingmédia. Até seis propostas locais do Astra em seguida. Reservar até duas vagas finais para remover fatores de uma combinação promissora e verificar sua contribuição. Se remoção duplicar receita conhecida ou não existir combinação, usar uma alteração local ainda não testada do mesmo espaço, com justificativa, ou encerrar sem preencher vagas. Todas contam no mesmo teto. Comparar pais/filhos somente nas seeds e recortes comuns; a receita final pode acumular fatores, sem atribuir o contraste completo a um único fator.

## 4. Métricas e seleção predefinidas

Não criar uma média arbitrária de lucro, correlação, MSE e acurácia. Métricas respondem perguntas diferentes; o primário continua sendo previsão pontual do retorno24h.

**Primário:** para cada recorte/seed, `q=MSE_modelo/MSE_Naive`; score Q é a média igualmente ponderada dos q. Apresentar também `skill=100×(1−Q)`: positivo supera retorno zero, negativo perde, zero empata. Não confundir com R² contra a média observada de teste. RMSE ajuda a ler unidades, mas não acrescenta um voto independente a MSE.

| Eixo | Medidas | Interpretação e cautela |
|---|---|---|
| Tamanho do erro | MSE/skill, MAE, RMSE, P95 do erro absoluto | MAE mede erro típico; P95 mostra erros grandes; MAE/Naive é razão, não MASE padrão |
| Informação temporal | Pearson e Spearman entre previsão/retorno | Pearson mede associação linear; Spearman mede ordenação temporal, não IC transversal de carteira; constante gera NA, não correlação inventada |
| Direção | balanced accuracy, recall de alta/queda, precisão dos sinais positivos/negativos e cobertura | Distinguir prever sempre alta de discriminar ambos os lados; zeros contam como abstinência e não acerto nos recalls |
| Calibração e colapso | viés, média/desvio, sd(previsão)/sd(alvo), cinco grupos ordenados de previsão | Variância pequena pode ser apropriada; não inflar saídas artificialmente. Grupos são diagnóstico, não faixas escolhidas para negociar |
| Estabilidade | cada recorte, seed, pior recorte e diferenças pareadas | Uma média não pode ocultar colapso temporal; seeds não são amostras independentes do mercado |
| Operação final | retorno líquido, drawdown, giro, exposição, custos/funding e contribuição comprada/vendida | Mesmas regras e mercados; comparar caixa/comprar-manter; não selecionar pelo maior lucro |

Treino continua horário; painel00:00UTC serve para verificar o alinhamento com a decisão operacional diária. Janelas24h horárias se sobrepõem; inferência não trata cada linha como independente. Não usar MAPE em retornos próximos de zero, acerto do nível de preço como substituto de retorno ou log-loss/Brier numa saída que não é probabilidade. Previsão probabilística/quantílica requer outro alvo/contrato e outro ciclo.

Triagem: duas seeds42/17 em cada S1–S3; classificar por Q somente após seis ajustes completos. Até três menores scores recebem seed2026 nos três recortes; ambas as âncoras também recebem essa terceira seed. Não eliminar por apenas uma seed ou por lucro. Falha/incompletude não recebe uma média baseada apenas nos ajustes favoráveis.

Definir R como a âncora com menor Q nas mesmas três seeds e recortes; desempate pelo ID. Uma candidata só pode avançar se:

1. seus nove ajustes estão completos/auditados e `Q_c ≤ 0,999 × min(1,Q_A0,Q_R0,Q_media_constante)`;
2. MSE médio é menor que R em ao menos dois dos três recortes e em ao menos seis dos nove pares;
3. em nenhum recorte o MSE médio excede1,05vezes R;
4. a média de MAE/MAE_Naive não excede1,01vezes R.

Denominadores precisam ser positivos; degeneração dos dados interrompe a qualificação. Mediana constante é diagnóstico de MAE, não entra em Q. Limiares0,1%/5%/1% são convenções práticas propostas antes da execução, **não valores ótimos demonstrados nem testes de significância**. Não relaxá-los se nenhuma candidata passar. Entre elegíveis: menor Q, menor pior razão por recorte, menos parâmetros, ID. Se ninguém passar, encerrar com resultado negativo, sem forçar uma finalista. Correlação/direção/atividade qualificam a interpretação, não criam outro campeão escolhido depois.

## 5. Avaliação final e incerteza

Uma candidata congelada, duas âncoras e Naive; oito seeds42/17/2026/7/123/31415/271828/161803 por rede/bloco. Média de modelos individuais, não ensemble. Todos usam população comum336 e mesmo executor efetivo. Inferência temporal pareada em dias completos (24origens juntas), bootstrap2.000réplicas de seeds e blocos contíguos de14dias dentro de cada semestre, sensibilidades7/28. Alinhar as datas e seeds entre todas as versões. Não cruzar fronteiras entre carteiras independentes.

Três contrastes MSE predefinidos: candidata−A0, candidata−R0 e candidata−Naive. Reportar IC95% descritivo e IC98,333% por contraste para família de três (Bonferroni). Esses intervalos são condicionais à seleção: não corrigem toda a procura adaptativa nem consultas prévias. Para reduzir MSE significativamente é preciso que o intervalo pertinente fique abaixo de zero; se inclui zero, a superioridade é inconclusiva. Mesmo um intervalo negativo não demonstra lucro futuro.

Operação posterior no motor F03 congelado: Smart e direcional_filtrada, braços Spot comprado e futuro bilateral, custos base/estresse. Teto96séries de modelo ×2políticas×2braços×2custos=768carteiras, mais32controles caixa/comprar-manter por bloco/mercado/custo, **800 no total**. Quantidade efetivamente nova depende da herança certificada. F03 anterior permanece preservada; não mover seus ponteiros. Não repetir futuro comprado, já estudado como controle de instrumento, nem retunar limiar, stops, tamanho ou alavancagem.

Não usar simulador futuro F03 em2023 com dados2024–2025: essa cobertura não existe no artefato atual. A busca não recebe lucros finais; avaliação operacional só depois de congelar a candidata. Relatar resultados por bloco/seed, dispersão e cenários de custos, sem um ranking único ou anúncio de Sharpe significativo. Não adotar Sharpe/Sortino/Calmar/DeflatedSharpe como seletor automático com retornos curtos, dependentes e políticas já exploradas; DSR não elimina sozinho toda a seleção desconhecida do projeto.

## 6. Orçamento de um dia e reaproveitamento

| Etapa | Máximo de ajustes reais |
|---|---:|
| Duas âncoras ×3recortes×2seeds | 12 |
| Controle real de reprodução de A0/S1/42 | 1 |
| 12candidatas×3recortes×2seeds | 72 |
| Terceira seed de até3promovidas×3recortes | 9 |
| Terceira seed das duas âncoras×3recortes | 6 |
| Final: candidata e duas âncoras×4blocos×8seeds | 96 |
| Controle real da candidata final B1/42 | 1 |
| **Máximo sem reaproveitamento** | **197** |

Os controles não entram nas médias. Naive/média/mediana não exigem treino neural. Referências novas de desenvolvimento são indispensáveis porque mudou a divisão temporal. As64referências finais antigas só podem ser herdadas mediante equivalência de dados, origens, receita, escalas, inicialização, treino, seleção, checkpoints e inferência; fontes diferentes não autorizam assumir equivalência. Se as64forem certificadas, o teto cai para133novos ajustes. Congelar a relação herdados/novos antes da autorização da execução, sem decidir reutilização pelo resultado favorável.

**24h é teto de relógio de toda a sessão, não promessa de preencher o orçamento.** Planejar qualificação/início até1h; referências/triagem até11h; reforço/selecção até14h; final até22h; auditoria/publicação até24h. Até12consultas Astra, esforço max,30min por consulta e45min por ajuste; o prazo global prevalece. Medir custo/memória das âncoras já orçadas e usar tempos observados para evitar iniciar uma fase que claramente não cabe na reserva. Não introduzir pilotos de mercado extras ou reduzir silenciosamente épocas/seeds para caber. Reduzir número de propostas iniciadas, preservando cobertura dos candidatos comparados.

Estimativa inicial: **10–20h**, com grande incerteza por receita, chamadas Astra e verificações; limite24h. A rodada antiga teve medianas≈1,1min no desenvolvimento e≈2,7min no final, P90≈1,8/4,3min. São tempos internos, não estimativa do trabalho total. Não ocupar GPU ou gastar tokens sem hipótese útil apenas para completar um dia. Se faltar tempo para a final completa, registrar avaliação incompleta e não emitir conclusão com médias parciais. Uma continuação requer decisão explícita; não reabrir busca após observar parte do final.

## 7. Agente, resiliência e rastreabilidade

GPT-6 Astra via Codex CLI autenticado, conforme mecanismo já usado, sem API paga ou modelo substituto. Consultas efêmeras, sem ferramentas/memória/navegação/acesso ao repositório; apenas JSON sob esquema. Lista positiva dos campos enviados (receita, pai, T/V/S, custo, diagnóstico), em vez de confiar só em bloquear nomes como `teste`. Registrar versão CLI/modelo solicitado, prompt/resposta, uso e hash dos dados permitidos. Qualificar efetivamente ausência de ferramentas; flags antigas não são garantia em uma versão nova. Quota/permissão dependem da conta e não são prometidas.

Astra propõe a mudança e uma explicação falsificável: mecanismo esperado, métrica que deveria melhorar, risco e custo. Validador aplica espaço/um fator/pai/cobertura; avaliador e seletor são imutáveis. Astra não escolhe a seed, a época olhando S, os custos, o avaliador ou os pesos numéricos diretamente.

Coordenador único e worker CUDA único, com PID/host/identidade/lock; monitorar progresso por épocas, tempo, GPU/VRAM e artefatos reais. Reinício/timeout de wrapper não prova término do worker. Histórico append-only de propostas/tentativas e manifestos; não apagar falhas ou repetir uma seed ruim.

Receita duplicada/fora do esquema: registrar rejeição, consumir a consulta e pedir outra somente dentro do teto. OOM/NaN de uma candidata: preservar e marcar inviável, sem alterar batch/receita para salvar aquela tentativa; prosseguir apenas após confirmar que o worker encerrou e o ambiente continua saudável. Falha de referência, dados, auditoria/recarga, isolamento ou integridade: interromper toda a sessão. Cota Astra: interromper sem fallback pago. Retomada após reinício exige checagem de processos e fontes; não inferir autorização para alteração científica. Parada humana impede novos ajustes e preserva o que está em curso.

## 8. O que falta antes de iniciar

Esta proposta **não é um executor implementado/qualificado**. A etapa seguinte deve criar novo pacote, sem editar `experimentos/busca_astra/`: contratos T/V/S e grupos de indicadores; avaliador/seleção com testes sintéticos (perfeito, zero, constante, invertido, direção única, NA); recálculo das novas métricas em previsões antigas somente como teste de engenharia, sem alterar critérios para favorecer C05; orçamento e isolamento do agente; qualificação CUDA e herança. Congelar fontes/dados/configuração e vincular autorização humana ao ID concreto. A confirmação desta proposta deverá autorizar esse preparo e o orçamento correspondente; não reutilizar o “ok” da busca001.

Cada hipótese tem receita/pai, diferença única, motivação, fontes, tempos, seeds, curvas e previsão por origem. Publicações de desenvolvimento, final e operação são separadas. Um relatório canônico por ciclo, cronologia em `docs/andamento.md`, catálogo por identidade: não criar um documento explicativo novo a cada consulta do Astra. Não chamar horas rodadas, quantidade de tokens ou candidatos examinados de evidência de qualidade.

## 9. Fundamentação consultada

- [Cawley e Talbot (2010)](https://jmlr.org/papers/v11/cawley10a.html): selecionar repetidamente por um critério estimado também pode produzir sobreajuste; motivação da separação e do orçamento.
- [Hyndman e Athanasopoulos, avaliação temporal](https://otexts.com/fpp3/toolbox.html#time-series-cross-validation): avaliações com passado permitido e erros fora do treino; motivação dos recortes progressivos e controles simples.
- [Bailey e López de Prado (2014)](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf): viés de seleção e backtests; não tratar o melhor Sharpe observado como prova.
- [OpenAI Docs: execução não interativa e JSON Schema](https://learn.chatgpt.com/docs/non-interactive-mode) e [GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra): capacidades do mecanismo, não garantia de orçamento/resultado científico.

Os valores da grade, datas, gates e orçamento são decisões propostas para este projeto, não parâmetros universalmente recomendados por esses trabalhos.
