# Dados do protocolo

Os CSVs e o metadado de checkpoint exploratórios foram removidos. Esta pasta não contém dados ou resultados oficiais do estudo.

A coleta futura seguirá [o protocolo](../docs/protocolo_experimental.md): BTCUSDT, ETHUSDT e XRPUSDT; Binance Spot; 2021-01-01 a 2026-01-01, limite final exclusivo, UTC; candles-base de 15 minutos.

Layout a implementar:

```text
dados/
  brutos/{fonte}/{par}/{intervalo}/
  processados/{versao_dataset}/{par}/{intervalo}/
  experimentos/{id_experimento}/{par}/{intervalo}/{horizonte}/{fold}/{seed}/
```

Preservar arquivos originais, hashes e manifesto. O identificador deve distinguir todos os parâmetros para evitar sobrescrita entre granularidades, horizontes e folds. Cada amostra deve carregar timestamps de início/fim do contexto e do alvo; posição de linha não substitui timestamp.

As rotas CSV preservadas em `dataview/` ainda precisam ser adaptadas a esse contrato; a interface atual não as utiliza.
