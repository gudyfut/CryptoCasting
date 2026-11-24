# 0022 — Busca adaptativa assistida por Astra

- Decisão:03/11/2026 (Brasília); implementação04/11UTC.
- Situação:autorizada pelo pesquisador, qualificação/preparação antes de execução.
- Evidência: pedido para deixar Astra em loop experimental, seguido de “ok” ao plano delimitado na conversa.
- Ciclo:`busca_astra_001`; [protocolo](../protocolo_busca_astra.md), [estado](../../registros/busca_astra/estado.json).

## Contexto

As rodadas de estados, taxas, entradas e perdas foram consultadas. Crua/Huber tem melhor média descritiva entre quatro combinações, mas não demonstrou ganho robusto no critério corrigido nem lucro consistente. O pesquisador solicita exploração assistida por Astra para formular e testar mudanças; não há garantia de resultado favorável.

## Decisão

Separar busca adaptativa de estudos congelados. Astra via Codex/ChatGPT recebe resumos de desenvolvimento e propõe receitas JSON; avaliador e worker permanecem fixos e não recebem código arbitrário. Até12h/12candidatas, até3promovidas, uma finalista. Refazer referência com o mesmo aquecimento336 para comparação justa de entradas/contextos. Teto108ajustes reais,408carteiras; fase final até12h após congelar receita. Orçamento inclui controles e referências, não ciclos indefinidos.

Permitir representações/indicadores/arquitetura/otimização e contração determinística de pesos de saída em cópia. Edição arbitrária de tensores ou programas gerados não é automaticamente executada: exigiria qualificação própria. Não confundir seleção adaptativa de uma receita com ablação causal de um fator.

## Limites e preservação

Desenvolvimento2023; testes2024/2025retrospectivos, já expostos. Não enviar testes ao agente nem usar lucro como seletor. Uma busca sem candidata elegível é conclusão válida. Preservar todas as tentativas e as referências anteriores; não promovê-las/substituí-las automaticamente. Não mudar objetivo do TCC para vencer Naive ou lucrar. Nenhum recurso pago contratado e nenhuma redefinição de cota autorizada.
