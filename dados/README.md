# Dados do protocolo

Os CSVs e o metadado de checkpoint exploratórios foram removidos. A coleta oficial produziu ZIPs brutos e manifesto; a Entrega 3 produziu o dataset `daeec76f001afb50a8fe`. Ainda não há resultados preditivos.

A coleta seguiu [o protocolo](../docs/protocolo_experimental.md): BTCUSDT, ETHUSDT, BNBUSDT e XRPUSDT; Binance Spot; 2021-01-01 a 2026-01-01, limite final exclusivo, UTC; candles-base de 15 minutos. O manifesto registra 216 meses completos e 24 com lacunas auditadas.

Layout implementado para coleta e pré-processamento, com experimentos planejados:

```text
dados/
  brutos/binance_spot/{par}/{intervalo}/
  brutos/manifestos/
  processados/{id_dataset}/candles/{par}/{granularidade}.parquet
  processados/{id_dataset}/amostras/{tarefa}/{par}/{granularidade}/{contexto}.parquet
  processados/{id_dataset}/relatorios/
  experimentos/{id_experimento}/{par}/{intervalo}/{horizonte}/{fold}/{seed}/
```

O comando e a arquitetura da coleta estão na [Entrega 2](../docs/entregas/02_pipeline_coleta/README.md). Preservar arquivos originais, hashes e manifesto. O ID do dataset identifica entradas, contrato, código e versões; os caminhos das amostras distinguem tarefa, par, granularidade e contexto. Os futuros IDs de experimento deverão distinguir também folds, seeds e demais parâmetros para evitar sobrescrita. Cada amostra carrega timestamps de início/fim do contexto e do alvo; posição de linha não substitui timestamp.

O contrato detalhado e as verificações do dataset processado estão na [Entrega 3](../docs/entregas/03_pre_processamento_amostras/README.md); os [resultados observados](../docs/entregas/03_pre_processamento_amostras/resultados_execucao_oficial.md) resumem cobertura e volatilidade da execução do pesquisador.

As rotas CSV preservadas em `dataview/` ainda precisam ser adaptadas a esse contrato; a interface atual não as utiliza.
