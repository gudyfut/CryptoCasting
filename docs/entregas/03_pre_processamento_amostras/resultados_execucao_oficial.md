# Entrega 3 — resultados da execução oficial

**Execução pelo pesquisador em 28/09/2026.** Dataset processado: `dados/processados/daeec76f001afb50a8fe/`. Contrato: `entrega3-v1`. Estes são resultados de **qualidade, cobertura e descrição dos dados**; ainda não há desempenho preditivo do AR(1) ou do Mamba.

## Evidência de integridade

- O manifesto da coleta contém 240 arquivos mensais: 216 completos e 24 com exclusivamente lacunas de candles, ZIP e checksum oficial válidos.
- As 24 ocorrências correspondem aos mesmos seis meses em cada par. A falta soma 70 candles de 15m por par, ou 280 ocorrências de par/candle.
- O relatório processado agrupou essas ausências em **28 intervalos contínuos** (sete por par). Os intervalos têm os mesmos timestamps nos quatro pares, fato observado nos arquivos; isso não estabelece a causa das interrupções.
- O manifesto da Entrega 3 lista **67 arquivos de saída**, todos presentes e com SHA-256 conferido após a execução. Os arquivos brutos não foram alterados.

## População efetiva da matriz principal

| Medida | Resultado |
|---|---:|
| Pares × granularidades | 4 × 4 = 16 células |
| Origens diárias comuns elegíveis | **1.661** |
| Primeira origem | 23/01/2021 00:00 UTC |
| Última origem | 31/12/2025 00:00 UTC |
| Candles-base 15m preservados por par | 175.226 |
| Candles-base ausentes por par | 70 |
| Retornos diários válidos nos mesmos dias dos quatro pares | **1.811** |

Para 15m, 1h e 4h, cada par tem 1.661 origens elegíveis antes da interseção. A célula diária possui 1.668 candidatas, das quais sete são retiradas para compartilhar exatamente a grade intradiária. Os **7 e 14 dias** de contexto resultam nas mesmas 1.661 origens por célula. Em cada par, as quatro resoluções têm `origem_utc`, `alvo_fim_utc`, preço de origem, preço-alvo e classe iguais nas amostras principais. Pares diferentes têm seus próprios rótulos; o que é comum entre eles são as datas de previsão.

Os 12 folds planejados (D1–D4 e F1–F8) têm treino, validação e teste não vazios e ambas as classes presentes em todos os blocos/células contados. Após a purga, os **testes finais da matriz principal** têm entre 89 e 91 amostras por trimestre. Na tarefa complementar de próximo candle, o número de testes por trimestre varia com a frequência: 8.639–8.831 em 15m, 2.159–2.207 em 1h e 539–551 em 4h. Esses números são contagens de amostras, não scores nem amostras independentes entre si.

## Hipótese de volatilidade

O desvio-padrão dos retornos logarítmicos diários foi calculado nos **mesmos 1.811 dias de retorno** dos quatro pares. A tabela apresenta o período completo; o relatório gerado também contém mediana e percentil 95 do retorno absoluto.

| Par | Desvio diário | Desvio anualizado por √365 |
|---|---:|---:|
| BTCUSDT | 3,05% | 58,30% |
| ETHUSDT | 4,13% | 78,97% |
| BNBUSDT | 4,26% | 81,35% |
| XRPUSDT | 5,13% | 97,98% |

No período completo, os dados **sustentam a ordem proposta** BTC < ETH < BNB < XRP segundo essa medida. A ordem não é estável em todos os anos:

| Ano do candle UTC | Dias comuns | Ordem crescente do desvio diário |
|---|---:|---|
| 2021 | 352 | BTC < ETH < BNB < XRP |
| 2022 | 365 | BTC < BNB < XRP < ETH |
| 2023 | 363 | BTC < BNB < ETH < XRP |
| 2024 | 366 | BTC < BNB < ETH < XRP |
| 2025 | 365 | BTC < BNB < ETH < XRP |

Assim, a caracterização dos ativos acrescenta diversidade ao estudo, mas não justifica tratar uma ordem fixa de volatilidade como propriedade intrínseca das moedas. Os percentuais anualizados são estatísticas descritivas desta amostra histórica; não são previsão de risco ou promessa de desempenho do modelo.

## Arquivos para auditoria e reunião

- `manifesto_processamento.json`: contrato, versões, procedência, contagens e hashes.
- `grade_comum_utc.parquet`: datas idênticas usadas na matriz principal.
- `relatorios/lacunas_15m.csv`: início, fim e extensão das 28 lacunas contínuas por par.
- `relatorios/cobertura_candles.csv`: 16 células e perdas por interseção.
- `relatorios/contagens_folds.csv`: amostras, altas, não altas e empates por bloco.
- `relatorios/volatilidade_dias_comuns.csv` e `relatorios/volatilidade.md`: medidas completas por ativo e ano.

**Atualização de 28/09/2026:** o ARIMA(1,0,0) já foi executado em BTCUSDT/D1–D4 e a revisão 1.6 do protocolo acrescentou a LSTM à Entrega 4. Este dataset e suas divisões continuam sendo a base para as duas redes e o AR(1); a Entrega 3 não realizou comparação Mamba versus baselines, referência de 50% ou teste PT.
