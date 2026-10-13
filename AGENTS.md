# AGENTS.md

TCC científico: prever direção de criptomoedas com Mamba e OHLCV. Leia `plano.md` e `docs/protocolo_experimental.md` antes de implementar. O protocolo é a referência metodológica; não reintroduza configurações dos testes antigos.

## Estado atual

O usuário solicitou a remoção dos experimentos exploratórios em 14/09/2026. Pipeline experimental antigo, análises, previsões, dados de teste e documentação antiga foram removidos. Coleta (Entrega 2) e pré-processamento (Entrega 3) foram implementados e executados pelo pesquisador. O dataset oficial `daeec76f001afb50a8fe` tem 1.661 origens diárias comuns; cobertura/volatilidade estão em `docs/entregas/03_pre_processamento_amostras/resultados_execucao_oficial.md`. AR(1) BTCUSDT/D1–D4 foi executado pelo pesquisador. Em 13/10/2026, as Entregas 4 e 5 receberam LSTM, treinador pareado Mamba/LSTM, métricas/PT, consolidação e painel Next.js. Após autorização explícita do usuário, o agente executou e auditou o piloto neural BTCUSDT/1d/D1/seed 42 em CPU, identidade `481b79d054b046fe6b70`: BA Mamba 41,46%, LSTM 50,00%, AR(1) 46,34%. Checkpoints recarregados reproduzem exatamente as previsões. Relatório: `docs/entregas/05_mamba_base/resultados_piloto_BTC_D1_cpu.md`. Não há resultados neurais D2–D4 nem finais de 2024–2025. Consultar `docs/entregas/05_mamba_base/README.md`. A revisão técnica acrescentou auditoria com recálculo das métricas, snapshots de código/protocolo e matriz experimental gerada. `scripts/atualizar_plano_experimental.py` só gera documentação e não treina.

## Execução

O usuário executa toda coleta, pipeline e treinamento. Agentes editam código e usam somente verificações Python rápidas sem treinamento, como `python -m py_compile`. Não executar `run_pipeline.py` ou `run_treino.py` quando forem reconstruídos. Frontend pode ser verificado com lint/build.

**Exceção autorizada pelo usuário em 13/10/2026:** o agente pode preparar, executar e auditar o piloto de treinamento LSTM/Mamba necessário à validação das Entregas 4 e 5, com o dataset oficial existente. Registrar configuração, ambiente, artefatos e resultados; manter a avaliação restrita ao desenvolvimento e preservar o bloqueio F1–F8. Esta autorização não inicia automaticamente a grade completa das entregas posteriores.

## Restrições científicas

**Revisão de escopo solicitada em 13/10/2026:** consultar `docs/estudo_tarefas_previsao.md`. A interface separa moeda, candle, horizonte, alvo, contexto e políticas. O catálogo A–H foi substituído por cinco formulações visuais: direção, retorno/preço, faixa probabilística, volatilidade e barreiras. Direção diária/próximo candle são vigentes; outros alvos e prazos são candidatos. O usuário pediu pesquisa e visualização das alternativas, não execução de todas elas. Não converter uma proposta em configuração científica nem misturar exemplos fictícios da interface com resultados. O contrato operacional 1.6 e seus bloqueios continuam vigentes até decisão explícita; o piloto NVIDIA é qualificação técnica da tarefa diária. Magnitude e volatilidade são possibilidades de extensão, ainda fora do escopo executável binário.

- Mamba é a arquitetura investigada; LSTM unidirecional em PyTorch é a baseline neural. ARIMA(1,0,0) dos log-retornos é a baseline estatística simples. Sem outras arquiteturas concorrentes, notícias, sentimento, macroeconomia ou previsão com LLM. O random walk sem deriva coincide com 50% de balanced accuracy após conversão ao alvo binário. Manter separadas as comparações Mamba versus AR(1), Mamba versus LSTM, referência de 50% e teste de Pesaran–Timmermann. LSTM e Mamba usam as mesmas entradas, folds e regras de treino do protocolo; implementação não equivale a avaliação científica executada. A CLI atual aceita somente D1–D4/seed 42; preservar o bloqueio final até o congelamento.
- Pares: BTCUSDT, ETHUSDT, BNBUSDT e XRPUSDT. Granularidades: 15m, 1h, 4h e 1d. A ordem BTC < ETH < BNB < XRP em volatilidade é hipótese descritiva a verificar, não pressuposto do experimento.
- Alvo binário: alta versus não alta. Não filtrar observações com base na magnitude futura.
- Walk-forward expansivo por datas; não restaurar split fixo 70/15/15 ou avaliação de checkpoint único como substituto.
- Ajustar transformações somente no treino de cada fold. Purgar rótulos que cruzem fronteiras temporais.
- Somente o DataLoader de treino pode embaralhar amostras; validação e teste preservam a ordem.
- Preservar timestamps de origem e do alvo. Nunca alinhar parquets distintos por índice de linha.
- Dados, features, dimensões de entrada e metadados devem corresponder à configuração efetivamente executada.
- Identificadores/argumentos novos em português; parâmetros da API Mamba preservam compatibilidade.

