# Estados internos32 e64 — sequência controlada

Delimitação em29/10/2026, depois de consultar os resultados de estados16 e8. O pesquisador autorizou explicitamente guardar as rodadas anteriores e executar primeiro estado32/seis seeds e, separadamente depois, estado64/seis seeds. O protocolo das duas rodadas fica definido antes do primeiro ajuste; não selecionar a segunda configuração pelo resultado da primeira.

## Pergunta e fatores

Como aumentar somente `d_state` altera erro, estabilidade entre seeds, custo do ajuste e política operacional na referência OHLCV? Maior capacidade pode ajudar a extrair padrões ou aumentar sobreajuste; nenhuma direção de resultado é pressuposta.

Estado32: contagem esperada26.401 parâmetros. Estado64:38.689. Estados anteriores:16/20.257 parâmetros e8/17.185. A única alteração da arquitetura é d_state. Preservar largura32, duas camadas, d_conv4, expand2, dropout0,1 e pré-LayerNorm; Mamba-1 oficial CUDA, sem fallback. Contexto continua168 candles, não32/64 horas. Contagens/dimensões são comprovadas na qualificação e nos checkpoints.

## Dados, treinamento e orçamento

Mesmo conjunto `dados/entradas/0420879c2afc454c7754`, BTCUSDT/1h, cinco canais, scalers de treino publicados, contexto168h, log-retorno terminal24h. Treino2021–2023, validação2024, teste2025; purga e origens horárias idênticas às rodadas anteriores. Sem recoleta, nova receita ou mudança de frequência/indicadores.

Cada rodada tem exatamente **seis ajustes reais Mamba**, seeds **17,42,2026,7,123,31415**, na ordem42,17,2026,7,123,31415. São **12 ajustes novos no total**, sem novos LSTM/Naive/ARIMA ou complemento de seeds do estado16. Não acrescentar repetição real adicional. A ausência de repetição completa da mesma seed em mercado é uma limitação explícita do desenho herdado; antes de cada grade há reprodução sintética e recarga exata por ajuste.

Manter100 épocas máximas, paciência10, batch64/microbatch32, AdamW0,0002, weight decay0,001 com isenções oficiais, clipping1 e seeds fixadas. Selecionar menor MSE de validação, empate pela primeira época. Teste e simulação não selecionam época, seed ou configuração. Checkpoints por melhora, recarga exata e métricas conferidas. Falha de CUDA/memória/controle interrompe a sequência para investigação; não alterar dimensões/lote/otimizador silenciosamente.

## Qualificação e congelamento prévios

Cada arquitetura passa por dois ajustes curtos sintéticos seed42, forward/backward, atualização, grupos de otimização herdados, seleção, repetição nos limites anteriores e recarga exata em validação/teste/operacional artificiais. Ensaiar também orçamento e ordem da fila, parada em falha e publicação dos grupos pareados. Nenhuma qualificação usa alvos de mercado para ajustar pesos.

Congelar fontes/configuração/protocolo/ambiente/qualificação e heranças em identidades próprias para32 e64. A configuração64 é congelada **antes do treino32**. Como resultados32 ainda não existem nessa ocasião, a dependência de64 liga a identidade e hash do congelamento32; quando32 concluir, a execução64 exige cobertura, integridade e conferência dos seus resultados. Isso permite sequência automática sem adaptar o estudo aos resultados observados.

Referências16/8 preservadas com ponteiros originais. Cada tamanho tem `registros/estados_ampliados/estadoN/execucao.json`, `dados/experimentos/estados_ampliados_N_<id>/`, fontes/configurações congeladas, pesos, previsões e publicação. Definição genérica Mamba e camadas já qualificadas são reutilizadas intactas. O dataset comum é intencional e não mistura pesos ou resultados.

## Comparações e limites

1. Estado32 versus8 nas mesmas seis seeds; estado64 versus32 nas mesmas seis seeds. São contrastes previamente fixados, não busca do melhor par.
2. Estados8/32/64 comparáveis nas seis seeds. Os quatro tamanhos8/16/32/64 comparáveis nas seeds17/42/2026. Manter esses grupos separados; não apresentar estado16 como tendo seis seeds.
3. Naive, ARIMA e LSTM são referências herdadas, identificadas sem contar como novos ajustes. A publicação32 contém6 novos+14 herdados; a publicação64 contém6 novos+20 herdados, incluindo os seis32.
4. MSE primário; RMSE,MAE,viés,sinal,dispersão e trimestres secundários. Média de perdas, não ensemble. Diferenças pareadas e bootstrap em dias7/14/28,2.000 réplicas, principal14. Intervalos exploratórios não ajustados para toda multiplicidade/seleção adaptativa; interpretar efeito e incerteza, sem declarar estado ótimo universal.
5. Estado8 e referências16 foram observados antes desta escolha.2024/2025 permanecem retrospectivos e não são holdout intocado. Não trocar datas, amostras ou hipóteses entre32 e64. Resultados negativos são preservados.

## Operação

Conservar a política R0: Spot comprado/caixa, decisões00UTC, latência1min, saída24h depois, capital10.000USDT, taxa0,10%/slippage0,05% por lado, cenário agravado e bruto com os mesmos sinais. Manter contabilidade/rotatividade originais para comparar apenas estado interno. Auditorias Binance e manutenção de posição entre sinais consecutivos são estudos posteriores separados; não introduzir sua mudança simultaneamente aqui. Não interpretar MSE como lucro ou execução real de conta/futuros.

## Fila e encerramento

Único coordenador com lock, host/PID/boot e logs, ordem fixa32→64. Só iniciar64 após32 concluído, seis tentativas íntegras, publicação íntegra e conferência posterior. Em falha, registrar incidente e deixar64 pendente; nenhuma busca ou alteração automática. Uma retomada exige processo encerrado confirmado e ação explícita. Um executor já encerrado nunca é chamado para regenerar relatórios; o coordenador pode apenas conferir seus resultados de leitura e prosseguir ao próximo pendente.

Após64, produzir comparação conjunta dos grupos de três e seis seeds e conferir as duas publicações. Estados individuais e fila distinguem preparado/executando/concluído/conferido. Sem novos ciclos autorizados além desses12 ajustes. Logs, fontes, tentativas, falhas e publicações permanecem separados. Conferência não comprova backup externo ou aceite acadêmico.
