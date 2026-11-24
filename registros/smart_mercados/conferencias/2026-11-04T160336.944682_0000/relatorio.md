# Smart retida: comparação Spot/futuros e filtro — F02

Execução `9e1d6c3686499c020389` concluída e conferida: **1.632 carteiras, zero novos treinamentos**, 64 séries herdadas. [Método congelado](protocolo_smart_mercados.md), [decisão](adr/0025-smart-spot-futuros.md), [estado](../registros/smart_mercados/estado.json).

Quatro blocos independentes de2024–2025,727datas, oito seeds por receita. Primeiro média de seeds por bloco, depois peso igual entre os quatro blocos. Percentuais não são retorno acumulado de dois anos nem retorno anual.

A Smart ajusta parcialmente e mantém posição: não liquida diariamente. Mesma reserva5%, quantidade causal, mínimo100USDT, passo0,001BTC e cobrança equivalenteUSDT nos mercados. Essa Smart95 comum não é reprodução exata da Smart histórica; usar comparações dentro desta rodada.

## Resultado principal, custos iguais

Comissão0,05% e slippage0,05% por ajuste em ambos os mercados. Funding histórico nos braços designados.

| Receita | Política | Spot comprado | Futuro comprado sem funding | Futuro comprado com funding | Futuro bilateral com funding |
|---|---|---:|---:|---:|---:|
| astra | smart | +11.75% | +11.74% | +8.52% | +1.46% |
| astra | smart_filtrada | +9.30% | +9.30% | +6.83% | +2.23% |
| crua | smart | -1.25% | -1.25% | -1.97% | -13.08% |
| crua | smart_filtrada | +0.00% | +0.00% | +0.00% | +0.00% |

## Diferenças pareadas

Cada diferença usa os mesmos32pares bloco/seed. Pontos percentuais positivos favorecem o primeiro termo. Contagens não equivalem a teste de significância; não foi calculado intervalo confirmatório.

| Receita | Política | Contraste | Diferença média p.p. | Pares com ganho |
|---|---|---|---:|---:|
| astra | smart | futuro_sem_funding_menos_spot | -0.01 | 9/32 |
| astra | smart | futuro_menos_futuro_sem_funding | -3.22 | 0/32 |
| astra | smart | futuro_menos_spot | -3.23 | 0/32 |
| astra | smart | futuro_bilateral_menos_futuro | -7.06 | 15/32 |
| astra | smart_filtrada | futuro_sem_funding_menos_spot | -0.00 | 10/32 |
| astra | smart_filtrada | futuro_menos_futuro_sem_funding | -2.47 | 0/32 |
| astra | smart_filtrada | futuro_menos_spot | -2.47 | 0/32 |
| astra | smart_filtrada | futuro_bilateral_menos_futuro | -4.60 | 2/32 |
| crua | smart | futuro_sem_funding_menos_spot | +0.01 | 1/32 |
| crua | smart | futuro_menos_futuro_sem_funding | -0.73 | 0/32 |
| crua | smart | futuro_menos_spot | -0.72 | 0/32 |
| crua | smart | futuro_bilateral_menos_futuro | -11.10 | 2/32 |
| crua | smart_filtrada | futuro_sem_funding_menos_spot | +0.00 | 0/32 |
| crua | smart_filtrada | futuro_menos_futuro_sem_funding | +0.00 | 0/32 |
| crua | smart_filtrada | futuro_menos_spot | +0.00 | 0/32 |
| crua | smart_filtrada | futuro_bilateral_menos_futuro | +0.00 | 0/32 |
| astra | spot | filtrada_menos_smart | -2.45 | 11/32 |
| astra | futuro_sem_funding | filtrada_menos_smart | -2.44 | 12/32 |
| astra | futuro | filtrada_menos_smart | -1.69 | 13/32 |
| astra | futuro_bilateral | filtrada_menos_smart | +0.76 | 12/32 |
| crua | spot | filtrada_menos_smart | +1.25 | 8/32 |
| crua | futuro_sem_funding | filtrada_menos_smart | +1.25 | 8/32 |
| crua | futuro | filtrada_menos_smart | +1.97 | 8/32 |
| crua | futuro_bilateral | filtrada_menos_smart | +13.08 | 20/32 |

## Blocos: Smart sem filtro, custos iguais

| Bloco | Receita | Spot | Futuro comprado | Futuro bilateral |
|---|---|---:|---:|---:|
| B1 | astra | +33.30% | +25.97% | +25.07% |
| B1 | crua | +2.04% | +1.41% | -5.37% |
| B2 | astra | +20.84% | +19.12% | -9.28% |
| B2 | crua | +0.00% | +0.00% | -37.62% |
| B3 | astra | +10.12% | +8.22% | +8.08% |
| B3 | crua | +7.45% | +6.59% | +6.59% |
| B4 | astra | -17.27% | -19.23% | -18.02% |
| B4 | crua | -14.50% | -15.90% | -15.90% |

## Risco, exposição e frequência — custos iguais