## Mamba e ambientes

`modelo/mamba_modelo.py:_importar_mamba()` tenta `mamba_ssm` e recorre a `modelo/mamba_minimal.py`. O fallback é de primeira classe; não assumir disponibilidade de CUDA. O classificador recebe dimensões explicitamente, sem configuração experimental global.

Ambiente verificado em 13/10/2026: Python 3.13.14 do Windows e PyTorch 2.9.1+cpu; GPU AMD Radeon RX 6600, CUDA indisponível. O ambiente WSL2 `~/.venvs/cc` citado historicamente está ausente nesta máquina; PyTorch/Mamba oficial não estão instalados no Ubuntu verificado. Não presumir disponibilidade do backend oficial. O fluxo do piloto CPU foi auditado; a qualificação científica da implementação e a qualificação CUDA permanecem pendentes. `scripts/setup_wsl_mamba.sh` é uma receita específica preservada; `scripts/test_mamba.py` é diagnóstico a cargo do usuário. Registrar backend e versões em cada execução científica; não misturar implementações silenciosamente.

## Histórico científico

Preparação do notebook NVIDIA (13/10/2026): `configuracoes/treino_piloto_nvidia.json` delimita BTCUSDT/1d/D1/seed 42, OHLCV/StandardScaler e contexto de 7 dias, backend oficial/CUDA, microbatch 32. `run_verificacao.py` faz qualificação sintética sem otimização ou recarga/auditoria de checkpoints; consulte `docs/entregas/05_mamba_base/guia_notebook_nvidia.md`. Não confundir testes CPU aprovados com validação NVIDIA. A grade WSL de 128 treinos não é o piloto. Os novos registros incluem fontes instaladas e opções numéricas; alterações de código exigem outra identidade, preservando o piloto antigo.

Toda tentativa científica deve ser registrada em `historico/`, inclusive falhas, resultados desfavoráveis e testes sob suspeita. Usar `run_registro.py` após encerrar a tentativa; consultar `historico/README.md`. Preservar os originais, registrar revisões por data em `acompanhamento.md` e criar outra identidade para novos treinos. Não inventar metadados ausentes, não confundir data de importação com execução e não chamar integridade de artefatos de validação científica. Checkpoints/datasets fora do Git exigem backup separado.

**Revisão de 13/10/2026:** o piloto Mamba está `em_revisao`. Há diferença entre a inicialização de `dt_proj.bias` do fallback e a referência oficial; isso não demonstra a causa da BA baixa. Consultar `historico/analises/2026-10-13_diagnostico_mamba.md`. O aceite funcional CPU não certifica equivalência entre implementações. Não repetir a grade para procurar resultados favoráveis antes de qualificar a implementação e documentar o teste controlado.

## Frontend

Next.js/React/Tailwind/ECharts em `dataview/`. Executar npm nesse diretório. Alias `@/*` aponta para `src/*`. Painel de pesquisa com método, matriz de treinos, moedas, entregas, piloto histórico identificado e matriz final pendente. A tabela usa `dataview/src/lib/plano-experimental.json`, gerado de `experimentos/planejamento.py`; não editar números de janelas/folds manualmente no JSON. API `/api/estudo/resultados` lê resumos locais `pareado_*`; `/api/estudo/documentos/[id]` expõe somente documentos permitidos.

Rotas genéricas preservadas acessam CSVs em `process.cwd()/../dados`; precisarão ser adaptadas ao contrato do novo dataset. Não há servidor Python API separado. Não apresentar dados simulados ou antigos como resultados científicos.
