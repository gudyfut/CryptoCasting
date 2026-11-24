# 0037 — Continuidade e redução de giro na execução diária

- Data da decisão e do registro:11/11/2026.
- Situação: ampliação concluída e auditada; adotada como referência identificada de execução para comparações futuras pertinentes, sem promoção de uma estratégia lucrativa geral.
- Autorização: pesquisador solicitou registrar o marco e aplicar a continuidade a todas as avaliações completas da receita diária padronizada, com Naive, ARIMA e comprar/manter.

## Contexto

O primeiro backtest de continuidade BTC `25516ee56ae224e583c6` usou as mesmas previsões e reduziu custos ao negociar somente a diferença de posição. No cenário provisório1bp, a média de três seeds em2025 passou de−14,27% para−0,94%, com menor drawdown. O controle de quantidades herdadas separou a economia de execução do efeito posterior sobre os tamanhos das posições. [Resultados originais](../../registros/continuidade_diaria/execucao.json).

Esse é um marco de **mudança de execução/política**, não melhoria dos pesos, MSE ou prova de capacidade preditiva nova. A saída obrigatória24h era uma convenção identificada do desenho anterior; sua substituição não torna aqueles registros fraudulentos ou resultados de um bug. A revisão ampliada encontrou uma falha específica na aplicação do mínimo nocional por ordem: alguns aumentos pequenos eram executados. Seus efeitos devem ser medidos com a versão corrigida, preservando o primeiro estudo.

## Decisão

Separar decisões diárias de fechamento obrigatório. Em continuidade, conservar a posição se o lado persistir, negociar apenas a diferença até o alvo de95%, zerar em caixa, fechar e abrir em inversão e liquidar no fim da avaliação. Aplicar filtros por ordem; aumentos abaixo do mínimo aguardam, reduções usam `reduceOnly` e respeitam lote/quantidade. Preservar funding e custos efetivos simulados.

Promover o mecanismo para `codigo/simulacao_operacoes/continuidade_diaria/`, com auditor independente. Fontes e resultados originais permanecem nos caminhos congelados. A [ampliação](../protocolo_continuidade_moedas.md) cobre BTC/ETH/BNB/XRP,2024/2025, três seeds, ensemble e referências. ARIMA diário é estimado no treino com ordem selecionada por erro de validação; Naive zero fica em caixa. Comprar/manter é posição fixa no mesmo futuro, distinta de sempre comprado rebalanceado.

## Consequências e limites

A mudança não autoriza retreinar redes, alterar entradas, filtrar por lucro ou substituir publicações financeiras históricas. Usar nas próximas comparações pertinentes como execução identificada, mantendo a versão diária como contraste. Mesmo menor giro não garante lucro e referências simples também podem melhorar.

Os resultados de2024–2025 são retrospectivos e a referência foi escolhida com informação já conhecida. Slippage e tarifas são cenários; drawdown é envelope, não execução de ticks/liquidação real.

## Resultado da ampliação

Concluída `945f0e52b1f85184c3e7`,408carteiras, sem retreino neural. Em2025, médias de três seeds: BTC−14,27% →−0,99%, ETH+31,37% →+60,76%, BNB−38,61% →−25,50%, XRP−31,78% →−18,76%. O ganho de execução não melhora previsões nem demonstra superioridade robusta contra Naive/ARIMA/comprar-manter. A revisão do mínimo nocional muda o primeiro BTC contínuo de−0,94% para−0,99%; ambos ficam preservados, sem escolher o resultado favorável.

A tentativa inicial parou no auditor por resíduo numérico de quantidade XRP após fechamento. Continuação técnica com grade inteira no auditor preservou307carteiras exatas e os ajustes ARIMA; completou101 e auditou408. A [cronologia](../andamento.md#11112026--marco-operacional-continuidade-das-posições-diárias) reúne interpretação e limites; tabelas/ledgers/controles estão na publicação vinculada ao fechamento. Esta decisão não altera retrospectivamente as convenções dos estudos anteriores.

## Evidências

- [Primeira comparação e controle de custos](../../registros/continuidade_diaria/execucao.json).
- [Protocolo da ampliação e correção dos filtros](../protocolo_continuidade_moedas.md).
- [Estado e execução da ampliação](../../registros/continuidade_moedas/estado.json).
- [Fechamento da ampliação e conferência posterior](../../registros/continuidade_moedas/fechamento.json).
- [Catálogo](../../registros/catalogo_estudos.json) e [cronologia](../andamento.md).
