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

### GPU com Mamba oficial via WSL2 (opcional, recomendado para treino final)

O modelo usa o `mamba-ssm` oficial automaticamente quando disponível. Caso contrário, cai para `modelo/mamba_minimal.py` (PyTorch puro, roda em CPU/Windows).

O `mamba-ssm` oficial (kernels CUDA otimizados) só funciona em **Linux/WSL2** com GPU NVIDIA. No Windows nativo, use o fallback PyTorch puro (CPU).

#### Pré-requisitos

- Windows 10/11 com **WSL2** instalado (`wsl --install` no PowerShell como admin, reiniciar)
- Ubuntu como distro WSL (`wsl --install -d Ubuntu`)
- **Python 3.12** no WSL (`/usr/bin/python3.12`)
- GPU NVIDIA com driver recente (testado com RTX 4050, driver 581.80)

#### Instalação (rodar dentro do WSL/Ubuntu)

O script `setup_wsl_mamba.sh` automatiza toda a instalação:

```bash
# No terminal do Ubuntu (não PowerShell):
cd /mnt/c/Users/<seu-usuario>/Documents/GitHub/CryptoCasting
sed -i 's/\r$//' setup_wsl_mamba.sh   # corrige quebras de linha Windows
bash setup_wsl_mamba.sh
```

O que o script faz:

1. Cria venv Python 3.12 no filesystem Linux (`~/.venvs/cc`) — evita a lentidão do `/mnt/c`
2. Instala **PyTorch 2.6.0 + CUDA 11.8**
3. Instala **causal-conv1d** e **mamba-ssm** via wheels pré-compilados do GitHub (sem precisar de `nvcc`)
4. Instala as dependências do `requirements.txt`
5. Aplica um patch no `__init__.py` do mamba-ssm (ignora `Mamba3`, que exige triton 3.5+)
6. Verifica se GPU + mamba-ssm estão funcionando

Para verificar a instalação a qualquer momento:

```bash
source ~/.venvs/cc/bin/activate
cd /mnt/c/Users/<seu-usuario>/Documents/GitHub/CryptoCasting
python test_mamba.py
```

#### Uso no dia a dia (sempre no terminal do Ubuntu)

```bash
source ~/.venvs/cc/bin/activate
cd /mnt/c/Users/<seu-usuario>/Documents/GitHub/CryptoCasting

python run_pipeline.py     # pipeline de dados
python run_treino.py       # treino Mamba na GPU
```

> **Importante:** o venv GPU fica em `~/.venvs/cc` (filesystem Linux). Não use o `.venv` do Windows para treino — ele não tem CUDA. O `.venv` do Windows serve apenas para testes rápidos em CPU.

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
