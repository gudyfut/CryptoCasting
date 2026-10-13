# CryptoCasting

TCC de Ciência da Computação: previsibilidade direcional de criptomoedas com Mamba e dados OHLCV.

## Estado do projeto

**Atualizado em 13/10/2026.** As Entregas 1–3 estão documentadas e a coleta e o pré-processamento foram executados pelo pesquisador. O dataset `daeec76f001afb50a8fe` tem 1.661 origens diárias comuns; [cobertura e volatilidade](docs/entregas/03_pre_processamento_amostras/resultados_execucao_oficial.md) foram auditadas. Há resultados de desenvolvimento do AR(1) para BTCUSDT.

**As Entregas 4 e 5 estão implementadas para desenvolvimento D1–D4:** LSTM, Mamba, treinamento compartilhado, métricas, teste PT, checkpoints e consolidação. O [piloto pareado BTCUSDT/1d/D1 em CPU](docs/entregas/05_mamba_base/resultados_piloto_BTC_D1_cpu.md) foi executado pelo agente após autorização do usuário e auditado: BA Mamba 41,46%, LSTM 50,00%, AR(1) 46,34%. O aceite funcional CPU está concluído. Mamba oficial/CUDA não foi validado na máquina atual (GPU AMD RX 6600, ambiente WSL ausente); não existem resultados finais de 2024–2025. F1–F8 permanecem bloqueados até uma etapa futura de congelamento metodológico.

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
| `modelo/mamba_modelo.py` e `modelo/lstm_modelo.py` | Classificadores Mamba e LSTM com dimensões explícitas |
| `modelo/mamba_minimal.py` | Fallback Mamba em PyTorch puro para CPU/Windows |
| `scripts/` | Preparação e diagnóstico do ambiente WSL2/CUDA |
| `experimentos/` | Leitura íntegra do dataset, treino pareado, avaliação, registros e consolidação |
| `historico/` | Linha do tempo versionada, fichas de cada tentativa, evidências e revisões científicas |
| `run_registro.py` | Exportação leve de uma execução, inclusive incompleta, sem treinamento |
| `run_treino.py`, `run_avaliacao.py` | Execução e consolidação dos experimentos de desenvolvimento |
| `configuracoes/treino_*.json` | Piloto CPU e grade inicial WSL/CUDA |
| `dataview/` | Caderno visual Next.js: objetivo, método, moedas, decisões, progresso e resultados locais |
| `dados/README.md` | Contrato dos dados e artefatos científicos |

O protótipo exploratório foi removido em setembro de 2026. Os novos orquestradores seguem o protocolo vigente; coleta e processamento não treinam modelos.

## Desenvolvimento

Python e PyTorch no backend; Mamba oficial em Linux/WSL2 com CUDA ou fallback PyTorch. Dependências gerais em `requirements.txt`; versões finais serão registradas e fixadas na infraestrutura experimental.

`scripts/setup_wsl_mamba.sh` preserva uma receita específica de Python 3.12/PyTorch 2.6/CUDA 11.8 e pressupõe o ambiente `~/.venvs/cc` existente. Não é um instalador universal. A execução da preparação e dos diagnósticos cabe ao usuário.

Frontend, a partir de `dataview/`:

```bash
npm install
npm run dev
```

Acesse **http://localhost:3000**. A interface possui seis seções: Resumo do projeto, Metodologia, Configurações experimentais, Dados e ativos, Entregas e execução e Resultados e interpretação. Apresenta evidências documentadas com fontes, permite explorar contexto/horizonte e lê novos resultados em `dados/experimentos/pareado_*`. Ausência de resultados é mostrada explicitamente. O registro editorial está em `dataview/src/lib/estudo.ts`; a matriz de planejamento é gerada dos contratos Python por `scripts/atualizar_plano_experimental.py`; as rotas de leitura atuais estão em `/api/estudo/`. As antigas rotas genéricas de CSV permanecem preservadas e não alimentam este painel.

