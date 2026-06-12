# Arquitetura do Sistema — CryptoCasting

## Visão Geral

O CryptoCasting é um sistema de previsão direcional de criptomoedas baseado na arquitetura Mamba. O projeto transforma dados brutos da Binance em previsões direcionais (alta/baixa), apresentadas ao usuário por meio de uma interface web interativa.

O objetivo científico é investigar se a arquitetura Mamba consegue identificar padrões temporais em séries históricas de criptomoedas, produzindo previsões superiores a um modelo ingênuo. O sistema é composto por um **backend em Python** responsável pela pipeline de dados e treinamento do modelo, e um **frontend em Next.js/TypeScript** responsável pela visualização dos resultados.

---

## Stack Tecnológica

### Linguagens

| Tecnologia | Versão | Uso |
|-----------|--------|-----|
| **Python** | 3.11+ | Linguagem do backend: pipeline de dados, treinamento do modelo Mamba, API |
| **TypeScript** | 5.x | Linguagem do frontend: tipagem estática sobre JavaScript, garantindo segurança nos contratos de dados e nos componentes de UI |

---

### Backend — Pipeline de Dados

| Tecnologia | Uso | Descrição |
|-----------|-----|-----------|
| **Binance API** | Fonte primária de dados | API pública da exchange Binance. Fornece dados OHLCV (Open, High, Low, Close, Volume) históricos via endpoint `get_historical_klines`. Não requer autenticação para dados de mercado |
| **python-binance** | Cliente Python para Binance | Biblioteca que encapsula a API REST da Binance. Utilizada para solicitar klines (candles) com parâmetros de par, intervalo e período. Conexão pública, sem necessidade de API key |
| **Pandas** | Manipulação de DataFrames | Biblioteca fundamental para tratamento tabular dos dados. Usada em todas as etapas da pipeline: leitura, limpeza, ordenação, cálculo de indicadores, merge incremental e exportação |
| **NumPy** | Operações numéricas e arrays | Usado para cálculos numéricos de baixo nível (operações vetoriais nos indicadores técnicos) e como formato de saída dos datasets finais (.npz) |
| **scikit-learn** | Normalização | Fornece `StandardScaler` e `MinMaxScaler` para normalização das features. O fit é feito apenas no conjunto de treino para evitar data leakage |

---

### Backend — Armazenamento

| Tecnologia | Uso | Descrição |
|-----------|-----|-----------|
| **Parquet** | Formato de dados intermediários | Formato colunar binário com compressão eficiente. Usado para persistir dados em cada etapa da pipeline (`brutos/`, `processados/`, `features/`, `normalizados/`). Preserva tipos (timestamps, floats) e é mais compacto que CSV |
| **NumPy .npz** | Formato dos datasets finais | Formato nativo do NumPy para persistir arrays multidimensionais. Usado na última etapa da pipeline para salvar as janelas temporais prontas para consumo pelo PyTorch |

---

### Backend — Modelo e Treinamento

| Tecnologia | Uso | Descrição |
|-----------|-----|-----------|
| **PyTorch** | Framework de deep learning | Framework principal para definição do modelo, DataLoader, loop de treinamento e inferência. Escolhido pela compatibilidade nativa com CUDA e com a biblioteca Mamba |
| **Mamba (mamba-ssm)** | Arquitetura do modelo | Modelo baseado em State Space Models (SSM). Alternativa aos Transformers que processa sequências de forma linear (O(n) ao invés de O(n²)). Capaz de capturar dependências temporais longas sem mecanismo de atenção, o que o torna eficiente para séries temporais extensas |
| **CUDA** | Aceleração por GPU | Toda a implementação é compatível com GPU CUDA. O treinamento e a inferência do Mamba são executados em GPU para viabilizar o processamento de sequências temporais longas |

---

### Frontend

| Tecnologia | Uso | Descrição |
|-----------|-----|-----------|
| **Next.js** | Framework React | Framework React com renderização do lado do servidor (SSR), geração estática (SSG) e roteamento baseado em arquivo. Fornece a estrutura base da aplicação web, incluindo API Routes para comunicação com o backend Python, otimização automática de bundling e suporte nativo a TypeScript |
| **React** | Biblioteca de UI | Biblioteca de construção de interfaces declarativas e componentizadas. Utilizada via Next.js para renderizar dashboards, gráficos, tabelas e formulários |
| **TypeScript** | Tipagem estática | Superset do JavaScript que adiciona tipagem estática ao projeto. Garante segurança nos contratos de dados entre frontend e backend (via interfaces/tipos), reduz bugs em runtime e melhora a experiência de desenvolvimento com autocompletion e refatoração segura |
| **ECharts** | Visualização de dados | Biblioteca de gráficos JavaScript de alto desempenho. Utilizada para renderizar candlesticks, curvas de treinamento, gráficos de accuracy, predições corretas/incorretas e evolução temporal dos erros. Suporta zoom, tooltip interativo e responsividade |

---

### Ferramentas de Desenvolvimento

