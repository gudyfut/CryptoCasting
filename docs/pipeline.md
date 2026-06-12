# Pipeline de Dados — CryptoCasting

Documentação detalhada de cada etapa da pipeline de processamento de dados.

---

## Configuração Centralizada (`pipeline/config.py`)

Todos os parâmetros do sistema estão centralizados em um único arquivo de configuração. Nenhum valor é espalhado pelo código.

| Parâmetro | Valor padrão | Descrição |
|-----------|-------------|-----------|
| `PARES` | BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT | Lista de pares negociáveis |
| `PAR_PRINCIPAL` | BTCUSDT | Par prioritário do TCC |
| `INTERVALO_CANDLES` | `1d` | Intervalo dos candles (diário) |
| `PERIODO_HISTORICO` | `365 day ago UTC` | Período de dados históricos |
| `MAX_RETRIES` | 3 | Tentativas em caso de falha na API |
| `RETRY_DELAY_SEGUNDOS` | 10 | Segundos entre tentativas |
| `RATE_LIMIT_DELAY_SEGUNDOS` | 0.5 | Pausa entre requisições |
| `SMA_PERIODOS` | [7, 21, 50] | Períodos das médias móveis simples |
| `RSI_PERIODO` | 14 | Período do RSI |
| `MACD_RAPIDO` | 12 | EMA rápida do MACD |
| `MACD_LENTO` | 26 | EMA lenta do MACD |
| `MACD_SINAL` | 9 | Linha de sinal do MACD |
| `VOLATILIDADE_JANELA` | 21 | Janela da volatilidade móvel |
| `TAMANHO_JANELA` | 60 | Tamanho da sliding window |
| `NORMALIZADOR` | `standard` | Método de normalização |
| `TRAIN_RATIO` | 0.70 | Proporção do conjunto de treino |
| `VAL_RATIO` | 0.15 | Proporção do conjunto de validação |
| `TEST_RATIO` | 0.15 | Proporção do conjunto de teste |
| `DIRECAO_ALTA` | 1 | Label para fechamento em alta |
| `DIRECAO_BAIXA` | 0 | Label para fechamento em baixo |

---

## Etapa 1 — Coleta de Dados (`pipeline/coleta.py`)

### Responsabilidades

- Conectar à Binance API pública (sem necessidade de API key)
- Baixar dados OHLCV (Open, High, Low, Close, Volume) com timestamp
- Suportar atualização incremental (apenas dados novos)
- Persistir dados em formato Parquet

### Funções

| Função | Descrição |
|--------|-----------|
| `carregar_bruto(par)` | Carrega o Parquet bruto existente para um par |
| `salvar_bruto(par, df)` | Persiste um DataFrame como Parquet em `dados/brutos/` |
| `ultimo_timestamp(par)` | Retorna o timestamp mais recente de um dataset existente |
| `coletar_par(client, par, intervalo, periodo, incremental)` | Baixa klines da Binance com retry automático |
| `mesclar_incremental(par, df_novo)` | Combina dados existentes com novos, removendo duplicatas |
| `executar_coleta(pares, intervalo, periodo, incremental)` | Orquestra a coleta para todos os pares |

### Mecanismo de Atualização Incremental

```
1. Verifica se dados/brutos/{PAR}.parquet existe
2. Se existe:
   a. Lê o último timestamp do arquivo
   b. Solicita à Binance apenas dados a partir desse timestamp
   c. Filtra registros com timestamp > último conhecido
   d. Concatena ao dataset existente
   e. Remove duplicatas por timestamp (keep="last")
3. Se não existe:
   a. Baixa o período completo configurado
```

### Tratamento de Erros

- Retry automático com até 3 tentativas por par
- Backoff exponencial em caso de rate limit (delay * tentativa * 2)
- Delay fixo de 10s para outros erros de API
- Pausa de 0.5s entre requisições para evitar rate limiting

### Formato de Saída

```
dados/brutos/BTCUSDT.parquet

Colunas:
  timestamp  | open  | high  | low   | close | volume
  2025-06-11 | 85000 | 86500 | 84200 | 86100 | 1234.5
```

---

## Etapa 2 — Limpeza e Validação (`pipeline/limpeza.py`)

### Responsabilidades

- Ordenar registros por timestamp
- Remover duplicatas por timestamp
- Tratar valores ausentes (drop de linhas com NaN em OHLCV)
- Garantir consistência temporal
- Validar integridade dos dados OHLCV

### Funções

| Função | Descrição |
|--------|-----------|
| `limpar(df)` | Pipeline de limpeza completa |
| `_validar_consistencia(df)` | Verifica integridade dos dados |
| `executar_limpeza(par)` | Carrega bruto, limpa e salva processado |

### Validações Realizadas

1. **Ordenação temporal**: Dados são ordenados por timestamp antes de qualquer processamento

2. **Detecção de duplicatas**: Registros com mesmo timestamp são identificados e removidos (mantém o primeiro)

