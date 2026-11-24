# ADR0010 — Reduzir somente o estado interno do Mamba

Decisão e registro:29/10/2026, depois de observar a referência R0. O pesquisador solicitou auditar OHLCV/custos e uma alteração de configuração com seis seeds, somente Mamba. Escolheu explicitamente seis ajustes novos e comparação pareada nas três seeds antigas.

## Decisão

Investigar `d_state16→8`, motivado pela divergência entre melhora de treino e validação. Manter dados, representação, contexto, alvo, camadas/largura, otimizador e critério de seleção. Não presumir melhora. O [protocolo](../protocolo_estado_mamba.md) delimita hipótese, orçamento, sementes, heranças e publicação.

As seeds17/42/2026 permitem comparação pareada com R0. As adicionais7/123/31415 descrevem estabilidade da candidata; não compará-las como se existissem seis ajustes na referência. O orçamento de seis não inclui repetição real adicional. Qualificação usa reprodução sintética antes da grade e recarga exata por ajuste, explicitando a ausência de repetição completa de uma mesma seed no mercado.

As transformações reproduzem a matriz/scalers e preservam geometria, mas há mudanças de distribuição e extremos. Sua influência causal exige outra ablação. A auditoria encontrou aproximação da comissão de compra e limitações de execução; sensibilidades ficam separadas. Não alterar entradas/custos junto com o estado interno.

## Consequências

Novo código/configuração/identidade, fontes e protocolo congelados; R0 e estudos preliminares preservados. Mamba/LSTM/Naive/ARIMA anteriores são referências herdadas e não novos ajustes. Testes2024/2025 permanecem retrospectivos. Conclusão negativa é válida; não autoriza buscas futuras. Progresso e resultados em `registros/estado_mamba/` e na cronologia, sem placar nesta decisão.
