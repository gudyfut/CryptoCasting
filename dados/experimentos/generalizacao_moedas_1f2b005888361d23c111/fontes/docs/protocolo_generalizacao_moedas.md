# Generalização da receita diária padronizada — 001

Autorizado pelo pesquisador em 09/11/2026: organizar/preservar os estudos, coletar dados e iniciar treinamento, validação e teste em ETH, BNB e XRP. Confirmou a versão padronizada pelo menor erro. [ADR0036](adr/0036-generalizacao-tres-moedas.md), [receita](../configuracoes/generalizacao_moedas_001.json). Não há autorização para outra busca, taxa menor, transferência de pesos ou ordens reais.

## Referência e pergunta

Referência `f3f8772670f244779ad7`: menor MSE médio de retorno no teste BTC2025 entre as quatro receitas diárias diretamente comparáveis. Não é vencedora operacional universal. A versão de preço teve menor perda operacional, com erro maior; modelos horários, políticas Smart e estudos Astra não podem ser colocados no mesmo ranking. Escolha retrospectiva conhecida, confirmada pelo pesquisador, não seleção intocada. BTC não será retreinado.

Pergunta: como essa mesma receita se comporta quando ajustada separadamente a ETHUSDT, BNBUSDT e XRPUSDT? Cada moeda tem seus próprios pesos, escalas, checkpoints, controles, previsões e carteiras. Não treinar rede conjunta nem reutilizar pesos de BTC. A referência teve colapso funcional de ramos nas sondas: preservar essa limitação e observar os novos checkpoints depois do treino, sem mudar configuração ou seleção conforme atividade/lucro.

## Dados e divisões

Binance USD-M perpétuos, cotação e margem USDT. Arquivos oficiais diários2020–2025, negociação e marcação1m2024–2025, funding histórico por arquivo e API reconciliados. CHECKSUM remoto de cada ZIP; corpos, URLs, hashes, fontes e incidentes preservados. UTC em milissegundos, OHLC positivo/consistente, volumes finitos/não negativos, duplicatas e calendário conferidos. Reconciliar candles diários com agregação dos minutos em2024–2025. OHLC deve coincidir; volumes apresentam divergências oficiais em14/29jan2025 nas três moedas (até aproximadamente1,45% frente à soma1m). Preservar o volume do ZIP diário oficial, como na referência, registrando ambas as observações; não substituir por API revisada ou soma1m. A API diária também difere do arquivo em14jan para ETH/BNB. Isso é limitação de proveniência, não concordância integral. Qualquer outra divergência bloqueia. Cinco dias XRP ausentes emZIPs de2022 (26–28fev e1–2abr) são complementados por candles oficiais da API, com corpos/URLs/hashes próprios; não interpolação.

Treino até2024-01-01 exclusivo: ETH desde2020-01-01, XRP desde2020-01-07 e BNB desde2020-02-11; dias inaugurais parciais excluídos segundo disponibilidade do contrato. Isso deixa1446/1440/1405 exemplos de treino, respectivamente. Validação2024:351 exemplos; teste2025:350. Mantidas as janelas separadas por partição e a exclusão da última janela herdada da receita pública. Não alegar proporção exata2/3 em moedas com listagem posterior nem chamar divisão fixa de walk-forward.

Escalas z-score por canal ajustadas exclusivamente nos candles únicos das janelas de treino de cada moeda. Sem pooling de escalas, sem clipping, sem ajuste em validação/teste. Timestamp/OHLCV, volume dividido por1e9, valoresfloat32 antes dos momentosfloat64, mesmos contratos da referência. Entrada[B,6,14], saída[B] de retorno simples decimal para o fechamento do próximo dia. Alvo nunca é canal; preço equivalente=último close×(1+retorno).

### Limite observado em XRP

Marcação1m em2024-08-12 às10:02 e10:03UTC ausente no arquivo mensal, diário e API. Negociação1m completa. Tentativa estrita interrompida/preservada. Fonte oficial5m para10:00–10:04:59 fornece extremos; estes ficam em `marca_envelopes.parquet`, separados do arquivo1m original incompleto. No avaliador, somente high/low de risco usam esse intervalo maior nos dois minutos; open/close continuam ausentes. Não chamar isso de recuperação1m, interpolar preços ou excluir operações com conhecimento posterior. Registrar as carteiras que atravessam a lacuna. O envelope amplia a incerteza intraminuto e pode ser mais conservador; não certifica a trajetória real. Sinal, preço de execução e funding permanecem independentes dessa substituição de extremos. Qualquer lacuna não prevista bloqueia, sem fallback automático.

