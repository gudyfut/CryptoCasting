# Ablação dos ramos Mamba — protocolo 001

Autorizado pelo pesquisador em **12/11/2026**: BTC, três seeds e 200 épocas completas, camadas lineares treinadas do zero contra a referência A, restante preservado. [Configuração](../configuracoes/ablacao_linear_diaria_001.json). Pergunta: os ramos Mamba acrescentam desempenho sob esta receita, em comparação às mesmas projeções treinadas sem esses ramos? Não pressupor melhoria, equivalência ou irrelevância universal do SSM.

## Intervenção e atribuição

A é a referência de canais derivada do CryptoMamba de Sepehri et al., commit `fef42727861a9c3a32241283ab981ef21a49e291`, com Mamba-1 oficial. A fonte/licença MIT permanece no acervo. L conserva as três projeções 14→16→32→1 e a combinação de seis canais→1. Remove os 12 blocos CMBlock, incluindo seus LayerNorm e ramos Mamba, substituindo-os por identidades. Sem novas ativações, sem alterar eixos, sem reparametrizar as projeções em uma regressão única. Não é nova arquitetura SSM nem reprodução integral do artigo publicado.

A tem **136.952 parâmetros**; L tem **824**, distribuídos em 240+544+33+7. A diferença é consequência da ablação. L é uma composição afim, com coeficientes canal×dia separáveis; seu treinamento fatorado com Adam/L2 não equivale ao ajuste Ridge de 84 coeficientes. A baseline Ridge permanece separada.

Para cada seed, construir A na mesma ordem e então remover os blocos **antes de qualquer atualização**. Os oito tensores das projeções mantêm nomes, valores e estado RNG da inicialização de A. Não carregar pesos de mercado para inicializar L. Os parâmetros restantes recebem Adam com penalização uniforme **0,001**, inclusive biases; não confundir esta ablação com a penalização seletiva S.

Desativar ramos de um checkpoint já treinado responde sobre a inferência; treinar L desde o início também investiga a contribuição dos ramos durante o aprendizado. Igualdade na inferência não prova igualdade das trajetórias. Remover LayerNorm também faz parte da remoção do ramo; não atribuir eventual diferença a uma matriz isolada do SSM.

## Dados, treinamento e seleção

BTC USD-M Binance, candles diários, seis canais Timestamp/Open/High/Low/Close/Volume, contexto14, entrada `[lote,6,14]`, previsão de retorno simples entre o último fechamento e o fechamento seguinte. Timestamp em segundos, volume/1e9; z-score dos seis canais ajustado exclusivamente nos candles únicos das janelas de treino, sem clipping. Alvo não padronizado. Dados, lacunas, populações e escalas idênticos a A: treino2020–2023, validação2024, teste retrospectivo2025, respectivamente1446/351/350 exemplos.2026 excluído desta rodada. A repetição dos períodos conhecidos não produz novo holdout.

Adam0,01, betas0,9/0,999 e epsilon1e−8, weight_decay0,001 uniforme; StepLR100/gamma0,5 no final da época; lote32 com lote final parcial. Perda `sqrt(MSE + 1e-8)` por lote. **200 épocas completas**, sem early stopping ou clipping; teto técnico4h por ajuste. Mesma permutação por época controlada por gerador CPU e seed. Checkpoint escolhido pelo menor RMSE global de validação, primeiro em empate. Nenhuma seleção por teste, lucro ou diagnóstico dos ramos.

Seeds42/17/2026. Herdar A somente após reconferir igualdade de dados, fontes, recarga e equivalência da seleção restrita às primeiras200 épocas. A teve1000 épocas originalmente, mas os checkpoints selecionados coincidem com os mínimos do prefixo200. Herança não conta como novo treino.

## Qualificação e controles

Antes de congelar: integridade dos estudos anteriores e mercados; contrato de único fator; testes causais de dados/alvo/escalas; inicialização e RNG iguais por seed; remoção de todos os Mamba/LayerNorm; contagem de parâmetros; contratos de forma/float32/CUDA; saída e gradientes das projeções iguais aos de A com ramos zerados, em lotes1/6/32; decomposição afim; reprodução de seis épocas artificiais A/L com65 exemplos; igualdade de A com o treinador anterior; recarga das três referências e prova de prefixo200. Ensaios sintéticos não selecionam receita nem acessam teste para treinar.

