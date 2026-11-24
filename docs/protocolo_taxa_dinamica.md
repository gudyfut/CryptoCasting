# Mamba16: taxa constante versus redução por estagnação

Versão1, 30/10/2026. Rodada autorizada pelo pedido de seguir a recomendação, organizar o projeto e iniciar os treinos necessários. O agente delimita a autorização a **seis ajustes Mamba16**, seeds17/42/2026/7/123/31415, sem busca automática ou repetição real extra. Controles de reprodução são sintéticos. Implementação em `experimentos/taxa_dinamica/`, análise reutilizável em `analises/`, configuração `configuracoes/mamba16_taxa_dinamica_001.json`, entrada `run_experimento.py taxa_dinamica`, registros `registros/taxa_dinamica/`. Fontes antigas não são editadas/movidas.

## Hipótese e fator único

Partir de taxa0,0002 e reduzir ao estagnar a validação poderá melhorar a otimização/generalização em relação à taxa constante. As curvas existentes melhoram o treino enquanto a validação piora depois da época escolhida; isso motiva a hipótese, mas não prova taxa incorreta ou que reduzir corrige sobreajuste. O critério e esta hipótese foram definidos antes dos novos diagnósticos e treinamentos.

Fator alterado: política da taxa. `ReduceLROnPlateau(mode=min,factor=0.5,patience=2,threshold=0,threshold_mode=abs,cooldown=0,min_lr=0.000025,eps=1e-8)`, atualizado ao final de cada época com MSE global de validação em retorno real. Na semântica do PyTorch, patience2 tolera duas épocas sem melhora e reduz na terceira. A taxa nova vale na época seguinte. Patamar mínimo0,000025. Não reiniciar o contador do encerramento ao reduzir a taxa. Registrar taxa usada/próxima por época. Não trocar por scheduler diferente ou ajustar seus parâmetros depois de observar resultado.

Referência: Mamba16 com AdamW0,0002, seis seeds existentes em `registros/referencias/mamba16_ohlcv24_001.json`. Mesmos BTCUSDT/1h, cinco canais OHLCV, contexto168h, alvo log-retorno24h, dataset0420879c2afc454c7754, mesmas origens e purga24h. Treino2021–23/validação2024/teste2025, scalers somente no treino. Largura32, dois blocos oficiais CUDA, estados16, convolução4, expansão2, dropout0,1,20.257parâmetros. MSE supervisionado sobre alvo padronizado, AdamW com decay0,001/isencões A_log/D, batch64/microbatch32, clipping1, máximo100épocas/paciência10. Seleção pelo menor MSE global de validação, recarga exata antes do teste. Mudança da taxa também muda o decay efetivo por passo de AdamW; mede-se o efeito total dessa política, não um mecanismo isolado.

Ordem42→17→2026→7→123→31415. Não mudar as outras seeds conforme a primeira. Heranças:53séries dos estudos Mamba temporal/LSTM/Naive/ARIMA; nenhum treino antigo é repetido. CryptoMamba/Adam/AdamW permanecem preservados e não guiam esta comparação. Se houver falha, preservar e interromper; retomada só após investigação e processo encerrado, reiniciando somente a célula incompleta com a mesma seed.

## Critério e métricas adicionais

Primário: diferença de MSE médio de validação, scheduler menos taxa constante, seis seeds pareadas. Bootstrap circular por dias7/14/28, principal14,2.000réplicas/seed20261020. Evidência favorável requer média menor e IC95%14dias inteiramente negativo; inconclusivo não promove. Um único contraste primário; outras comparações são auxiliares. Teste2025 e operação não selecionam taxa/época/seed. Médias individuais, não ensemble.

Acrescentar diagnósticos descritivos às previsões existentes e novas: MAE,mediana/P95 de erro absoluto,vitórias/empates/derrotas contra Naive,Pearson/Spearman (indefinidos para constantes),viés/dispersão e trimestres. Todas as origens preservam a avaliação anterior;00UTC descreve decisões diárias sem tratar horas sobrepostas como replicações independentes. Faixas de previsão com cortes20/40/60/80% derivados somente de previsões de validação por seed, aplicados ao teste sem adaptação. Empates podem colapsar faixas; não inventar correlação ou selecionar exemplos pela magnitude do retorno futuro. Diagnósticos não são nova política, seleção por retorno ou escore composto.

## Operação e orçamento secundário

Preservar SpotR0 para comparabilidade histórica. Adicional: mesma Smart2% do backtest8ec8a66648313caa48e3, Spot long/caixa, decisão00UTC, execução00:01, capital10.000USDT, filtros aproximados, custos ideal/base/agravado. São36carteiras novas (6seeds×2períodos×3custos) e18controles de previsão constante (média diária de validação aplicada só no teste), total54. Nenhuma nova estratégia ou limiar. Não confundir2%com stop ou previsão de risco. Benchmarks e carteiras anteriores são herdados, sem sobrescrever o backtest369 ou a ablação do otimizador.

## Qualificação e preservação

Conferir host/GPU/processo/lock e ausência de treinamento concorrente. Conferir entradas/dependências, fontes instaladas oficiais, pesos/seleção/previsões/publicações anteriores por hashes. Ler referências encerradas sem executar novamente seus orquestradores. Guardar preservação antes/depois; uma conferência não é backup externo.

Antes de mercado: testes da trajetória exata do scheduler, contador de parada independente, igualdade das atualizações quando o scheduler não reduz, dimensões/forward/backward/atualização, repetição sintética e recarga exata, além da contabilidade do motor já fixado. Congelar código/configuração/protocolo/ambiente/dados/qualificação e autorização vinculada à identidade. Conservar falhas; não repetir um controle até obter resultado favorável.

Depois: seis conclusões, checkpoints compatíveis, taxas reconstruídas de todas as épocas, seleção somente por validação, previsões/métricas recalculadas, contraste pareado,54carteiras com verificador de lançamentos,manifestos/preservação e relatório. Não executar treinamento concluído para gerar relatórios. Estimativa baseada nos ajustes16anteriores (aprox.9,45s/época,20min para seis ajustes); scheduler pode alongar a convergência. Máximo600épocas no conjunto; preparar/auditar/publicar consome tempo adicional.

2024/2025 já conhecidos: estudo exploratório retrospectivo, não holdout intocado nem walk-forward. Mais seeds não corrigem seleção adaptativa. O objetivo acadêmico é investigar decisões do modelo, sem obrigação de lucro. Sem compra de computação ou ordens reais.