## Treino e seleção

Mamba-1 oficial, selective_scan_ref CUDA explícito, sem fused/fallback. Arquitetura herdada14→16→32→1, densidade4, estado64, convolução4, expansão2, LayerNormeps1e−5. Scan percorre seis canais; dias são atributos das projeções. Adam taxa0,01, weight_decay0,001 em todos os parâmetros, lote32, RMSE por lote com epsilon1e−8,1000épocas, StepLR100/gamma0,5; sem clipping/parada antecipada, limite4h por ajuste. Manter essas decisões para medir generalização da receita, não otimizar separadamente cada moeda.

Ordem ETH→BNB→XRP; em cada moeda42→controle42→17→2026. Nove ajustes principais e três controles,12000épocas no total. Controle exige retornos exatamente iguais e mesma época antes das demais seeds e do teste daquela moeda. Falha interrompe; não repetir seed ruim. Checkpoints pelo menor RMSE global de retorno na validação, empate mantém primeiro. Teste/lucro não escolhem época. Recarga exata e vínculo com moeda/escala/execução obrigatórios.

Qualificação: testes de contratos herdados e novos, causalidade/divisões, representação e lotes/ticks, efeitos dos envelopes somente no risco;60sondas forward/backward exatas e equivalência com implementação oficial; duas repetições artificiais50épocas/192exemplos, histórico/pesos/previsões exatos e teste inacessível. Nenhum ensaio artificial conta como treino de mercado. Conferir ambiente/GPU/PID/boot/locks antes de iniciar. Observação posterior dos checkpoints usa32janelas fixas de treino, não seleciona modelo.

## Métricas e operações

Principal preditivo MSE de retorno, comparado ao Naive na mesma moeda/população; acompanhar RMSE/MAE em retorno, erro em preço, acerto de sinal e viés. Não ordenar moedas pelo erro absoluto em USDT. Reportar três seeds e sua média; ensemble em separado. Incerteza exploratória por seeds/blocos7/14/28dias,2000réplicas; preços e retornos identificados. Seeds não são novos mercados independentes.2024seleciona checkpoints;2025e moedas já consultados em estudos anteriores, não holdout intocado.

Mesma política bilateral diária da referência:10milUSDT por carteira,95%nocional, sinal acima de±0,20%, entrada00:01UTC e encerramento24h depois, sem stop/take. Comissão0,05%por lado, slippage0,05%/0,10%/0,15%, funding histórico, buffer prudencial bloqueante. Tick/quantidade/nocional por símbolo via snapshot de exchangeInfo: ETH0,01/0,001/20; BNB0,01/0,01/5; XRP0,0001/0,1/5. Esses filtros atuais são convenções explícitas, não reconstrução dos filtros/tarifas históricos. Conferir mínimos/máximos de quantidade em cada operação. Não configurar alavancagem ou conta real.

70carteiras por moeda:3seeds+ensemble+Naive+semprecomprado+semprevendido ×5cenários ×2fases. Total210. Cenários base,slippage2,slippage3,somentecompra,somentevenda; não escolher lado/filtro por lucro posterior. Ledger independente confere comissões,funding,caixa e envelope de risco. Não somar retornos de carteiras independentes nem inferir lucro de MSE isolado. Não há critério de promoção automática ou promessa de sucesso.

## Organização e encerramento

`mercado_futuros/multimoeda.py` coleta; `experimentos/generalizacao_moedas/` coordena; `registros/generalizacao_moedas/` contém ponteiros, preparo, incidentes, controles e estado; `dados/experimentos/generalizacao_moedas_<id>/<simbolo>/` separa cada moeda e seus ajustes/publicações. Congelar receita, dados, fontes, protocolo, ambiente e autorização antes de iniciar; preservar cadeia anterior por hash. Publicações concluídas não são reabertas. Novo ciclo ou retomada após falha exige diagnóstico explícito.

Fontes: [arquivos e CHECKSUMs Binance](https://github.com/binance/binance-public-data), [instrumentos, funding e marcação](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data). Preservação local não comprova backup remoto; aplicar a política de armazenamento do projeto.
