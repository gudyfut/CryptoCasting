# CryptoCasting

Projeto de TCC (Murilo R. F. Monferrari) — sistema de previsão direcional de criptomoedas com a arquitetura **Mamba** (State Space Models).

O objetivo científico é investigar se o Mamba consegue identificar padrões temporais em séries históricas de criptomoedas, produzindo previsões direcionais (alta/baixa) superiores a um modelo de referência ingênuo.

---

## Stack

- **Python 3.11+** — backend: pipeline de dados, treinamento do Mamba, API
- **PyTorch** — framework de deep learning
- **Mamba (mamba-ssm)** — arquitetura do modelo (com fallback puro PyTorch)
- **Pandas / NumPy / scikit-learn** — processamento e métricas
- **Next.js + TypeScript (dataview/)** — frontend de visualização

---

## Estrutura

```
CryptoCasting/
├── pipeline/        # Pipeline de dados (coleta → limpeza → features → norm → janelas)
├── modelo/          # Modelo Mamba (dataset, treino, avaliação, baseline, walk-forward)
├── dados/           # Dados em cada etapa (brutos, processados, features, normalizados, janelas, resultados)
├── dataview/        # Frontend Next.js
├── docs/            # Documentação (arquitetura.md, pipeline.md, mamba.md)
├── run_pipeline.py  # Orquestrador da pipeline de dados
├── run_treino.py    # Orquestrador do treino Mamba
└── requirements.txt
```

---

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

pip install -r requirements.txt
```

### GPU (opcional, recomendado para treino final)

O modelo usa o `mamba-ssm` oficial automaticamente quando disponível. Caso contrário, cai para `modelo/mamba_minimal.py` (PyTorch puro, roda em CPU/Windows). Para ativar GPU (Linux/WSL2):

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install causal-conv1d>=1.1.0 mamba-ssm
```

---

## Uso — Pipeline de dados

Gera os datasets `.npz` prontos para o PyTorch a partir da Binance API.

```bash
# Pipeline completa (padrão: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT)
python run_pipeline.py

# Customizar pares e período
python run_pipeline.py --pares BTCUSDT --periodo "730 day ago UTC"

# Janela e normalização
python run_pipeline.py --janela 30 --normalizacao minmax

# Reprocessar sem baixar de novo
python run_pipeline.py --sem-coleta
```

Saída: `dados/janelas/{PAR}/{train,val,test}.npz` com shape `(n_amostras, janela, 15)`.

---

## Uso — Treinamento Mamba

```bash
# Padrão (BTCUSDT, 50 epochs, early stopping)
python run_treino.py

# Customizar
python run_treino.py --pares BTCUSDT ETHUSDT --epochs 80 --lr 5e-4 --batch-size 32

# Sem walk-forward (mais rápido)
python run_treino.py --sem-walkforward
```

A execução treina o Mamba, computa o baseline ingênuo (momentum) e gera:

- `dados/resultados/{PAR}_mamba.pt` — melhores pesos (checkpoint)
- `dados/resultados/{PAR}_metricas.json` — métricas Mamba + baseline + histórico + walk-forward

### Hiperparâmetros

Edite `modelo/config.py`:

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `D_MODEL` | 64 | Dimensão interna do Mamba |
| `N_LAYERS` | 4 | Número de blocos Mamba |
| `D_STATE` | 16 | Dimensão do estado do SSM (memória) |
| `BATCH_SIZE` | 64 | Tamanho do batch |
| `EPOCHS` | 50 | Épocas máximas |
| `LEARNING_RATE` | 1e-3 | Learning rate (AdamW) |
| `DROPOUT` | 0.1 | Regularização |

---

## Rodar o frontend

```bash
cd dataview
npm install
npm run dev
```

---

## Documentação

- [docs/arquitetura.md](docs/arquitetura.md) — stack, fluxo de dados e decisões arquiteturais
- [docs/pipeline.md](docs/pipeline.md) — detalhes das 5 etapas da pipeline de dados
- [docs/mamba.md](docs/mamba.md) — guia completo do Mamba (teoria, implementação, hiperparâmetros, experimentação)
- [plano.md](plano.md) — especificação e hipóteses do TCC

---

## Licença

Ver [LICENSE](LICENSE).