O treinador reutiliza o corpo aprovado em namespace privado, substituindo somente o construtor. O avaliador reutiliza o corpo aprovado, resolvendo receita/carregador no novo namespace. Nenhum global de outro estudo é modificado. Fontes, protocolo, configuração, testes e dependências são congelados antes da execução.

Ordem de mercado: **controle A42 → L42 → controle L42 → L17 → L2026**. Cada ajuste tem200 épocas. A42 deve reproduzir exatamente história científica, seleção, todos os checkpoints e previsões do prefixo herdado. L42 deve reproduzir exatamente sua primeira execução. Controles ficam fora das médias. Falha bloqueia as etapas seguintes; conservar o incidente e investigar, sem afrouxar tolerâncias ou repetir até passar. São três ajustes científicos novos, dois controles e três referências herdadas.

Antes de iniciar: conferir host, processos, GPU, PID, boot, locks, logs e progresso. Exclusão mútua por ciclo e GPU. Nenhuma retomada automática, substituição de fontes ou duplicação de processo vivo. L permanece em CUDA/float32 para controlar o ambiente; não mudar CPU, batching ou precisão para acelerar.

## Avaliação preditiva e operacional

MSE principal; RMSE, MAE, viés, direção/recalls, correlação e dispersão secundários. Média/desvio das três redes separados do ensemble de suas previsões. Naive de retorno zero e Ridge com grade anterior selecionada exclusivamente em validação. Contraste principal L−A; comparação com baselines secundária. Bootstrap pareado por seeds e blocos7/14/28dias,14principal,2000 réplicas. Ensemble fixo reamostra dias, não novas redes. Intervalos exploratórios, três seeds e períodos conhecidos; intervalo incluindo zero não demonstra equivalência, e não há correção da busca histórica.

Mesmo backtest de continuidade: decisão diária, mantém lado persistente, negocia apenas diferenças para exposição alvo95% do patrimônio liquidável; encerra em caixa/inversão/fim. Filtro±0,2%, capital10milUSDT, latência1min, comissão0,05% por lado, slippage provisório0,01% e estresses0,02%/0,03%, funding histórico e filtros BTC, sem stop/take. Não fechar/reabrir artificialmente a cada dia. Sem ordens reais ou certificação de custos históricos.

60 carteiras: seis redes, dois ensembles, Naive e Ridge × validação/teste × três cenários de custo. Mesmo auditor independente por colateral/preço médio e lotes inteiros;30 reproduções A/Naive obrigatórias. Conservar falhas prudenciais e não excluí-las para melhorar médias. Métricas, lucro, drawdown, exposição, funding e custos são dimensões distintas.

Após a grade, repetir o diagnóstico de desativação em **todas** as populações de treino/validação/teste dos seis checkpoints e decompor as projeções em coeficientes afins. Nenhum peso atualizado por essa análise. Em L, contribuição zero dos ramos é estrutural, não colapso aprendido. Resíduo da decomposição em float64 pode incluir arredondamento frente ao forward float32. Tempo de execução e número de parâmetros serão informados; tempos antigos em outra carga não provam ganho causal de velocidade.

## Registro e encerramento

Código/testes no namespace `ablacao_linear_diaria`; recibos em `registros/ablacao_linear_diaria/`; dados preparados, fontes, todos os checkpoints, tentativas e publicações em `dados/experimentos/ablacao_linear_diaria_<id>/`. Preservar referências e penalização seletiva antes/depois. Finalizar após cobertura, controles e auditorias, independentemente do resultado. Não acrescentar hipóteses, moedas, seeds, épocas ou filtros por desempenho. Incorporar a conclusão ao artigo distinguindo necessidade na inferência, contribuição no aprendizado e utilidade operacional, sem chamar a versão reduzida de Mamba.
