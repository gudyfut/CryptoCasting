# Continuidade das posições diárias e referências operacionais

Autorizado pelo pesquisador em11/11/2026: registrar a descoberta de redução de giro e ampliar a avaliação da receita diária padronizada completa para BTC/ETH/BNB/XRP, incluindo Naive, ARIMA e comprar/manter. Receita e execução em [configuração](../configuracoes/continuidade_moedas_001.json) e [estado](../registros/continuidade_moedas/estado.json). Não treinar novas redes nem alterar checkpoints.

## Pergunta e escopo

Comparar zerar/reabrir após24h com continuidade e negociação apenas da diferença até o alvo diário de95% do patrimônio liquidável. Mesmas previsões, três seeds, filtro±0,20%, origens, latência1min, capital10milUSDT, mercados, funding e parâmetros do instrumento. Sem stop/take ou busca de política. Em caixa fecha; em inversão fecha e abre o outro lado; liquidação final obrigatória. Comissão0,05%por lado, slippage provisório1bp e estresses2/3bp, sem certificação histórica.

Cobrir2024/2025: três seeds individuais, ensemble separado, Naive, ARIMA, sempre comprado e sempre vendido nos dois modos, mais comprar/manter passivo. São408carteiras. Não incluir receitas horárias ou variantes diárias como se fossem esta mesma receita. A rodada de taxa em andamento mantém sua identidade e não entra parcialmente nesta seleção.

## Revisão técnica identificada

A primeira comparação BTC `25516ee56ae224e583c6` demonstrou ganho de execução e conserva suas fontes/resultados. Sua implementação admitia pequenos aumentos abaixo do mínimo nocional. A nova versão identifica e deixa esses ajustes aguardando; reduções usam `reduceOnly`, sem isenção de quantidade mínima/máxima. Não executar aumentos inválidos, inventar fragmentação ou modificar os resultados antigos. Reproduzir o BTC legado com filtros desativados apenas como conferência; sua antiga média não é a média corrigida.

O valor liquidável usa fechamento hipotético adverso e comissão para dimensionamento nos dois modos. Custos hipotéticos não são debitados quando a ordem não ocorre. Toda negociação real simulada paga custo sobre a quantidade executada. Funding na fronteira pertence à posição após a decisão. Contabilidade por caixa equivalente é conferida por conta independente de colateral/preço médio e Decimal.

## Referências

Naive prevê retorno zero: com o mesmo filtro permanece em caixa; isso não é comprar/manter. ARIMA diário novo: nove ordens(p,1,q),p/q0..2, sem deriva, ajustadas apenas no treino original de cada moeda; validação escolhe por MSE de retorno simples, com desempate por complexidade/p/q. Sem selecionar por lucro, reestimar parâmetros em2025 ou reutilizar parâmetros horários. Estados filtrados incorporam somente fechamentos já observados, um passo à frente. Preservar candidatos, avisos, falhas, seleção, parâmetros, previsões e repetição exata da ordem selecionada. São36ajustes candidatos+4controles, não novos treinos Mamba.

Comprar/manter abre uma quantidade fixa com95% do capital inicial e fecha no fim, no mesmo perpétuo; paga comissão, slippage e funding. Não rebalanceia diariamente. Sempre comprado é outra referência, com alvo95% reavaliado diariamente. Não comparar instrumento Spot sem declarar diferença.

## Conferência e interpretação

Antes do mercado: testes sintéticos de continuidade, caixa, inversão, funding, minNotional/reduceOnly, risco e causalidade ARIMA; conferir snapshots, mercados, fontes e processos. Primeiro reproduzir resumos financeiros vigentes, quantidades e curvas das referências; conferir o BTC legado antes de publicar. Usar origem comum por moeda, sem interpolar lacunas. XRP conserva dois minutos de mark ausentes e envelope5m apenas para risco.

Critério primário: diferença de crescimento log diário da continuidade contra diário, média das mesmas três seeds. Bootstrap pareado de seeds/blocos7/14/28dias,2000réplicas,14principal. Mostrar retorno, drawdown, custos, giro, funding, exposição, dispersão e comparações descritivas contra referências. IC não remove adaptação anterior ou dependência entre moedas. Não somar carteiras ou apresentar média como ensemble;2024não confirma generalização e2025é retrospectivo.

Conferir cada carteira com auditor independente, regras de ordem, funding, saldo, risco e identidade de PnL bruto menos custos. Drawdown é envelope conservador intraminuto, não ticks/liquidação certificados. Congelar fontes/configuração/protocolo e entradas, preservar tentativas; publicar somente após cobertura e conferência. Registro do marco na ADR0037, cronologia e roteiro, com resultados vinculados à nova publicação.

Fontes primárias para as convenções: [mínimo nocional/reduceOnly Binance](https://developers.binance.com/en/docs/products/derivatives-trading-usds-futures/error-code), [ARIMA statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima.model.ARIMA.html). A implementação instalada e seus hashes constam do congelamento.
