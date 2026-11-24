# ADR 0008 — Contratos de consumo por família

Decisão e registro:29/10/2026. Adotada para a revisão solicitada dos modelos, sem iniciar treinamentos.

## Contexto

Após separar mercado e entradas, o pesquisador pediu revisar Mamba, LSTM, Naive e ARIMA: entradas, dimensões, janelas, alvo e estrutura de arquivos. O código preparado fixa cinco canais e mistura essas responsabilidades ao executor. A ADR0007 permite evolução modular preservando execuções anteriores.

## Decisão

Criar `modelos/` com ponte de consumo, contratos, arquivos por família, inferência e conferência. As redes recebem dimensões e ordem dos canais do conjunto identificado. Pedidos de previsão não contêm resultado futuro; alvos supervisionados são acessados separadamente. Redes devolvem log-retorno após inversão da escala, Naive devolve zero real e ARIMA mantém entrada univariada e estados filtrados.

Preservar arquiteturas/hiperparâmetros de R0 e demonstrar igualdade de forward sob pesos iguais. Verificar ARIMA com parâmetros fixos sintéticos, sem fit. Não editar o executor congelado nem as camadas de dados publicadas. Referência técnica: [arquitetura dos modelos](../arquitetura_modelos.md).

## Consequências e limites

A comparação exige mesmas origens/alvo, sem alegar que ARIMA receba a mesma janela OHLCV das redes. Parâmetros/pesos passam a carregar contrato de dados; cabe ao futuro executor demonstrar proveniência do ajuste. Treinamento, seleção e simulação continuam fora deste módulo e dependem da próxima revisão. Estado verificável: [registros/modelos](../../registros/modelos/estado.json); cronologia em [andamento](../andamento.md).
