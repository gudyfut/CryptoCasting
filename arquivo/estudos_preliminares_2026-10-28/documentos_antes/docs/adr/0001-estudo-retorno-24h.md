# 0001 — Concentrar o estudo no retorno terminal de 24h

- Decisão: 20/10/2026.
- Registro desta ADR: 27/10/2026, retrospectivo.
- Situação: adotada.
- Autorização: pesquisador; registrada em [decisões](../decisoes.md) e [plano](../../plano.md).

## Contexto e decisão

Após discutir direção, preço e barreiras, o pesquisador definiu o estudo de retorno em 24h. A pergunta é como contextos de 1/3/7/14 dias afetam Mamba e LSTM em quatro moedas, tendo Naive e ARIMA como referências. Adotaram-se candles e origens horários, entrada única de retornos, saída numérica e MSE como métrica principal. Outros candles, horizontes e entradas ficaram como extensões futuras.

Foi autorizada a preservação do estudo anterior, a substituição do projeto ativo e a implementação, auditoria e execução integral do novo protocolo. Não é necessário renovar autorização para etapas já compreendidas nesse escopo; novas hipóteses não são automaticamente autorizadas.

## Consequências

O arquivo de barreiras permanece imutável e separado. Protocolos e artefatos da referência conservam a implementação realmente executada. A avaliação foi posteriormente consultada: a declaração de exposição prévia original não torna esses períodos intocados para novos ciclos.

## Evidências

- [Protocolo científico](../protocolo_experimental.md) e [configuração](../../configuracoes/retorno24_001.json).
- [Ponteiro da referência](../../registros/execucao_atual.json).
- [Resultados de desenvolvimento](../resultados_desenvolvimento.md) e [avaliação](../resultados_avaliacao.md).
- [Fechamento auditado](../../registros/auditorias/1e7c5ed662fba55ddd25/fechamento.json).

Esta ADR organiza decisões anteriores; não altera o contrato congelado nem comprova que os artefatos estão disponíveis em todas as máquinas.
