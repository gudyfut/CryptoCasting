# Ensemble diário congelado: avaliação posterior em 2026

Autorização do pesquisador em **11/11/2026**: avaliar o ensemble nas quatro moedas até o último dia completo, mesmos modelos/regras, sem novos treinos; coletar o necessário e comparar com comprar e manter. [Configuração](../configuracoes/ensemble_2026_001.json), [exposição](../registros/ensemble_2026/exposicao.json) e [estado](../registros/ensemble_2026/estado.json). Esta etapa estende a ADR0037 e não substitui seus resultados de2024/2025.

## População e pergunta

De01/01 a10/11/2026, 314 decisões diárias por moeda, entradas às00:01UTC e encerramento final em11/11 às00:01UTC. Corte escolhido pelo calendário antes de produzir resultados. Contexto anterior de14dias vem de dezembro2025 das fontes preservadas. Aquece-se a janela com passado disponível, sem perder os primeiros14dias do ano ou truncar a última janela por convenção de partição do treinamento antigo. A transformação de cada janela é idêntica, com teste de equivalência nas origens comuns.

Pergunta: o ensemble e a política escolhidos após observar2025 preservam utilidade operacional em um período posterior que não participou do ajuste dos modelos? Conferir exposição antes de coletar/avaliar. Dados de conta, conhecimento humano e arquivos em outros dispositivos não são auditáveis pelo inventário local. Consultas de livro atual para custos são exposição a mercado, mas não equivalem a teste de previsões. Não afirmar holdout absolutamente intocado; registrar o alcance real e eventual declaração humana separadamente.

## Modelos e decisão fixos

Receita diária padronizada: BTC `f3f8772670f244779ad7`, ETH/BNB/XRP da generalização `1f2b005888361d23c111`, XRP em `continuacao_001`. Mesmos checkpoints selecionados em validação2024, sementes42/17/2026, arquitetura e scan oficial de referência CUDA. Não reestimar pesos, escalas, hiperparâmetros, épocas, pesos do ensemble ou limiares. Executar `eval()`/`inference_mode`, lote32. Reproduzir integralmente as350previsões2025 por modelo e repetir2026 exatamente; verificar estado da rede e hashes antes/depois. Controles não são novos treinamentos.

Entrada: Timestamp Unix segundos e OHLCV diários, volume dividido por1e9, conversão float32 e padronização float64→float32 com as seis escalas antigas. Janela `[lote,6,14]` só usa candles encerrados antes da origem. Saída nativa é retorno simples diário; preço equivalente usa o último fechamento conhecido. Ensemble é média dos três preços previstos, exatamente como o executor anterior; filtro±0,20% define compra/venda/caixa. Não usar alvo futuro na decisão. Alvos ficam separados para métricas.

Continuidade e filtros por ordem da referência, sem stop/take, alvo95% do patrimônio liquidável e latência1min. Comprar/manter abre quantidade fixa com95% do capital inicial e fecha no fim, no mesmo futuro. Capital10milUSDT por carteira, comissão0,05% por lado, slippage provisório0,01% e estresses0,02%/0,03%, funding histórico observado. Manter lotes/ticks/mínimos herdados, sem certificar filtros ou tarifas históricos oficiais. São24carteiras:4moedas×3custos×2políticas. Nada de escolher moeda, período ou cenário pelo lucro.

## Mercado e proveniência

Reutilizar coletor mensal, parser e validadores do módulo de mercado. Arquivos oficiais Binance Vision mensais para meses completos, diários para a cauda, cada ZIP com CHECKSUM. API oficial para arquivo diário ainda não publicado, até10lacunas pontuais por arquivo e os dois minutos de11/11 necessários ao fechamento. Falha/lacuna extensa interrompe; não interpolar nem inventar velas. Guardar URLs, respostas, hashes e a versão recebida. Mercado em `dados/mercado/ensemble_2026/<identidade>/<moeda>/`, separado das fontes anteriores.

OHLCV diário é fonte das entradas; minutos de negócio e mark servem à execução/risco. Conferir calendário completo, unidades, positividade, extremos, volumes, conciliação OHLC diário/minutos. Manter divergências de volume entre granularidades explicitadas, sem substituir valores seletivamente. Funding API mantém markPrice efetivo; meses completos conferem taxas e calendário contra arquivos mensais. A cauda exige eventos ordenados/únicos, cobertura de fronteiras e ausência de lacuna superior a8h; outra frequência/falha exige investigação. Não preencher funding ausente com zero ou outro preço. Dados posteriores ao fechamento são usados apenas para conferir fronteiras da coleta, nunca para sinais.

## Conferência e interpretação

Antes das carteiras2026, reproduzir quatro carteiras completas do ensemble2025 no mesmo motor. Auditar cada carteira nova por conta independente de colateral/preço médio e lotes inteiros, eventos de funding, filtros, preços, saldos, risco e reconciliação Decimal. Publicar somente com12controles de previsão, quatro financeiros e24carteiras completos, ou identificar interrupção sem esconder resultados.

Primário descritivo: retorno líquido do ensemble e diferença contra comprar/manter, acompanhado de drawdown por envelope conservador intraminuto, exposição/lados/episódios, custos e funding. MSE/MAE/viés de retorno são avaliação complementar. Bootstrap temporal pareado7/14/28dias,2000réplicas,14principal, compara crescimento log diário das duas carteiras; não reamostra seeds do ensemble já fixo nem toma moedas correlacionadas como réplicas independentes. Menos operações implica suporte menor. Não escolher outro filtro/seed após o resultado nem chamar a simulação de operações reais.

Congelar fontes, configuração, modelos/scalers e proveniência, preservar incidentes e versões editoriais anteriores. Catálogo, cronologia e narrativa recebem o fato material após conferência, sem relatório paralelo por conversa. Documentação primária: [Binance Public Data](https://github.com/binance/binance-public-data), [API oficial USD-M de mercado](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data). Fontes consultadas em11/11/2026.
