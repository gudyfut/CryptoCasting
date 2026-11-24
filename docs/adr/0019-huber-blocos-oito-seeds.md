# ADR0019 — MSE versus Huber em blocos e oito seeds

Data03/11/2026. Situação: desenho e início autorizados explicitamente pelo pesquisador; qualificação/identidade devem preceder mercado. Oito seeds não garantem certeza de melhora.

## Contexto

A rodada anterior de seis seeds em divisão única apresentou melhora modesta de Huber, sem satisfazer o critério de incerteza. O pesquisador informou quatro dias para concluir experimentos e duas semanas para artigo, e pediu ampliar Huber/non-Huber com aproximadamente oito seeds, podendo usar blocos. A proposta anterior de três seeds com LSTM auxiliar não foi executada e é substituída por esta delimitação autorizada.

## Decisão

Quatro blocos expansivos B1–B4 em2024/2025, oito seeds pareadas por versão/bloco, Mamba16 com MSE ou2×Huber(delta1 padronizado).64ajustes principais, mais dois controles reais B1/42 antes das outras seeds, total66. Mesmas entradas/arquitetura/AdamW/taxa constante0,0002/parada e escolha por validação. Scalers e pesos novos por bloco. Sem novos LSTM/ARIMA; quatro Naive sem treino e408simulações de Smart/diaria24/benchmarks em carteiras independentes por bloco.

Primário predefinido do novo ciclo: MSE de teste, média igual entre quatro blocos e oito seeds, diferença pareada com bootstrap de seeds/dias14, sensibilidades7/28. A decisão anterior continua preservada. Avaliação retrospectiva, sem alegação de holdout novo ou certeza. Não ajustar a grade aos resultados, nem promover por lucro isolado. [Protocolo](../protocolo_huber_blocos.md).

## Implementação e consequências

Namespace `experimentos/huber_blocos/`, entrada `python -m experimentos.huber_blocos`, testes `tests_huber_blocos/`, registros/ponteiro próprios `registros/huber_blocos/`. Reutilizar treinadores e motor congelados sem editá-los. Verificação de artefatos deduplica dentro de cada fase, mas uma fase nova confere hashes de novo. A última sessão de cada bloco é excluída por calendário conhecido; não confundir retornos de carteiras reiniciadas com retorno contínuo. Hipóteses novas de entradas/otimizador ficam fora deste orçamento. O objetivo é uma conclusão defensável, inclusive inconclusiva, não maximizar placar ou provar lucro.
