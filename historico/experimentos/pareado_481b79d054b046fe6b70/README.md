# BTCUSDT 1d D1 - piloto pareado AR(1), LSTM e Mamba CPU

- ID: `pareado_481b79d054b046fe6b70`
- Situação inicial: **em_revisao**
- Execução UTC: 2026-10-13T16:00:00.354049+00:00
- Célula: `{"par": "BTCUSDT", "granularidade": "1d", "contexto_dias": 7, "fold": "D1", "seed": 42, "tarefa": "principal"}`
- Dataset: `daeec76f001afb50a8fe`
- Estado de execução: concluido
- Auditoria: Hashes, contratos e métricas dos parquets conferidos; não valida equivalência com Mamba oficial.

Executado pelo agente com autorizacao do pesquisador. Integridade e recarga de checkpoints conferidas. Diferenca de inicializacao do fallback requer qualificacao; causa da baixa BA nao isolada. Consulte [diagnostico posterior](../../analises/2026-10-13_diagnostico_mamba.md).

## Dados e configuração registrados

```json
{
  "fold": {
    "nome": "D1",
    "tipo": "desenvolvimento",
    "fim_treino": "2022-10-01",
    "fim_validacao": "2023-01-01",
    "fim_teste": "2023-04-01"
  },
  "configuracao": {
    "contrato": "entregas45-v1",
    "dataset": "dados/processados/daeec76f001afb50a8fe",
    "pares": [
      "BTCUSDT"
    ],
    "granularidades": [
      "1d"
    ],
    "contextos_dias": [
      7
    ],
    "tarefa": "principal",
    "folds": [
      "D1"
    ],
    "seeds": [
      42
    ],
    "features": "ohlcv",
    "normalizador": "standard",
    "largura_mamba": 32,
    "largura_lstm": 32,
    "backend_mamba": "pytorch",
    "dispositivo": "cpu",
    "microbatch": 32
  },
  "features": [
    "open",
    "high",
    "low",
    "close",
    "volume"
  ],
  "dimensao_entrada": 5,
  "contagens": {
    "treino": 495,
    "validacao": 91,
    "teste": 82
  }
}
```

As datas acima são fronteiras exclusivas dos blocos. Os CSVs preservam as origens efetivamente avaliadas após a purga e exclusão de lacunas.

## Métricas observadas

| Bloco | Modelo | Amostras | BA | Accuracy | F1 macro |
|---|---|---:|---:|---:|---:|
| validacao | ar1 | 91 | 0.5160 | 0.5824 | 0.4119 |
| validacao | lstm | 91 | 0.5000 | 0.5714 | 0.3636 |
| validacao | mamba | 91 | 0.5256 | 0.5165 | 0.5164 |
| teste | ar1 | 82 | 0.4634 | 0.4634 | 0.3167 |
| teste | lstm | 82 | 0.5000 | 0.5000 | 0.3333 |
| teste | mamba | 82 | 0.4146 | 0.4146 | 0.3242 |

## Treinamento efetivamente registrado

```json
{
  "lstm": {
    "modelo": "lstm",
    "backend": "torch.nn.LSTM",
    "parametros": 13506,
    "epocas_executadas": 11,
    "melhor_epoca": 1,
    "melhor_ba_validacao": 0.5,
    "segundos_treino_e_avaliacao": 1.0466173000168055,
    "pico_memoria_cuda_bytes": null,
    "determinismo": "seeds fixas; deterministic_algorithms warn_only; kernels podem não ser estritamente determinísticos",
    "regras_treino": {
      "otimizador": "AdamW",
      "taxa_aprendizado": 0.0002,
      "weight_decay": 0.001,
      "batch_efetivo": 32,
      "epocas_maximas": 100,
      "paciencia": 10,
      "clipping": 1.0,
      "perda": "cross_entropy_sem_pesos",
      "limiar_alta": 0.5,
      "selecao": "BA_validacao; empate mantém checkpoint mais antigo",
      "scheduler": null
    },
    "microbatch": 32
  },
  "mamba": {
    "modelo": "mamba",
    "backend": "pytorch",
    "parametros": 20290,
    "epocas_executadas": 14,
    "melhor_epoca": 4,
    "melhor_ba_validacao": 0.5256410256410257,
    "segundos_treino_e_avaliacao": 4.588251500041224,
    "pico_memoria_cuda_bytes": null,
    "determinismo": "seeds fixas; deterministic_algorithms warn_only; kernels podem não ser estritamente determinísticos",
    "regras_treino": {
      "otimizador": "AdamW",
      "taxa_aprendizado": 0.0002,
      "weight_decay": 0.001,
      "batch_efetivo": 32,
      "epocas_maximas": 100,
      "paciencia": 10,
      "clipping": 1.0,
      "perda": "cross_entropy_sem_pesos",
      "limiar_alta": 0.5,
      "selecao": "BA_validacao; empate mantém checkpoint mais antigo",
      "scheduler": null
    },
    "microbatch": 32
  }
}
```

BA está na escala 0–1. Matrizes de confusão, métricas por classe, versões e hashes estão nos originais. As comparações entre modelos, a referência de 50% e o PT têm interpretações separadas.

## Evidências

[Registro e inventário](registro.json) contém tamanho, configuração disponível, caminhos e hashes. `originais/` preserva os JSONs e documentos existentes; `previsoes/` guarda os parquets leves convertidos em CSV, com timestamps e rótulos. O hash do CSV é distinto do hash do parquet de origem. Ausências de metadados permanecem explícitas.

Checkpoints e demais binários locais não estão neste pacote; precisam de backup separado para reprodução completa. Os hashes permitem verificar a cópia, mas não recuperam arquivos perdidos.

[Acompanhamento e revisões](acompanhamento.md). Nunca substituir os originais para corrigir um resultado histórico.