| Receita | Política | Braço | Drawdown médio | Exposição média absoluta | Ordens médias | Carteiras ativas |
|---|---|---|---:|---:|---:|---:|
| astra | smart | futuro | 23.17% | 67.04% | 82.2 | 31/32 |
| astra | smart | futuro_bilateral | 24.17% | 63.16% | 100.1 | 32/32 |
| astra | smart | futuro_sem_funding | 22.56% | 66.91% | 83.3 | 31/32 |
| astra | smart | spot | 22.50% | 66.92% | 83.3 | 31/32 |
| astra | smart_filtrada | futuro | 19.67% | 58.30% | 17.5 | 30/32 |
| astra | smart_filtrada | futuro_bilateral | 21.28% | 56.35% | 18.6 | 31/32 |
| astra | smart_filtrada | futuro_sem_funding | 19.15% | 57.97% | 18.0 | 30/32 |
| astra | smart_filtrada | spot | 19.12% | 57.98% | 18.0 | 30/32 |
| crua | smart | futuro | 10.17% | 26.79% | 20.9 | 20/32 |
| crua | smart | futuro_bilateral | 30.97% | 67.84% | 38.4 | 32/32 |
| crua | smart | futuro_sem_funding | 9.99% | 26.80% | 21.2 | 20/32 |
| crua | smart | spot | 9.96% | 26.79% | 21.2 | 20/32 |
| crua | smart_filtrada | futuro | 0.00% | 0.00% | 0.0 | 0/32 |
| crua | smart_filtrada | futuro_bilateral | 0.00% | 0.00% | 0.0 | 0/32 |
| crua | smart_filtrada | futuro_sem_funding | 0.00% | 0.00% | 0.0 | 0/32 |
| crua | smart_filtrada | spot | 0.00% | 0.00% | 0.0 | 0/32 |

## Sensibilidade de custos e referências

Ideal zera execução, mas preserva funding. Por mercado: Spot0,10% e futuro0,05% de comissão; slippage0,05% nos dois. Política/filtro não mudam entre cenários.

| Receita | Política | Braço | Ideal | Custos iguais | Custos por mercado |
|---|---|---|---:|---:|---:|
| astra | smart | spot | +12.17% | +11.75% | +11.52% |
| astra | smart | futuro | +8.94% | +8.52% | +8.52% |
| astra | smart | futuro_bilateral | +2.11% | +1.46% | +1.46% |
| astra | smart_filtrada | spot | +9.52% | +9.30% | +9.18% |
| astra | smart_filtrada | futuro | +7.06% | +6.83% | +6.83% |
| astra | smart_filtrada | futuro_bilateral | +2.52% | +2.23% | +2.23% |
| crua | smart | spot | -1.18% | -1.25% | -1.29% |
| crua | smart | futuro | -1.92% | -1.97% | -1.97% |
| crua | smart | futuro_bilateral | -12.97% | -13.08% | -13.08% |
| crua | smart_filtrada | spot | +0.00% | +0.00% | +0.00% |
| crua | smart_filtrada | futuro | +0.00% | +0.00% | +0.00% |
| crua | smart_filtrada | futuro_bilateral | +0.00% | +0.00% | +0.00% |
| comprar_manter | smart | spot | +21.40% | +21.19% | +21.08% |
| comprar_manter | smart | futuro | +16.18% | +15.97% | +15.97% |
| comprar_manter | smart | futuro_bilateral | +16.18% | +15.97% | +15.97% |
| caixa | smart | spot | +0.00% | +0.00% | +0.00% |
| caixa | smart | futuro | +0.00% | +0.00% | +0.00% |
| caixa | smart | futuro_bilateral | +0.00% | +0.00% | +0.00% |

## Como interpretar

O filtro usa magnitude fixa≈0,30%, baseada nos custos Spot anteriores, igual em todos os mercados. Abaixo disso mantém a posição já aberta. Pode reduzir giro e prejuízos, mas também exposição a altas e velocidade de saída; não mede confiança do modelo e não garante lucro. Carteira em caixa não comprova acerto preditivo.

O braço futuro sem funding é contrafactual, não uma modalidade negociável. Sua diferença para Spot inclui preços negociados, marcação e efeito desses preços no dimensionamento. Funding também altera patrimônio e operações posteriores: a diferença entre braços não é apenas a soma dos pagamentos.

Mesmos modelos e previsões: MSE/MAE não mudaram. Resultados retrospectivos, sem novo holdout e sem promoção automática por lucro. Mais carteiras não são amostras independentes. As médias por seed/bloco e os contrastes completos estão na publicação.

Exposição controlada na abertura/aumento; perdas podem elevar exposição efetiva. Buffer prudencial2% não é fórmula integral de liquidação Binance; violação interromperia a rodada. Custos/filtros são hipóteses, sem livro de ofertas ou certificação de conta real. Sem ordens reais ou novos treinamentos.

Auditoria posterior: [recibo](../registros/smart_mercados/conferencias/2026-11-04T160336.944682_0000/conferencia.json). Dados completos em `dados/experimentos/smart_mercados_9e1d6c3686499c020389/publicacao/resultados.json`; ordens, funding, diários e curvas preservados por carteira. Ledgers/curvas volumosos locais, resumos/fontes/manifestos elegíveis ao Git. Estudos anteriores intactos.
