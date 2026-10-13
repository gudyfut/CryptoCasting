# AR(1) BTCUSDT D1 - piloto historico

- ID: `piloto_ar1_f39a7dd1df543363b7d0`
- Situação inicial: **exploratorio**
- Execução UTC: não registrada na origem
- Célula: `{"par": "BTCUSDT", "fold": "D1", "tarefa": "principal", "granularidade": "1d"}`
- Dataset: `daeec76f001afb50a8fe`
- Estado de execução: historico_sem_estado_explicito
- Auditoria: Hashes históricos conferidos; sem reconstrução retroativa do ambiente/código.

Executado pelo pesquisador. Data de execucao e snapshot completo do codigo nao foram preservados. Baseline de desenvolvimento, sem conclusao sobre Mamba ou avaliacao final.

## Dados e configuração registrados

```json
{
  "metodo": "ARIMA(1,0,0) nos log-retornos, AR(1) com intercepto estimado por MQO condicional",
  "serie": "retornos de fechamentos diários UTC",
  "contexto_dias_amostras": 7,
  "fronteiras_utc": {
    "fim_treino": "2022-10-01",
    "fim_validacao": "2023-01-01",
    "fim_teste": "2023-04-01"
  },
  "fold": "D1",
  "pares_retorno_ajuste": 495,
  "coeficientes": {
    "alfa": -0.0021849289556473864,
    "phi": -0.05479373450156828
  }
}
```

As datas acima são fronteiras exclusivas dos blocos. Os CSVs preservam as origens efetivamente avaliadas após a purga e exclusão de lacunas.

## Métricas observadas

| Bloco | Modelo | Amostras | BA | Accuracy | F1 macro |
|---|---|---:|---:|---:|---:|
| validacao | ar1 | 91 | 0.5160 | 0.5824 | 0.4119 |
| teste | ar1 | 82 | 0.4634 | 0.4634 | 0.3167 |

BA está na escala 0–1. Matrizes de confusão, métricas por classe, versões e hashes estão nos originais. As comparações entre modelos, a referência de 50% e o PT têm interpretações separadas.

## Evidências

[Registro e inventário](registro.json) contém tamanho, configuração disponível, caminhos e hashes. `originais/` preserva os JSONs e documentos existentes; `previsoes/` guarda os parquets leves convertidos em CSV, com timestamps e rótulos. O hash do CSV é distinto do hash do parquet de origem. Ausências de metadados permanecem explícitas.

Checkpoints e demais binários locais não estão neste pacote; precisam de backup separado para reprodução completa. Os hashes permitem verificar a cópia, mas não recuperam arquivos perdidos.

[Acompanhamento e revisões](acompanhamento.md). Nunca substituir os originais para corrigir um resultado histórico.
