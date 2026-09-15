# AGENTS.md

TCC científico: prever direção de criptomoedas com Mamba e OHLCV. Leia `plano.md` e `docs/protocolo_experimental.md` antes de implementar. O protocolo é a referência metodológica; não reintroduza configurações dos testes antigos.

## Estado atual

O usuário solicitou a remoção dos experimentos exploratórios em 14/09/2026. Pipeline, orquestradores, análises, previsões, dados de teste e documentação antiga foram removidos. Restam componentes Mamba reutilizáveis, preparação do ambiente, infraestrutura genérica de gráficos e o protocolo. Ainda não há implementação validada do estudo.

## Execução

O usuário executa toda coleta, pipeline e treinamento. Agentes editam código e usam somente verificações Python rápidas sem treinamento, como `python -m py_compile`. Não executar `run_pipeline.py` ou `run_treino.py` quando forem reconstruídos. Frontend pode ser verificado com lint/build.

## Restrições científicas

- Mamba-only e PyTorch-only para a arquitetura investigada. Sem arquiteturas neurais concorrentes, notícias, sentimento, macroeconomia ou previsão com LLM. Implementar as quatro referências B0–B3 do protocolo, incluindo AR(1), como controles metodológicos.
- Pares: BTCUSDT, ETHUSDT e XRPUSDT. Granularidades: 15m, 1h, 4h e 1d.
- Alvo binário: alta versus não alta. Não filtrar observações com base na magnitude futura.
- Walk-forward expansivo por datas; não restaurar split fixo 70/15/15 ou avaliação de checkpoint único como substituto.
- Ajustar transformações somente no treino de cada fold. Purgar rótulos que cruzem fronteiras temporais.
- Somente o DataLoader de treino pode embaralhar amostras; validação e teste preservam a ordem.
- Preservar timestamps de origem e do alvo. Nunca alinhar parquets distintos por índice de linha.
- Dados, features, dimensões de entrada e metadados devem corresponder à configuração efetivamente executada.
- Identificadores/argumentos novos em português; parâmetros da API Mamba preservam compatibilidade.

## Mamba e ambientes

`modelo/mamba_modelo.py:_importar_mamba()` tenta `mamba_ssm` e recorre a `modelo/mamba_minimal.py`. O fallback é de primeira classe; não assumir disponibilidade de CUDA. O classificador recebe dimensões explicitamente, sem configuração experimental global.

Windows `.venv`: CPU. WSL2 `~/.venvs/cc`: PyTorch/CUDA/Mamba oficial. `scripts/setup_wsl_mamba.sh` é uma receita específica preservada; `scripts/test_mamba.py` é diagnóstico a cargo do usuário. Registrar backend e versões em cada execução científica; não misturar implementações silenciosamente.

## Frontend

Next.js/React/Tailwind/ECharts em `dataview/`. Executar npm nesse diretório. Alias `@/*` aponta para `src/*`. Interface atual mostra a matriz planejada sem resultados.

Rotas genéricas preservadas acessam CSVs em `process.cwd()/../dados`; precisarão ser adaptadas ao contrato do novo dataset. Não há servidor Python API separado. Não apresentar dados simulados ou antigos como resultados científicos.
