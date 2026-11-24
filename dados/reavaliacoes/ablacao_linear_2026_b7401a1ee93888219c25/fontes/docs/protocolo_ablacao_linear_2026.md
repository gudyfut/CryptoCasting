# Ablação linear: extensão retrospectiva a 2026

Autorizada em **13/11/2026**, para comparar os modelos **A** (núcleo completo derivado do CryptoMamba) e **L** (projeções afins treinadas do zero, sem os 12 ramos Mamba e suas LayerNorms). É uma extensão sem treinamento do [fechamento entre ativos](protocolo_fechamento_ramos_diarios.md), com [configuração própria](../configuracoes/ablacao_linear_2026_001.json). Resultados e interpretação entram no [relatório canônico](resultados_ablacao_linear_diaria.md); não substituir publicações anteriores.

## População, controles e limites

Reutilizar os 24 checkpoints A/L de BTC, ETH, BNB e XRP, seeds 42, 17 e 2026. A equivalência da seleção limitada às primeiras 200 épocas está documentada no fechamento anterior; L foi treinado durante 200 épocas. Não atualizar pesos, reestimar escalas, selecionar épocas, moeda, filtro ou configuração. Reutilizar também o Ridge selecionado em 2024 e Naive de retorno zero.

Usar exatamente as **314 origens de 01/01 a 10/11/2026**, dados e mercado preservados da avaliação anterior de A; saída final em 11/11 às 00:01 UTC. Janela causal de 14 candles encerrados, seis canais padronizados pelo treino, tensor `[lote,6,14]`, alvo retorno simples do próximo dia. Conferir novamente as janelas contra OHLCV de origem e as escalas congeladas, inclusive contexto de dezembro de 2025. Testar que alterar o candle do alvo não muda sua entrada.

2026 já foi observado para A e a hipótese de L foi desenvolvida posteriormente. Portanto, esta comparação é **retrospectiva**. Não é uma confirmação intocada nem uma busca por um vencedor. O recorte não representa o ano inteiro.

Antes da inferência nova, congelar fontes, configuração, modelos e dependências; conferir processos e adquirir lock de GPU. Reproduzir exatamente previsões de validação e teste das 24 redes; repetir inferência de 2026, comprovar pesos intactos e reproduzir todas as previsões A/2026 anteriores. Medir também a diferença ao zerar temporariamente as saídas dos ramos A, sem treinar ou promover outra variante. Guardar controles, incidentes e preservação antes/depois.

## Avaliação fixa

Publicar por moeda: cada seed, média das métricas das três seeds e métricas do ensemble, separadamente. Ensemble é média de preços equivalentes antes do filtro. MSE é o contraste preditivo principal; RMSE, MAE, direção, dispersão e Naive/Ridge dão contexto. Não confundir média de erros com erro da média das previsões.

O mesmo simulador de continuidade decide compra/venda/caixa com filtro ±0,20%, alvo de exposição 95%, capital de 10 mil USDT, latência de um minuto, comissão de 0,05% por lado e slippage provisório de 0,01% por lado (estresses 0,02% e 0,03%). Funding histórico, filtros por ordem e risco preservados. Mesmo lado mantém a posição e negocia somente o ajuste líquido. Caixa, inversão ou fim encerram; não há stop/take. Comprar/manter usa quantidade fixa no mesmo futuro. São 132 carteiras: quatro moedas × onze unidades × três custos.

Contrastes pareados L−A e contra Naive/Ridge: MSE e crescimento log diário líquido, bootstrap de blocos consecutivos de 7/14/28 dias, 2.000 réplicas, bloco 14 principal. Para médias individuais, reamostrar também pares de seeds; para ensemble fixo, apenas dias. Três seeds e quatro moedas correlacionadas não garantem generalização; IC abrangendo zero não prova equivalência. Retorno acumulado e drawdown são descritivos, acompanhados de custos e exposição.

Auditar cada carteira pelo verificador independente e reproduzir as 24 carteiras A-ensemble/comprar-manter anteriores. Recalcular métricas, intervalos e reconciliações em conferência posterior sem sobrescrever recibos congelados. Publicar somente com cobertura completa ou identificar falhas explicitamente. Preservar documentos anteriores antes de atualizar navegação e interpretação.
