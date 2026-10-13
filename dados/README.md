# Dados do protocolo

Os CSVs e o metadado de checkpoint exploratórios foram removidos. A coleta oficial produziu ZIPs brutos e manifesto; a Entrega 3 produziu o dataset `daeec76f001afb50a8fe`. Existem resultados AR(1) de desenvolvimento em BTCUSDT. Em 13/10/2026, o piloto neural BTCUSDT/1d/D1/seed 42 foi executado em CPU com autorização do usuário e auditado: `pareado_481b79d054b046fe6b70`, consolidado em `aceite_piloto_cpu_481b79d054b046fe6b70`. O [relatório do piloto](../docs/entregas/05_mamba_base/resultados_piloto_BTC_D1_cpu.md) registra métricas e limitações. Não há resultados finais.

A coleta seguiu [o protocolo](../docs/protocolo_experimental.md): BTCUSDT, ETHUSDT, BNBUSDT e XRPUSDT; Binance Spot; 2021-01-01 a 2026-01-01, limite final exclusivo, UTC; candles-base de 15 minutos. O manifesto registra 216 meses completos e 24 com lacunas auditadas.

Layout implementado para coleta, pré-processamento e experimentos:

```text
dados/
  brutos/binance_spot/{par}/{intervalo}/
  brutos/manifestos/
  processados/{id_dataset}/candles/{par}/{granularidade}.parquet
  processados/{id_dataset}/amostras/{tarefa}/{par}/{granularidade}/{contexto}.parquet
  processados/{id_dataset}/relatorios/
  experimentos/pareado_{id}/resultado.json
  experimentos/pareado_{id}/normalizador.json
  experimentos/pareado_{id}/indices_ajuste_normalizador.npy
  experimentos/pareado_{id}/{lstm,mamba}/melhor.pt
  experimentos/pareado_{id}/{lstm,mamba}/historico.json
  experimentos/pareado_{id}/previsoes_{modelo}_{bloco}.parquet
  experimentos/ar1_compartilhado/{id}/
```

O comando e a arquitetura da coleta estão na [Entrega 2](../docs/entregas/02_pipeline_coleta/README.md). Preservar arquivos originais, hashes e manifesto. O ID do dataset identifica entradas, contrato, código e versões; os caminhos das amostras distinguem tarefa, par, granularidade e contexto. Os IDs dos experimentos distinguem célula, fold, seed, parâmetros, código, protocolo, versões e ambiente. Novas tentativas recebem um sufixo exclusivo. Cada amostra carrega timestamps de início/fim do contexto e do alvo; posição de linha não substitui timestamp.

O contrato detalhado e as verificações do dataset processado estão na [Entrega 3](../docs/entregas/03_pre_processamento_amostras/README.md); os [resultados observados](../docs/entregas/03_pre_processamento_amostras/resultados_execucao_oficial.md) resumem cobertura e volatilidade da execução do pesquisador.

A [Entrega 5](../docs/entregas/05_mamba_base/README.md) descreve checkpoints, estados, consolidação e comandos. O painel lê os resumos pareados reais por `/api/estudo/resultados`; não utiliza as antigas rotas CSV preservadas. Artefatos grandes e resultados locais permanecem fora do Git conforme `.gitignore`.

O arquivo científico leve está em **[historico/](../historico/README.md)**, versionado no Git: configurações, métricas, previsões convertidas em CSV, relatórios e hashes dos artefatos locais. `run_registro.py` exporta tentativas concluídas ou incompletas sem treinar e sem sobrescrever registros. Pesos e datasets continuam nesta árvore local; precisam de backup separado para reprodução completa. O piloto Mamba foi registrado como **em revisão**, conforme o [diagnóstico posterior](../historico/analises/2026-10-13_diagnostico_mamba.md).