3. **Valores ausentes**: Linhas com NaN nas colunas OHLCV ou volume são removidas

4. **Gaps temporais**: O sistema detecta e reporta gaps na série temporal (diferenças entre timestamps consecutivos que divergem do intervalo mais frequente)

5. **Consistência OHLCV**: Assertions que verificam:
   - High >= Low
   - High >= Open
   - High >= Close
   - Low <= Open
   - Low <= Close
   - Volume >= 0

### Formato de Saída

Mesmo esquema da entrada, porém limpo e validado:

```
dados/processados/BTCUSDT.parquet
```

---

## Etapa 3 — Feature Engineering (`pipeline/features.py`)

### Responsabilidades

- Gerar indicadores técnicos a partir dos dados OHLCV
- Garantir que nenhum indicador utilize dados futuros (look-ahead bias)
- Calcular a variável target (direção do próximo fechamento)

### Indicadores Gerados

#### Médias Móveis Simples (SMA)

| Indicador | Período | Descrição |
|-----------|---------|-----------|
| `sma_7` | 7 | Média curta — captura tendência recente |
| `sma_21` | 21 | Média intermediária |
| `sma_50` | 50 | Média longa — captura tendência macro |

Calculadas via `rolling(window=p, min_periods=p)` sobre o preço de fechamento. As primeiras N linhas (onde N é o período) ficam com NaN, o que é esperado e representa a janela mínima necessária para o cálculo.

#### RSI (Relative Strength Index)

| Indicador | Período |
|-----------|---------|
| `rsi_14` | 14 |

Calculado usando a abordagem Wilder (EWM com alpha=1/14). O RSI varia de 0 a 100 e indica sobrecompra (>70) ou sobrevenda (<30).

#### MACD (Moving Average Convergence Divergence)

| Indicador | Descrição |
|-----------|-----------|
| `macd` | Diferença entre EMA(12) e EMA(26) |
| `macd_signal` | EMA(9) do MACD |
| `macd_hist` | Histograma (MACD - Signal) |

#### Retornos

| Indicador | Descrição |
|-----------|-----------|
| `retorno_diario` | Variação percentual do close: `(close_t - close_{t-1}) / close_{t-1}` |
| `retorno_acumulado` | Soma cumulativa dos retornos diários |

#### Volatilidade

| Indicador | Período | Descrição |
|-----------|---------|-----------|
| `volatilidade_21` | 21 | Desvio padrão móvel dos retornos diários |

### Variável Target

```python
direcao = 1  se close(t+1) > close(t)  (alta)
direcao = 0  se close(t+1) <= close(t) (baixa)
```

Calculada via `shift(-1)`. A última linha do dataset recebe NaN pois não há fechamento seguinte conhecido. Essa linha é removida na etapa seguinte (normalização).

### Funções

| Função | Descrição |
|--------|-----------|
| `sma(df, periodos)` | Calcula SMAs para múltiplos períodos |
| `rsi(df, periodo)` | Calcula o RSI via Wilder smoothing |
| `macd(df, rapido, lento, sinal)` | Calcula MACD, Signal e Histograma |
| `retornos(df)` | Calcula retorno diário e acumulado |
| `volatilidade(df, janela)` | Calcula volatilidade móvel |
| `gerar_features(df)` | Aplica todos os indicadores e calcula a direção |
| `executar_feature_engineering(par)` | Pipeline completa de feature engineering |

### Schema de Saída

```
dados/features/BTCUSDT.parquet

Colunas (15 features + timestamp + target):
  timestamp | open | high | low | close | volume
  sma_7 | sma_21 | sma_50
  rsi_14
  macd | macd_signal | macd_hist
  retorno_diario | retorno_acumulado
  volatilidade_21
  direcao  ← target (0 ou 1)
```

---

## Etapa 4 — Normalização (`pipeline/normalizacao.py`)

### Responsabilidades

- Normalizar as features numéricas
- Evitar data leakage (fit apenas no conjunto de treino)
- Suportar múltiplos métodos de normalização

### Prevenção de Data Leakage

Este é um ponto crítico da pipeline. A normalização é realizada da seguinte forma:

```
1. Identifica o ponto de corte do treino (70% dos dados)
2. Seleciona apenas as linhas do conjunto de treino
3. Faz o FIT do scaler apenas nessas linhas
4. Aplica o TRANSFORM em todos os dados (treino + validação + teste)
```

Isso garante que nenhuma informação do futuro (validação/teste) vaze para as estatísticas de normalização.

### Métodos Suportados

| Método | Classe | Descrição |
|--------|--------|-----------|
| `standard` | `StandardScaler` | Z-score: (x - media) / desvio. Centro em 0, variância 1 |
| `minmax` | `MinMaxScaler` | Escala para [0, 1]. Preserva a distribuição original |

