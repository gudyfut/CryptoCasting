# Matriz de configurações e períodos

Gerado a partir dos contratos Python por `python scripts/atualizar_plano_experimental.py`. Não editar esta tabela manualmente.

Protocolo 1.6. Planejamento, sem treinamento ou resultados novos. A execução final continua bloqueada.

## 1. Moedas, resolução e janelas

Cada linha representa um modelo separado por arquitetura, contexto, horizonte, fold e seed. As moedas não são misturadas em um único treinamento.

| Par | Candle de entrada | Janela de 7 dias | Janela de 14 dias | Alvo principal: 24h | Alvo complementar |
|---|---|---:|---:|---|---|
| BTCUSDT | 15m | 672 candles | 1344 candles | 96 candle(s) | 15m |
| BTCUSDT | 1h | 168 candles | 336 candles | 24 candle(s) | 1h |
| BTCUSDT | 4h | 42 candles | 84 candles | 6 candle(s) | 4h |
| BTCUSDT | 1d | 7 candles | 14 candles | 1 candle(s) | 1d |
| ETHUSDT | 15m | 672 candles | 1344 candles | 96 candle(s) | 15m |
| ETHUSDT | 1h | 168 candles | 336 candles | 24 candle(s) | 1h |
| ETHUSDT | 4h | 42 candles | 84 candles | 6 candle(s) | 4h |
| ETHUSDT | 1d | 7 candles | 14 candles | 1 candle(s) | 1d |
| BNBUSDT | 15m | 672 candles | 1344 candles | 96 candle(s) | 15m |
| BNBUSDT | 1h | 168 candles | 336 candles | 24 candle(s) | 1h |
| BNBUSDT | 4h | 42 candles | 84 candles | 6 candle(s) | 4h |
| BNBUSDT | 1d | 7 candles | 14 candles | 1 candle(s) | 1d |
| XRPUSDT | 15m | 672 candles | 1344 candles | 96 candle(s) | 15m |
| XRPUSDT | 1h | 168 candles | 336 candles | 24 candle(s) | 1h |
| XRPUSDT | 4h | 42 candles | 84 candles | 6 candle(s) | 4h |
| XRPUSDT | 1d | 7 candles | 14 candles | 1 candle(s) | 1d |

Na tarefa principal, há uma origem por dia elegível às 00:00 UTC em todas as resoluções. Na complementar, há uma origem a cada candle completo, contexto fixo de 7 dias. A complementar diária reutiliza a principal.

Uma janela é um exemplo: 672 candles em 15m representam 7 dias de entrada, não 672 exemplos. Tensor por exemplo: `[candles, 5]` (OHLCV) ou `[candles, 8]` (indicadores). O batch efetivo tem até 32 exemplos; o último pode ser menor.

## 2. Timestamp de abertura, origem e alvo

Exemplo didático: BTCUSDT, entrada 15m, contexto de 7 dias, origem em 15/01/2023 00:00 UTC. Essas datas ilustram alinhamento; não certificam elegibilidade nos dados reais.

| Campo | Instante UTC | Significado |
|---|---|---|
| contexto_inicio_utc | 2023-01-08T00:00:00+00:00 | Primeiro candle abre em 08/01; só o passado integra a entrada. |
| ultimo_candle_abertura_utc | 2023-01-14T23:45:00+00:00 | Último candle de entrada abre 15 minutos antes da origem. |
| origem_utc | 2023-01-15T00:00:00+00:00 | O último candle acabou; aqui é emitida a previsão. |
| alvo_fim_utc | 2023-01-16T00:00:00+00:00 | Fechamento 24 horas depois, usado somente como desfecho. |

Alvo binário: `close(alvo) > close(origem)` significa alta; baixa ou empate significa não alta. Na complementar de 15m, o alvo desse exemplo é 15/01/2023 00:15 UTC.

## 3. Sequência de configurações de desenvolvimento

Todas as etapas abaixo usam horizonte de 24h, quatro pares, quatro resoluções, D1–D4 e seed 42. São comparações sequenciais de um fator por vez, não uma busca de todas as combinações possíveis.

| Etapa | Contexto | Entradas | Scaler | Larguras | Decisão |
|---|---|---|---|---|---|
| E0 — Referência inicial | 7 dias | OHLCV (5) | StandardScaler | Mamba 32 / LSTM 32 | Registrar as 16 células nos quatro folds D1–D4. |
| E1 — Sensibilidade ao contexto | 14 dias | OHLCV (5) | StandardScaler | Mamba 32 / LSTM 32 | Comparar com E0. Publicar 7 e 14 dias separadamente; os próximos passos usam 7 dias. |
| E2 — Representação | 7 dias | OHLCV + indicadores (8) | StandardScaler | Mamba 32 / LSTM 32 | Comparar com E0. Escolher features pela BA global de desenvolvimento do Mamba e aplicá-las a ambas as redes. |
| E3 — Normalização | 7 dias | Escolhidas em E2 | MinMaxScaler | Mamba 32 / LSTM 32 | Comparar com StandardScaler nas mesmas features. Escolher pela BA global do Mamba; aplicar a ambas. |
| E4 — Largura das redes | 7 dias | Escolhidas em E2 | Escolhido em E3 | Mamba 64 / LSTM 64 | Comparar cada rede à sua largura 32. Escolher cada largura pela própria BA global; empate favorece 32. |

