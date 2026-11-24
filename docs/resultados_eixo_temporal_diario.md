# Resultado do fatorial temporal e penalização

Execução `143e7037d9d6cf620cf3`, concluída em **12/11/2026 às07h44BRT**, após aproximadamente4h04. [Protocolo](protocolo_eixo_temporal_diario.md), [fechamento](../registros/eixo_temporal_diario/fechamento.json), [conferência posterior](../registros/eixo_temporal_diario/conferencia_posterior.json). Não houve novo treino ou backtest na conferência posterior.

**Conclusão:** a adaptação temporal não demonstrou superar a referência A. Com penalização0,001, o erro médio aumentou; sem penalização, a variante temporal melhorou numericamente em relação ao eixo de canais, mas permaneceu próxima e ligeiramente pior que A em erro. Retirar a penalização manteve contribuição funcional dos ramos nas sondas; isso não estabeleceu superioridade preditiva ou operacional. Não promover outro modelo pelo teste retrospectivo.

## Execução e comparabilidade

BTC, treino2020–2023, seleção2024, avaliação retrospectiva2025;1446/351/350exemplos. A=canais/0,001; B=canais/0; C=dias/0,001; D=dias/0. Três seeds42/17/2026. A/B herdados após prova de equivalência da seleção nas primeiras200épocas. Seis ajustes científicos C/D e dois controles completaram200épocas cada; controles exatos aprovados, fora das médias. Mesmas escalas e dados, Adam0,01/StepLR100, perdaRMSE e seleção pelo mínimo global de validação.2026 não foi usado. A adaptação inclui projeção/cabeça e106parâmetros adicionais; preservar atribuição ao CryptoMamba, sem chamar o contraste de transposição pura.

Foram publicadas36séries de previsão (duas fases,12redes,4ensembles,Naive,Ridge) e108carteiras. Trinta reproduções financeiras A/Naive aprovadas, doze recargas de validação e doze reproduções de séries herdadas de validação/teste exatas. Nenhuma violação prudencial. A conferência posterior verificou363hashes, histórias/seleções, métricas por somatórios independentes, médias, ensembles e contabilidade agregada das108carteiras. A auditoria por evento está na publicação original. O lançador Windows registrou código de saída nulo; esse campo isolado não comprova sucesso. A conclusão se sustenta no fechamento, cobertura, controles, preservação, ausência do processo e artefatos conferidos.

## Previsão de2025: médias individuais e ensemble

MSE em retorno decimal ao quadrado. RMSE e MAE abaixo estão em **pontos percentuais do retorno diário**, convertidos de decimal×100. Balanced accuracy é a média dos recalls de alta e queda; Naive zero é ausência de sinal, não classificador que erra tudo.

|Receita|MSE médio das3seeds|RMSE médio(p.p.)|MAE médio(p.p.)|Acerto balanceado médio|
|---|---:|---:|---:|---:|
|A — canais,0,001|0,000477667|2,1856|1,5712|50,38%|
|B — canais,0|0,000502583|2,2414|1,6262|49,52%|
|C — dias,0,001|0,000480945|2,1930|1,5762|49,52%|
|D — dias,0|0,000478768|2,1881|1,5733|50,38%|
|Naive|0,000475433|2,1804|1,5633|Não se aplica|
|Ridge|0,000477301|2,1847|1,5726|50,00%|

|Receita|MSE do ensemble|RMSE(p.p.)|MAE(p.p.)|Acerto balanceado|
|---|---:|---:|---:|---:|
|A|0,000474907|2,1792|1,5637|51,43%|
|B|0,000491742|2,2175|1,5968|48,57%|
|C|0,000479580|2,1899|1,5733|50,00%|
|D|0,000477326|2,1848|1,5690|50,00%|

O MSE médio deC é0,69%maior queA; o deD é4,74%menor queB, mas0,23%maior queA. As médias das quatro receitas permanecem piores queNaive. O ensembleA tem MSE0,11%menor queNaive, diferença pequena e inconclusiva no intervalo principal; seu MAE é ligeiramente maior. Não descrever essa diferença como previsão claramente superior. Média dosRMSE individuais não é a raiz da média dosMSE nem oRMSE do ensemble.

Em validação2024, MSE médioA/B/C/D foi0,000752385/0,000763718/0,000754971/0,000754055; Naive0,000762158 eRidge0,000760213. A seleção de checkpoints usa2024, portanto esses valores não confirmam generalização.

## Operações de2025

Mesma continuidade com95%de nocional, filtro±0,20%, comissão0,05%por lado, slippage provisório0,01%por lado e funding histórico. Decisão diária não obriga encerramento24h depois; manutenção/deltas conforme o sinal. Carteiras independentes; não somar retornos.

