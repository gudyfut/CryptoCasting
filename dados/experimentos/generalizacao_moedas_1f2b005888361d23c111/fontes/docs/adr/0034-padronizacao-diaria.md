# ADR0034 — Padronizar os seis canais no desenho diário de retorno

Data:07/11/2026. Status: autorizado pelo pesquisador; executar somente após qualificação técnica.

## Contexto

O contraste anterior reduziu o erro médio, mas piorou as operações de2025. O diagnóstico encontrou menor dispersão das previsões, fraca correlação, instabilidade do viés e sinais pequenos diante dos custos. As entradas vigentes possuem escalas extremamente diferentes; a LayerNorm interna não remove a escala do caminho residual. Isso sustenta uma hipótese de condicionamento, sem demonstrar causa das perdas.

## Decisão

Testar z-score por canal, ajustado nos candles únicos presentes nas janelas de treino. Manter os seis canais, alvo de retorno, arquitetura, Adam/LR/scheduler, perda, seleção, períodos, seeds e política. Referência `de09c2193737c2581261` preservada. Três seeds+controle42,1000épocas cada,70carteiras. [Protocolo](../protocolo_padronizacao_diaria.md).

## Limites

Não modificar filtro por lucro posterior, calibrar saída usando teste, retreinar referência ou reutilizar esta autorização para outras hipóteses. Dados2024/2025 são retrospectivos já consultados. Padronização muda condicionamento e regularização efetiva, não garante utilidade operacional; identificar esse efeito sem afirmar otimização ideal de cada receita.
