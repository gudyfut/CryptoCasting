# Exploração do processo de melhoria de modelos com inteligência artificial

> Nota de escopo — 11/11/2026: objetivos e “próximas etapas” descritos nesta síntese representam o planejamento histórico da fase. A orientação vigente prioriza a investigação e as conclusões para o TCC, conforme as [diretrizes de pesquisa](diretrizes_pesquisa.md) e o [plano atual](../plano.md). A conclusão do artigo não depende de obter um modelo lucrativo. O relato e os resultados abaixo conservam seu contexto original.

Síntese consolidada em 05/11/2026. Esta é a **leitura principal única** da exploração assistida por Astra posterior à reformulação do panorama web de 03/11/2026. A etapa está encerrada e organizada; o próximo trabalho será definir e investigar uma combinação final de modelo e operação. Nenhum modelo final foi escolhido por esta consolidação.

## 1. Delimitação e finalidade

A interface atual apresenta 14 etapas do estudo OHLCV até 03/11, conforme seu [recibo de exportação](../registros/interface/panorama_20261103/exportacao.json). Depois dela, experimentamos como usar uma IA para propor alterações no Mamba, executar comparações controladas e procurar utilidade operacional. A fase também exigiu melhorar a comparação entre receitas, separar previsão de política e execução, revisar o simulador e construir diagnósticos que deem feedback útil à IA.

Organizamos esse conjunto como **exploração do próprio processo de exploração**: aprendemos tanto sobre os modelos testados quanto sobre a forma de conduzir uma busca assistida por IA. Essa é uma síntese retrospectiva para consulta e redação; não substitui os objetivos, critérios ou autorizações que cada ciclo tinha quando foi executado. Os estudos anteriores da interface permanecem separados.

O objetivo posterior do pesquisador é encontrar uma combinação Mamba + política operacional economicamente satisfatória em futuros cripto, permitindo compras e vendas, com lucro líquido, risco e estabilidade explícitos. O trabalho realizado até aqui não demonstrou que esse objetivo foi alcançado. Tampouco demonstrou que seja impossível alcançá-lo com outro desenho.

## 2. Como a IA participou

Astra atuou como **proponente de hipóteses e receitas**, dentro de espaços de alteração e orçamentos definidos. O executor local preparou as entradas, treinou o Mamba, escolheu checkpoints e calculou métricas/backtests. Os pesos foram atualizados pelo treinamento numérico; a IA não editou manualmente os pesos para garantir lucro.

O processo geral foi: pergunta e referências → proposta de receita → verificação de compatibilidade → treino/validação → avaliação de desenvolvimento → feedback à IA → reforço ou rejeição → congelamento antes de uma avaliação posterior, quando os critérios permitiam. A separação entre proponente e avaliador buscou impedir alterações oportunistas na medição.

As rodadas não foram idênticas. A primeira otimizou principalmente erro preditivo e chegou a uma candidata final. A segunda tornou a seleção mais exigente e não aprovou finalista. A terceira passou a investigar conjuntamente modelo e política de futuros, incluindo alvos de payoff. Entre elas, avaliações sem treino demonstraram quanto a forma de operar altera o resultado.

## 3. O que efetivamente foi executado

