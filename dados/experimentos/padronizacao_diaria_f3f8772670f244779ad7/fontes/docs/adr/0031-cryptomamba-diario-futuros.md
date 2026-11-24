# ADR0031 — Referência diária CryptoMamba e operações futuras de24h

Data:05/11/2026. Estado: autorizado pelo pesquisador; execução exige qualificação e congelamento próprios.

O pesquisador pediu copiar a receita CryptoMamba (candle/contexto/entradas/arquitetura/Adam/taxa/scheduler/lote/perda/orçamento) para2020–2025 na proporção4:1:1, trocando a fonte por Binance e adotando compra/venda com fechamento24h depois. É uma nova referência composta, não ablação do histórico e não réplica dos lucros do artigo. A autorização permite preparar e executar esta rodada; não exige outro “Ok” após concretizar a identidade.

Decisão: BTCUSDT perpétuo USD-M,2020–2023 treino,2024 validação,2025 teste retrospectivo. Contexto14candles diários, seis canais públicos (timestamp+OHLCV), alvo de preço do fechamento seguinte em USDT. A saída operacional é a variação prevista relativamente ao último fechamento conhecido. Preservar a escala de preço e RMSE evita transformar a cópia em outro problema de otimização. O atraso de1min e fechamento24h após entrada geram pequena diferença entre preço alvo e preço de execução; medir ambos sem confundi-los.

Três seeds42/17/2026 e um controle42 real, total4ajustes de1000épocas, sem busca. Seleção por RMSE global de validação, não lucro. Sem parada antecipada: o script público consultado não implementa o mecanismo mencionado no artigo. Adam com penalização em todos os parâmetros, conforme script público, inclusive marcadores no_decay; essa escolha é explícita e não altera as referências antigas. RMSE acrescenta epsilon1e−8 para gradiente definido em errozero. A arquitetura usa SSM oficial CUDA com equivalência ao núcleo público, sem adapter168→14.

Operação: uma posição, decisão diária,24h exatas, sem stop/take,95%de nocional, sem ampliação de capital por alavancagem; limiar0,20% fixo corresponde ao custo-base aproximado de ida e volta.70carteiras: duas fases × sete unidades (três seeds,ensemble,Naive,sempre comprado,sempre vendido) × cinco cenários fixos. Funding histórico, slippage, comissão e envelope intraminuto de risco. O limiar/custos não são otimizados por lucro. Não há certificado de filtros históricos, execução ou liquidação da exchange.

Consequências: avaliação fixa, não walk-forward;2024/2025 já consultados. Não apresentar diferença para os antigos resultados de payoff/2023 como efeito isolado ou comparação pareada. Nenhuma referência anterior é substituída; resultados negativos, controles e incidentes permanecem preservados. Detalhes no [protocolo](../protocolo_cryptomamba_diario.md).