| Tecnologia | Uso | Descrição |
|-----------|-----|-----------|
| **argparse** | CLI da pipeline | Módulo da stdlib Python usado no entry point (`run_pipeline.py`) para aceitar parâmetros como pares, período, janela e método de normalização via linha de comando |
| **logging** | Registro de execução | Módulo da stdlib Python usado em toda a pipeline para registrar progresso, warnings e erros. Saída simultânea em console e arquivo `pipeline.log` |

---

## Estrutura de Diretórios

```
CryptoCasting/
├── pipeline/                  # Módulo da pipeline de dados
│   ├── __init__.py
│   ├── config.py              # Parâmetros centralizados
│   ├── coleta.py              # Etapa 1 — Coleta de dados
│   ├── limpeza.py             # Etapa 2 — Limpeza e validação
│   ├── features.py            # Etapa 3 — Feature engineering
│   ├── normalizacao.py        # Etapa 4 — Normalização
│   └── janelas.py             # Etapa 5 — Construção de janelas
├── dados/                     # Dados persistentes em cada etapa
│   ├── brutos/                # Dados crus da Binance (.parquet)
│   ├── processados/           # Dados limpos e validados
│   ├── features/              # Dados com indicadores técnicos
│   ├── normalizados/          # Dados normalizados
│   └── janelas/               # Datasets finais (.npz por split)
├── frontend/                  # Aplicação Next.js
│   ├── src/
│   │   ├── app/               # Rotas (App Router)
│   │   ├── components/        # Componentes reutilizáveis
│   │   ├── lib/               # Utilitários e tipos TypeScript
│   │   └── styles/            # Estilos globais
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.js
├── docs/                      # Documentação
│   ├── arquitetura.md         # Este arquivo
│   └── pipeline.md            # Documentação detalhada da pipeline
├── run_pipeline.py            # Orquestrador / entry point
├── plano.md                   # Especificação do TCC
└── pipeline.log               # Log de execução
```

---

## Fluxo de Dados

```
Binance API
    │
    ▼
┌─────────────────────────────────┐
│  ETAPA 1 — COLETA (coleta.py)  │
│  Download OHLCV + incremental   │
└──────────────┬──────────────────┘
               │  dados/brutos/{PAR}.parquet
               ▼
┌─────────────────────────────────────┐
│  ETAPA 2 — LIMPEZA (limpeza.py)    │
│  Ordenar, deduplicar, validar       │
└──────────────┬──────────────────────┘
               │  dados/processados/{PAR}.parquet
               ▼
┌──────────────────────────────────────────┐
│  ETAPA 3 — FEATURE ENGINEERING           │
│  (features.py)                           │
│  SMA, RSI, MACD, Retornos, Volatilidade  │
└──────────────┬───────────────────────────┘
               │  dados/features/{PAR}.parquet
               ▼
┌──────────────────────────────────────────┐
│  ETAPA 4 — NORMALIZAÇÃO                  │
│  (normalizacao.py)                       │
│  StandardScaler / MinMaxScaler           │
│  Fit apenas no conjunto de treino        │
└──────────────┬───────────────────────────┘
               │  dados/normalizados/{PAR}.parquet
               ▼
┌──────────────────────────────────────────┐
│  ETAPA 5 — JANELAS TEMPORAIS             │
│  (janelas.py)                            │
│  Sliding windows + split temporal        │
│  70% treino / 15% validação / 15% teste  │
└──────────────┬───────────────────────────┘
               │  dados/janelas/{PAR}/
               │    ├── train.npz
               │    ├── val.npz
               │    └── test.npz
               ▼
         Pronto para PyTorch
```

> A documentação detalhada de cada etapa, incluindo funções, validações, schemas de entrada/saída e decisões de implementação, está em [docs/pipeline.md](pipeline.md).

---

## Decisões Arquiteturais

### Separação Backend / Frontend

O backend Python é responsável por tudo que envolve dados, ML e lógica científica. O frontend Next.js é responsável exclusivamente por apresentação e interação. Essa separação permite que cada camada evolua independentemente.

### Tipagem End-to-End

O uso de TypeScript no frontend garante que os contratos de dados com a API Python sejam verificados em tempo de compilação. Interfaces TypeScript espelham os schemas JSON do backend, detectando quebras de compatibilidade antes do deploy.

### Modularidade

Cada etapa da pipeline é um módulo Python independente com uma função `executar_*` como ponto de entrada. Módulos podem ser executados isoladamente ou combinados. Cada um lê da etapa anterior e escreve na próxima.

### Sem Valores Hardcoded

Todos os parâmetros da pipeline estão em `config.py`. Valores padrão podem ser sobrescritos via linha de comando ou chamada de função.

### Prevenção de Data Leakage

A normalização faz fit apenas no conjunto de treino. Os indicadores técnicos usam apenas dados passados (rolling, ewm com min_periods). A variável target usa shift(-1). O split temporal preserva a ordem cronológica.

### Rastreabilidade

Cada etapa salva seu resultado intermediário em disco, permitindo inspeção manual e reprocessamento a partir de qualquer ponto da pipeline.

### Extensibilidade

Novos indicadores podem ser adicionados em `features.py`. Novos métodos de normalização podem ser registrados no dict `SCALERS` em `normalizacao.py`. O tamanho da janela e os ratios de split são parametrizáveis. No frontend, novos gráficos e páginas podem ser adicionados como componentes React independentes.