| Etapa | Pergunta e execução | Novos ajustes reais | Novas carteiras | Conclusão |
|---|---|---:|---:|---|
| Busca Astra 001 | 11 candidatas; final com oito seeds/quatro blocos | 106, incluindo controles | 408 | C05 foi avaliada; melhoria pequena frente à referência, sem superioridade conclusiva sobre Naive |
| Comparação Astra × crua/Huber | Mesmo executor e população; 32 Astra herdados | 34, incluindo dois controles | 192; outras 216 herdadas | Diferença preditiva pequena; política e exposição explicam parte da diferença operacional |
| F01 — futuros | Transferir os sinais existentes para operações compradas/bilaterais diárias | 0 | 804 | Giro e custos elevados; não comparável diretamente à Smart Spot retida |
| F02 — política Smart comum | Comparar Spot/futuro, funding e filtro com política alinhada | 0 | 1.632 | A diferença de mercado é menor quando a política é comparável; funding e shorts alteram o resultado |
| F03 — revisão operacional | Corrigir convenções de execução e separar hipóteses de saída/filtro | 0 | 1.200 | Correções não produziram uma estratégia bilateral robusta; risco e lucro respondem à política |
| Busca Astra 002 | Duas âncoras, 12 receitas, triagem e reforço em 2023 | 100, incluindo um controle | 0 | Nenhuma finalista; etapas condicionais de avaliação final não executadas |
| Busca operacional de futuros | Oito receitas, três seeds, três recortes; retorno terminal ou payoff por lado | 74, incluindo dois controles | 1.260 | Nenhuma finalista; só uma combinação receita/recorte operou em S e perdeu |
| Diagnóstico posterior | Magnitude, direção, regimes, seeds, calibração e atribuição de perdas | 0 | 0 | Revelou limitações do sinal e pistas para a próxima hipótese |

São **314 ajustes reais novos** e **5.496 carteiras novas** nesses ciclos, incluindo controles e cenários. Heranças e releituras não foram somadas novamente. Essas contagens medem trabalho executado, não hipóteses independentes, evidências independentes ou estratégias lucrativas. As publicações de cada ciclo continuam sendo a fonte das contagens e das médias.

## 4. Resultados que importam para interpretar essa exploração

### Primeira busca: ganho pequeno de previsão, lucro dependente da política

A candidata C05 da busca001 usou OHLCV relativo à própria janela, contexto de 72h e Huber, mantendo Mamba de 16 estados, duas camadas, AdamW e taxa 0,0002. Mudaram representação e contexto; não foi uma ablação de um único fator.

Na média de oito seeds/quatro blocos, MSE: referência **0,0006212452**, candidata **0,0006122753**, Naive **0,0006092954**. A candidata reduziu o MSE em 1,44% frente à referência, mas ficou 0,49% acima do Naive. Os intervalos pareados incluíram zero. A balanced accuracy permaneceu perto de 50%.

Na Smart Spot, a candidata teve retorno médio de +12,15% por bloco, contra +11,42% da referência; na política de liquidar diariamente, teve −3,04% com custos. São médias de carteiras independentes, não retorno composto de dois anos. Comprar/manter superou a média da candidata em cada bloco. Portanto, o lucro observado não demonstrou vantagem preditiva sobre referências simples.

### Comparação justa com crua + Huber

Com o mesmo executor e população, crua/Huber teve MSE **0,0006114371**, contra **0,0006122753** da candidata Astra: diferença de apenas 0,137%, sem superioridade conclusiva. Ambas ficaram acima do Naive.

Na Smart, Astra teve +12,15% e crua −0,59% de retorno médio, com drawdowns médios de 24,23% e 15,76%, respectivamente. Astra assumiu mais exposição. Na política diária, a crua ficou em caixa em todas as 32 carteiras porque suas previsões eram pequenas demais para superar o limiar de entrada. **Zero retorno não significou previsão correta.**

Esse ciclo mostrou por que comparar receitas vindas de executores ou populações diferentes pode induzir conclusões erradas, e por que MSE menor não implica automaticamente carteira melhor.

### Revisões de operação: o backtest é parte do desenho

F01 fechava/reabria posições diariamente e a Astra bilateral teve retorno médio de −30,65%. F02 adotou Smart retida comum; a Astra bilateral teve +1,46% no cenário de custos iguais. Essa diferença não mede uma melhoria da rede: mudaram as regras de operação e as convenções comparadas.

F03 distinguiu correções técnicas — comissão, reversão, arredondamento, reduceOnly e reconciliação — de hipóteses novas, como sair integralmente ao sinal contrário e filtrar entradas. Com a receita Astra:

| Política F03, custos base | Spot comprado | Futuro comprado | Futuro bilateral |
|---|---:|---:|---:|
| Smart revisada | +11,61% | +8,44% | +1,46% |
| Saída no sinal contrário | +2,68% | +2,11% | −1,71% |
| Saída + filtro de entrada | +1,87% | +1,60% | +0,32% |

O bilateral filtrado passou de +0,32% para −0,50% quando a derrapagem aumentou. A Smart bilateral apresentou drawdown médio de 24,12% e médias por seed entre −5,11% e +8,41%. **Uma média positiva existiu, mas não estabeleceu robustez operacional.**

A revisão preservou os preços/sinais e auditou a contabilidade. Continuaram limitações de filtros históricos, liquidez intraminuto, preenchimentos e liquidação completa da exchange. As simulações não certificam execução em conta real. A redução de risco com filtros também reduziu exposição e, em vários casos, lucro.

### Segunda busca: a triagem não resistiu ao reforço

Astra002 testou contexto, momentum, volatilidade, volume relativo, pooling, dropout, taxa e representação, com mudanças identificadas frente ao pai de cada receita. Na triagem de duas seeds, N07 alcançou razão MSE/Naive de **1,008103**; após a terceira seed, passou a **1,016391**. As âncoras ficaram em 1,013510 e 1,014131.

Nenhuma receita cumpriu os critérios. A fase final com oito seeds e as carteiras condicionais não ocorreram. O teto de tempo/treinamentos não era uma obrigação de continuar buscando até aparecer um resultado positivo. A principal lição foi a fragilidade de pequenas vantagens de triagem e a necessidade de reforço pareado.

### Busca econômica: alvo e política passaram a ser investigados juntos

A rodada seguinte separou T (pesos), V (checkpoint), C (política) e S (comparação adaptativa). R0 previa retorno terminal; P0 e C01–C06 previam o payoff líquido de uma compra e de uma venda com stop/take/prazo definidos. Os scores de payoff não são probabilidades de alta/queda.

Das oito receitas, só C05/D2 aprovou uma política em C: **+0,467%**, seguido de **−8,228% em S**, média das três seeds, todas negativas. As demais combinações ficaram em caixa após reprovação em C. Isso revelou uma limitação do feedback: retorno zero após o bloqueio esconde informações úteis sobre o sinal rejeitado.

As 74 execuções representaram oito receitas, não 74 ideias diferentes. Grande parte da variação estava nas entradas; o alvo de payoff e as saídas permaneceram bastante restritos. A rodada não representa uma busca exaustiva por todas as formas de prever e operar.

### Diagnóstico final: o que deve orientar uma próxima tentativa

- **Magnitude:** R0 acertou 50,17% das direções; previsões maiores não mostraram melhora consistente. Sua dispersão era apenas 3,09% da dispersão dos retornos reais. Isso não prova sozinho erro de implementação, mas exige testar se a pequena variação prevista ordena oportunidades.
- **Assimetria:** P0 preferia venda em 96,08% das origens. Recall alto de quedas podia resultar dessa preferência quase constante. Precisão, recall, prevalência e balanced accuracy precisam ser vistos juntos.
- **Regime:** 94,88% das observações de S ficaram no tercil de volatilidade inferior definido em T. Em D3, a vantagem histórica relativa da venda se inverteu. Uma janela de treinamento mais recente passou a ser uma hipótese justificável, ainda não executada.
- **Sinal seletivo:** C06, com volume relativo, teve 74 previsões de payoff acima de 0,5% com média observada de +0,317%. O mesmo corte foi negativo em C; o intervalo exploratório incluiu perdas e houve desequilíbrio entre seeds. É pista de baixa confiança, não filtro aprovado.
- **Direção versus lucro:** nas carteiras C05/D2, vendas acertaram a direção terminal em 58,37% dos casos, compras em 40,24%; ambos os lados perderam. Das 169 operações que acertaram a direção, 55 tiveram prejuízo por saídas/custos/caminho do preço. Não concluir que todo prejuízo short significa pior previsão de quedas.
- **Treinamento:** a perda de treino continuou caindo enquanto a validação piorava após os melhores checkpoints. Mais épocas, isoladamente, não estavam justificadas.

