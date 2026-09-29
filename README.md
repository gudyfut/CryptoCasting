# CryptoCasting

TCC de Ciência da Computação: previsibilidade direcional de criptomoedas com Mamba e dados OHLCV.

## Estado do projeto

Fundação metodológica reiniciada em 14/09/2026. A implementação e os dados exploratórios anteriores foram removidos. As camadas de coleta (Entrega 2) e pré-processamento (Entrega 3) estão implementadas e foram executadas pelo pesquisador. O dataset processado `daeec76f001afb50a8fe` tem 1.661 origens diárias comuns na matriz principal; [cobertura e volatilidade observadas](docs/entregas/03_pre_processamento_amostras/resultados_execucao_oficial.md) foram auditadas. Há resultados de desenvolvimento da baseline AR(1) para BTCUSDT. O protocolo 1.6 acrescenta LSTM como segunda baseline; ela ainda não foi implementada. Ainda não há avaliação do Mamba neste protocolo nem resultados finais de 2024–2025.

A entrega da Atividade 1 está em **[docs/protocolo_experimental.md](docs/protocolo_experimental.md)**. Ela define BTC, ETH, BNB e XRP, candles de 15 minutos, 1 hora, 4 horas e 1 dia, contextos de 7 e 14 dias, horizontes de próximo candle e 24 horas, baselines AR(1) e LSTM, métricas e folds walk-forward.

## Estrutura atual

| Caminho | Finalidade |
|---|---|
| `docs/protocolo_experimental.md` | Desenho experimental e critérios para implementar as próximas atividades |
| `docs/baseline_metodologia.md` | Pesquisa da escolha histórica do AR(1) e registro da inclusão posterior da LSTM; distinção entre baselines, 50% de BA e teste PT |
| `docs/Cronograma_Atividades_TCC2_Murilo_Monferrari.pdf` | Cronograma acadêmico original |
| `docs/entregas/` | Pastas das 12 entregas do cronograma e seus documentos de acompanhamento |
| `plano.md` | Objetivo e limites científicos |
| `camada_dados/` | Entrada, preservação, auditoria e manifesto dos dados brutos |
| `configuracoes/coleta_oficial.json` | Contrato fechado dos 240 arquivos mensais esperados |
| `run_coleta.py` | Interface da coleta executada pelo usuário |
| `configuracoes/pre_processamento.json` | Contrato fechado da transformação e das amostras |
| `pre_processamento/` | Agregação UTC, indicadores, elegibilidade, folds, scaler e relatórios |
| `run_pipeline.py` | Interface do processamento executado pelo usuário após a coleta |
| `baseline_ar1/`, `run_baseline.py` e `run_baseline_desenvolvimento.py` | Baseline ARIMA(1,0,0) e execução dos folds D1–D4 pelo usuário |
| `modelo/mamba_modelo.py` | Classificador Mamba reutilizável, com parâmetros explícitos; ainda exige validação |
| `modelo/mamba_minimal.py` | Fallback Mamba em PyTorch puro para CPU/Windows |
| `scripts/` | Preparação e diagnóstico do ambiente WSL2/CUDA |
| `dataview/` | Interface com matriz planejada e componentes genéricos de gráficos preservados |
| `dados/README.md` | Contrato previsto para os futuros dados |

Os antigos orquestradores foram removidos com o protótipo. O novo `run_pipeline.py` implementa a Entrega 3; `run_treino.py` ainda será construído. Coleta e processamento não treinam modelos.

## Desenvolvimento

Python e PyTorch no backend; Mamba oficial em Linux/WSL2 com CUDA ou fallback PyTorch. Dependências gerais em `requirements.txt`; versões finais serão registradas e fixadas na infraestrutura experimental.

`scripts/setup_wsl_mamba.sh` preserva uma receita específica de Python 3.12/PyTorch 2.6/CUDA 11.8 e pressupõe o ambiente `~/.venvs/cc` existente. Não é um instalador universal. A execução da preparação e dos diagnósticos cabe ao usuário.

Frontend, a partir de `dataview/`:

```bash
npm install
npm run dev
```

Verificações: `npm run lint`, `npm run build` e compilação sintática dos módulos Python. Agentes não executam coleta nem treinamento. A interface inicia sem dados e sem resultados; as rotas genéricas de CSV são infraestrutura preservada para adaptação posterior.

## Entrega 2

A arquitetura, os comandos e o material visual estão em **[docs/entregas/02_pipeline_coleta/README.md](docs/entregas/02_pipeline_coleta/README.md)**. A coleta foi executada pelo usuário; os 24 registros não completos têm somente lacunas presentes nos ZIPs oficiais, sem checksum divergente.

## Entrega 3

A implementação e o contrato de arquivos estão em **[docs/entregas/03_pre_processamento_amostras/README.md](docs/entregas/03_pre_processamento_amostras/README.md)**. O pipeline foi executado pelo pesquisador, preservou as lacunas dos 240 arquivos auditados e gerou os [resultados oficiais de cobertura e volatilidade](docs/entregas/03_pre_processamento_amostras/resultados_execucao_oficial.md).

## Piloto da Entrega 4

O [ARIMA(1,0,0) nos quatro folds de desenvolvimento de BTCUSDT](docs/entregas/04_infraestrutura_baselines/resultados_desenvolvimento_BTC_D1_D4.md) foi executado pelo pesquisador. A BA média foi 49,11%, com raro reconhecimento das altas. A [Entrega 4](docs/entregas/04_infraestrutura_baselines/README.md) agora inclui a implementação planejada da LSTM, para comparação com o Mamba nas mesmas entradas. Os testes finais de 2024–2025 continuam reservados.
