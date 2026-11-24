# ADR0029 — Diagnóstico das previsões operacionais

Data: 05/11/2026. Situação: autorizado pelo pesquisador; execução e conferência em registro próprio.

O pesquisador solicitou investigar acurácia por intensidade, assimetria entre altas/baixas e demais informações úteis para orientar a próxima hipótese. Esta etapa lê exclusivamente a rodada operacional `f0dd11f393b5e26edaf8`: 72 ajustes principais, dois controles apenas para integridade, previsões V/C/S e carteiras existentes. Zero novos treinamentos, zero novas simulações, nenhuma alteração de modelo, política ou critério encerrado.

O código fica em `analises/diagnostico_operacional/`, a configuração em `configuracoes/diagnostico_operacional_001.json`, os ponteiros em `registros/diagnostico_operacional/` e os artefatos em `dados/diagnosticos/`. O relatório canônico é `docs/diagnostico_operacional.md`. Preservar fontes, entradas e resultados com hashes antes/depois; uma falha deve permanecer registrada. Não mover nem sobrescrever as execuções anteriores.

Separar retorno terminal de payoff líquido por lado. Examinar distribuição, magnitude, precisão/recall direcional, erro e calibração, ordenação por quintis definidos em C, estabilidade temporal/entre seeds, frequência de observação, regimes conhecidos na origem, saída e atribuição contábil. Cada tabela informa suporte amostral. S cobre trimestres distintos de 2023; V/C/S de folds diferentes se sobrepõem e não serão tratados como observações independentes.

Incerteza por reamostragem sincronizada de dias em blocos de 7/14/28 e seeds, sem tratar previsões horárias como eventos independentes. Os cortes são exploratórios, sem garantia simultânea por múltiplas comparações. Uma média positiva de payoffs hipotéticos não representa uma carteira executável. Um filtro sugerido aqui exigirá hipótese e nova avaliação identificada, sem promoção nesta fase.
