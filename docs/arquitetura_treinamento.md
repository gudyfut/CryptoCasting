# Treinamento, seleção, checkpoints e avaliação

Ablação de 12/11/2026: `codigo/experimentos/ablacao_linear_diaria/` reutiliza o corpo do treinador aprovado em namespace privado, substituindo apenas o construtor. A mantém o núcleo completo; L remove os ramos antes do primeiro passo. Adam com weight_decay0,001 uniforme, lote32, taxa0,01/StepLR100, perda RMSE por lote e seleção RMSE global de validação permanecem iguais;200épocas completas. Qualificação:98testes, pesos/RNG iniciais pareados, seis épocas sintéticas repetidas exatamente e recargas de A aprovadas. A42 e L42 passaram pelos controles integrais exatos antes das demais seeds; a rodada encerrou com60carteiras e sem falhas. [Resultados](resultados_ablacao_linear_diaria.md). [Protocolo](protocolo_ablacao_linear_diaria.md), [estado vivo](../registros/ablacao_linear_diaria/estado.json). Não confundir qualificação aprovada com conclusão dos controles completos.

Extensão de12/11/2026: `codigo/experimentos/penalizacao_seletiva_diaria/` preserva o algoritmo diário e explicita grupos Adam em `otimizacao.py`: isenta marcadores oficiais, LayerNorm e biases na candidata S; A conserva penalização uniforme. Testes AST restringem alterações ao otimizador, marcos e diagnóstico L2 efetivo; inicialização/forward/dados e algoritmo de seleção são iguais. Controle novo A42 reproduz prefixo200; S42 é repetido antes de17/2026. [Protocolo](protocolo_penalizacao_seletiva_diaria.md). Os controles completos A42/S42 foram aprovados; fechamento e limites estão no [relatório](resultados_penalizacao_seletiva_diaria.md). Ensaios sintéticos e controles reais têm funções distintas.

Extensão de12/11/2026: `codigo/experimentos/eixo_temporal_diario/` coordena o fatorial de eixo/penalização. O treinador reutiliza as operações da função instrumentada por namespace privado, trocando somente o construtor e os marcos de observação; não modifica globals dos ciclos anteriores.200épocas completas, Adam0,01/StepLR100, mínimo global de validação. A/B preservados com prova da seleção no prefixo200, controle antigo e recarga exatos; C/D novos com repetição integral da seed42 antes das demais. [Protocolo](protocolo_eixo_temporal_diario.md), [estado](../registros/eixo_temporal_diario/estado.json). Dados de teste só entram na avaliação após a grade; custos de continuidade são camada posterior. Nenhuma alteração no executor congelado após início.

Extensão de 11/11/2026: `codigo/experimentos/taxa_diaria/` isola a taxa inicial 0,001 versus 0,01, ambas com Adam sem penalização. Reutiliza a função de treinamento sem penalização e congela as dependências reais em `codigo/`. Cache de validação foi numericamente equivalente no ensaio, mas não aprovado por ganho insuficiente; a execução conserva o treinador original. Controle compara trajetória, épocas, pesos de todos os checkpoints e previsões exatamente. A avaliação usa custos vigentes comuns, identifica a releitura financeira e compara com a referência preservada, sem chamar seu executor encerrado. [Protocolo](protocolo_taxa_diaria.md), [estado](../registros/taxa_diaria/estado.json).

Extensão ADR0036: `codigo/experimentos/generalizacao_moedas/` coordena modelos independentes ETH/BNB/XRP com a receita padronizada congelada. Reutiliza o treinador de retorno sem alterar seu código; escala/moeda/execução vinculadas ao checkpoint, três seeds e controle por moeda. [Protocolo](protocolo_generalizacao_moedas.md). As receitas históricas abaixo não são instruções para sobrescrever a rodada atual.

Extensão ADR0035: `codigo/experimentos/sem_penalizacao_diaria/` isola a ablação de weight_decay0. Treinador conserva operações da referência e acrescenta `observacao.py` em marcos predefinidos; equivalência exata de trajetória é qualificada antes do uso. Hooks temporários não alteram pesos/RNG ou seleção. Simulador e carregador da referência permanecem herdados; novos resultados têm namespace próprio.

Extensão ADR0034: `codigo/experimentos/padronizacao_diaria/` coordena a nova transformação de entrada; importa o treinador de retorno sem alteração. Avaliador isolado compara `referencia` versus `padronizado`, ambas prevendo retorno, com escalas congeladas por execução.

