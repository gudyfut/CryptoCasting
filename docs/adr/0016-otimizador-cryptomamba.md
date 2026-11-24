# ADR0016 — Isolar Adam → AdamW no CryptoMamba adaptado

- Decisão/registro: 30/10/2026, antes dos ajustes desta candidata.
- Autorização: pedido humano de escolher o próximo teste de hipótese, conferir a preservação e prosseguir com treino, validação e teste. Não é autorização para busca indefinida.

O CryptoMamba adaptado foi encerrado com previsões quase constantes; o backtest posterior não demonstrou vantagem econômica do sinal variável. A próxima ablação troca somente Adam por AdamW nessa adaptação, preservando taxa, arquitetura, dados, normalização, perda, população e seis seeds. O valor nominal de decay igual não implica regularização efetiva igual. A hipótese investiga um mecanismo plausível, não diagnostica um bug nem promete melhora.

Orçamento: seis ajustes novos e 59 referências herdadas; controle de reprodução sintético, sem treinamento real adicional. Mamba16 já usa AdamW e não será retreinado. Primário: MSE de validação pareado com as seis versões Adam preservadas, com intervalo temporal. Teste e operação são secundários retrospectivos. Não escolher otimizador, época, seed ou receita pelo lucro de teste.

Usar fontes próprias em `experimento_otimizador/`; o treinador anterior é copiado com diferença científica única conferida por AST. Referências e 369 simulações anteriores permanecem intactas. A camada operacional Smart já fixada recebe somente as seis novas séries, em 54 simulações delimitadas, sem novo limiar ou busca. [Protocolo](../protocolo_otimizador_cryptomamba.md), `registros/otimizador/estado.json` e catálogo distinguem autorização, qualificação, execução e conferência.
