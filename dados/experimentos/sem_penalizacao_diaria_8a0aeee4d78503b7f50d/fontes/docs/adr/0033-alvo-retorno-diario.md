# ADR0033 — Alvo de retorno diário com restante da receita fixo

06/11/2026. Pesquisador autorizou explicitamente testar retorno diário em vez de preço, mantendo o restante igual, organizar separadamente e iniciar treinos/testes.

Referência preservada: `ac8183e1ecfb91102b48`, alvo preço, três seeds e controle reproduzível. Nova execução: `experimentos/alvo_retorno_diario/`, registros próprios. Retorno **simples decimal** `fechamento_seguinte / ultimo_close - 1`, sem multiplicar por100, sem log, padronização ou clipping. Exemplo100→102: alvo0,02. A saída continua um escalar linear; o modelo oficial/scan de referência CUDA é o mesmo.

Mudar o alvo implica calcular RMSE de treino/seleção em retorno, em lugar de USDT. A fórmula e epsilon1e−8 permanecem. Erros relativos passam a ter o mesmo peso independentemente do nível de preço; a escala dos gradientes também muda. Não alegar que a alteração é neutra para otimização nem retunar Adam/LR para compensá-la nesta rodada.

Todos os demais campos científicos são conferidos por igualdade: dados, calendário, janelas, canais, arquitetura, inicialização/seeds, Adam, decay, LR/scheduler, lote, épocas, política, custos e cenários. Novos quatro ajustes (42, controle42,17,2026),1.000épocas cada e70carteiras. Referências anteriores herdadas, sem novo treino de preço/LSTM/ARIMA. Nenhum descarte da seed2026.

Preço equivalente para o avaliador: `ultimo_close*(1+retorno_previsto)`; a conversão não recebe preço futuro. Guardar retornos nativos e preços reconstruídos, com alvos e unidades explícitos. Previsões abaixo de−100% permanecem nas métricas e produzem abstenção como preços não positivos da referência; não corrigir silenciosamente. Avaliar as duas versões nas mesmas origens e unidades comuns de preço/retorno, com seeds pareadas, média de métricas e ensemble separados.

2024seleciona checkpoints;2025é avaliação retrospectiva já consultada, não confirmação intocada. Resultado negativo informa a hipótese, não autoriza busca adicional. [Protocolo](../protocolo_alvo_retorno_diario.md).