Extensão ADR0033: `codigo/experimentos/alvo_retorno_diario/` usa o mesmo construtor reproduzível, mas treinador/seleção em retorno simples decimal. Publicação guarda retorno nativo e preço equivalente separadamente; `comparacao.py` usa origens/seeds/unidades comuns da referência preservada. Não carregar essas saídas como preço bruto.

Extensão ADR0032: `codigo/experimentos/cryptomamba_reproducivel/` isola o backend de referência oficial CUDA, treinador/avaliador correspondentes e nova identidade; a implementação diária original permanece congelada. Não reutilizar seu carregador fused para checkpoints da reexecução: usar o carregador do namespace correspondente.

Extensão ADR0031: `codigo/treinamento/cryptomamba_diario.py` implementa Adam/RMSE de preço/StepLR100 e1000épocas, com seleção global emV e teste fora do treinador. `codigo/experimentos/cryptomamba_diario/` coordena qualificação,identidade,controle real,grade e publicação. As camadas históricas abaixo permanecem intactas; consultar o protocolo diário para o contrato atual.

Esta camada integra [dados](arquitetura_dados.md) e [modelos](arquitetura_modelos.md), mantendo o [desenho OHLCV](desenho_ohlcv24.md). A preparação anterior `92e3eb82e3f6adf99994` permanece intacta. A execução modular terá identidade própria e aguarda autorização explícita do pesquisador. Evidências e estado ficam em `registros/treinamento/`.

## Responsabilidades

```text
codigo/mercado_binance/       coleta e candles auditados
codigo/entradas_modelo/       canais, alvo, janelas, populações, escalas
codigo/modelos/              arquiteturas e inferência; não ajusta parâmetros
codigo/treinamento/
  configuracao.py     verifica desenho e orçamento da rodada
  otimizacao.py       seed, AdamW, microbatches e clipping
  neural.py          treino e seleção exclusivamente por validação
  arima.py           ajustes dos nove candidatos e seleção por validação
  selecao.py         desempates e parada antecipada
  checkpoints.py     pesos, vínculo ao contrato, integridade e recarga
  avaliar.py         previsões após seleção e conferência da recarga
  preservacao.py     tentativas publicadas e exclusão mútua de processos
  ciclo.py           preparação, verificação e execução explícitas
  qualificacao.py    ensaio sintético e conferência dos dados reais
  ambiente.py        identidade do ambiente CUDA oficial
codigo/avaliacao/
  metricas.py        erros de previsão em log-retorno real
  mercado.py         minutos auditados para a política Spot
  spot.py            execução simulada da política predefinida
  publicacao.py      conferência independente, contrastes e publicação
run_treinamento.py    único ponto de entrada da execução modular
```

Os executores históricos não são importados pela nova cadeia. As funções de métricas e política Spot foram migradas da referência preservada, mantendo suas regras. A publicação deriva daquela preparação, adaptando o identificador de candle e a origem dos minutos; não importa seu executor. A configuração anterior é lida como referência de decisões científicas: divergências na rodada inicial são rejeitadas. Ampliar a investigação requer outro ciclo, não editar fontes congeladas.

## Do exemplo ao ajuste

Cada exemplo tem uma janela de168 candles×5 canais e um alvo: log-retorno terminal das próximas24h. As janelas são construídas pelo consumidor já conferido. Os scalers continuam os publicados com as entradas; o treinamento não os recalcula. O cache de janelas de treino em GPU preserva valores, eixos e sequência dentro de cada janela. Embaralham-se as linhas do treino a cada época; nenhuma linha muda de partição e nenhum candle dentro da janela é embaralhado.

Mamba e LSTM minimizam MSE do alvo padronizado de treino. Batch64 com microbatch32: a soma dos erros de cada pedaço é dividida pelo tamanho **efetivo** daquele lote; só depois de todos os pedaços há clipping e uma atualização AdamW. Assim o último lote incompleto não recebe peso excessivo. Taxa0,0002, decay0,001, clipping1, até100 épocas/paciência10. A_log e D marcados pelo Mamba oficial têm decayzero; os demais parâmetros conservam a regra prevista. Os grupos efetivos são registrados por nome.

A cada época, `eval()` desliga dropout, gradientes ficam desativados e as previsões da validação voltam à unidade real de log-retorno. O menor MSE de validação seleciona a época. Empate exato conserva a época mais antiga; dez épocas consecutivas sem melhora encerram o ajuste. Teste e lucro não selecionam época. A semente controla inicialização, dropout e ordem dos exemplos; há três ajustes independentes por rede, não três pedaços do mercado.

