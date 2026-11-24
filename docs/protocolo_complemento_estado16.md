# Complemento do estado16: seis seeds pareadas

Autorizado pelo pesquisador em29/10/2026: completar treino, validação e teste do Mamba16 para seis seeds e acrescentar sua média à tabela comparativa. Os resultados anteriores já foram consultados; esta extensão é retrospectiva, sem novo holdout ou busca de configuração.

## Delimitação

Reutilizar integralmente as três seeds17/42/2026 de R0 `ab5baf3eab3a2e66d8b2`; executar somente **três ajustes novos**, seeds **7,123,31415**, nessa ordem. O conjunto final é17/42/2026/7/123/31415, idêntico aos estados8/32/64. Não refazer modelos existentes nem acrescentar baselines ou repetição real extra. Os dois controles reais R0 continuam preservados; o complemento exige reprodução sintética prévia e recarga exata de cada checkpoint. Não selecionar seeds favoráveis.

Arquitetura exatamente R0: Mamba-1 oficial CUDA, estado16, largura32, duas camadas, convolução4, expansão2, dropout0,1 e pré-LayerNorm;20.257 parâmetros. Mesmo conjunto `dados/entradas/0420879c2afc454c7754`, BTCUSDT/1h, cinco canais OHLCV, contexto168h, alvo log-retorno terminal24h; treino2021–2023, validação2024 e teste2025, mesmas origens, purga e scalers. Manter AdamW0,0002, decay0,001 com isenções oficiais, batch64/microbatch32, clipping1,100 épocas/paciência10. Menor MSE de validação seleciona checkpoint; empate pela primeira época. Teste nunca seleciona época, seed ou arquitetura.

## Execução e preservação

Nova identidade, configuração e pacote `experimento_complemento16/`, entrada `run_complemento16.py`, ponteiro `registros/complemento_estado16/execucao.json`. Não alterar fontes/configurações/protocolos/publicações das execuções anteriores. Congelar também vínculos e hashes de todas as referências8/16/32/64/LSTM/Naive/ARIMA. Qualificar dimensões, atualização, reprodução curta sintética, seleção e recarga; testar orçamento, heranças, autorização e bloqueio de reexecução antes dos ajustes reais. Verificar hardware, ausência de processo concorrente e lock com host/PID. Preservar toda tentativa e interrupção; falha exige investigação, nunca mudança silenciosa.

Publicar três ajustes novos e26 referências herdadas, com origem individual. Conferir cobertura, manifestos, seleção mínima, dimensão dos checkpoints, métricas e recarga. Manter política Spot R0 (decisões00UTC, latência1min, saída24h, capital10.000USDT, taxa0,10% e slippage0,05% por lado; bruto mesmos sinais e agravado). Não incorporar sensibilidades posteriores de custos/manutenção de posição.

## Comparação

MSE primário; RMSE,MAE,habilidade contra Naive,direção,dispersão e operação secundários. Média aritmética das métricas por seed, inclusive RMSE; não ensemble nem carteira combinada. Preservar consolidação anterior e gerar recibo novo para os quatro estados nas seis seeds, mantendo também o quadro das três seeds. Comparar todos os pares por diferença de perdas e bootstrap temporal circular em dias7/14/28,2.000 réplicas, principal14, seed20261020. Intervalos exploratórios, condicionais aos modelos, sem correção global de multiplicidade. Não alegar estado ótimo universal nem utilidade financeira por MSE. Atualizar o relatório comparativo existente e a cronologia, sem criar relatório concorrente. Nenhum novo ciclo além desses três ajustes fica autorizado.
