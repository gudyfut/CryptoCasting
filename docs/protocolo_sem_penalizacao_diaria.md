# Adam sem penalização no modelo diário — protocolo 001

Autorizado pelo pesquisador em 08/11/2026: testar `weight_decay` zero, manter todo o restante igual, mesmas três seeds e controle; organizar/documentar separadamente, conferir e iniciar treinos/testes. [ADR0035](adr/0035-sem-penalizacao-diaria.md). Referência padronizada `f3f8772670f244779ad7`, concluída e conferida, herdada sem retreino/edição. Os resultados anteriores permanecem históricos.

## Hipótese e mudança única

O diagnóstico posterior mostrou que os 12 ramos Mamba não contribuíam numericamente para as previsões dos checkpoints padronizados. A penalização global do Adam é uma hipótese causal forte, mas ainda não isolada. Alterar somente `treinamento.weight_decay` de 0,001 para 0,0. Não trocar Adam por AdamW, não criar grupos especiais, não mudar taxa, arquitetura, canais ou política. Retirada total é ablação diagnóstica, não declaração de coeficiente ótimo ou promessa de lucro.

Contrato automatizado exige igualdade da configuração após remover somente identidades e essa diferença. O campo descritivo de escopo da penalização continua indicando todos os parâmetros; o coeficiente efetivo é zero para todos. Matrizes, alvos, origens e escalas devem ser exatamente iguais às da referência.

## Invariantes e orçamento

BTCUSDT USD-M Binance, candles diários, contexto de 14 dias, seis canais Timestamp/OHLCV. Mesmos valores float32; padronização por canal ajustada nos 1459 candles únicos das janelas de treino, sem clipping nem reajuste em validação/teste. Volume já dividido por 1e9. Alvo retorno simples decimal do fechamento seguinte; preço equivalente somente para avaliação/operação. Treino 2020–2023 (1446 exemplos), validação2024 (351), teste2025 (350).

Mamba-1 oficial com scan de referência CUDA explícito, sem fallback/fused; entradas [B,6,14], mesmos eixos herdados, larguras14→16→32→1, densidade4, estado64, convolução4, expansão2, LayerNorm epsilon1e−5. Adam taxa0,01, StepLR a cada100épocas com gamma0,5; lote32, RMSE por lote com epsilon1e−8, 1000épocas, limite4h por ajuste, sem clipping ou parada antecipada. Seleção pelo menor RMSE global de retorno em validação, empate conserva primeira época. Teste/lucro não selecionam checkpoint.

Ordem: seed42 → repetição de controle42 → seed17 → seed2026. Quatro ajustes reais novos, três seeds nas médias; controle excluído. Controle exige mesma época e retornos exatamente iguais, além de igualdade/tolerância monetária herdada, antes das outras seeds e da publicação de teste. Falha interrompe; sem busca ou repetição automática. Nenhuma ordem real ou computação paga.

## Observação sem alterar a trajetória

Treinador isolado conserva as operações do treinador de retorno e acrescenta observação na inicialização, épocas1/5/10/25/50/100/250/500/1000 e no checkpoint selecionado. Usa 32 janelas de treino igualmente espaçadas, fixas, sem alvos na sonda e sem consultar validação/teste para decidir o que medir.

Registrar normas de LayerNorm/A_log/D/demais projeções, fração de parâmetros pequenos, amplitude das saídas Mamba em float64, diferença ao zerar temporariamente os ramos apenas na sonda e amplitude da previsão. Nos marcos de treino, registrar também norma do gradiente do último lote antes da atualização e contribuição L2, que deve ser zero. São diagnósticos; não alteram seleção, scheduler, orçamento ou política, nem encerram treino por desempenho ruim. Gradientes de um lote não equivalem à trajetória do Adam. Hooks removidos imediatamente; pesos, estado de RNG e modo conferidos/preservados.

Antes de congelar/iniciar, qualificar o observador contra o treinador herdado **usando o mesmo coeficiente zero**: um ajuste artificial sem observação e duas repetições instrumentadas, 50épocas/192exemplos; históricos sem tempo, checkpoints, previsões e seleção devem coincidir exatamente. Teste artificial inacessível. Adicionalmente60sondas forward/backward reproduzíveis e equivalência com implementação oficial; contratos herdados e novos; conferir dados reais, ambiente, PID/boot, GPU e locks. Ensaios artificiais não contam como seeds de mercado.

## Avaliação e simulação

Mesmo avaliador e simulador da referência; contraste pareado `referencia` versus `sem_penalizacao` com origens/alvos iguais. Publicar métricas de retorno e preço, três seeds individualmente e médias; ensemble calculado separadamente, não confundir com média de carteiras.

70carteiras: três seeds, ensemble, Naive, semprecomprado e semprevendido × cinco cenários × validação/teste. Capital10milUSDT, nocional95%, entrada00:01UTC e saída24h depois, filtro±0,20%, comissão/slippage base0,05%por lado, funding histórico, passos/ticks/buffer herdados, sem stop/take. Slippage estressado0,10%/0,15%, restrições por lado predefinidas. Baselines operacionais precisam reproduzir exatamente os saldos da referência. Não escolher filtro, lado ou seed pelo lucro posterior.

Principal preditivo: MSE de retorno. Relatar RMSE/MAE, viés, correlação, magnitude, contribuição dos ramos, estabilidade entre seeds, lucro líquido, drawdown, exposição, custos e funding. Bootstrap pareado de seeds/blocos7/14/28dias, 2000réplicas (principal14), diferenças de MSE de retorno e crescimento log diário. Maior variabilidade ou ramos ativos não bastam para aprovar melhora; não promover automaticamente por lucro isolado. 2024seleciona checkpoints,2025já consultado e retrospectivo, não holdout intocado. Convenções de backtest não certificam execução/tarifas Binance.

## Separação e encerramento

Namespace `experimentos/sem_penalizacao_diaria/`; receita `configuracoes/sem_penalizacao_diaria_001.json`; ponteiros/qualificação/logs `registros/sem_penalizacao_diaria/`; identidade e artefatos `dados/experimentos/sem_penalizacao_diaria_<id>/`. Referência e cadeia anterior preservadas antes/depois por hash; fontes/configuração/protocolo congelados imutáveis. Sem execução duplicada ou retomada automática após reinício. Conferência posterior usa leitura própria, não reabre executor encerrado. A autorização termina nesta rodada; outra hipótese exige nova decisão.