O ARIMA recebe somente o prefixo permitido de treino para estimar cada uma das nove ordens. Candidatos não convergidos ou inválidos são registrados, sem descarte silencioso; ausência de candidato válido interrompe o ciclo. A validação seleciona MSE, depois menor p+q, p e q. A ordem selecionada não é reajustada com validação/teste. Durante previsão os estados filtrados evoluem com o passado disponível; os coeficientes ficam fixos. Naive devolve zero de log-retorno real e não treina.

## Seleção e recarga verificáveis

Cada melhora gera `checkpoints/epoca_NNN.pt`, sem sobrescrever pesos de uma época anterior. `selecao.json` aponta o arquivo escolhido e seu SHA256. O pacote liga pesos à família, arquitetura, contrato dos dados, canais, escalas, execução, célula, seed, configuração de treinamento, época e MSE de validação. Uma janela de mesma dimensão mas receita diferente não é intercambiável.

Ao terminar, a rede recarrega o checkpoint selecionado e refaz o MSE que justificou a escolha. Só então produz validação/teste/operacional. Outra instância carrega os mesmos pesos e deve gerar previsões **exatamente iguais** em todas as origens. ARIMA também é recarregado dos parâmetros publicados. As previsões são salvas com as mesmas populações do conjunto; verdade observada é juntada pelo avaliador após prever. Métricas são recalculadas de forma independente com somas escalares, evitando confiar apenas no número emitido durante o treino.

Os controles Mamba42/LSTM42 repetem ajustes inteiros. São executados depois dos principais de seed42 e antes das outras seeds. Exigem mesma época, diferença máxima de previsão≤1e−5 e relativa de MSE≤1e−4. Esses limites de repetição toleram diferenças dos kernels; a recarga de um mesmo checkpoint exige igualdade exata. Uma reprovação é um problema a investigar, não autorização para procurar uma repetição favorável.

## Congelamento e retomada

```text
python -m comandos.treinamento qualificar
python -m comandos.treinamento preparar --qualificacao <recibo aprovado>
python -m comandos.treinamento conferir
# Somente depois do Ok explícito e de registrar sua autorização:
python -m comandos.treinamento executar --autorizacao <recibo da autorização>
```

Qualificação usa dados artificiais para atualizar pesos e ensaiar o caminho completo; dados reais só passam por verificações de integridade, dimensões e alinhamento. Não existe autorização de mercado implícita no sucesso do ensaio. A preparação congela fontes, configurações, hashes dos dados, ambiente, protocolo e qualificação; registra `aguardando_ok`. O recibo futuro de autorização precisa identificar a execução e todas as dez células: seis ajustes neurais principais, dois controles, Naive e ARIMA com nove candidatos.

O executor exige Linux/WSL, CUDA e implementação oficial. Antes de executar/retomar verifica a cadeia de artefatos e as fontes. Um lock exclusivo e o registro de host, boot, PID e início real do processo impedem duplicação. Um processo indicado em outro computador exige conferência naquela máquina. Depois de encerramento inesperado, `--retomar` é explícito; incidente e tentativa incompleta permanecem guardados. Um ajuste incompleto recomeça do início com a mesma seed; não se afirma continuação do otimizador a partir do melhor checkpoint.

Tentativas concluídas têm manifesto e são reutilizadas somente se íntegras. Duas tentativas concluídas para uma célula são erro, nunca escolha do melhor resultado. Publicações usam pastas novas; uma execução concluída não pode ser reexecutada para refazer relatórios. Logs, épocas, candidatos inválidos, interrupções e ensaios falhos são evidências. Binários locais devem acompanhar recibos quando houver backup científico; Git sozinho não contém os pesos ou dados.

## Avaliação e limites

As médias são de perdas das três seeds; não se transforma silenciosamente o conjunto em um ensemble. Intervalos pareados usam blocos circulares de dias corridos14/7/28,2.000 réplicas, condicionais aos modelos ajustados. Origens horárias com alvos sobrepostos não são observações independentes. A validação2024 serve à seleção; o teste2025 é retrospectivo e já conhecido no projeto, não um holdout intocado. Esta divisão fixa não é walk-forward.

A política Spot conserva os sinais diários, saída24h depois, custos, latência e regras de indisponibilidade do desenho. O adaptador lê os minutos publicados com os campos explicitamente nomeados; não confunde volume com quantidade de negócios. O orçamento de comparação econômica não altera o critério de seleção dos modelos. A verificação técnica aumenta a confiança no procedimento, mas não garante bom desempenho, lucro ou ausência de toda limitação estatística.