Esse diagnóstico leu previsões e carteiras existentes; não abriu operações novas nem treinou modelos. Os payoffs hipotéticos horários se sobrepõem e não podem ser somados como retorno de carteira.

## 5. O que aprendemos sobre construir uma busca com IA

1. **Separar proponente, executor e avaliador.** A IA pode sugerir alterações; não deve alterar a métrica, apagar tentativas ou afrouxar critérios durante a comparação congelada.
2. **Dar feedback informativo.** Mostrar erro e viés por lado, magnitude, calibração, atividade, exposição, custo, saída e motivo de rejeição. Apenas lucro agregado ou caixa não explica por que uma receita falhou.
3. **Comparar na mesma implementação.** Dados, origens, transformação, calendário, seeds e simulador precisam ser equivalentes ou suas diferenças explicitamente declaradas.
4. **Escolher o que está sendo investigado.** Uma ablação altera um fator; uma busca conjunta pode mudar uma receita completa, mas não atribui o resultado a um componente isolado.
5. **Separar previsão, decisão e execução.** Um modelo pode prever bem uma média e não superar custos. Uma política pode lucrar por exposição comprada sem demonstrar antecipação. Corrigir contabilidade não melhora a rede.
6. **Tratar triagem como triagem.** Reforçar seeds e períodos antes de promover. Seeds repetem inicializações, não criam novos mercados; janelas horárias de 24h também se sobrepõem.
7. **Usar critérios econômicos acompanhados de suporte.** Lucro líquido, drawdown, crescimento composto, custos agravados, atividade e estabilidade devem ser vistos em conjunto. Nenhuma métrica isolada garante lucro futuro; caixa e pouca atividade não podem parecer sucesso artificial.
8. **Não obrigar o mercado a oferecer oportunidades iguais em todo regime.** Exigir atividade mínima em todos os lados/recortes pode rejeitar estratégias seletivas; uma mudança desse critério deve ser prospectiva e compensada por suporte temporal e incerteza, sem adaptação ao resultado já visto.
9. **Separar desenvolvimento de confirmação.** 2023 foi usado adaptativamente; 2024–2025 já foram consultados em ciclos anteriores. Não chamá-los de teste intocado. O ano 2026 também requer verificação de exposição antes de ser reservado.
10. **Manter rastreabilidade sem produzir um documento por conversa.** Uma síntese de fase, um desenho vigente e registros estruturados por execução são suficientes. Explicações cotidianas permanecem no chat.

## 6. Como usar esta fase no TCC

Formulação sustentada: **foi conduzida uma exploração iterativa de um processo de busca assistida por IA para melhorar receitas Mamba e sua aplicação operacional. Foram avaliados mecanismos de proposição, comparação, seleção, execução e diagnóstico. Algumas melhorias descritivas apareceram, mas não se estabeleceu uma combinação final com vantagem operacional robusta. A exploração forneceu requisitos e hipóteses para a etapa seguinte.**

Não afirmar que a IA provou melhorar modelos em geral, que o número de treinamentos equivale a número de hipóteses, que a busca foi exaustiva, ou que um backtest positivo garante lucro. Esta fase tem valor como desenvolvimento metodológico e evidência empírica, inclusive pelas tentativas negativas. Sua inclusão no escopo acadêmico definitivo deve ser alinhada ao texto e ao orientador; esta consolidação não altera o PDF original.

## 7. Transição para o modelo e backtest final

A próxima etapa ainda será desenhada. O objetivo será uma combinação concreta de modelo, previsão e operação em futuros, com referências simples e avaliação de lucro líquido/risco/estabilidade. Antes de executar, identificar:

- tarefa prevista, horizonte, frequência de decisão, entradas e histórico de treino;
- referência e fatores que poderão mudar;
- política, custos, funding, restrições e convenções de saída;
- períodos de desenvolvimento e confirmação, considerando exposição já ocorrida;
- orçamento, critérios de promoção/parada e tratamento de tentativas negativas;
- quais evidências serão suficientes para chamar a combinação de resultado final do trabalho.

Janela móvel de treino e hipóteses seletivas de volume são propostas, não decisões incorporadas. O próximo ciclo terá identidade própria e herdará apenas componentes explicitamente verificados. Nenhum executor encerrado deve ser reaberto como se fosse continuação desta consolidação.

## 8. Onde as evidências ficaram

Esta síntese substitui a necessidade de ler vários relatos para entender a fase. Cinco relatos editoriais sem vínculo de hash de entrega foram retirados de `docs/` após conferência de suas cópias exatas no [pacote histórico único](../arquivo/exploracao_ia_2026-11-05/relatorios_editoriais_originais.zip), acompanhado do [manifesto](../arquivo/exploracao_ia_2026-11-05/manifesto.json). Relatórios vinculados a entregas, protocolos e fontes científicas permanecem nos caminhos exigidos pelos hashes. São **anexos de ciclos encerrados**, não desenhos ativos ou instruções para iniciar treinamento. Checkpoints, previsões, curvas e incidentes foram preservados.

| Etapa / identidade | Registro verificável | Anexo técnico |
|---|---|---|
| Astra001 — `b34bad73d6cef1d10a97` | [Estado](../registros/busca_astra/estado.json) | [Protocolo](protocolo_busca_astra.md); relato editorial no pacote histórico |
| Comparação — `ce284eb4a489f604fb9c` | [Estado](../registros/comparacao_astra_crua/estado.json) | [Protocolo](protocolo_comparacao_astra_crua.md); relato editorial no pacote histórico |
| F01 — `3e17e6fc15b66ca60313` | [Estado](../registros/futuros/estado.json) | [Protocolo](protocolo_futuros.md); relato editorial no pacote histórico |
| F02 — `9e1d6c3686499c020389` | [Estado](../registros/smart_mercados/estado.json) | [Protocolo](protocolo_smart_mercados.md); relato editorial no pacote histórico |
| F03 — `6c1a00a9967e2617b8b1` | [Estado](../registros/revisao_operacional/estado.json) | [Resultado original](resultados_revisao_operacional.md) |
| Astra002 — `932da51c61935c911ec5` | [Estado](../registros/busca_astra_002/estado.json) | [Protocolo](protocolo_busca_astra_002.md); relato editorial no pacote histórico |
| Operacional — `f0dd11f393b5e26edaf8` | [Estado](../registros/operacional_futuros/estado.json) | [Resultado original](resultados_operacional_futuros.md), [desenho congelado](desenho_operacional_futuros.md) |
| Diagnóstico — `afa26746c7994ec042ea` | [Estado](../registros/diagnostico_operacional/estado.json) | [Tabelas, método e quatro figuras](diagnostico_operacional.md) |

O [catálogo](../registros/catalogo_estudos.json) liga as identidades e as heranças. `dados/experimentos/<identidade>/` conserva tentativas, modelos e publicações; `dados/diagnosticos/` conserva a análise posterior; `registros/` conserva os ponteiros e conferências. `experimentos/`, `analises/` e `simulacao_operacoes/` mantêm as implementações separadas. A cronologia factual única continua em [andamento](andamento.md).

A organização e a limpeza desta consolidação são verificáveis em `registros/organizacao_exploracao_ia_001/`. Arquivos científicos volumosos locais precisam de pacote de preservação ao transferir de máquina; esta organização não equivale a commit, envio ao GitHub ou backup externo.