|Receita|Retorno médio das3carteiras|Drawdown médio das3carteiras|Retorno do ensemble|Drawdown do ensemble|
|---|---:|---:|---:|---:|
|A|−0,99%|25,39%|+12,83%|8,36%|
|B|−13,91%|35,71%|−26,00%|38,33%|
|C|−11,92%|30,73%|−2,58%|18,96%|
|D|−3,00%|25,90%|−1,33%|20,29%|
|Naive|0%|0%|—|—|
|Ridge|+0,49%|14,40%|—|—|

Naive permanece em caixa. Ridge abriu somente posições vendidas,125dias em um episódio: PnL do movimento do contrato−117,21USDT, funding+195,82USDT, comissão24,32USDT e slippage/ticks4,88USDT, saldo final10.049,41. Seu lucro pequeno não demonstra que acertou quedas. A política não usa funding futuro para decidir; essa decomposição é posterior.

EnsembleA ficou comprado24dias em6episódios; C121dias em30episódios; D114dias em31episódios. Nenhum dos três vendeu a descoberto nesse recorte. B teve98dias comprado e60vendido,99episódios. Não atribuir a diferença de lucro somente a capacidade direcional: exposição, limiar, giro e custos também mudam. Os estresses de slippage0,02%/0,03% estão na publicação completa e não foram critérios de seleção.

Em2024, retornos médios A/B/C/D: +95,13%/+63,36%/+77,47%/+61,58%; ensembles: +95,53%/+106,07%/+73,01%/+92,59%. A inversão de resultados entre anos reforça a distinção entre desempenho na validação e utilidade posterior.

## Seeds, contribuição funcional e incerteza

|Receita|Épocas selecionadas42/17/2026|Retornos individuais2025 na mesma ordem|
|---|---|---|
|A|25/14/44|+10,25%;−13,32%;+0,11%|
|B|69/25/32|+10,40%;−22,95%;−29,17%|
|C|8/194/16|−11,81%;−11,97%;−11,97%|
|D|14/18/12|−1,00%;−19,27%;+11,26%|

D melhorou o MSE frente aB em duas seeds e piorou na42. C piorou frente aA nas três. Não selecionar a seed2026 deD pelo resultado favorável. A época194 deC17 também delimita a conclusão ao orçamento200; não presumir equivalência para1000épocas nessa nova arquitetura.

Nas32janelas fixas de treino, zerar os ramosMamba mudou a saída em RMS exatamente0 nas três redesA; emC,0/6,98e−10/1,00e−8 (valores zero ou residuais emFP32). C17 produziu retorno constante nas sondas e nos conjuntos avaliados, deixando correlação indefinida; não preencher essa medida com zero. B apresentou RMS0,00271–0,00655 eD0,00110–0,00712. Portanto, retirar a penalização evita a supressão funcional observada tanto em canais quanto em dias; trocar o eixo sozinho não resolveu isso. Sonda funcional não prova vantagem doSSM nem explica causalmente todo o desempenho.

IC95%principal de14dias para diferenças deMSE médio das seeds: C−A[−2,535e−6;+1,172e−5]; D−B[−5,405e−5;+4,798e−6]; interação(D−C)−(B−A)[−6,109e−5;+3,483e−6]. Incluem zero. Nos ensembles fixos, C−A[+9,650e−7;+9,652e−6], D−C[−4,428e−6;−2,157e−7] e interação[−3,512e−5;−1,916e−6] excluem zero no bloco principal. Esses intervalos condicionam às três redes escolhidas e reamostram apenas dias; não provam estabilidade entre outras seeds. Os contrastes financeiros principais C−A,D−B e interação incluem zero, tanto para médias individuais quanto para ensembles. Resultados exploratórios, múltiplos contrastes e período conhecido; sem declaração de superioridade universal.

## Implicação para o TCC e evidências

Esta rodada responde a uma hipótese estrutural com resultado útil: temporalidade explícita e contribuição funcional doSSM não bastaram para superar a receita de referência no recorte estudado. A penalização interage com a atividade dos ramos; os efeitos no erro e nas operações são distintos. ManterA como referência preservada, sem concluir que foi encontrada uma estratégia robustamente lucrativa ou que Mamba temporal em geral não funciona. Não abrir outra grade automaticamente.

Evidências canônicas na pasta da execução: [previsões/métricas/contrastes](../dados/experimentos/eixo_temporal_diario_143e7037d9d6cf620cf3/publicacao/previsao.json), [operações e incerteza](../dados/experimentos/eixo_temporal_diario_143e7037d9d6cf620cf3/publicacao/operacoes.json), [índice dos modelos](../dados/experimentos/eixo_temporal_diario_143e7037d9d6cf620cf3/modelos.json), [controles](../dados/experimentos/eixo_temporal_diario_143e7037d9d6cf620cf3/controles.json) e [conferência do executor](../dados/experimentos/eixo_temporal_diario_143e7037d9d6cf620cf3/publicacao/conferencia.json). Checkpoints,sondas,NPZ e ledgersZIP permanecem nessa identidade; nada foi sobrescrito para compor este relatório.
