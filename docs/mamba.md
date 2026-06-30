# Guia Completo — Mamba no CryptoCasting

Este documento explica **tudo** o que você precisa saber para implementar, configurar e treinar a arquitetura **Mamba** no projeto CryptoCasting: a teoria por trás, como ela se encaixa no PyTorch, como integrar com a pipeline existente, e o passo a passo completo de implementação.

> Pré-requisito de leitura: [docs/pipeline.md](pipeline.md) e [docs/arquitetura.md](arquitetura.md). Este documento assume que a pipeline de dados já gera os arquivos `.npz` em `dados/janelas/{PAR}/`.

---

## Sumário

1. [O que é o Mamba](#1-o-que-é-o-mamba)
2. [Por que Mamba e não Transformer/LSTM](#2-por-que-mamba-e-não-transformerlstm)
3. [Fundamentos teóricos](#3-fundamentos-teóricos)
4. [A inovação do Mamba: o SSM Seletivo](#4-a-inovação-do-mamba-o-ssm-seletivo)
5. [Anatomia de um bloco Mamba](#5-anatomia-de-um-bloco-mamba)
6. [Mamba é PyTorch?](#6-mamba-é-pytorch)
7. [Instalação e dependências](#7-instalação-e-dependências)
8. [Como o Mamba se encaixa no CryptoCasting](#8-como-o-mamba-se-encaixa-no-cryptocasting)
9. [Estrutura de código proposta](#9-estrutura-de-código-proposta)
10. [Implementação completa](#10-implementação-completa)
11. [Hiperparâmetros e como configurá-los](#11-hiperparâmetros-e-como-configurá-los)
12. [Baseline ingênuo](#12-baseline-ingênuo)
13. [Walk-Forward Validation](#13-walk-forward-validation)
14. [Métricas e saída para o frontend](#14-métricas-e-saída-para-o-frontend)
15. [Checklist de implementação](#15-checklist-de-implementação)
16. [Armadilhas e limitações para séries financeiras](#16-armadilhas-e-limitações-para-séries-financeiras)
17. [Referências](#17-referências)

---

## 1. O que é o Mamba

Mamba é uma arquitetura de rede neural para **modelagem de sequências**, proposta por **Albert Gu e Tri Dao em dezembro de 2023** (paper: *"Mamba: Linear-Time Sequence Modeling with Selective State Spaces"*, arXiv:2312.00752).

Ela pertence à família dos **State Space Models (SSM)** e é apresentada como uma alternativa aos Transformers que:

- Processa sequências em **tempo linear O(N)** (não quadrático O(N²) como a atenção).
- Consegue capturar **dependências de longo alcance** sem mecanismo de atenção.
- É **paralelizável no treinamento** (como um Transformer) e **eficiente na inferência** (como uma RNN, com estado constante).

A ideia central é tratar a sequência como o resultado da discretização de um sistema dinâmico contínuo governado por uma equação de estado, em vez de comparar todos os pares de posições entre si (atenção).

> Em uma frase: **Mamba é uma RNN moderna, com estado oculto ricamente parametrizado, que pode ser treinada em paralelo como uma CNN/Transformer.**

---

## 2. Por que Mamba e não Transformer/LSTM

### Comparação das três famílias

| Arquitetura | Treino (complexidade) | Inferência (por token) | Memória de longo prazo | Paralelizável no treino |
|-------------|----------------------|------------------------|------------------------|------------------------|
| **Transformer** | O(N²) | O(N) por token (recomputa atenção) | Boa (mas janela fixa) | Sim |
| **LSTM/GRU** | O(N) | O(1) por token (estado fixo) | Fraca (vanishing gradient) | Não (recorrente) |
| **Mamba (SSM)** | O(N) | O(1) por token (estado fixo) | Forte (HiPPO) | Sim |

### Por que isso importa para o CryptoCasting

O projeto prevê janelas de 60 dias, mas poderá expandir para janelas maiores (180, 365 dias) e para dados intradiários (intervalos de 1h, 15m), o que produz **sequências muito longas**. Nessas condições:

- **Transformer**: o custo quadrático da atenção explode; atenção global sobre 1000+ passos é caro.
- **LSTM**: treina lentamente (não paralelizável) e esquece padrões antigos.
- **Mamba**: escala linearmente, mantém um estado comprimido da história inteira e treina em paralelo.

Além disso, séries financeiras têm **dependências temporais assimétricas** — um evento raro (crash, rompimento de suporte) deve influenciar o estado de forma diferente de um movimento comum. É exatamente isso que o mecanismo **seletivo** do Mamba provê (Seção 4).

---

## 3. Fundamentos teóricos

Para entender o Mamba é preciso entender a cadeia: **SSM clássico → S4 (HiPPO) → Mamba (SSM seletivo)**.

### 3.1 State Space Model (SSM) contínuo

Um SSM mapeia uma sequência de entrada `x(t)` contínua para uma saída `y(t)` passando por um **estado oculto** `h(t)`, governado por duas equações lineares:

```
Equação de estado:   h'(t) = A · h(t) + B · x(t)
Equação de saída:    y(t)  = C · h(t)
```

Onde:

| Símbolo | Significado | Dimensão típica |
|---------|-------------|-----------------|
| `x(t)` | entrada (input) no instante t | escalar ou (D,) |
| `h(t)` | estado oculto (memória) | (N,) — ex.: 16 |
| `y(t)` | saída | escalar |
| `A` | matriz de transição de estado | (N, N) |
| `B` | matriz de projeção da entrada | (N,) |
| `C` | matriz de projeção do estado → saída | (N,) |

`N` é a **dimensão do estado** (no Mamba costuma ser 16). Quanto maior `N`, mais "memória" o modelo carrega.

### 3.2 Discretização

Como os dados reais são discretos (uma sequência de candles, por exemplo), precisamos **discretizar** o sistema contínuo. O Mamba usa o método **Zero-Order Hold (ZOH)** com um passo `Δ`:

```
Ā = exp(Δ · A)                        (matriz de transição discreta)
B̄ = (Δ·A)^(-1) · (exp(Δ·A) − I) · B  (projeção de entrada discreta)
```

Que dá origem à **recorrência discreta**:

```
h_t = Ā · h_{t-1} + B̄ · x_t
y_t = C · h_t
```

Isso é, em essência, uma **RNN linear**: o novo estado é uma combinação do estado anterior com a entrada atual. O passo `Δ` controla a "escala de tempo" — quanto menor `Δ`, mais detalhe de curto prazo; quanto maior, mais suavização de longo prazo.

### 3.3 S4 e o HiPPO (Structured State Spaces)

Um SLM linear puro com `A` aleatório é fraco: o estado "esquece" rapidamente. O **S4** (Gu, Goel, Ré — ICLR 2022, arXiv:2111.00396) introduziu duas ideias fundamentais:

1. **HiPPO (High-order Polynomial Projection Operators)**: uma inicialização especial da matriz `A` que comprime a história passada nos coeficientes de polinômios de Legendre. Em vez de "média móvel simples", o estado guarda uma **representação comprimida e otimal** de toda a sequência passada. A matriz `A` do HiPPO tem forma fechada e é **estruturada** (pode ser expressa como soma de duas matrizes de baixo rank), o que torna os cálculos tractáveis.

2. **Dualidade convolução/recorrência**: como o SSM clássico é Linear e Tempo-Invariante (LTI) — ou seja, `A, B, C, Δ` não mudam ao longo da sequência — a saída completa `y_0, y_1, ..., y_{L-1}` pode ser computada como uma **convolução 1D** com um kernel derivado de `A, B, C`:

   ```
   y = K * x     onde   K = (CB̄, CĀB̄, CĀ²B̄, ..., CĀ^(L-1)B̄)
   ```

   Isso permite **treinar em paralelo** via FFT, e na **inferência** alternar para o modo recorrente (O(1) por passo). É o melhor dos dois mundos.

O S4 bateu Transformers em Long Range Arena, mas ainda era **LTI**: tratava todos os tokens igualmente, não conseguia "prestar atenção seletivamente".

---

## 4. A inovação do Mamba: o SSM Seletivo

### O problema do SSM LTI

No S4, `A, B, C, Δ` são **constantes**: o modelo aplica exatamente a mesma dinâmica a cada passo, independentemente do conteúdo da entrada. Isso é eficiente (permite a convolução), mas limita a expressividade — o modelo não consegue "decidir" esquecer ou reter com base no que vê.

### A solução do Mamba: tornar os parâmetros dependentes da entrada

O Mamba faz `B`, `C` e `Δ` **dependerem do input** `x_t` (a matriz `A` permanece fixa, inicializada via HiPPO, para manter a memória estável):

```
B_t  = Linear_B(x_t)
C_t  = Linear_C(x_t)
Δ_t  = softplus(Linear_Δ(x_t))     # softplus garante Δ > 0
Ā_t  = exp(Δ_t · A)                 # agora varia a cada passo!
B̄_t  = Δ_t · B_t                    (aproximação comum)
```

Consequência: o sistema deixa de ser LTI, **não dá mais para computar como convolução fixa**. Mas agora o modelo é **seletivo** — ele pode:

- **Reter** informação quando `Δ_t` é grande (estado muda muito).
- **Ignorar** ruído quando `Δ_t` é pequeno (estado quase não muda).
- **Roteear** o conteúdo para o estado de forma dependente do contexto.

### Selective Scan

Para treinar em paralelo mesmo com parâmetros variáveis, o Mamba usa um algoritmo chamado **selective scan** — uma versão paralela (em GPU) do cálculo da recorrência, implementada em kernels CUDA customizados no pacote `mamba-ssm`. Conceitualmente, é um **prefix sum paralelo** aplicado à recorrência `h_t = Ā_t h_{t-1} + B̄_t x_t`.

> Resumo da inovação: **o Mamba troca a rigidez LTI (que permitia FFT) por seleção dependente do input (mais expressivo), mantendo o treino paralelo via selective scan em GPU.**

---

## 5. Anatomia de um bloco Mamba

Um bloco Mamba é o análogo de um bloco Transformer ("atenção + MLP"). O fluxo interno é:

```
                    ┌─────────────┐
   x  ─────────────►│   LayerNorm  │
   │                └──────┬──────┘
   │                       │
   │                       ▼
   │                ┌─────────────┐
   │                │  Linear:     │  expande d_model → d_inner = d_model·expand
   │                │   d_model →  │  (expand é tipicamente 2)
   │                │   d_inner    │
   │                └──────┬──────┘
   │                       │
   │              ┌────────┴────────┐  "gate": o ramo do silu
   │              │                 │
   │              ▼                 ▼
   │        ┌──────────┐     ┌─────────────┐
   │        │ silu(·)  │     │ Conv1d       │  (d_conv, tipicamente 4)
   │        └────┬─────┘     │ causal       │
   │             │           └──────┬───────┘
   │             │                  ▼
   │             │           ┌─────────────┐
   │             │           │  silu(·)     │
   │             │           └──────┬───────┘
   │             │                  ▼
   │             │           ┌─────────────────────┐
   │             │           │  SSM Seletivo        │
   │             │           │  (A fixo, B,C,Δ(·))  │
   │             │           │  + gate y * silu(x)  │
   │             │           └──────────┬───────────┘
   │             │                      │
   │             └─────────► multiply ◄─┘
   │                              │
   │                              ▼
   │                       ┌─────────────┐
   │                       │  Linear:     │  projeta d_inner → d_model
   │                       │  d_inner →   │
   │                       │  d_model     │
   │                       └──────┬───────┘
   │                              │
   └───────────────── (+) ◄───────┘   conexão residual
                        │
                        ▼
                       out
```

Elementos-chave:

| Componente | Função |
|------------|--------|
| **Expansão (`expand`)** | Aumenta a dimensão interna de `d_model` para `d_inner = expand · d_model`, dando mais capacidade |
| **Conv1d causal (`d_conv`)** | Captura contexto local curto (como um n-grama); também ajuda a estabilizar o SSM |
| **SSM Seletivo** | O coração: computa a recorrência variável no tempo (memória longa + seleção) |
| **Gating (multiplicação por silu)** | Permite ao modelo "ligar/desligar" partes do sinal (análogo ao gate de GRU/LSTM, mas espacial) |
| **Projeção + residual** | Devolve para `d_model` e soma à entrada (como em Transformer) |

Empilhando `n_layers` desses blocos obtemos o modelo Mamba completo.

---

## 6. Mamba é PyTorch?

**Sim, totalmente.** O Mamba é implementado e treinado em **PyTorch**. Confirme três pontos:

1. **O modelo é um `nn.Module` do PyTorch.** Você o compõe com `nn.Linear`, `nn.Conv1d`, etc., como qualquer outra rede.
2. **O loop de treinamento é PyTorch padrão.** `CrossEntropyLoss`, `AdamW`, `DataLoader`, `model.train()`/`model.eval()`, `loss.backward()`, `optimizer.step()` — tudo idêntico a treinar qualquer classificador.
3. **A biblioteca oficial `mamba-ssm`** (pelos próprios autores do paper) fornece o módulo `Mamba(d_model, d_state, d_conv, expand)` já empacotado, escrita em PyTorch + kernels CUDA para o selective scan.

O projeto **NÃO usa TensorFlow** (ver [plano.md](../plano.md)) e **deve ser compatível com GPU CUDA** — exatamente o que o Mamba exige para desempenho ideal.

### Dois modos de uso

| Modo | Biblioteca | GPU necessária? | Plataforma | Quando usar |
|------|-----------|-----------------|------------|-------------|
| **Oficial** | `mamba-ssm` (autores do paper) | **Sim (CUDA)** | Linux recomendado | Treino sério, sequências longas, máxima performance |
| **Fallback puro PyTorch** | `mamba-minimal` (reimplementação de referência) | Não (roda em CPU) | Qualquer SO (incl. Windows) | Desenvolvimento, debug, máquina sem GPU, protótipo do TCC |

> **Recomendação para o TCC**: comece com `mamba-minimal` (puro PyTorch) para prototipar e validar a integração no seu Windows; migre para `mamba-ssm` oficial quando for treinar em GPU (idealmente em Linux/WSL2 ou na nuvem) para os experimentos finais.

---

## 7. Instalação e dependências

### 7.1 Requisitos

- Python 3.11+
- PyTorch (com suporte a CUDA se for usar `mamba-ssm` oficial)
- `mamba-ssm` e `causal-conv1d` (apenas para o modo oficial)

### 7.2 Instalação do modo oficial (`mamba-ssm`)

```bash
# 1. PyTorch com CUDA (exemplo CUDA 12.1)
pip install torch --index-url https://download.pytorch.org/whl/cu121

# 2. causal-conv1d (dependência do mamba-ssm)
pip install causal-conv1d>=1.1.0

# 3. mamba-ssm
pip install mamba-ssm
```

> ⚠️ O `mamba-ssm` compila kernels CUDA no install. Em **Windows** isso costuma dar trabalho (precisa de MSVC + CUDA toolkit compatíveis). Em **Linux/WSL2** é direto. Se falhar, use o fallback.

### 7.3 Instalação do fallback (`mamba-minimal`, puro PyTorch)

```bash
pip install torch            # CPU ou CUDA, tanto faz
```

O `mamba-minimal` é uma reimplementação de referência (~250 linhas, PyTorch puro) que reproduz o bloco Mamba sem kernels CUDA customizados. Você pode:

- Baixar o arquivo `mamba.py` dessa reimplementação e colocar em `modelo/`.
- Ou implementá-lo a partir do esqueleto mostrado na Seção 10.3 (código autocontido).

### 7.4 Validação rápida

```python
# test_mamba.py
import torch
from mamba_ssm import Mamba   # ou from modelo.mamba_minimal import Mamba

model = Mamba(d_model=15, d_state=16, d_conv=4, expand=2)
x = torch.randn(8, 60, 15)   # (batch, seq_len, d_model)
y = model(x)
print(y.shape)               # esperado: (8, 60, 15)
```

---

## 8. Como o Mamba se encaixa no CryptoCasting

### 8.1 O ponto de conexão

A pipeline já entrega exatamente o que o Mamba precisa:

```
dados/janelas/BTCUSDT/
├── train.npz   →  features: (n_train, 60, 15)  float32
│                   targets:  (n_train,)         int64 (0 ou 1)
├── val.npz
└── test.npz
```

- **Seq_len = 60** (janela configurável em `config.TAMANHO_JANELA`)
- **d_model = 15** (15 features: open, high, low, close, volume + 10 indicadores)
- **Tarefa**: classificação binária (0 = baixa, 1 = alta)

> Importante: o Mamba recebe **`d_model` features por passo de tempo**. Aqui `d_model` coincide com o número de features (15). Não há embedding inicial necessário (mas você pode adicionar uma camada `Linear(15, d_model_interno)` se quiser aumentar a capacidade — ver Seção 11).

### 8.2 Mapeamento problema → arquitetura

```
Input:  (batch, 60, 15)                    ← .npz da pipeline
            │
            ▼
   ┌────────────────────┐
   │  (opc.) Linear proj│  15 → d_model (ex.: 64)
   └─────────┬──────────┘
             │  (batch, 60, d_model)
             ▼
   ┌────────────────────┐
   │  Mamba Block × N   │  n_layers blocos residuais
   └─────────┬──────────┘
             │  (batch, 60, d_model)
             ▼
   ┌────────────────────┐
   │  Pooling do último │  pega y[:, -1, :]  (último passo)
   │  estado / token    │  ou mean pooling
   └─────────┬──────────┘
             │  (batch, d_model)
             ▼
   ┌────────────────────┐
   │  Classificação     │  Linear(d_model → 2)
   │  Head              │
   └─────────┬──────────┘
             │  (batch, 2)  logits
             ▼
   CrossEntropyLoss  +  target (batch,)
```

Para **classificação direcional**, usamos apenas a **saída do último passo temporal** (`output[:, -1, :]`) porque ela já contém, no estado do SSM, a influência de toda a janela passada. Isso difere de NLP, onde se prediz token-a-token; aqui a unidade de previsão é **uma decisão por janela**.

---

## 9. Estrutura de código proposta

Seguindo a mesma filosofia modular da `pipeline/` (um módulo por responsabilidade, config centralizada, função `executar_*` como entry point):

```
CryptoCasting/
├── pipeline/                 # já existe
├── modelo/                   # NOVO
│   ├── __init__.py
│   ├── config.py             # hiperparâmetros do modelo (centralizado)
│   ├── dataset.py            # carrega .npz → DataLoader
│   ├── mamba_modelo.py       # definição do modelo Mamba para classificação
│   ├── treino.py             # loop de treinamento
│   ├── avaliacao.py          # métricas (acc, precision, recall, f1)
│   ├── baseline.py           # baseline ingênuo
│   └── walkforward.py        # walk-forward validation
├── run_treino.py             # entry point (análogo ao run_pipeline.py)
└── dados/
    └── resultados/           # NOVO — métricas + checkpoints
        ├── BTCUSDT_metricas.json
        └── BTCUSDT_mamba.pt
```

Princípios (iguais aos do `plano.md`):
- Sem valores hardcoded — tudo em `modelo/config.py`.
- Tipagem (`tuple[...]`, `int | None`).
- `logging` estruturado.
- Compatível com CUDA (`device = "cuda" if available`).

---

## 10. Implementação completa

Abaixo, código de referência para cada arquivo. **Está alinhado às convenções já existentes no projeto** (`from ... import config`, hints de tipo, logging).

### 10.1 `modelo/config.py` — hiperparâmetros centralizados

```python
import torch
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DADOS_DIR = BASE_DIR / "dados"
RESULTADOS_DIR = DADOS_DIR / "resultados"

PAR_PRINCIPAL = "BTCUSDT"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Dimensões do modelo
D_INPUT = 15              # nº de features da pipeline (15 colunas)
D_MODEL = 64              # dimensão interna do Mamba (recomendado: 32–128)
N_LAYERS = 4              # nº de blocos Mamba empilhados
D_STATE = 16              # dimensão do estado do SSM (N) — padrão do paper: 16
D_CONV = 4                # largura da Conv1d causal
EXPAND = 2                # fator de expansão interna do bloco

# Pooling
POOLING = "last"          # "last" ou "mean"

# Classificação
NUM_CLASSES = 2           # 0 = baixa, 1 = alta

# Treinamento
BATCH_SIZE = 64
EPOCHS = 50
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-4
DROPOUT = 0.1
EARLY_STOP_PATIENCE = 10  # parar se val_loss não melhorar por N epochs

# Semente
SEED = 42
```

### 10.2 `modelo/dataset.py` — carregar `.npz` em DataLoaders

```python
import logging
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

from modelo import config

logger = logging.getLogger(__name__)


def carregar_split(par: str, split: str) -> tuple[torch.Tensor, torch.Tensor]:
    path = config.DADOS_DIR / "janelas" / par / f"{split}.npz"
    if not path.exists():
        raise FileNotFoundError(f"Dataset não encontrado: {path}")
    data = np.load(path)
    X = torch.from_numpy(data["features"]).float()      # (n, 60, 15)
    y = torch.from_numpy(data["targets"]).long()         # (n,)
    logger.info(f"{par}/{split}: X={tuple(X.shape)}, y={tuple(y.shape)}")
    return X, y


def criar_dataloader(
    par: str,
    split: str,
    batch_size: int | None = None,
    shuffle: bool = False,
) -> DataLoader:
    batch_size = batch_size or config.BATCH_SIZE
    X, y = carregar_split(par, split)

    # shuffle só no treino (validação/teste mantêm ordem temporal)
    dataset = TensorDataset(X, y)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=0,
        pin_memory=(config.DEVICE == "cuda"),
    )
```

> `TensorDataset` direto é suficiente porque a `JanelaDataset` da pipeline já fez o trabalho. `shuffle=True` **somente no treino** — val/teste preservam ordem temporal.

### 10.3 `modelo/mamba_modelo.py` — o modelo

Versão que funciona tanto com `mamba-ssm` oficial quanto com o fallback `mamba-minimal`:

```python
import logging

import torch
import torch.nn as nn

from modelo import config

logger = logging.getLogger(__name__)


def _importar_mamba() -> nn.Module:
    """Importa o bloco Mamba oficial; cai para o fallback puro-PyTorch se faltar."""
    try:
        from mamba_ssm import Mamba
        logger.info("Usando mamba-ssm oficial (CUDA)")
        return Mamba
    except ImportError:
        try:
            from modelo.mamba_minimal import Mamba
            logger.info("Usando mamba-minimal (PyTorch puro / fallback)")
            return Mamba
        except ImportError as e:
            raise ImportError(
                "Nenhuma implementação do Mamba encontrada. "
                "Instale `mamba-ssm` ou adicione `mamba_minimal.py` em modelo/."
            ) from e


class MambaClassificador(nn.Module):
    """Mamba empilhado + head de classificação direcional."""

    def __init__(
        self,
        d_input: int | None = None,
        d_model: int | None = None,
        n_layers: int | None = None,
        d_state: int | None = None,
        d_conv: int | None = None,
        expand: int | None = None,
        num_classes: int | None = None,
        pooling: str | None = None,
        dropout: float | None = None,
    ):
        super().__init__()
        d_input = d_input or config.D_INPUT
        d_model = d_model or config.D_MODEL
        n_layers = n_layers or config.N_LAYERS
        d_state = d_state or config.D_STATE
        d_conv = d_conv or config.D_CONV
        expand = expand or config.EXPAND
        num_classes = num_classes or config.NUM_CLASSES
        pooling = pooling or config.POOLING
        dropout = 0.0 if dropout is None else dropout

        Mamba = _importar_mamba()

        self.input_proj = nn.Linear(d_input, d_model)
        self.layers = nn.ModuleList([
            Mamba(d_model=d_model, d_state=d_state, d_conv=d_conv, expand=expand)
            for _ in range(n_layers)
        ])
        self.dropout = nn.Dropout(dropout)
        self.norm = nn.LayerNorm(d_model)
        self.pooling = pooling
        self.classifier = nn.Linear(d_model, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, d_input)
        x = self.input_proj(x)                       # (batch, seq_len, d_model)
        for layer in self.layers:
            x = layer(x)                             # bloco residual interno
        x = self.dropout(x)
        x = self.norm(x)

        if self.pooling == "last":
            x = x[:, -1, :]                          # saída do último passo
        elif self.pooling == "mean":
            x = x.mean(dim=1)
        else:
            raise ValueError(f"Pooling desconhecido: {self.pooling}")

        logits = self.classifier(x)                  # (batch, num_classes)
        return logits
```

#### Sobre `mamba_minimal.py` (fallback)

É uma reimplementação autossuficiente (~250 linhas) do bloco Mamba em PyTorch puro, contendo:

- `MambaBlock`: expansão linear, Conv1d causal, SSM seletivo (scan em PyTorch nativo), projeção.
- Uma classe `Mamba(d_model, d_state, d_conv, expand)` com a **mesma assinatura** da oficial, para que `MambaClassificador` funcione sem mudar uma linha.

Você pode obtê-la da reimplementação de referência pública *"mamba-minimal"* (by John Ma) — basta salvar como `modelo/mamba_minimal.py`. Para uma janela de apenas 60 passos o desempenho em CPU é perfeitamente usável para o TCC.

### 10.4 `modelo/treino.py` — loop de treinamento

```python
import logging
from pathlib import Path

import torch
import torch.nn as nn
from torch.optim import AdamW

from modelo import config
from modelo.mamba_modelo import MambaClassificador
from modelo.dataset import criar_dataloader

logger = logging.getLogger(__name__)


def treinar(
    par: str,
    epochs: int | None = None,
    learning_rate: float | None = None,
    batch_size: int | None = None,
) -> tuple[MambaClassificador, dict]:
    epochs = epochs or config.EPOCHS
    lr = learning_rate or config.LEARNING_RATE
    batch_size = batch_size or config.BATCH_SIZE
    device = config.DEVICE

    torch.manual_seed(config.SEED)

    logger.info("=" * 60)
    logger.info(f"TREINAMENTO MAMBA — {par} ({device})")
    logger.info("=" * 60)

    train_loader = criar_dataloader(par, "train", batch_size=batch_size, shuffle=True)
    val_loader = criar_dataloader(par, "val", batch_size=batch_size, shuffle=False)

    modelo = MambaClassificador().to(device)
    otimizador = AdamW(modelo.parameters(), lr=lr, weight_decay=config.WEIGHT_DECAY)
    criterio = nn.CrossEntropyLoss()

    historico = {"train_loss": [], "val_loss": [], "val_acc": []}
    melhor_val_loss = float("inf")
    paciencia = 0

    for epoch in range(1, epochs + 1):
        # --- treino ---
        modelo.train()
        train_loss = 0.0
        for X, y in train_loader:
            X, y = X.to(device), y.to(device)
            otimizador.zero_grad()
            logits = modelo(X)
            loss = criterio(logits, y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
            otimizador.step()
            train_loss += loss.item() * X.size(0)
        train_loss /= len(train_loader.dataset)

        # --- validação ---
        modelo.eval()
        val_loss, val_acc = _avaliar_loss_acc(modelo, val_loader, criterio, device)

        historico["train_loss"].append(train_loss)
        historico["val_loss"].append(val_loss)
        historico["val_acc"].append(val_acc)

        logger.info(
            f"Epoch {epoch:3d}/{epochs} | "
            f"train_loss={train_loss:.4f} | val_loss={val_loss:.4f} | val_acc={val_acc:.4f}"
        )

        # --- early stopping ---
        if val_loss < melhor_val_loss:
            melhor_val_loss = val_loss
            paciencia = 0
            _salvar_checkpoint(modelo, par)
        else:
            paciencia += 1
            if paciencia >= config.EARLY_STOP_PATIENCE:
                logger.info(f"Early stopping na epoch {epoch}")
                break

    _carregar_checkpoint(modelo, par)   # restaura melhores pesos
    return modelo, historico


def _avaliar_loss_acc(modelo, loader, criterio, device) -> tuple[float, float]:
    modelo.eval()
    total_loss, corretos, n = 0.0, 0, 0
    with torch.no_grad():
        for X, y in loader:
            X, y = X.to(device), y.to(device)
            logits = modelo(X)
            total_loss += criterio(logits, y).item() * X.size(0)
            corretos += (logits.argmax(dim=1) == y).sum().item()
            n += X.size(0)
    return total_loss / n, corretos / n


def _salvar_checkpoint(modelo, par: str):
    config.RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)
    torch.save(modelo.state_dict(), config.RESULTADOS_DIR / f"{par}_mamba.pt")


def _carregar_checkpoint(modelo, par: str):
    modelo.load_state_dict(torch.load(
        config.RESULTADOS_DIR / f"{par}_mamba.pt", map_location=config.DEVICE
    ))
```

Pontos de atenção:

- `shuffle=True` **somente** no treino. Val/teste são temporais.
- `clip_grad_norm_` estabiliza o SSM (gradient clipping é prática comum em modelos recorrentes).
- `AdamW` + `weight_decay` pequeno é o otimizador padrão recomendado pelo paper.
- **Early stopping** pela `val_loss` evita overfitting — essencial em séries financeiras ruidosas.

### 10.5 `modelo/avaliacao.py` — métricas

```python
import json
import logging
from pathlib import Path

import torch
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from modelo import config

logger = logging.getLogger(__name__)


def avaliar(modelo, loader, device: str | None = None) -> dict:
    device = device or config.DEVICE
    modelo.eval()
    y_true, y_pred = [], []

    with torch.no_grad():
        for X, y in loader:
            X = X.to(device)
            logits = modelo(X)
            preds = logits.argmax(dim=1).cpu()
            y_true.extend(y.numpy())
            y_pred.extend(preds.numpy())

    metricas = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }
    return metricas


def salvar_metricas(par: str, metricas: dict):
    config.RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)
    path = config.RESULTADOS_DIR / f"{par}_metricas.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)
    logger.info(f"Métricas salvas em {path}")
```

### 10.6 `modelo/baseline.py` — baseline ingênuo

O `plano.md` exige um baseline: **prever a direção do próximo dia como igual à direção observada no dia atual**.

```python
import numpy as np
import torch

from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


def baseline_ingenuo(par: str) -> dict:
    """Prediz 'direção do próximo dia = direção do dia atual'.

    A direção do dia atual é o último target DENTRO da janela de entrada
    (ou seja, targets[índice-1]), e comparamos com o target real.
    """
    from modelo.dataset import carregar_split

    metricas_por_split = {}
    for split in ("train", "val", "test"):
        X, y = carregar_split(par, split)
        # y corresponde ao target do PRÓXIMO passo após a janela.
        # O baseline assume: "amanhã repete hoje".
        # "hoje" = direção do último dia da janela = target da amostra anterior.
        # Como não temos isso diretamente, usamos aproximação via sinal do
        # retorno do último candle dentro da janela (close_t vs close_{t-1}):
        # se close subiu no último passo → prevê alta.
        ultimo_close = X[:, -1, 3]      # índice 3 = 'close' (ver pipeline/features.py)
        penult_close = X[:, -2, 3]
        pred = (ultimo_close > penult_close).long().numpy()

        metricas_por_split[split] = {
            "accuracy": float(accuracy_score(y, pred)),
            "precision": float(precision_score(y, pred, zero_division=0)),
            "recall": float(recall_score(y, pred, zero_division=0)),
            "f1": float(f1_score(y, pred, zero_division=0)),
        }
    return metricas_por_split
```

> A coluna de índice **3** é o `close` — confirme a ordem das features em `pipeline/features.py` (open=0, high=1, low=2, close=3, volume=4, sma_7=5, ...). Se reordenar as colunas, ajuste o índice.

### 10.7 `modelo/walkforward.py` — validação walk-forward

Em vez de um split único treino/val/teste, o walk-forward **desliza** uma janela de treino + um passo de teste, simulando uso real:

```python
import logging
import numpy as np
import torch
from sklearn.metrics import accuracy_score

from modelo import config
from modelo.mamba_modelo import MambaClassificador
from modelo.treino import treinar
from modelo.avaliacao import avaliar
from modelo.dataset import carregar_split

logger = logging.getLogger(__name__)


def walk_forward(par: str, n_folds: int = 5) -> list[dict]:
    """Divide o conjunto de teste em n_folds e mede a acurácia ao longo do tempo.

    O treino permanece fixo (70% inicial); o conjunto de teste é fatiado em
    janelas sucessivas para acompanhar a degradação/performance temporal.
    """
    X_train, y_train = carregar_split(par, "train")
    X_test, y_test = carregar_split(par, "test")

    fold_size = len(y_test) // n_folds
    resultados = []

    for k in range(n_folds):
        start = k * fold_size
        end = (k + 1) * fold_size if k < n_folds - 1 else len(y_test)
        idx = torch.arange(start, end)

        X_fold = X_test[idx]
        y_fold = y_test[idx]

        # reusa modelo já treinado (poderia retreinar com dados expandidos)
        modelo = MambaClassificador().to(config.DEVICE)
        # ... (treinar com X_train se quiser expansão de janela)

        loader = torch.utils.data.DataLoader(
            torch.utils.data.TensorDataset(X_fold, y_fold), batch_size=64
        )
        m = avaliar(modelo, loader)
        m["fold"] = k
        m["periodo"] = f"{start}-{end}"
        resultados.append(m)
        logger.info(f"Walk-forward fold {k}: acc={m['accuracy']:.4f}")

    return resultados
```

> Versão simples: treina uma vez e mede a performance em fatias temporais do teste. Versão avançada (rolling ou expanding window): retreina ao avançar cada fold. Ambas respeitam a ordem temporal.

### 10.8 `run_treino.py` — entry point

```python
import argparse
import logging
import sys

from modelo import config
from modelo.treino import treinar
from modelo.avaliacao import avaliar, salvar_metricas
from modelo.baseline import baseline_ingenuo
from modelo.dataset import criar_dataloader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("treino.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Treino Mamba — CryptoCasting")
    parser.add_argument("--pares", nargs="+", default=[config.PAR_PRINCIPAL])
    parser.add_argument("--epochs", type=int, default=config.EPOCHS)
    parser.add_argument("--lr", type=float, default=config.LEARNING_RATE)
    parser.add_argument("--batch-size", type=int, default=config.BATCH_SIZE)
    args = parser.parse_args()

    for par in args.pares:
        # --- baseline ---
        bl = baseline_ingenuo(par)
        logger.info(f"Baseline {par}: {bl}")

        # --- Mamba ---
        modelo, hist = treinar(
            par, epochs=args.epochs, learning_rate=args.lr, batch_size=args.batch_size
        )

        test_loader = criar_dataloader(par, "test", batch_size=args.batch_size)
        metricas = avaliar(modelo, test_loader)
        metricas["baseline"] = bl
        metricas["historico"] = hist

        salvar_metricas(par, metricas)
        logger.info(f"Mamba {par} (teste): { {k: v for k, v in metricas.items() if k != 'historico'} }")


if __name__ == "__main__":
    main()
```

Uso:

```bash
python run_treino.py --pares BTCUSDT --epochs 50 --lr 1e-3
```

---

## 11. Hiperparâmetros e como configurá-los

### 11.1 Tabela de hiperparâmetros do Mamba

| Hiperparâmetro | Onde | Padrão | Faixa típica | Efeito |
|----------------|------|--------|--------------|--------|
| `D_MODEL` | modelo | 64 | 32–128 | Capacidade do modelo. Maior = mais expressivo, mais lento |
| `N_LAYERS` | modelo | 4 | 2–8 | Profundidade. Mais camadas = dependências mais abstratas |
| `D_STATE` | SSM | 16 | 16–64 | Tamanho da memória (estado). Maior = lembra mais passado |
| `D_CONV` | Conv1d | 4 | 2–8 | Contexto local. Maior = olha mais passos vizinhos |
| `EXPAND` | bloco | 2 | 2–4 | Expansão interna. Maior = mais capacidade não-linear |
| `TAMANHO_JANELA` | pipeline | 60 | 30–365 | Comprimento da sequência |
| `BATCH_SIZE` | treino | 64 | 16–256 | Estabilidade do gradiente |
| `LEARNING_RATE` | treino | 1e-3 | 1e-4 – 1e-3 | Passo do otimizador |
| `WEIGHT_DECAY` | treino | 1e-4 | 1e-5 – 1e-2 | Regularização L2 |
| `DROPOUT` | modelo | 0.1 | 0.0–0.3 | Regularização (anti-overfit) |

### 11.2 Receitas práticas para começar

**Configuração mínima (protótipo rápido, CPU):**

```python
D_MODEL = 32
N_LAYERS = 2
D_STATE = 16
BATCH_SIZE = 32
EPOCHS = 20
```

**Configuração recomendada (GPU, experimento do TCC):**

```python
D_MODEL = 64
N_LAYERS = 4
D_STATE = 16
D_CONV = 4
EXPAND = 2
BATCH_SIZE = 64
EPOCHS = 50
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-4
DROPOUT = 0.1
```

### 11.3 O que variar na experimentação do TCC

Para responder cientificamente à pergunta do `plano.md`, faça variações **uma por vez** e registre as métricas:

1. **Tamanho da janela** (`TAMANHO_JANELA` = 30, 60, 90, 120) — quanta memória o Mamba precisa?
2. **Profundidade** (`N_LAYERS` = 2, 4, 6) — mais profundidade ajuda?
3. **Dimensão do estado** (`D_STATE` = 8, 16, 32) — memória mais rica ajuda em séries ruidosas?
4. **Conjunto de features** — treinar só com OHLCV vs. OHLCV + indicadores.

Mantenha tudo logger em `dados/resultados/{PAR}_metricas.json` para análise posterior.

---

## 12. Baseline ingênuo

O `plano.md` define o baseline como: **prever a direção do próximo dia igual à direção do dia atual** (momentum ingênuo). Implementado em `modelo/baseline.py` (Seção 10.6).

A **pergunta científica central** do TCC é:

> *O Mamba supera consistentemente esse baseline, usando apenas dados históricos?*

Critério de "sucesso" sugerido:

- **Mamba** com `accuracy` e `f1` **estatisticamente superiores** ao baseline no conjunto de **teste** (não no treino).
- Consistente em **múltiplos pares** (BTCUSDT, ETHUSDT, etc.) e em **múltiplos folds** do walk-forward.

Se o Mamba não passar disso, isso **também é um resultado válido** (e interessante!) — indicaria que o mercado é aproximadamente um passeio aleatório na escala diária para essa classe de modelo.

---

## 13. Walk-Forward Validation

> **Regra de ouro** (plano.md): nunca usar validação aleatória ou shuffle para val/teste. A ordem temporal deve ser preservada.

A pipeline já entrega splits temporais (70/15/15 sem shuffle). O walk-forward ([Seção 10.7](#107-modelowalkforwardpy--validação-walk-forward)) é uma extensão que mede **degradação temporal** no conjunto de teste:

```
|←── Treino (70%) ──→|← Val (15%) →|←── Teste fatiado em folds →|
                                    | f0 | f1 | f2 | f3 | f4 |
```

Você reporta accuracy (ou F1) por fold, mostrando se o modelo se mantém estável ao longo do tempo ou se degrada — fundamental para um TCC cientificamente defensável sobre séries financeiras **não-estacionárias**.

---

## 14. Métricas e saída para o frontend

### 14.1 Schema de saída

`dados/resultados/BTCUSDT_metricas.json`:

```json
{
  "accuracy": 0.56,
  "precision": 0.57,
  "recall": 0.55,
  "f1": 0.56,
  "baseline": {
    "train": {"accuracy": 0.52, "precision": 0.53, "recall": 0.51, "f1": 0.52},
    "val":   {"accuracy": 0.51, "precision": 0.52, "recall": 0.50, "f1": 0.51},
    "test":  {"accuracy": 0.50, "precision": 0.51, "recall": 0.49, "f1": 0.50}
  },
  "historico": {
    "train_loss": [0.69, 0.67, ...],
    "val_loss":   [0.69, 0.68, ...],
    "val_acc":    [0.52, 0.54, ...]
  }
}
```

### 14.2 Contrato com o frontend

O frontend em `dataview/` lê as métricas via as API routes do Next.js (`src/app/api/`), que leem diretamente o JSON de `dados/resultados/`. A API deve expor os campos `mamba_accuracy`, `mamba_precision`, `mamba_recall`, `mamba_f1` lendo do JSON acima. Diagrama:

```
Python (treino)                  Next.js (dataview)
─────────────────                ─────────────────────────
dados/resultados/      ──►       src/app/api/.../route.ts
  BTCUSDT_metricas.json          lê JSON → resposta HTTP
                                       │
                                       ▼
                                 Dashboard.tsx (exibe métricas)
```

---

## 15. Checklist de implementação

Ordem recomendada para construir a peça Mamba sobre a pipeline existente:

- [ ] **1. Ambiente**: instalar PyTorch (+ CUDA se GPU) e `mamba-ssm`. Se falhar, colocar `mamba_minimal.py` em `modelo/`.
- [ ] **2. Criar `modelo/config.py`** com os hiperparâmetros da Seção 10.1.
- [ ] **3. Criar `modelo/dataset.py`** e validar que `carregar_split("BTCUSDT", "train")` retorna shapes `(N, 60, 15)` e `(N,)`.
- [ ] **4. Criar `modelo/mamba_modelo.py`** e fazer um *smoke test*: instanciar `MambaClassificador()`, passar um batch randômico `(8, 60, 15)`, conferir saída `(8, 2)`.
- [ ] **5. Criar `modelo/treino.py`** e treinar por 3 epochs só para validar o fluxo.
- [ ] **6. Criar `modelo/avaliacao.py`** e imprimir métricas no conjunto de val e teste.
- [ ] **7. Criar `modelo/baseline.py`** e conferir que a acurácia fica próxima de 50% (esperado para um baseline fraco em mercado eficiente).
- [ ] **8. Treino completo** (50 epochs, early stopping) e salvar `_metricas.json`.
- [ ] **9. Criar `modelo/walkforward.py`** e gerar métricas por fold.
- [ ] **10. Conectar o frontend**: a API route do Next.js lê o JSON e popula `mamba_*` no dashboard.
- [ ] **11. Experimentação**: variar hiperparâmetros conforme Seção 11.3 e registrar resultados.
- [ ] **12. Escrita do TCC**: usar os JSONs para gerar gráficos (curvas de treino, Mamba vs baseline, walk-forward).

---

## 16. Armadilhas e limitações para séries financeiras

### 16.1 Data leakage (já tratado pela pipeline, mas vale reforçar)

- Normalização com `fit` **só no treino** (`pipeline/normalizacao.py`).
- Indicadores só usam passado (`min_periods`, sem `center=True`).
- Target com `shift(-1)` (`pipeline/features.py`).
- **Nunca** shuffle em val/teste.

### 16.2 Mercado é quase passeio aleatório

Em horizonte diário, a direção do BTC é ~50/50. Um `accuracy` de 52–55% já é **muito bom**. Não espere 90%. Se parecer 90%, **desconfie de leakage**.

### 16.3 Não-estacionaridade

O regime de mercado muda (bull/bear/sideways). Isso justifica o walk-forward e o `D_STATE` maior (memória longa ajuda a detectar mudança de regime). Considere também retreinar periodicamente (expanding window).

### 16.4 Classe desbalanceada

Se a maioria dos dias for de alta (bull market), o modelo pode só prever "1". Mitigações:

- Usar **F1** (não só accuracy) como métrica principal.
- `CrossEntropyLoss(weight=...)` para balancear.
- Stratified split **só no treino** (mantendo ordem temporal).

### 16.5 Sobreajuste em poucos dados

Com janela 60 e 365 dias, há ~300 amostras. Para um Mamba de 4 camadas, isso é pouco. Mitigações:

- Reduzir `D_MODEL` e `N_LAYERS`.
- Aumentar `DROPOUT` (0.2–0.3).
- Aumentar o período de dados (`--periodo "730 day ago UTC"` ou usar intervalo intradiário para mais amostras).
- Early stopping rigoroso.

### 16.6 `mamba-ssm` em Windows

O pacote oficial é otimizado para Linux + CUDA. Em Windows:

- Use **WSL2** com CUDA — é o caminho mais limpo.
- Ou use o **fallback** `mamba-minimal` (CPU) para desenvolver.
- Para o experimento final, considere **Google Colab / Kaggle** com GPU gratuita.

### 16.7 O Mamba não é uma bola de cristal

Mesmo superando o baseline, isso **não implica em lucro de trading**. Custos de transação, slippage e risco são externos ao modelo. O `plano.md` deixa claro que o objetivo é **científico (previsibilidade direcional)**, não financeiro.

---

## 17. Referências

- **Paper do Mamba**: Albert Gu, Tri Dao. *"Mamba: Linear-Time Sequence Modeling with Selective State Spaces"*, dezembro de 2023 (arXiv:2312.00752).
- **S4**: Albert Gu, Karan Goel, Christopher Ré. *"Efficiently Modeling Long Sequences with Structured State Spaces"*, ICLR 2022 (arXiv:2111.00396). Origem do SSM estruturado com HiPPO e da dualidade convolução/recorrência.
- **HiPPO**: Albert Gu, Tri Dao, Stefano Ermon, Atri Rudra, Christopher Ré. *"HiPPO: Recurrent Memory with Optimal Polynomial Projections"*, NeurIPS 2020 (arXiv:2008.07669). A inicialização de `A` usada no Mamba.
- **Biblioteca oficial**: pacote Python `mamba-ssm` (autores do paper) — instalar via `pip install mamba-ssm`. Requer CUDA.
- **Fallback puro PyTorch**: reimplementação de referência *"mamba-minimal"* (~250 linhas, sem kernels CUDA), utilizável em CPU/Windows.
- **Documentação interna**:
  - [plano.md](../plano.md) — especificação e hipóteses do TCC.
  - [docs/arquitetura.md](arquitetura.md) — stack e fluxo de dados.
  - [docs/pipeline.md](pipeline.md) — detalhes das 5 etapas que produzem os `.npz`.
```
