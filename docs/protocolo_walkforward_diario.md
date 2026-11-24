# Robustez temporal diária A/L em BTC — protocolo 001

Extensão autorizada pelo objetivo do pesquisador de completar as evidências do TCC. Pergunta: a proximidade entre a adaptação Mamba A e a ablação linear L se mantém quando as receitas são reestimadas em quatro momentos? É uma análise retrospectiva de robustez, não confirmação intocada nem demonstração de equivalência. A escolha das receitas foi informada por períodos já conhecidos.

BTCUSDT perpétuo Binance, fontes preservadas, OHLCV e timestamp, 14 dias, alvo retorno simples do dia seguinte. Para cada bloco, reestimar do zero as duas redes, as escalas nos candles únicos de treino e o checkpoint no trecho de validação. Reaproveitar o contrato diário: as janelas são internas à partição e a última possível permanece excluída, para preservar o desenho; isso reduz a cobertura no início de cada bloco. Limites UTC semiabertos:

| Bloco | Treino | Validação | Teste |
|---|---|---|---|
| B1 | 2020-01-01 a 2023-10-01 | até 2024-01-01 | até 2024-07-01 |
| B2 | 2020-01-01 a 2024-04-01 | até 2024-07-01 | até 2025-01-01 |
| B3 | 2020-01-01 a 2024-10-01 | até 2025-01-01 | até 2025-07-01 |
| B4 | 2020-01-01 a 2025-04-01 | até 2025-07-01 | até 2026-01-01 |

O fim de cada parte é o início da seguinte; nenhum alvo pode atravessá-lo. As quatro avaliações semestrais são distintos trechos de calendário, mas compartilham histórico e não constituem mercados independentes. O primeiro contexto de cada parte é descartado; os resultados não devem ser somados como carteira contínua.

Mesma receita A/L do fatorial diário: arquitetura e inicialização preservadas, Adam 0,01, penalização uniforme 0,001, StepLR 100/0,5, lote 32, perda `sqrt(MSE+1e-8)`, 200 épocas sem parada, seleção por RMSE global da validação. Seeds 42, 17 e 2026 pareadas. Total 24 ajustes científicos e dois controles repetidos integralmente em B1 para A42 e L42, precedidos de qualificação. Sem escolher bloco, seed ou modelo pelo teste. A e L são treinados de novo em cada bloco; fatiar previsões existentes não substitui walk-forward.

Por bloco: MSE, RMSE, MAE, direção e Naive zero; três seeds e ensemble separado. Contrastes A–L e A/L–Naive com bootstrap pareado em blocos de 14 dias, sensibilidades 7/28, 2.000 réplicas; média dos blocos com peso igual é descritiva, não transforma quatro períodos em amostras independentes. Calcular também resultados operacionais no mesmo simulador com continuidade, custos 1/2/3 bp, funding e latência preservados, com cada carteira e bloco independentes e auditoria. Não selecionar uma estratégia pelo lucro, excluir falhas prudenciais ou tratar essa simulação como execução real.

Qualificar causalidade, escalas, datas, dimensões, teste inacessível ao treino, reprodução CUDA e dependências antes do congelamento. A grade é sequencial sob lock da GPU compartilhado; verificar processos antes de iniciá-la. Preservar todas as tentativas, fontes, dados preparados, checkpoints, controle, previsões, carteiras e hashes. Publicar apenas com cobertura e auditoria, ou declarar interrupção. Evidências podem complementar o artigo sem reclassificar 2024–2025 como desconhecidos.
