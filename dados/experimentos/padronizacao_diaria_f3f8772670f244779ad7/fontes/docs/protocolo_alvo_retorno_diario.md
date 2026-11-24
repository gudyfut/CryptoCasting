# Alvo diário de retorno versus preço — protocolo001

Autorizado em06/11/2026 neste chat; [ADR0033](adr/0033-alvo-retorno-diario.md). Referência `ac8183e1ecfb91102b48` concluída, fontes/artefatos imutáveis. Complementa o [protocolo reproduzível](protocolo_cryptomamba_reproducivel.md) e o [protocolo diário original](protocolo_cryptomamba_diario.md). Os detalhes herdados continuam aplicáveis, exceto o alvo/unidade de seleção descritos abaixo.

## Mudança única e invariantes

Alvo `r = close_seguinte/ultimo_close - 1`, retorno simples decimal. Rede prevê esse escalar diretamente, sem100×, log, scaler ou restrição de sinal. RMSE por lote `sqrt(mean((rprev-rreal)^2)+1e−8)`; seleção pelo menor RMSE global de retorno na validação, empate conserva primeira época. Não selecionar por lucro. Alteração de alvo muda unidades/ponderação dos erros e escala de gradientes; manter hiperparâmetros permite testar essa hipótese sob receita fixa, não o melhor ajuste possível para cada alvo.

Entradas idênticas em bytes à referência: `[B,6,14]`, timestampUnix eOHLCV em nível, volume/1e9. BinanceBTCUSDTUSD-M, treino2020–2023, validação2024, teste2025;1446/351/350exemplos e origens comuns. Não recolher dados. Usar somente último fechamento conhecido no denominador, nunca preço futuro de execução. Preservar divergências oficiais de volume já documentadas.

Mesma rede oficialMamba-1 com scan de referência CUDA, estado64,3×4blocos, Adam0,01, decay0,001 em todos os parâmetros, StepLR100/0,5, lote32,1.000épocas, limite4h por ajuste, sem clipping/early stopping. Seeds42/17/2026 e repetição42, quatro ajustes novos. Ordem42→controle42→17→2026. Nenhum peso herdado; baselines/previsões e carteiras de preço são referências históricas, não ajustes novos.

## Contratos e reprodução

Comparar configuração com referência permitindo somente identidade/alvo/unidade de seleção; conferir igualdade deX, origens, preços conhecidos, alvos monetários e tamanho de populações. Testar100→102=0,02, quedas, Naivezero, ausência de broadcasting/vazamento e transformação inversa. Contratos anteriores de dados/contabilidade e isolamento continuam exigidos.

Repetir qualificação CUDA:60forward/backward exatos em três casos seed/lote, equivalência estrutural, dois ajustes artificiais50épocas/192exemplos no novo alvo com históricos/checkpoints/previsões exatos e teste inacessível. Controle real: mesma época, retornos nativos exatamente iguais; adicionalmente comparar preços reconstruídos na tolerância monetária anterior (`rtol1e−5/atol0,01USDT`). Recarga exata obrigatória; nenhum relaxamento por resultado observado.

## Saída, política e métricas

Preços equivalentes `Pprev=ultimo_close*(1+rprev)` são usados pelo mesmo motor congelado de futuros24h. O sinal é algebricamente o mesmo filtro±0,20% de retorno. Capital10.000, nocional95%, entrada00:01UTC, saída24h depois, comissão0,05%por lado, slippage0,05%base/0,10%/0,15%estresses, funding histórico, mesma prudência intraminuto.70carteiras:3seeds+ensemble+Naive+semprecomprado+semprevendido,5cenários,2fases. Não alterar política, remover shorts ou selecionar filtro. Retornos previstos≤−1 não são truncados: preço equivalente não positivo é contabilizado e abstém conforme referência.

Em cada ajuste, `validacao.npz/previsoes` e`y` são retornos; `preco_alvo` guarda verdade monetária. Na publicação, `previsoes` e`y` são preços para interoperabilidade; `previsoes_retorno` e`alvo_retorno` são retornos nativos. Cabeçalhos/metadados e protocolo identificam a unidade. Nunca usar MAPE sobre retornos próximos de zero. Publicar MSE/RMSE/MAE de retorno, erro de preço, viés, direção e inválidos; Naive corresponde a retornozero/últimopreço.

Comparação automática `publicacao/comparacao.json`: mesmas seeds/dias, métricas comuns das versões preço e retorno, retorno líquido,drawdown,exposição,custos/funding e ambos os lados. Métrica preditiva principal do contraste é MSE do retorno simples, com MSE de preço secundário; manter resultados antigos sem reescrever. Média das métricas individuais, ensemble separado. Bootstrap pareado seeds/dias7/14/28 (principal14),2.000réplicas, deltaMSEde retorno e delta de crescimento log diário. Sensibilidades não são critérios para escolher o resultado favorável. Não alegar lucro robusto apenas por melhoria de MSE. Referências operacionais sem modelo devem reproduzir exatamente os saldos antigos no mesmo cenário.

## Execução e preservação

Qualificar antes de preparar; congelar fontes/configuração/protocolo/ambiente/dados e autorização sob nova identidade. Conferir integridade do fechamento anterior e de todos os ancestrais, PID/host/boot/locks/GPU antes de iniciar. Falha interrompe; não repetir automaticamente. Não atualizar bibliotecas nem fontes históricas. Após os quatro ajustes/controle, produzir teste e70carteiras, contraste e fechamento com hashes.2024–2025já consultados: avaliação retrospectiva, sem holdout intocado.

Comandos: `CUBLAS_WORKSPACE_CONFIG=:4096:8 python -B -m experimentos.alvo_retorno_diario.qualificacao`; depois `python -B -m experimentos.alvo_retorno_diario preparar|conferir-preservacao|executar`. Treino/qualificação emWSL/CUDA; preparação/conferência podem usarPythonWindows. Processo local, sem ordens reais ou tarefa agendada. Autorização limitada a esta hipótese/rodada.
