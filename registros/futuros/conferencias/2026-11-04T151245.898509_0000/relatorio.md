# Simulação posterior de futuros — resultados F01

Execução `3e17e6fc15b66ca60313` concluída e conferida: **804 carteiras, zero treinamentos novos**, 64 séries herdadas. [Método](protocolo_futuros.md), [arquitetura](arquitetura_operacoes.md), [estado](../registros/futuros/estado.json).

Resultados retrospectivos de quatro blocos independentes (181/183/180/183 dias), oito seeds por receita. As tabelas usam primeiro a média das seeds de cada bloco e depois peso igual entre blocos. **Não são retorno anual nem retorno acumulado de dois anos.** Cada carteira inicia com10.000USDT.

## Comparação principal: mesmo futuro, cenário base

Sinal diário: positivo compra, negativo abre venda quando permitido. Encerra/reabre após24h. Comissão0,05% e slippage0,05% por lado, além de funding histórico.

| Receita | Modalidade | Retorno líquido médio | Drawdown médio de mark close | Operações médias | Funding médio USDT |
|---|---|---:|---:|---:|---:|
| astra | bilateral | -30.65% | 48.70% | 181.8 | -155.67 |
| astra | comprada | -15.74% | 35.62% | 127.8 | -287.05 |
| crua | bilateral | -37.74% | 51.68% | 181.8 | -17.32 |
| crua | comprada | -14.81% | 25.65% | 103.8 | -168.31 |

## Variação entre blocos e seeds

| Bloco | Astra comprada | Astra bilateral | Crua comprada | Crua bilateral |
|---|---:|---:|---:|---:|
| B1 | -2.26% | -20.23% | 1.98% | -35.42% |
| B2 | -10.86% | -51.36% | 0.00% | -55.19% |
| B3 | -12.45% | -13.47% | -18.72% | -17.86% |
| B4 | -37.38% | -37.53% | -42.50% | -42.50% |

astra: permitir shorts alterou a média em **-14.91 pontos percentuais**; melhorou 7/32 pares bloco/seed e 0/8 médias por seed. As médias bilaterais por seed vão de -39.35% a -23.18%; desvio-padrão dessas oito médias 5.42p.p. Isso é dispersão descritiva, não intervalo de confiança.

crua: permitir shorts alterou a média em **-22.93 pontos percentuais**; melhorou 1/32 pares bloco/seed e 0/8 médias por seed. As médias bilaterais por seed vão de -42.72% a -27.12%; desvio-padrão dessas oito médias 6.04p.p. Isso é dispersão descritiva, não intervalo de confiança.

## Custos e política secundária

O filtro usa limiar fixo aproximadamente0,20%, determinado pelo custo base, em todos os cenários. Não escolhemos o cenário com maior lucro. Ideal elimina comissão/slippage, mas mantém funding.

| Receita | Política | Modalidade | Ideal | Base | Agravado |
|---|---|---|---:|---:|---:|
| astra | sinal24 | comprada | 6.87% | -15.74% | -33.08% |
| astra | sinal24 | bilateral | -2.13% | -30.65% | -50.83% |
| astra | filtrada24 | comprada | 3.39% | -5.50% | -13.34% |
| astra | filtrada24 | bilateral | 3.70% | -6.99% | -16.33% |
| crua | sinal24 | comprada | 2.18% | -14.81% | -26.97% |
| crua | sinal24 | bilateral | -12.19% | -37.74% | -55.88% |
| crua | filtrada24 | comprada | 0.00% | 0.00% | 0.00% |
| crua | filtrada24 | bilateral | 2.35% | 1.15% | 0.08% |

## Referências e limites

| Referência diária, cenário base | Retorno médio | Drawdown médio |
|---|---:|---:|
| caixa | 0.00% | 0.00% |
| sempre_comprado | -17.52% | 38.72% |
| sempre_vendido | -42.14% | 49.86% |

Sempre comprado/vendido fecha e reabre diariamente, com mesmo dimensionamento; não é buy-and-hold puro. Caixa reproduz a ação do Naive de retorno zero. Previsões inalteradas: métricas MSE/MAE do estudo anterior continuam iguais.

Esta camada mede a combinação de sinal, política e mercado. Retorno positivo não comprova previsão superior nem lucro futuro; retorno negativo também é resultado válido. Não há teste confirmatório de significância. Mesmos períodos já consultados, sem novo holdout. Sinais treinados emSpot são transferidos a perpétuos, sujeitos à diferença entre mercados.

Exposição alvo95% do patrimônio conhecido e limite1× na abertura; quantidade fixa pode elevar a alavancagem efetiva com perdas. Buffer prudencial2% bloqueia trajetórias fora do escopo; não é liquidação oficial da Binance. Preços de minuto, custos fixos e filtros de pesquisa não reconstituem livro de ofertas, tiers históricos, conta VIP ou ADL. Nenhuma ordem real foi enviada.

Conferência independente: [2026-11-04T151245.898509_0000](../registros/futuros/conferencias/2026-11-04T151245.898509_0000/conferencia.json). Artefatos, operações, funding e curvas em `dados/experimentos/futuros_3e17e6fc15b66ca60313/carteiras/`; publicações anteriores preservadas.
