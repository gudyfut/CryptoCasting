# Adam versus AdamW no CryptoMamba adaptado

Versão 1, 30/10/2026, antes do treinamento desta variante. Rodada autorizada pelo pedido do pesquisador de escolher a próxima hipótese e prosseguir com treino, validação e teste. Orçamento fechado: **seis ajustes novos**, seeds 17/42/2026/7/123/31415, sem repetição de mercado adicional ou busca automática. Os controles de reprodução são sintéticos. Entrada `run_otimizador.py`, código `experimento_otimizador/`, configuração `configuracoes/cryptomamba_adamw_001.json`, registros `registros/otimizador/`.

## Pergunta e decisão

Cinco das seis previsões do CryptoMamba/Adam preservado foram constantes no teste; a sexta quase constante. Isso motiva investigar a regra de atualização/penalização, mas não prova causa. Testar **somente Adam → AdamW** na adaptação, sem confundir com o Mamba16, que já utiliza AdamW. O artigo [Decoupled Weight Decay Regularization](https://arxiv.org/abs/1711.05101) explica a diferença entre penalização L2 acoplada e decay desacoplado em métodos adaptativos. A implementação efetiva é a do PyTorch 2.6 instalado, registrada por versão e hash; não usar opções de versões posteriores.

Adam adiciona a penalização ao gradiente; AdamW aplica decay desacoplado. Manter o valor nominal 0,001 **não iguala a força efetiva de regularização**. O contraste mede o efeito total dessa troca sob receita fixa, não a superioridade universal de um otimizador nem o efeito isolado do momentum. Não baixar a taxa, mudar o decay, reiniciar seeds ou alongar a paciência depois de observar o resultado.

## O que fica fixo

Referência direta: execução `35dd98141ee20d9b8885`, seis CryptoMamba/Adam. Dataset `0420879c2afc454c7754`, BTCUSDT Spot, candles 1h, contexto 168h, cinco canais OHLCV, alvo log-retorno futuro 24h, mesmas origens e scalers ajustados só no treino. Treino 2021–2023, validação 2024, teste 2025; purga de 24h. Arquitetura pública adaptada com projeção temporal 168→14, três grupos de quatro blocos, estados 64, varredura nos cinco canais, 139.317 parâmetros, sem dropout. Não é reprodução literal do artigo CryptoMamba.

Taxa inicial 0,01; batch/microbatch 32; RMSE por lote sobre alvo padronizado, epsilon 1e−8; clipping 1; máximo 100 épocas, paciência 10; StepLR a cada 10 épocas, gamma 0,5; betas 0,9/0,999, epsilon do otimizador 1e−8. Mesmo decay nominal 0,001 e isenções oficiais A_log/D. Mesma inicialização, sequência de embaralhamento e seleção de checkpoint pelo MSE global de validação em log-retorno real. O parâmetro `nome` do otimizador é a única diferença científica na configuração; identificação/hipótese/descrição mudam para rastreabilidade.

Seis novas candidatas; 59 referências preditivas herdadas sem reexecução de treino. Ordem 42→17→2026→7→123→31415; a primeira seed não autoriza ajustes nas seguintes. O executor para em falha e conserva a tentativa. Uma retomada exige investigação, processo encerrado e integridade, preservando a incompleta e reiniciando somente a mesma célula. Não repetir executor concluído para relatórios.

## Critério e análise

Primário: média aritmética das diferenças de MSE de validação, AdamW menos Adam, nas seis seeds pareadas. Bootstrap circular sobre dias, blocos 7/14/28, principal 14, 2.000 réplicas e seed 20261020. Evidência favorável requer média menor e IC95% principal inteiramente abaixo de zero. Caso inconclusivo, não substituir a referência. É um único contraste primário; resultados com Mamba16/LSTM/Naive/ARIMA são auxiliares, sem promoção automática.

Métricas de teste, MAE/RMSE, preço reconstruído, direção, viés e dispersão das previsões são secundários. Diagnóstico por seed: amplitude, desvio, quantidade de previsões distintas, época escolhida e normas dos pesos. Constância não pode ser corrigida descartando checkpoints ou escolhendo uma época pelo teste. Médias são de modelos individuais, não ensemble. Publicar todas as seeds, inclusive as que não operarem ou piorarem.

## Eixo operacional preservado e avaliação adicional

Manter SpotR0 com a mesma receita anterior para comparação histórica. Seus custos, contabilidade e limites permanecem identificados; não substituir seus números pelos da carteira retida. A comparação de otimização não altera entradas, modelos ou política ao mesmo tempo.

Adicionalmente, usar o motor de carteira retida já congelado em `8ec8a66648313caa48e3`, sem mudar regras: Smart 2%, decisão 00UTC, execução 00:01, capital 10.000 USDT, Spot long/caixa, custos ideal/base/agravado e filtros aproximados daquele protocolo. São **36 simulações Smart** (6 seeds × 2 períodos × 3 custos), mais **18 controles Smart de previsão constante** (média das previsões diárias de validação, aplicada somente no teste). Total 54 novas simulações de carteira, sem novas políticas ou parâmetros. Comparar com as séries anteriores já publicadas, comprar/manter e caixa; a publicação anterior de 369 simulações permanece intacta. A hipótese de treinamento é única; avaliações adicionais não selecionam o otimizador ou uma seed por lucro.

## Qualificação, preservação e exposição

Antes: conferir dados/fontes/checkpoints/publicações anteriores e ausência de processo vivo; guardar hashes de preservação. Validar diferença única da configuração e do treinador por AST; conferir equivalência Adam/AdamW sem decay e diferença com decay em gradientes controlados, isenções e dimensões, forward/backward/atualização finitos, duas repetições sintéticas e recarga exata. Congelar fontes, receita, ambiente, dados, protocolo e autorização vinculada à identidade, antes do primeiro ajuste real.

Depois: conferir seis conclusões e recargas, metadados e dimensões dos checkpoints, seleção somente por validação, métricas por origem, contraste recalculado, custos e livro de carteira por verificador independente, cobertura e preservação antes/depois. Fontes/configurações/recibos anteriores permanecem imutáveis. Publicações e ferramentas posteriores de leitura não chamam o treinamento novamente.

2024 e 2025 já foram usados e consultados; a escolha desta hipótese ocorre após essas consultas. O contraste é exploratório retrospectivo e condicional aos modelos, não holdout novo, walk-forward ou prova de lucro futuro. Não se presume que mais seeds resolvam seleção adaptativa ou mudança de regime. Arquivos locais não equivalem a backup externo; não há compra de computação nem ordens reais.