Verificações: `npm run test`, `npm run lint`, `npm run build` e `python -m unittest discover -s tests`. A suíte usa dados sintéticos e verificações rápidas, sem treinamento. A autorização excepcional do piloto neural está registrada em `AGENTS.md`; ela não autoriza automaticamente a grade completa ou a avaliação final.

## Entrega 2

A arquitetura, os comandos e o material visual estão em **[docs/entregas/02_pipeline_coleta/README.md](docs/entregas/02_pipeline_coleta/README.md)**. A coleta foi executada pelo usuário; os 24 registros não completos têm somente lacunas presentes nos ZIPs oficiais, sem checksum divergente.

## Entrega 3

A implementação e o contrato de arquivos estão em **[docs/entregas/03_pre_processamento_amostras/README.md](docs/entregas/03_pre_processamento_amostras/README.md)**. O pipeline foi executado pelo pesquisador, preservou as lacunas dos 240 arquivos auditados e gerou os [resultados oficiais de cobertura e volatilidade](docs/entregas/03_pre_processamento_amostras/resultados_execucao_oficial.md).

## Entregas 4 e 5 — executar o primeiro piloto pareado

O [AR(1) em BTCUSDT/D1–D4](docs/entregas/04_infraestrutura_baselines/resultados_desenvolvimento_BTC_D1_D4.md) obteve BA média de 49,11%. A [Entrega 4](docs/entregas/04_infraestrutura_baselines/README.md) acrescenta LSTM e infraestrutura; a [Entrega 5](docs/entregas/05_mamba_base/README.md) documenta o treinamento pareado e todos os artefatos.

O piloto já foi executado. Para uma futura execução intencional, na raiz e com as dependências Python instaladas:

```powershell
python run_treino.py --configuracao configuracoes/treino_piloto_cpu.json --planejar
python run_treino.py --configuracao configuracoes/treino_piloto_cpu.json
```

O piloto usa BTCUSDT, candles diários, contexto de 7 dias, horizonte de 24h, fold D1 e seed 42. O AR(1) é comparado com LSTM e Mamba PyTorch/CPU nas mesmas datas. Não exige nova coleta ou pré-processamento. O treinador mediu 1,05 s para LSTM e 4,59 s para Mamba nessa pequena célula diária; isso não estima o custo da grade intradiária. Consulte a Entrega 5 antes de iniciar a grade maior em WSL/CUDA.

## Matriz dos experimentos

A [tabela completa](docs/entregas/05_mamba_base/matriz_experimental.md) detalha moedas, resolução dos candles, janelas de 7/14 dias, horizontes, entradas, sequência de comparações e períodos D1–D4/F1–F8. Na interface, abra **Configurações experimentais**. Os controles explicam o planejamento; não iniciam treinamento.

## Histórico e revisão dos resultados

Consulte a **[linha do tempo](historico/LINHA_DO_TEMPO.md)** e as [regras de registro](historico/README.md). Foram preservados os quatro pilotos históricos AR(1)/D1–D4 e o piloto pareado LSTM/Mamba/D1. Cada ficha reúne configuração, tamanho das amostras, métricas, previsões com timestamps, hashes e acompanhamento. Datas históricas ausentes permanecem desconhecidas; os experimentos removidos anteriormente não foram reconstruídos.

O [diagnóstico do Mamba](historico/analises/2026-10-13_diagnostico_mamba.md) coloca o piloto **em revisão científica**: o fluxo foi auditado, mas foi identificada uma diferença de inicialização entre o fallback e o Mamba oficial. A causa da baixa BA ainda não foi isolada. A análise apenas recarregou pesos existentes, sem novo treino.

Para registrar uma nova tentativa, inclusive uma falha, use o caminho real de sua execução:

```powershell
python run_registro.py --execucao dados/experimentos/pareado_ID --titulo "Descrição da tentativa" --situacao em_revisao --observacao "Objetivo, verificações e dúvidas pendentes."
```

Os arquivos leves entram no Git em `historico/`. Checkpoints e datasets continuam locais e precisam de backup separado; o inventário de hashes não substitui esse backup. Novas interpretações são acrescentadas em `acompanhamento.md`, preservando o registro original.
