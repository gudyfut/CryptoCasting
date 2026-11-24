# ADR0021 — Completar a combinação OHLCV cru com Huber

- Decisão e registro:03/11/2026, antes dos novos resultados.
- Situação: execução autorizada explicitamente pelo pesquisador nesta conversa.
- Origem: pedido para iniciar OHLCV cru+Huber com oito seeds, reutilizando ou completando referências necessárias.

## Decisão

Completar o fatorial entrada relativa/crua×perda MSE/Huber nos mesmos quatro blocos e oito seeds das ADRs0019/0020. Herdar64resultados relativos MSE/Huber da execução10dac17ea9df2c540c57 e32crua/MSE de76f6c437e70eaaa605ad. Executar somente32crua/Huber novos+1controle real B1/42,total33. Não repetir referências compatíveis ou incluir níveis padronizados/arquitetura nova.

Manter entrada crua sem transformação/padronização de X,alvo log-retorno24h padronizado pelo treino,estado16,AdamW0,0002 e seleção por MSE real de validação. Somente a perda supervisionada muda frente à crua/MSE, para2×Huber(delta1). Fontes e artefatos anteriores imutáveis; novo pacote/ponteiro/qualificação/congelamento/autorização por identidade.

Efeitos anteriores foram pequenos/inconclusivos contra a referência. Não presumir que seus ganhos se somam. Fixar três contrastes da combinação contra as referências e a interação de diferenças, IC98,75% Bonferroni na família de quatro,bootstrap seeds/dias14 e sensibilidades7/28. Teste primário é crua/Huber−crua/MSE,com pesos iguais entre blocos. Sem certeza,promoção automática ou busca até melhorar.

192carteiras novas,600herdadas,792comparáveis,mesmo motor/políticas/custos/calendário.2024/2025 retrospectivos já consultados. [Protocolo](../protocolo_crua_huber.md), `experimentos/crua_huber/`, `tests_crua_huber/`, `registros/crua_huber/`. Falha interrompe e permanece preservada; execução encerrada não é repetida para refazer relatórios.
