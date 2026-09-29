# Entrega 3 — pré-processamento e construção das amostras

**Estado em 28/09/2026:** implementação e execução oficial concluídas. O pesquisador executou a coleta e o pipeline; o dataset `daeec76f001afb50a8fe` foi auditado após a geração. Há resultados de cobertura e volatilidade, documentados em [resultados da execução oficial](resultados_execucao_oficial.md). Ainda não há resultados de previsão.

## Objetivo e fronteira da entrega

Transformar os ZIPs mensais da [Entrega 2](../02_pipeline_coleta/README.md) em candles alinhados, indicadores causais, índices de janelas, rótulos e divisões temporais auditáveis. A execução seguiu o [protocolo experimental](../../protocolo_experimental.md), versão 1.5; a revisão 1.6 acrescentou LSTM como consumidora das mesmas amostras, sem alterar este dataset. Esta entrega não estima AR(1), LSTM, Mamba, balanced accuracy ou teste PT: são etapas seguintes.

## O que está implementado

| Arquivo | Responsabilidade |
|---|---|
| `configuracoes/pre_processamento.json` | Contrato fechado de quatro pares, quatro granularidades, features e contextos. |
| `pre_processamento/origem.py` | Exige 240 registros auditados, confere SHA-256 de cada ZIP, aceita somente lacunas explícitas com checksum correto e revalida OHLCV e grade temporal. |
| `pre_processamento/transformacoes.py` | Agrega blocos UTC completos de 15m para 1h, 4h e 1d; calcula e associa indicadores só após o fechamento diário. |
| `pre_processamento/amostras.py` | Rejeita contexto ou horizonte com lacunas; cria amostras com índices locais ao parquet, timestamps, preços, retorno, classe e empate. |
| `pre_processamento/folds.py` | Define D1–D4 e F1–F8 por calendário UTC, purga rótulos nas fronteiras, ajusta `StandardScaler` nos candles únicos de treino e confere janelas. |
| `pre_processamento/relatorios.py` | Compara volatilidade em dias de retorno válidos para **todos** os quatro pares. |
| `pre_processamento/pipeline.py` e `run_pipeline.py` | Orquestram e registram arquivos, hashes, contagens e versões. |
| `tests/test_pre_processamento.py` | Casos pequenos de agregação, causalidade, alinhamento, lacunas, purga e normalização. |

## Definições temporais

- Um candle guarda `abertura_utc` e `fim_utc` (limite final exclusivo do intervalo de negociação). A previsão ocorre em `fim_utc`, quando o fechamento já está disponível.
- A matriz principal faz uma previsão em cada 00:00 UTC elegível, para as 24 horas seguintes. Cada célula dos quatro pares por quatro resoluções usa a **mesma grade de origens**, definida pela interseção de elegibilidade de 14 dias, indicadores e alvo. As amostras de 7 e 14 dias usam essa grade idêntica.
- `H=24h` corresponde a 96, 24, 6 e 1 candles de 15m, 1h, 4h e 1d. Os contextos de 7 dias têm 672, 168, 42 e 7 candles; os de 14 dias, o dobro.
- A análise complementar prevê o próximo candle em cada origem completa, com 7 dias de contexto. A célula diária reutiliza o arquivo principal de `1d/7d` e seus resultados deverão ser reutilizados na avaliação; não se treina uma cópia.
- `retorno_futuro = ln(preco_alvo/preco_origem)`. `classe_alta = 1` apenas quando o retorno é estritamente positivo; empate fica em 0. Não há filtro pela magnitude futura.

## Indicadores e ausência de vazamento

Os cinco canais básicos são `open, high, low, close, volume`. Os três candidatos adicionais, sempre nessa ordem, são retorno logarítmico do último dia completo, distância do fechamento desse dia à SMA dos últimos sete fechamentos diários e desvio amostral dos últimos sete retornos diários. A volatilidade requer oito fechamentos diários consecutivos. A associação intradiária usa o último dia encerrado em ou antes da origem; uma lacuna reinicia o aquecimento. Os arquivos guardam as oito colunas, mas o experimento começa com **cinco**; os três canais extras serão avaliados separadamente no desenvolvimento, conforme o protocolo.

Não existe scaler global salvo nesta entrega: ajustá-lo antes de escolher o fold causaria vazamento. `separar_fold` retorna treino, validação e teste em ordem cronológica. Uma amostra só entra no bloco se `alvo_fim_utc` for **estritamente anterior** à fronteira seguinte. Em cada célula/fold da futura execução experimental, `ajustar_normalizador(candles, treino_purgado, FEATURES_OHLCV)` cria um `StandardScaler` novo com a união dos candles usados nas janelas de treino; a mesma transformação é aplicada à validação e ao teste por `montar_janela`. O scaler ajustado e seus índices/estatísticas deverão ser persistidos junto ao experimento da Entrega 4/5. Janelas sobrepostas não dão peso repetido a um candle no ajuste.

## Execução pelo pesquisador

No diretório raiz do projeto, o pesquisador executa primeiro a [coleta](../02_pipeline_coleta/README.md). O pipeline depende do manifesto `dados/brutos/manifestos/manifesto_coleta.jsonl` e dos 240 ZIPs auditados; uma instalação nova ainda não contém esses arquivos.

```powershell
python -m pip install -r requirements.txt
python run_coleta.py --config configuracoes/coleta_oficial.json
```

