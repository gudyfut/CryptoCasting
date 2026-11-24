# Padronização dos seis canais diários — protocolo 001

Autorizado pelo pesquisador em 07/11/2026: padronizar os seis canais, manter o restante igual, comparar nas mesmas três seeds e iniciar após conferência. [ADR0034](adr/0034-padronizacao-diaria.md). Referência de retorno `de09c2193737c2581261`, concluída; herdar previsões, checkpoints e carteiras sem retreinar ou editar. Complementa o [protocolo de retorno](protocolo_alvo_retorno_diario.md).

## Mudança única

Nos canais Timestamp, Open, High, Low, Close e Volume, aplicar `z=(x-media_treino)/desvio_treino`. O volume continua previamente dividido por 1e9. Partir dos mesmos valores float32 da referência, calcular momentos em float64 com soma explícita `math.fsum` (independente dos strides da matriz) e transformação em float64, entregar float32 à mesma rede. Isso evita mudar adicionalmente a representação/precisão original do timestamp. Sem log, clipping, indicadores novos ou normalização do alvo.

Estimar média/desvio populacional (`ddof=0`) por canal nos candles únicos efetivamente presentes nas janelas de treino2020–2023. Para D dias e D−15 janelas de14dias, a união tem D−2 candles: primeira janela completa e o último candle de cada janela seguinte. Não contar repetidamente os candles sobrepostos. Verificar sobreposição exata; não deduplicar por igualdade dos valores de mercado. Em canal constante, usar escala1; rejeitar não finitos. São1459candles de ajuste,1446janelas de treino,351de validação e350de teste. As duas últimas datas de cada partição não entram no ajuste das escalas do treino.

Guardar escalas, população, extremos temporais e hash dos valores usados em `escalas.json` e no congelamento. Aplicar os mesmos seis pares de parâmetros a2024/2025, sem reestimar. Nas janelas de treino iniciais, a escala inclui dados posteriores ainda dentro do treino; isso é ajuste de um modelo batch com todo2020–2023, não avaliação walk-forward intratreino. O primeiro instante avaliado fora da amostra é posterior a todo esse ajuste.

## Invariantes e orçamento

BTCUSDT BinanceUSD-M, candles1dia, contexto14dias, mesmas origens e alvos. Retorno simples decimal como saída, RMSE por lote com epsilon1e−8; seleção pelo menor RMSE global de retorno na validação, empate preserva primeira época. Mamba-1 oficial, scan de referência CUDA explícito, estado64,3×4blocos, Adam0,01/weight_decay0,001 em todos os parâmetros, StepLR100/gamma0,5, lote32,1000épocas e limite4h por ajuste. Sem clipping de gradientes/early stopping. Nenhum ajuste de hiperparâmetro orientado pelo resultado.

Ordem42principal → repetição42 →17 →2026. Quatro ajustes novos, três seeds nas médias; controle excluído. A referência é herdada, não conta como novo treinamento. Escopo termina nesta rodada; falha interrompe e exige diagnóstico, sem repetição automática. Autorização não inclui ordens reais ou gastos externos.

## Qualificação e isolamento

Conferir igualdade da receita removendo somente identidade e campos de padronização; igualdade exata de alvos/preços conhecidos/origens, dimensões e contagens. Testar momentos contra candles únicos, invariância à alteração de validação/teste, causalidade das janelas, inversão da transformação, canal constante e não finitos. Testes herdados verificam simulador, unidades e isolamento.

Qualificação CUDA antes da grade:60sondas de forward/backward exatas sobre entradas em escala padronizada, equivalência numérica com implementação oficial; dois ajustes artificiais50épocas/192exemplos, mesmos históricos/checkpoints/previsões e recarga exata, teste inacessível. Não usar resultados de mercado para escolher a receita. Conferir ambiente/hardware, PID/boot e locks; nenhum processo duplicado. Fontes e dados congelados imutáveis.

Controle real exige mesma época selecionada e retornos nativos exatamente iguais; preços equivalentes também comparados na tolerância herdada. Controle aprovado antes das outras seeds e de qualquer teste/backtest. Cada checkpoint vincula identidade da rodada e hash das escalas.

## Avaliação e operação

Reutilizar treinador/métricas da referência por importação e mesmo simulador. Cópia isolada do coordenador de avaliação muda somente destino do contraste: `referencia` versus `padronizado`, ambas prevendo retorno; não chamar a referência de preço. Médias das métricas individuais e ensemble separados. Comparação exige mesmas origens, alvos, seeds e unidades; baselines operacionais devem produzir os mesmos saldos.

Publicar70carteiras:3seeds+ensemble+Naive+semprecomprado+semprevendido ×5cenários ×2fases. Mesma entrada00:01UTC, saída24h depois, capital10mil, nocional95%, filtro±0,20%, comissão/slippage0,05%por lado, funding histórico, lotes/ticks/buffer e estresses0,10%/0,15%. Sem stop/take, sem escolher filtro ou lado pelo teste. Preço equivalente usa último fechamento conhecido; custos e drawdown do envelope são convenções de simulação, não certificação Binance.

Critério preditivo principal: MSE do retorno; RMSE/MAE, viés, correlação e magnitude ajudam a interpretação posterior. Comparar lucro líquido, drawdown, custos, exposição e estabilidade, sem promover por MSE isolado. Bootstrap pareado de seeds/dias,2000réplicas, blocos7/14/28dias (principal14), deltaMSEretorno e delta crescimento log diário. Sem seleção de seed vencedora.2024seleciona checkpoints;2025já foi consultado, retrospectivo, não holdout intocado. Estimativa descritiva de melhora não garante lucro futuro.

## Caminhos

`entradas_modelo/padronizacao_diaria.py`: transformação; `experimentos/padronizacao_diaria/`: coordenação/qualificação/contraste; `configuracoes/padronizacao_diaria_001.json`: receita; `registros/padronizacao_diaria/`: ponteiros/logs; `dados/experimentos/padronizacao_diaria_<id>/`: fontes, escalas, ajustes e publicação. Conferências posteriores usam identidade própria, sem reabrir executor encerrado. Fontes/recibos podem ser versionados; checkpoints, matrizes e ledgers volumosos precisam de pacote externo para transferência. Organização local não comprova backup externo.
