# Estrutura do Modelo

## Visão Geral

A pasta `modelo/` contém todo o código de machine learning: arquitetura, treinamento, avaliação, e geração de previsões. A pipeline de dados (`pipeline/`) produz arquivos `.npz` que o `modelo/` consome. O orquestrador `run_treino.py` coordena tudo.

```
run_treino.py  ← você roda isto
    │
    ├── modelo/treino.py        treina o modelo
    ├── modelo/avaliacao.py     mede performance
    ├── modelo/baseline.py      compara com naive
    ├── modelo/walkforward.py   valida no tempo
    └── modelo/previsao.py      gera previsões para o frontend
```

## Arquivos e Responsabilidades

### Infraestrutura compartilhada (independente da arquitetura)

| Arquivo | O que faz | Interfere no treino? |
|---|---|---|
| `config.py` | Hiperparâmetros: `D_INPUT`, `D_MODEL`, `N_LAYERS`, `DROPOUT`, `LEARNING_RATE`, `BATCH_SIZE`, `EPOCHS`, `SEED`, `DEVICE`. **Fonte da verdade.** | **Sim** — define o tamanho do modelo, taxa de aprendizado, regularização |
| `dataset.py` | Carrega `.npz` → `DataLoader`. Duas funções: `carregar_split` (3 classes) e `carregar_split_direcional` (2 classes, drop NEUTRO). | Não — só carrega dados |
| `treino.py` | Loop de treinamento: forward, backward, checkpoint, early stopping, scheduler. | **Sim** — é o treino em si |
| `avaliacao.py` | Funções de avaliação: `avaliar` (acc/f1), `avaliar_seletivo` (por confiança), `avaliar_trade` (TP/SL expectancy), `avaliar_regime` (por regime de vol), `salvar_metricas`. | Não — só mede |
| `baseline.py` | Baseline ingênuo (momentum: prevê direção do último candle). Não usa modelo. | Não |
| `walkforward.py` | Divide o teste em 5 fatias temporais e mede acurácia em cada uma. Mostra se performance degrada no tempo. | Não |
| `previsao.py` | Roda o modelo no teste, gera `{par}_{nome}_previsoes.json` para o frontend. Resolve timestamps via join. | Não |

### Arquitetura Mamba (modelo atual)

| Arquivo | O que faz |
|---|---|
| `mamba_modelo.py` | Define `MambaClassificador` (input_proj → N camadas Mamba → dropout → classifier). Também tem `carregar_modelo()` que carrega do checkpoint com auto-detecção de arquitetura via meta sidecar. |
| `mamba_minimal.py` | Implementação pura PyTorch do bloco Mamba. Usado quando `mamba_ssm` (CUDA) não está disponível. API-compatible com o oficial. |

### Experimentos (novas arquiteturas)

```
modelo/experimentos/    ← pasta para novos modelos
```

Ver seção "Como Adicionar uma Nova Arquitetura" abaixo.

## Fluxo de Treinamento

Quando você roda `python run_treino.py --pares BTCUSDT --nome exp1`:

```
1. baseline_ingenuo(par)           → mede baseline momentum
2. treinar(par, nome="exp1")       → treina Mamba por até 100 epochs
   │  a cada epoch:
   │    - forward no treino, backward, step
   │    - avalia val_loss e val_acc
   │    - se val_acc bate recorde: salva checkpoint (BTCUSDT_exp1.pt + meta)
   │    - se val_acc não melhora por 20 epochs: early stop
   │  no final: carrega o melhor checkpoint de volta
   │
3. avaliar(modelo, test)            → accuracy, precision, recall, f1
4. avaliar_seletivo(modelo, test)   → sweep de confiança (0.50–0.70)
5. avaliar_trade(par, modelo)       → simula TP/SL, expectancy em R
6. avaliar_regime(par, modelo)      → accuracy + expectancy por regime de vol
7. walk_forward(par, nome)          → 5 folds temporais
8. salvar_metricas(par, m, nome)    → BTCUSDT_exp1_metricas.json
9. gerar_previsoes(par, nome)       → BTCUSDT_exp1_previsoes.json
```

### Checkpoint: o que fica salvo

Durante o treino, o checkpoint é salvo **só quando val_acc melhora** (novo recorde). Se a melhor epoch foi 23 e o treino continuou até 30, o arquivo `.pt` contém os pesos da epoch 23. No fim, o melhor checkpoint é recarregado.

Arquivos gerados por treino:

| Arquivo | Conteúdo |
|---|---|
| `{par}_{nome}.pt` | Pesos do modelo (state_dict) da melhor epoch |
| `{par}_{nome}_meta.json` | Arquitetura exata (d_model, n_layers, dropout, etc.) |
| `{par}_{nome}_metricas.json` | Todas as métricas + config usada + histórico |
| `{par}_{nome}_previsoes.json` | Previsões do teste para o frontend |

## Nomeando Modelos (`--nome`)

Cada treino salva com o nome que você escolher. Mesmo nome = sobrescreve.

```bash
# Treinar modelo base
python run_treino.py --pares BTCUSDT --nome baseline

# Treinar variante com mais capacidade
python run_treino.py --pares BTCUSDT --nome grande --d-model 64 --n-layers 4

# Avaliar um modelo específico sem retreinar
python run_treino.py --pares BTCUSDT --nome baseline --seletivo

# Sem --nome, default é "mamba"
python run_treino.py --pares BTCUSDT                  # → BTCUSDT_mamba.pt
```

Os arquivos de cada experimento ficam lado a lado em `dados/resultados/`:

```
dados/resultados/
├── BTCUSDT_baseline.pt
├── BTCUSDT_baseline_meta.json
├── BTCUSDT_baseline_metricas.json
├── BTCUSDT_grande.pt
├── BTCUSDT_grande_meta.json
├── BTCUSDT_grande_metricas.json
```

## Como Adicionar uma Nova Arquitetura

Para experimentar uma arquitetura diferente (Transformer, LSTM, etc.):

1. **Crie a pasta e o modelo** em `modelo/experimentos/`:

```
modelo/experimentos/
├── transformer/
│   ├── __init__.py
│   └── modelo.py       ← TransformerClassificador
```

2. **Siga a interface do MambaClassificador:**

```python
class TransformerClassificador(nn.Module):
    def __init__(self, d_input, d_model, n_layers, num_classes, dropout, **kwargs):
        super().__init__()
        # ... sua arquitetura ...

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # entrada: (batch, seq_len, d_input)
        # saída:   (batch, num_classes) logits
        return logits
```

3. **Adapte `treino.py`** para instanciar a classe certa (hoje é hardcoded `MambaClassificador`). Pode ser um parâmetro `--arquitetura` no futuro.

4. **Adicione `carregar_modelo`** para a nova arquitetura (ou generalize o existente).

5. **Treine com `--nome`:**

```bash
python run_treino.py --pares BTCUSDT --nome transformer_v1
```

O sistema de avaliação (`avaliar_trade`, `avaliar_regime`, `avaliar_seletivo`, walk-forward) funciona com qualquer modelo que siga a interface `(batch, seq, features) → logits`.