BA global: média com pesos iguais sobre os quatro ativos, quatro resoluções e quatro folds. Só concluir uma escolha após obter cobertura completa. Empates favorecem a opção inicial. A seleção final pode combinar Mamba 32 com LSTM 64, ou vice-versa, sem escolher por moeda/candle.

As decisões de features e normalização são compartilhadas; as larguras são próprias de cada arquitetura. O AR(1) mantém a especificação fixa e não recebe as janelas/features das redes.

O piloto CPU diário/D1 verifica funcionamento; não cobre a matriz de desenvolvimento. Não agregar backends/hardware diferentes na escolha global. Para reaproveitar o piloto na grade, configuração, dados, código, protocolo e ambiente precisam coincidir.

## 4. Períodos dos folds

Intervalos UTC `[início, fim)`: o fim é exclusivo. Além disso, remover rótulos cujo alvo termine no limite ou depois dele. Contexto de validação/teste pode usar passado anterior ao início do bloco.

| Fold | Fase | Treino | Validação | Avaliação |
|---|---|---|---|---|
| D1 | desenvolvimento | [2021-01-01, 2022-10-01) | [2022-10-01, 2023-01-01) | [2023-01-01, 2023-04-01) |
| D2 | desenvolvimento | [2021-01-01, 2023-01-01) | [2023-01-01, 2023-04-01) | [2023-04-01, 2023-07-01) |
| D3 | desenvolvimento | [2021-01-01, 2023-04-01) | [2023-04-01, 2023-07-01) | [2023-07-01, 2023-10-01) |
| D4 | desenvolvimento | [2021-01-01, 2023-07-01) | [2023-07-01, 2023-10-01) | [2023-10-01, 2024-01-01) |
| F1 | final | [2021-01-01, 2023-10-01) | [2023-10-01, 2024-01-01) | [2024-01-01, 2024-04-01) |
| F2 | final | [2021-01-01, 2024-01-01) | [2024-01-01, 2024-04-01) | [2024-04-01, 2024-07-01) |
| F3 | final | [2021-01-01, 2024-04-01) | [2024-04-01, 2024-07-01) | [2024-07-01, 2024-10-01) |
| F4 | final | [2021-01-01, 2024-07-01) | [2024-07-01, 2024-10-01) | [2024-10-01, 2025-01-01) |
| F5 | final | [2021-01-01, 2024-10-01) | [2024-10-01, 2025-01-01) | [2025-01-01, 2025-04-01) |
| F6 | final | [2021-01-01, 2025-01-01) | [2025-01-01, 2025-04-01) | [2025-04-01, 2025-07-01) |
| F7 | final | [2021-01-01, 2025-04-01) | [2025-04-01, 2025-07-01) | [2025-07-01, 2025-10-01) |
| F8 | final | [2021-01-01, 2025-07-01) | [2025-07-01, 2025-10-01) | [2025-10-01, 2026-01-01) |

D1–D4 permitem desenvolvimento. F1–F8 exigem congelamento prévio e declaração de exposição aos resultados antigos; suas seeds planejadas são 17, 42 e 2026. Datas de início são limites de calendário: contexto, aquecimento, lacunas e purga reduzem a quantidade efetiva de amostras.

## 5. Orçamento

| Escopo | Cálculo | Treinos neurais (duas redes) |
|---|---|---:|
| Uma etapa de desenvolvimento | 4 pares × 4 resoluções × 4 folds × 1 seed × 2 redes | 128 |
| Até cinco etapas | 128 × 5 | 640 |
| Final: 24h / 7 dias | 4 × 4 × 8 × 3 × 2 | 768 |
| Final: 24h / 14 dias | 4 × 4 × 8 × 3 × 2 | 768 |
| Final: próximo candle, somente 15m/1h/4h adicionais | 4 × 3 × 8 × 3 × 2 | 576 |
| Total final | 768 + 768 + 576 | 2.112 |

Contagens planejadas, sem estimativa de duração medida. AR(1) determinístico é adicional e não é multiplicado por seeds, features ou larguras. O orçamento pode ser revisto antes dos scores finais, com justificativa registrada no protocolo.