Depois de examinar o resumo da coleta, executar o pipeline se as únicas falhas forem as lacunas com ZIP e checksum corretos descritas abaixo. Para a coleta já realizada (`Itens: 240 | válidos: 216 | falhas: 24`), **não é necessário baixá-la novamente**:

```powershell
python run_pipeline.py --configuracao configuracoes/pre_processamento.json
```

O programa encerra com erro se faltar arquivo ou registro auditado, houver checksum divergente, duplicata, OHLCV inválido ou qualquer falha diferente das lacunas explicitamente registradas. Não inventa candles para preencher os 15 minutos ausentes. A primeira execução lê os ZIPs e pode demorar; a segunda verifica hashes dos arquivos processados já registrados e retorna o mesmo dataset. Cada mudança nas entradas, na configuração, nas versões de bibliotecas ou no código de processamento gera um novo identificador de dataset.

## Saídas e contrato para a Entrega 4

```text
dados/processados/{id}/
  manifesto_processamento.json
  grade_comum_utc.parquet
  candles/{PAR}/{15m|1h|4h|1d}.parquet
  amostras/principal/{PAR}/{granularidade}/{7d|14d}.parquet
  amostras/proximo_candle/{PAR}/{15m|1h|4h}/7d.parquet
  relatorios/cobertura_candles.csv
  relatorios/lacunas_15m.csv
  relatorios/contagens_folds.csv
  relatorios/volatilidade_dias_comuns.csv
  relatorios/cobertura_volatilidade.csv
  relatorios/volatilidade.md
```

Cada linha de `amostras` identifica `par`, `granularidade`, `tarefa`, `contexto_dias`, `horizonte_candles`, os índices de início/fim de contexto e do alvo **dentro do parquet de candles daquela mesma célula**, `contexto_inicio_utc`, `contexto_fim_utc`, `origem_utc`, `alvo_fim_utc`, os dois preços, retorno futuro, classe e indicador de empate. Os parquets de candles carregam explicitamente `par` e `granularidade`. Não alinhar parquets distintos por índices de linha. `montar_janela` checa identidade, timestamps e dimensões antes de ler a entrada.

O manifesto registra contrato, hashes da coleta e do código, versões de bibliotecas, dimensões 5/8, folds, arquivo e SHA-256 de cada saída. `lacunas_15m.csv` enumera os intervalos ausentes; sua soma deve coincidir com o manifesto da coleta. `cobertura_candles.csv` separa origens elegíveis por célula das removidas pela interseção comum; `contagens_folds.csv` mostra amostras e suporte de classes após a purga em cada bloco. Fold vazio é indisponível e não deve ser apresentado como score zero.

## Volatilidade das quatro moedas

O relatório calcula retornos entre fechamentos diários consecutivos e mantém somente os dias de retorno presentes nos quatro pares. Por ano do **candle negociado** (o candle de 31/12 termina em 01/01) e no período completo, registra número de dias comuns, desvio-padrão diário, anualizado por `sqrt(365)`, mediana e percentil 95 do retorno absoluto. `cobertura_volatilidade.csv` mostra também o número de retornos válidos individuais. A hipótese **BTC < ETH < BNB < XRP** deve ser comparada com essas medidas observadas: o papel econômico das moedas não determina previamente seu ranking.

## Verificações e critérios de aceite

Os testes locais não usam dados históricos nem treinam modelos:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q camada_dados pre_processamento run_coleta.py run_pipeline.py
```

**Conferido após a execução oficial:** 240 ZIPs inventariados; 24 com somente as lacunas descritas abaixo; 67 saídas com hashes íntegros; 280 ocorrências de candles ausentes nos quatro pares; 16 linhas de cobertura; 1.661 origens comuns; nenhum bloco de fold vazio ou sem alguma das classes; mesmos preços e rótulos entre resoluções da matriz principal, dentro de cada par. O [relatório de resultados](resultados_execucao_oficial.md) traz as quantidades e a análise da hipótese de volatilidade. Qualquer nova falha de integridade em execução posterior deve ser discutida com o orientador antes de alterar o protocolo.

## Achado da coleta oficial executada pelo pesquisador

O manifesto local registra 24 meses marcados `invalido` **exclusivamente** pela ausência de candles: os mesmos seis meses em cada um dos quatro pares. Todos os 24 ZIPs passaram na verificação do checksum oficial, e não houve duplicatas nem erros de OHLCV nesses registros. A quantidade ausente é de 70 candles de 15m por par, 280 ocorrências de par/candle no total. Isso não deve ser confundido com 280 timestamps distintos: as lacunas podem coincidir entre pares.

| Mês UTC | Candles de 15m ausentes por par |
|---|---:|
| 2021-02 | 5 |
| 2021-03 | 6 |
| 2021-04 | 28 |
| 2021-08 | 18 |
| 2021-09 | 8 |
| 2023-03 | 5 |

Repetir a mesma coleta baixa novamente arquivos que já correspondem aos checksums oficiais e não resolve essas ausências. A Entrega 3 preserva os ZIPs, registra os intervalos ausentes e rejeita blocos agregados e amostras cujo contexto ou alvo atravesse uma lacuna. A causa operacional dos candles faltantes não foi inferida a partir desse padrão.

Veja também a [visão visual](visao_visual.md) e os [resultados da execução oficial](resultados_execucao_oficial.md).
