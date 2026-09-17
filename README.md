# CryptoCasting

TCC de Ciência da Computação: previsibilidade direcional de criptomoedas com Mamba e dados OHLCV.

## Estado do projeto

Fundação metodológica reiniciada em 14/09/2026. A implementação e os dados exploratórios anteriores foram removidos. Ainda não existem dataset oficial, pipeline executável, modelo treinado ou resultados científicos deste protocolo.

A entrega da Atividade 1 está em **[docs/protocolo_experimental.md](docs/protocolo_experimental.md)**. Ela define BTC, ETH e XRP, candles de 15 minutos, 1 hora, 4 horas e 1 dia, alvo, baseline, métricas, comparação controlada e folds walk-forward.

## Estrutura atual

| Caminho | Finalidade |
|---|---|
| `docs/protocolo_experimental.md` | Desenho experimental e critérios para implementar as próximas atividades |
| `docs/baseline_metodologia.md` | Pesquisa, fórmulas e régua de interpretação das quatro baselines |
| `docs/Cronograma_Atividades_TCC2_Murilo_Monferrari.pdf` | Cronograma acadêmico original |
| `docs/entregas/` | Pastas das 12 entregas do cronograma e seus documentos de acompanhamento |
| `plano.md` | Objetivo e limites científicos |
| `modelo/mamba_modelo.py` | Classificador Mamba reutilizável, com parâmetros explícitos; ainda exige validação |
| `modelo/mamba_minimal.py` | Fallback Mamba em PyTorch puro para CPU/Windows |
| `scripts/` | Preparação e diagnóstico do ambiente WSL2/CUDA |
| `dataview/` | Interface com matriz planejada e componentes genéricos de gráficos preservados |
| `dados/README.md` | Contrato previsto para os futuros dados |

Os antigos `run_pipeline.py` e `run_treino.py` foram removidos com o protótipo. Serão reconstruídos nas respectivas atividades do cronograma. Os componentes preservados não equivalem a uma implementação validada do protocolo.

## Desenvolvimento

Python e PyTorch no backend; Mamba oficial em Linux/WSL2 com CUDA ou fallback PyTorch. Dependências gerais em `requirements.txt`; versões finais serão registradas e fixadas na infraestrutura experimental.

`scripts/setup_wsl_mamba.sh` preserva uma receita específica de Python 3.12/PyTorch 2.6/CUDA 11.8 e pressupõe o ambiente `~/.venvs/cc` existente. Não é um instalador universal. A execução da preparação e dos diagnósticos cabe ao usuário.

Frontend, a partir de `dataview/`:

```bash
npm install
npm run dev
```

Verificações: `npm run lint`, `npm run build` e compilação sintática dos módulos Python. Agentes não executam coleta nem treinamento. A interface inicia sem dados e sem resultados; as rotas genéricas de CSV são infraestrutura preservada para adaptação posterior.

## Próxima entrega

Implementar a coleta reproduzível dos três pares no período fechado do protocolo, com manifesto, checksums e auditoria de continuidade temporal. A sequência completa de implementação está no documento experimental.
