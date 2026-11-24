# ADR0030 — Contraste de histórico acumulado e12meses

Data05/11/2026. Status: autorizado para qualificar e executar o primeiro contraste; não autoriza a busca geral do planejamento.

O pesquisador autorizou prosseguir depois de discutir se padrões gerais exigiriam histórico acumulado. A resposta científica permanece aberta: mudança de distribuição não prova que janela recente melhora o sinal.

Comparar a mesma receita C06 do ciclo operacional com acumulado e12meses, nas mesmas três divisões/seeds, alterando só começo de T. Manter calendário ancestral: V/C mensais,6meses de treino e demais hipóteses ficam para decisões posteriores. Reestimar escalas é consequência necessária; orçamento de atualizações por época não é igual por haver mais exemplos no acumulado.

Escopo:18principais+2controles reais,456carteiras,zero consultas Astra/avaliação2024–2025. Política fixa comum mostra o sinal mesmo se calibração histórica escolher caixa; ambas ficam identificadas. Sem promoção automática, nova conta real ou custo pago.

Implementação própria `experimentos/historico_treino/`, mantendo bibliotecas e ciclos científicos congelados. [Protocolo](../protocolo_historico_treino.md), [estado](../../registros/historico_treino/estado.json), [configuração](../../configuracoes/historico_treino_001.json).