A escolha é feita via `config.NORMALIZADOR` ou argumento `--normalizacao` no entry point. Novos métodos podem ser adicionados ao dict `SCALERS`.

### O que é normalizado

Apenas as colunas de features. As colunas `timestamp` e `direcao` (target) são preservadas intactas.

### Funções

| Função | Descrição |
|--------|-----------|
| `normalizar(df, metodo, train_ratio)` | Normaliza com prevenção de data leakage. Retorna (df_norm, scaler) |
| `executar_normalizacao(par, metodo)` | Carrega features, remove NaN do target, normaliza e salva |

### Schema de Saída

```
dados/normalizados/BTCUSDT.parquet

Mesmas colunas de features, porém com valores normalizados.
Linhas com direcao=NaN são removidas antes da normalização.
```

---

## Etapa 5 — Janelas Temporais (`pipeline/janelas.py`)

### Responsabilidades

- Construir sliding windows para entrada do modelo
- Realizar split temporal (sem shuffle)
- Gerar datasets PyTorch prontos para treinamento
- Persistir em formato NumPy (.npz)

### Sliding Windows

Dado um dataset com N registros e um tamanho de janela W:

```
Amostra 0: features[0:W]   → target[W]
Amostra 1: features[1:W+1] → target[W+1]
Amostra 2: features[2:W+2] → target[W+2]
...
Amostra i: features[i:i+W] → target[i+W]
```

Cada amostra de entrada tem shape `(W, F)` onde:
- W = tamanho da janela (padrão: 60)
- F = número de features (15)

O target é a direção (0 ou 1) do registro imediatamente após a janela.

### Split Temporal

A separação dos dados preserva a ordem temporal, simulando condições reais:

```
|←────────── Treino (70%) ──────────→|← Val (15%) →|← Teste (15%) →|
```

Não há shuffle. Não há validação aleatória. Isso é fundamental para a integridade científica do experimento.

### JanelaDataset

Classe que herda de `torch.utils.data.Dataset`, encapsulando:

- `features`: Tensor float de shape `(n_amostras, janela, n_features)`
- `targets`: Tensor long de shape `(n_amostras,)` com valores 0 ou 1
- `indices`: Array de índices originais para rastreabilidade

Compatível diretamente com `torch.utils.data.DataLoader`.

### Funções

| Função | Descrição |
|--------|-----------|
| `criar_janelas(df, tamanho_janela)` | Cria arrays X, y, indices a partir do DataFrame |
| `split_temporal(X, y, indices, train_ratio, val_ratio)` | Divide em treino/validação/teste temporal |
| `executar_janelas(par, tamanho_janela)` | Pipeline completa de janelas para um par |

### Formato de Saída

```
dados/janelas/BTCUSDT/
├── train.npz   (features: float32, targets: int64, indices: int64)
├── val.npz
└── test.npz
```

Cada arquivo `.npz` contém:
- `features`: shape `(n_amostras, 60, 15)`
- `targets`: shape `(n_amostras,)`
- `indices`: shape `(n_amostras,)`

---

## Orquestrador (`run_pipeline.py`)

O entry point da pipeline. Coordena a execução sequencial de todas as etapas.

### Fluxo de Execução

```
1. Coleta de dados (todos os pares de uma vez)
2. Para cada par:
   a. Limpeza
   b. Feature Engineering
   c. Normalização
   d. Construção de Janelas
3. Relatório final com contagem de amostras por split
```

### Linha de Comando

```bash
# Pipeline completa com valores padrão
python run_pipeline.py

# Apenas BTCUSDT com período customizado
python run_pipeline.py --pares BTCUSDT --periodo "730 day ago UTC"

# Janela de 30 dias e normalização MinMax
python run_pipeline.py --janela 30 --normalizacao minmax

# Forçar coleta completa (ignora dados existentes)
python run_pipeline.py --completo

# Pular coleta (reprocessa dados já baixados)
python run_pipeline.py --sem-coleta

# Modo debug
python run_pipeline.py --debug
```

### Argumentos Disponíveis

| Argumento | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `--pares` | list | config.PARES | Lista de pares para processar |
| `--intervalo` | str | `1d` | Intervalo de candles |
| `--periodo` | str | `365 day ago UTC` | Período histórico |
| `--janela` | int | 60 | Tamanho da sliding window |
| `--normalizacao` | str | `standard` | Método: `standard` ou `minmax` |
| `--completo` | flag | — | Forçar coleta completa |
| `--sem-coleta` | flag | — | Pular etapa de coleta |
| `--debug` | flag | — | Ativar logging detalhado |

---

## Formato de Armazenamento

Todos os dados intermediários são salvos em **Parquet** por oferecer:

- Compressão eficiente (menor que CSV)
- Preservação de tipos (timestamps, floats)
- Leitura rápida com pandas
- Suporte a colunas aninhadas (futuro)

Apenas os datasets finais (janelas) são salvos em **NumPy (.npz)** por serem o formato nativo de entrada do PyTorch.
