# Ablação linear diária — resultados e interpretação

**Atualização de 13/11/2026:** o [fechamento fatorial e a replicação entre ativos](#fechamento-fatorial-e-replicação-entre-ativos) foram concluídos na execução `18efadab3f5a3771aacd`. A seção inicial conserva a análise do ciclo BTC de 12/11; a extensão abaixo acrescenta L0 e ETH/BNB/XRP, sem substituir os resultados anteriores.

Execução `9cf2c1776eade0b54937`, concluída e conferida em **12/11/2026 às 19h50 BRT**, cerca de 24min21s após o início. [Protocolo congelado](protocolo_ablacao_linear_diaria.md), [fechamento](../registros/ablacao_linear_diaria/fechamento.json) e [conferência posterior](../registros/ablacao_linear_diaria/conferencia_posterior.json).

**Conclusão:** retirar os ramos Mamba antes do treinamento produziu erro numericamente muito próximo de A, com MSE médio 0,095% menor e 99,40% menos parâmetros. O resultado operacional de 2025 melhorou nesta simulação: média das carteiras de −0,99% para +6,75%; ensemble de +12,83% para +17,01%. Os intervalos principais incluem zero; não há superioridade estatística estabelecida nem prova formal de equivalência. A arquitetura completa não demonstrou benefício incremental neste contraste.

## Comparação e verificações

A conserva os 12 CMBlock derivados do CryptoMamba de Sepehri et al., com 136.952 parâmetros. L remove esses blocos, incluindo LayerNorm, antes de qualquer atualização; restam as projeções afins 14→16→32→1 e a combinação dos seis canais, com 824 parâmetros. A inicialização das projeções e o estado RNG são idênticos por seed. Nenhum peso treinado foi herdado por L. L é uma composição linear afim fatorada, distinta do Ridge de 84 coordenadas usado como referência auxiliar; não é um novo SSM.

BTC USD-M, seis canais padronizados exclusivamente pelo treino, contexto14, alvo retorno simples diário. Treino2020–2023, validação2024 e avaliação retrospectiva2025:1446/351/350 exemplos. Mesmas seeds42/17/2026, Adam0,01 e weight_decay0,001 uniforme, StepLR100/gamma0,5, lote32, perda `sqrt(MSE+1e-8)` e200épocas completas. Seleção por menor RMSE global de validação, sem early stopping.2026 não foi usado.

- Qualificação:98testes e repetições sintéticas exatas aprovados.
- Controle A42 novo:200épocas, todos os checkpoints, trajetória científica e previsões exatamente iguais ao prefixo da referência preservada.
- Controle L42 novo: repetição integral exata. L17/L2026 só foram liberadas após sua aprovação.
- Três ajustes científicos L novos; três referências A herdadas com prova de seleção no prefixo200. Controles fora das médias.
- Épocas selecionadas:25/14/44 nas seeds42/17/2026, tanto em A quanto em L.
-60carteiras completas,30reproduções financeiras A/Naive aprovadas, nenhuma falha prudencial.
- Conferência posterior:320hashes da execução,1.427artefatos anteriores,168fontes e suas cópias;20séries preditivas,4ensembles exatos, seleções e contabilidade agregada das60carteiras. Ambos os controles de pesos/históricos/previsões foram reconferidos em WSL, sem novo treinamento.

A divergência máxima entre métricas recalculadas e publicadas foi2,22e−16, incluindo medidas derivadas como habilidade contra Naive. O leitor posterior não repetiu forward CUDA, bootstrap ou auditoria financeira por evento/minuto; essas verificações estão no executor congelado. Foram conferidos120membros do ZIP e10.314transições consecutivas do mesmo lado, sem fechamento/reabertura diária artificial. O `exit_code` nulo do lançador Windows não comprova sucesso isoladamente; o fechamento, processo encerrado, cobertura e controles sustentam a conclusão.

## Previsões no teste retrospectivo de 2025

MSE em retorno decimal ao quadrado; RMSE/MAE em **pontos percentuais do retorno diário**. Menor é melhor. Acerto balanceado é a média dos recalls de alta e queda. Naive prevê retorno zero e não é tratado como classificador ativo.

| Resultado | MSE | RMSE (p.p.) | MAE (p.p.) | Acerto balanceado |
|---|---:|---:|---:|---:|
| A — média das três redes | 0,000477667 | 2,1856 | 1,5712 | 50,38% |
| L — média das três redes | 0,000477213 | 2,1845 | 1,5704 | 50,29% |
| A — ensemble | 0,000474907 | 2,1792 | 1,5637 | 51,43% |
| L — ensemble | 0,000474584 | 2,1785 | 1,5634 | 48,57% |
| Naive | 0,000475433 | 2,1804 | 1,5633 | Não se aplica |
| Ridge | 0,000477301 | 2,1847 | 1,5726 | 50,00% |

O MSE médio de L caiu0,0950% frente a A; o MSE do ensemble caiu0,0679%. São mudanças pequenas, sem melhora direcional correspondente. A média das redes L ainda tem MSE0,3744% maior que Naive. O ensemble L tem MSE0,1785% menor que Naive, mas MAE ligeiramente maior; não demonstrou vantagem robusta sobre persistência.

O IC95% principal de L−A, bootstrap pareado com blocos14dias, é [−2,99999e−6; +1,00000e−6] para MSE médio e [−1,15380e−6; +3,26839e−7] para o ensemble. Para ensemble L−Naive: [−4,44929e−6; +3,86298e−6]. Todos incluem zero. Os intervalos são exploratórios; três seeds não são três mercados independentes. O ensemble fixo reamostra dias, não novas redes. Não há correção da busca histórica nem teste formal de equivalência.

## Simulações de operações em 2025

350decisões, capital10.000USDT, exposição alvo95%, filtro±0,2%, comissão0,05% e slippage provisório0,01% por lado, funding histórico e latência1min. Mesmo motor de continuidade: mantém posições quando o lado persiste, negociando apenas diferenças; encerra em caixa/inversão/fim. Sem stop/take, ordens reais ou certificação dos custos históricos da exchange.

| Resultado | Retorno líquido | Drawdown máximo | Capital final (USDT) | Dias posicionado |
|---|---:|---:|---:|---:|
| A — média das carteiras | −0,99% | 25,39% | 9.901,31 | 142,33 |
| L — média das carteiras | +6,75% | 24,19% | 10.674,95 | 134,33 |
| A — ensemble | +12,83% | 8,36% | 11.282,53 | 24 |
| L — ensemble | +17,01% | 8,32% | 11.701,45 | 18 |
| Naive — caixa | 0,00% | 0,00% | 10.000,00 | 0 |
| Ridge | +0,49% | 14,40% | 10.049,41 | 125 |

Médias individuais são estatísticas de três carteiras independentes. Não representam uma carteira executada, e o drawdown médio não é o drawdown de uma curva combinada. O ensemble calcula primeiro a média das previsões, depois gera uma carteira única.

A melhora de L é +7,74p.p. na média dos lucros e +4,19p.p. no ensemble. O IC95% da diferença de crescimento log diário L−A inclui zero: médias [−0,00035398; +0,00113842], ensemble [−0,00018309; +0,00046515]. Essas unidades são crescimento log diário, não porcentagens de retorno total. O ganho observado é real dentro da simulação, mas sua repetição em outro período não está demonstrada.

### O que mudou na operação do ensemble

Em2025, A e L diferiram na decisão de **seis dias**. L ficou comprado em18dias, todos também negociados por A; ficou em caixa nos outros seis dias em que A permaneceu comprado. Nenhum ensemble abriu venda. Portanto, este resultado não demonstra habilidade de lucrar dos dois lados do mercado.

Apesar de menos dias exposto, L teve8episódios de posição e18ordens, contra6episódios e14ordens de A. A diferença de capital final de+418,93USDT resulta de +438,79 de movimento do contrato, +4,53 de funding e −24,39 de comissões/slippage adicionais. Não foi economia de custos que explicou o ganho do ensemble. As seis decisões alteram também a trajetória do capital e o dimensionamento posterior; não interpretar a diferença inteira como soma isolada de seis retornos diários.

Pequenas mudanças na magnitude da previsão podem cruzar o filtro±0,2% e modificar as operações, mesmo com MSE quase igual. O ensemble L teve acerto balanceado global inferior ao de A, mas essa métrica mede todos os dias; a política atua só no subconjunto cujo sinal passa o filtro. Isso explica a possibilidade de rankings diferentes, sem demonstrar superioridade geral da previsão.

### Estabilidade entre seeds

| Seed | MSE A | MSE L | Retorno A | Retorno L | Drawdown L |
|---|---:|---:|---:|---:|---:|
| 42 | 0,000478476 | 0,000479329 | +10,25% | +3,36% | 31,09% |
| 17 | 0,000478824 | 0,000476343 | −13,32% | +15,77% | 23,19% |
| 2026 | 0,000475700 | 0,000475966 | +0,11% | +1,11% | 18,30% |

Somente a seed17 melhorou MSE;42e2026 pioraram ligeiramente. O lucro melhorou em dois pares, mas a seed17 explica a maior parte da melhora média. Todas as carteiras L terminaram positivas, com quedas máximas ainda relevantes. O desvio dos retornos entre seeds caiu de11,82 para7,89p.p.; três observações não estabelecem estabilidade geral. L42 e L17 operaram somente compradas; L2026 somente vendida.

### Sensibilidade ao slippage por lado

| Slippage | A médio | L médio | A ensemble | L ensemble |
|---|---:|---:|---:|---:|
| 0,01% | −0,99% | +6,75% | +12,83% | +17,01% |
| 0,02% | −1,18% | +6,42% | +12,70% | +16,83% |
| 0,03% | −1,44% | +6,14% | +12,54% | +16,66% |

A ordem numérica se mantém nesses cenários predefinidos. Isso não comprova robustez a outros mercados, regimes ou condições de execução.

## Validação de 2024

O MSE médio de L foi0,000752193, contra0,000752385 de A (−0,0255%); no ensemble0,000751896 contra0,000752079 (−0,0243%). Lucro médio+95,50% em L e+95,13% em A; drawdown médio32,95% e33,69%, respectivamente.

Os ensembles tiveram **as mesmas decisões, ordens e curva financeira**: +95,53% de retorno e34,58% de drawdown,312dias comprados e nenhum vendido. Previsões numéricas diferentes não mudaram a decisão operacional nesse período.2024 selecionou checkpoints e não é confirmação independente.

## Contribuição funcional e custo computacional

Desativar os ramos dos três checkpoints A novamente não alterou nenhuma previsão, com igualdade exata float32 nas populações completas de treino, validação e teste. A decomposição afim dos seis checkpoints reproduziu as saídas residuais com diferença máxima6,47e−9, compatível com arredondamento. Em L não há ramos por construção; não chamar esse fato de colapso aprendido.

L chegou a resultados preditivos próximos com99,40%menos parâmetros. Os três ajustes científicos de200épocas duraram54,45s,61,87s e54,10s, média56,81s. O controle A42 levou1180,23s, aproximadamente19min40s. A razão observada é cerca de20,8vezes; trata-se de tempo nessa execução, incluindo instrumentação e salvamento, não de benchmark dedicado nem garantia para outros ambientes.

O resultado não elimina a possibilidade de os ramos terem influenciado as trajetórias de aprendizado de A: A e L tiveram pesos/previsões diferentes. Contudo, não foi identificado benefício incremental da arquitetura completa nas métricas examinadas sob esta receita. Não extrapolar para outros contextos, alvos, regularizações, inicializações ou dados.

## Contribuição para o TCC

Formulação sustentada: **“No recorte BTC e no protocolo avaliados, remover os blocos Mamba antes do treinamento reduziu substancialmente o número de parâmetros e o tempo observado de ajuste, mantendo erro numericamente próximo ao da arquitetura completa. Não foi demonstrado benefício incremental dos blocos; diferenças pequenas nas previsões produziram resultados operacionais distintos pela política de decisão. Os ganhos financeiros observados permanecem retrospectivos e estatisticamente inconclusivos.”**

Isso acrescenta um estudo de ablação à adaptação do CryptoMamba, sem reivindicar arquitetura original nem invalidar o artigo publicado. A referência A continua preservada; L constitui evidência de simplicidade e uma comparação útil, sem promoção por teste conhecido. Escopo concluído; nenhuma nova busca, alteração de filtro ou avaliação de2026 autorizada por este fechamento.

Evidências: [métricas/intervalos](../dados/experimentos/ablacao_linear_diaria_9cf2c1776eade0b54937/publicacao/previsao.json), [operações](../dados/experimentos/ablacao_linear_diaria_9cf2c1776eade0b54937/publicacao/operacoes.json), [diagnóstico afim](../dados/experimentos/ablacao_linear_diaria_9cf2c1776eade0b54937/publicacao/diagnostico_afim.json), [controles](../dados/experimentos/ablacao_linear_diaria_9cf2c1776eade0b54937/controles.json), [conferidor posterior](../codigo/analises/etapas/ablacao_linear_diaria/conferir.py). Editoriais anteriores ao fechamento preservados em [recibo](../registros/ablacao_linear_diaria/encerramento_editorial/preservacao.json).

## Fechamento fatorial e replicação entre ativos

Execução **`18efadab3f5a3771aacd`**, autorizada por Goal e concluída em **13/11/2026 às 02h40 BRT**. Duração do processo científico: aproximadamente **89 minutos**. [Protocolo](protocolo_fechamento_ramos_diarios.md), [fechamento](../registros/fechamento_ramos_diarios/fechamento.json), [auditoria posterior](../registros/fechamento_ramos_diarios/conferencia_posterior.json), [tabela completa](../registros/fechamento_ramos_diarios/publicacao_final/comparacao.csv).

**Conclusão central:** na receita diária adaptada do CryptoMamba, os ramos Mamba tiveram contribuição funcional nula ou extremamente pequena nos checkpoints A das quatro moedas. Treinar apenas as projeções conservou desempenho preditivo próximo em BTC/ETH, piorou numericamente em BNB e melhorou a média em XRP. Nenhum contraste principal A/L estabeleceu superioridade estatística. Em BTC, retirar a penalização aumentou o erro médio tanto na rede completa quanto na linear; os ramos permaneceram ativos em B, sem benefício preditivo demonstrado. As operações produziram ganhos, perdas e inversões de ranking entre média das seeds e ensemble. Não há vencedor operacional universal.

### Escopo efetivamente executado

| Receita | Ramos Mamba | Penalização Adam | Parâmetros por rede | Participação |
|---|---|---:|---:|---|
| A | Presentes | 0,001 | 136.952 | Referência nas quatro moedas |
| B | Presentes | 0 | 136.952 | Fatorial BTC |
| L | Removidos antes de treinar | 0,001 | 824 | Ablação nas quatro moedas |
| L0 | Removidos antes de treinar | 0 | 824 | Nova célula do fatorial BTC |

Mamba-1 oficial; núcleo derivado do CryptoMamba de Sepehri et al., commit `fef42727861a9c3a32241283ab981ef21a49e291`. Este estudo usa a adaptação local de retorno e canais padronizados, não os checkpoints ou a tarefa exata do artigo publicado. O eixo percorrido continua sendo o dos seis canais, com os 14 dias na dimensão de atributos.

Foram **12 ajustes científicos novos**: L0/BTC e L/ETH/BNB/XRP, três seeds por célula. Mais **oito controles**: B42/BTC, A42 nas outras moedas e repetição da primeira rede linear em cada moeda. Todos completaram 200 épocas. As 18 redes herdadas tiveram dados, escalas, previsões e seleção limitada ao prefixo de 200 épocas reconferidos. Controles não entram nas médias. Nenhuma receita, seed ou moeda foi selecionada pelo resultado desta execução.

Permaneceram fixos Adam 0,01, StepLR100/gamma0,5, batch32, perda `sqrt(MSE+1e-8)`, ausência de early stopping/clipping e seleção pelo menor RMSE global de validação. Treino até 2023, validação 2024, retrospectiva 2025. São 351/350 previsões de validação/teste por moeda; as origens de teste vão de 15/01 a 30/12/2025, UTC. Nenhuma avaliação de 2026 foi acrescentada.

O WSL foi recuperado antes dos ajustes, com incidente e resolução preservados. Qualificação CUDA: 100 testes aprovados, repetições sintéticas exatas das quatro receitas e recarga exata das 18 referências. O executor encerrou com **288 carteiras**, sem falhas prudenciais, e 120 reproduções financeiras A/Naive. A conferência posterior recalculou 96 séries, 90 diagnósticos, 1.296 intervalos e a contabilidade das carteiras; reconferiu os oito controles e os 2.703 arquivos anteriores. A maior divergência numérica das métricas foi **4,44e−16**. Foram conferidas 45.363 transições consecutivas do mesmo lado. Essa contagem soma carteiras/custos; não representa eventos de mercado independentes.

### BTC: o que acrescentou a célula L0

MSE em retorno decimal ao quadrado; RMSE e MAE em pontos percentuais. Na coluna “média”, calcula-se a métrica de cada rede e depois sua média. O RMSE médio não é definido como a raiz do MSE médio. No ensemble, primeiro são combinadas as previsões, depois calculadas as métricas.

| Receita e agregação | MSE | RMSE (p.p.) | MAE (p.p.) | Acerto balanceado |
|---|---:|---:|---:|---:|
| A — média | 0,000477667 | 2,1856 | 1,5712 | 50,38% |
| B — média | 0,000502583 | 2,2414 | 1,6262 | 49,52% |
| L — média | 0,000477213 | 2,1845 | 1,5704 | 50,29% |
| L0 — média | 0,000488606 | 2,2104 | 1,6063 | 49,43% |
| A — ensemble | 0,000474907 | 2,1792 | 1,5637 | 51,43% |
| B — ensemble | 0,000491742 | 2,2175 | 1,5968 | 48,57% |
| L — ensemble | 0,000474584 | 2,1785 | 1,5634 | 48,57% |
| L0 — ensemble | 0,000476200 | 2,1822 | 1,5730 | 49,43% |
| Naive | 0,000475433 | 2,1804 | 1,5633 | Não se aplica |
| Ridge | 0,000477301 | 2,1847 | 1,5726 | 50,00% |

Sem penalização, o MSE médio de L0 ficou **2,39% maior que L**, e o de B ficou **5,22% maior que A**. L0 reduziu o erro médio em **2,78% frente a B**, mas ainda ficou acima de A, L e Naive. Todas as três seeds L0 tiveram MSE maior que suas correspondentes L; L0 melhorou frente a B em duas das três seeds. Isso favorece numericamente manter a penalização nesta receita, sem provar uma regra universal.

Contrastes predefinidos de MSE médio, IC95% principal em blocos de 14 dias: A−L = 4,54e−7 [−1,00e−6; 3,00e−6]; B−L0 = 1,40e−5 [−9,05e−6; 3,88e−5]; interação `(B−L0)−(A−L)` = 1,35e−5 [−8,85e−6; 3,71e−5]. No ensemble, o IC da interação também inclui zero: [−6,06e−7; 3,04e−5]. Portanto, não foi estabelecida uma interação estatística, embora a contribuição funcional dos ramos seja claramente diferente entre A e B.

| BTC, retrospectiva 2025 | Retorno médio | Drawdown médio | Retorno ensemble | Drawdown ensemble |
|---|---:|---:|---:|---:|
| A | −0,99% | 25,39% | +12,83% | 8,36% |
| B | −13,91% | 35,71% | −26,00% | 38,33% |
| L | +6,75% | 24,19% | +17,01% | 8,32% |
| L0 | −4,22% | 29,88% | −1,99% | 24,21% |

L0 operou comprado em 39 dias e vendido em 29, com 52 episódios de posição. Maior atividade bilateral não produziu maior lucro. Seus retornos individuais foram −8,68%, +3,35% e −7,34%, nas seeds 42/17/2026. Os ensembles A/L operaram apenas comprados e ficaram integralmente em caixa no segundo semestre. Não interpretar seus lucros como habilidade demonstrada nos dois lados ou durante todo o ano.

### Replicação A versus L nas quatro moedas

Variação relativa de MSE abaixo é `(L/A−1)×100`: negativo favorece L. Todos os IC95% principais A/L incluem zero, tanto para médias individuais quanto para ensemble. Ativos correlacionados e três seeds não formam uma grande amostra de mercados independentes.

| Moeda | Δ MSE médio L/A | Δ MSE ensemble L/A | Seeds em que L reduziu MSE | Habilidade MSE de L médio / ensemble contra Naive |
|---|---:|---:|---:|---:|
| BTC | −0,095% | −0,068% | 1/3 | −0,374% / +0,178% |
| ETH | −0,074% | −0,113% | 2/3 | +0,518% / +0,600% |
| BNB | +1,885% | +0,679% | 1/3 | −4,735% / −3,234% |
| XRP | −2,508% | −0,064% | 2/3 | −0,323% / +0,010% |

Habilidade positiva significa menor MSE que Naive; não é porcentagem de acertos. Nenhuma vantagem de L contra Naive foi estabelecida pelos intervalos principais. Em BNB, o intervalo da diferença **média L−Naive é inteiramente positivo** [4,84e−7; 9,75e−5], evidenciando erro maior nesse contraste exploratório. Não omitir esse resultado desfavorável.

Para as outras moedas, cada célula abaixo apresenta **A → L**. RMSE/MAE em p.p.; direção em acerto balanceado. A tabela completa também conserva as dispersões nas publicações por ativo e os valores individuais no [CSV de seeds](../registros/fechamento_ramos_diarios/publicacao_final/seeds.csv).

| Moeda / agregação | RMSE A → L | MAE A → L | Acerto balanceado A → L |
|---|---:|---:|---:|
| ETH — média | 3,9454 → 3,9439 | 2,7526 → 2,7540 | 50,99% → 51,06% |
| ETH — ensemble | 3,9445 → 3,9423 | 2,7513 → 2,7521 | 50,15% → 51,27% |
| BNB — média | 2,8022 → 2,8283 | 1,9866 → 1,9919 | 49,89% → 49,44% |
| BNB — ensemble | 2,7987 → 2,8082 | 1,9819 → 1,9747 | 52,31% → 45,97% |
| XRP — média | 4,4065 → 4,3511 | 2,9386 → 2,8722 | 50,08% → 50,30% |
| XRP — ensemble | 4,3453 → 4,3439 | 2,8637 → 2,8640 | 51,66% → 50,83% |

MSE menor não implica simultaneamente MAE ou direção melhores. Em XRP, por exemplo, a melhora média é muito maior que a melhora do ensemble: as três redes originais divergiam mais entre si, e a média de suas previsões já eliminava parte dessa variação.

| Referências de 2025 | RMSE Naive / Ridge (p.p.) | MAE Naive / Ridge (p.p.) | Retorno Ridge | Drawdown Ridge |
|---|---:|---:|---:|---:|
| BTC | 2,1804 / 2,1847 | 1,5633 / 1,5726 | +0,49% | 14,40% |
| ETH | 3,9542 / 3,9495 | 2,7461 / 2,7456 | +35,76% | 32,66% |
| BNB | 2,7638 / 2,7750 | 1,9396 / 1,9572 | −19,89% | 45,64% |
| XRP | 4,3441 / 4,3706 | 2,8606 / 2,8901 | −24,58% | 62,20% |

Naive prevê retorno zero e fica em caixa: retorno e drawdown zero nesta política. Ridge usa 84 coordenadas e penalização escolhida pela validação; não é a mesma parametrização fatorada de L. Não ordenar moedas por RMSE bruto, pois suas volatilidades diferem.

### Operações, estabilidade e concentração

O motor é o mesmo de continuidade: conserva o lado, negocia a diferença para o alvo e encerra em caixa, inversão ou fim. Capital de 10 mil USDT, exposição alvo de 95%, filtro ±0,2%, comissão de 0,05%, slippage **provisório** de 0,01% por lado, latência de um minuto e funding histórico. As carteiras não fecham e reabrem artificialmente a cada dia. Custos maiores de 0,02%/0,03% foram avaliados como sensibilidades fixas, sem selecionar o cenário pelo lucro.

| Moeda | Retorno médio A → L | Drawdown médio A → L | Retorno ensemble A → L | Drawdown ensemble A → L |
|---|---:|---:|---:|---:|
| BTC | −0,99% → +6,75% | 25,39% → 24,19% | +12,83% → +17,01% | 8,36% → 8,32% |
| ETH | +60,76% → +61,14% | 46,10% → 44,53% | +39,81% → +61,71% | 48,35% → 43,94% |
| BNB | −25,50% → −17,98% | 51,33% → 48,19% | −20,51% → −11,84% | 54,56% → 43,94% |
| XRP | −18,76% → −5,12% | 43,03% → 48,40% | +41,15% → −1,24% | 44,47% → 48,45% |

**XRP é o contraponto essencial:** L melhorou o MSE médio e a média dos retornos individuais, mas o ensemble caiu de +41,15% para −1,24%. Em A, nenhuma carteira individual de XRP lucrou (duas perderam e uma ficou em caixa), embora a carteira da média das previsões tenha lucrado. O filtro é aplicado depois da combinação e produz outras decisões. Não é correto calcular o resultado do ensemble pela média dos lucros.

Em BNB, retirar os ramos piorou MSE e reduziu o prejuízo; em ETH, a melhora de MSE foi pequena e o ganho do ensemble foi maior. Os IC95% principais das diferenças de crescimento log diário A/L incluem zero em todas as moedas, para médias e ensembles. Eles não são intervalos em pontos percentuais do retorno total. A média de crescimento log também não equivale à média aritmética dos retornos totais.

As três carteiras L de ETH lucraram; as três de BNB perderam. Em XRP/L, uma lucrou e duas perderam. Junto com as comparações pareadas de MSE, isso mostra instabilidade entre inicializações e ativos. Não promover uma seed isolada nem escolher uma arquitetura diferente para cada moeda usando este teste.

Os recortes semestrais são descrições da **mesma curva**, sem reiniciar capital. Em 2025, L/BTC obteve todo o lucro no primeiro semestre; L/ETH passou de −1,61% no primeiro para +64,36% no segundo; L/BNB de +18,14% para −25,38%; L/XRP de +23,93% para −20,31%. Esses retornos se compõem, não se somam. O drawdown por semestre no CSV usa fechamentos diários; as tabelas principais usam a avaliação intradiária conservadora do simulador.

Dos ganhos positivos por movimento do contrato do ensemble L/BTC, 82,00% vieram dos três melhores episódios, em apenas oito episódios totais. Essa fração não é participação no lucro líquido, pois não distribui artificialmente custos/funding por episódio. Nos ensembles L/ETH, L/BNB e L/XRP houve respectivamente 160/42, 72/124 e 4/201 dias comprados/vendidos. Portanto, a operação bilateral existe, mas atividade vendida não garante habilidade ou lucro.

Com slippage de 0,03%, os ensembles A/L tiveram: BTC +12,54%/+16,66%; ETH +38,90%/+60,39%; BNB −21,42%/−14,07%; XRP +36,89%/−3,47%. O ranking A/L por moeda se manteve nesses três cenários. Isso não certifica custos históricos reais nem robustez fora dos períodos observados.

2024 selecionou os checkpoints e permanece separado: retornos dos ensembles A/L foram BTC +95,53%/+95,53%; ETH +40,85%/+34,09%; BNB +150,96%/+173,46%; XRP +247,01%/+293,02%. Os resultados mais altos nesse ano não constituem confirmação independente, e a ordem não se conserva em todos os casos em 2025.

### Contribuição dos ramos e interpretação do mecanismo

Foram comparadas as previsões completas e com saídas Mamba zeradas em todas as populações de treino, validação e teste dos 30 checkpoints científicos. **Onze das 12 redes A não mudaram qualquer previsão na precisão utilizada.** A única exceção, ETH/seed17, teve alteração máxima de 1,58e−8 no treino e 1,12e−8 no teste, em retorno decimal. Nenhuma decisão de lado de A mudou com essa intervenção, nas populações verificadas e sob o filtro fixo. É ausência de contribuição detectável ou contribuição extremamente pequena neste recorte, não prova matemática para toda entrada possível.

Em B/BTC, os ramos permanecem ativos: as maiores alterações de previsão no teste ao retirá-los são aproximadamente 0,97, 1,65 e 2,10 p.p., nas três seeds. A retirada posterior reduziu numericamente o MSE de cada uma dessas redes. Isso é um diagnóstico dos checkpoints fixados, não um novo candidato selecionado e retestado. Atividade do SSM não equivale a informação útil.

As sondas anteriores de A mostram contribuição inicial mensurável, seguida de forte redução, acompanhada pela queda das normas LayerNorm. Por exemplo, na seed42 de BTC, a diferença máxima caiu de 0,0676 na inicialização para zero observado no checkpoint escolhido da época25. A norma LayerNorm caiu de aproximadamente 15,75 para 9,22e−5. As sondas usam 32 janelas e checkpoints salvos, não todas as épocas. Normas e gradientes do último lote documentam o processo; não isolam a causa em um parâmetro nem representam o passo efetivo inteiro do Adam. A comparação A/B muda a penalização da rede toda; a comparação A/L muda também sua trajetória de aprendizado.

Assim, **contribuição na inferência e influência durante o treinamento são perguntas diferentes**. Os ramos podem ter modificado os gradientes e os pesos lineares nas épocas iniciais, mesmo desaparecendo funcionalmente no checkpoint final. Treinar L do zero ajuda a investigar sua necessidade, mas não obriga L a terminar com pesos ou checkpoint iguais aos de A. BNB evidencia essa diferença. Não concluir que o treinamento de A “nunca usou Mamba”.

Sem os ramos, a função pode ser escrita como `b + soma(canal,dia) coef[canal,dia] * x[canal,dia]`. Cada rede possui coeficientes separáveis por canal e defasagem, de posto1; a média de três redes continua afim e pode ter posto até3 (posto3 observado nas decomposições BTC). A combinação não acrescenta outro SSM ou não linearidade. Ridge tem parametrização distinta. Os coeficientes e as contribuições por canal/defasagem estão preservados, sem interpretá-los como importância causal.

O timestamp não domina a variação algébrica das previsões do ensemble A/BTC em 2025: desvios das contribuições foram **0,00938 p.p. para timestamp, 0,05967 p.p. para OHLC conjunto e 0,00973 p.p. para volume**. O desvio da previsão foi 0,07060 p.p. Essas parcelas são correlacionadas e não devem ter variâncias somadas como se fossem independentes. Medir efeito de retirar uma entrada exigiria outro experimento, que não foi realizado aqui.

### Eficiência e conclusão acadêmica

L/L0 reduziram os parâmetros por rede em **99,40%**: 824 contra 136.952. Nesta execução, os ajustes lineares completos levaram **52,38 a 57,30 segundos**, enquanto os controles completos Mamba levaram **1.034,93 a 1.069,06 segundos**. Isso representa aproximadamente 18–20 vezes menos tempo observado para 200 épocas. É uma medição no mesmo notebook e backend, incluindo observações/salvamentos, não um benchmark isolado de kernels, inferência ou consumo energético. O tempo total de 89 minutos inclui controles, avaliações e conferências do executor.

Formulação para o artigo: **“Na adaptação diária investigada, a arquitetura completa apresentou contribuição funcional nula ou extremamente pequena dos ramos Mamba nos checkpoints regularizados das quatro criptomoedas. A ablação treinada do zero reduziu substancialmente a complexidade e o tempo observado, sem benefício incremental dos ramos estatisticamente estabelecido. A retirada da penalização preservou sua atividade em BTC, mas não melhorou os resultados preditivos ou operacionais de forma demonstrada. As divergências entre erro, agregação de seeds e lucro evidenciaram a necessidade de avaliar separadamente arquitetura, previsão e política de operação.”**

Essa contribuição é uma avaliação crítica e controlada de uma adaptação atribuída ao CryptoMamba; não reivindica arquitetura inédita nem invalida o modelo oficial ou o artigo original. Três seeds, quatro ativos correlacionados, uma divisão temporal fixa, custos de cenário e períodos previamente consultados limitam a generalização. ICs são exploratórios, sem remover o efeito da busca histórica ou provar equivalência. O orçamento foi cumprido e a etapa experimental está encerrada; o próximo passo deste Goal é a redação com essas evidências, sem nova busca automática por lucro.

### Evidências para escrita e reprodução

- [Tabela completa de previsões e operações](../registros/fechamento_ramos_diarios/publicacao_final/comparacao.csv), [seeds](../registros/fechamento_ramos_diarios/publicacao_final/seeds.csv), [288 carteiras e custos](../registros/fechamento_ramos_diarios/publicacao_final/carteiras.csv), [semestres](../registros/fechamento_ramos_diarios/publicacao_final/semestres.csv), [concentração operacional](../registros/fechamento_ramos_diarios/publicacao_final/atribuicao_operacional.json).
- [Intervenção nos ramos](../registros/fechamento_ramos_diarios/publicacao_final/contribuicao_ramos.csv), [coeficientes por canal e defasagem](../registros/fechamento_ramos_diarios/publicacao_final/coeficientes_afins.csv), [contribuições por canal](../registros/fechamento_ramos_diarios/publicacao_final/contribuicoes_canais.csv), [decomposição dos ensembles](../registros/fechamento_ramos_diarios/publicacao_final/decomposicao_ensembles.csv), [gradientes observados](../registros/fechamento_ramos_diarios/publicacao_final/gradientes_observados.csv), [tempos e seleção](../registros/fechamento_ramos_diarios/publicacao_final/eficiencia.csv).
- Figuras em PNG, com PDF homônimo: [fatorial BTC](../registros/fechamento_ramos_diarios/publicacao_final/fatorial_btc.png), [comparação entre ativos](../registros/fechamento_ramos_diarios/publicacao_final/comparacao_ativos.png), [carteiras dos ensembles](../registros/fechamento_ramos_diarios/publicacao_final/carteiras_ensemble.png), [trajetória dos ramos](../registros/fechamento_ramos_diarios/publicacao_final/trajetoria_ramos.png), [estrutura e ablação](../registros/fechamento_ramos_diarios/publicacao_final/estrutura_ablacao.png). [Inspeção visual aprovada](../registros/fechamento_ramos_diarios/publicacao_final/inspecao_visual.json); o manifesto de geração conserva o estado anterior à inspeção.
- [Execução e fontes congeladas](../registros/fechamento_ramos_diarios/execucao.json), [diagnóstico histórico consolidado](../registros/fechamento_ramos_diarios/diagnostico_previo.json), [conferência independente](../registros/fechamento_ramos_diarios/conferencia_posterior.json), [versões editoriais anteriores](../registros/fechamento_ramos_diarios/editoriais_finais_antes/preservacao.json). Cada símbolo na pasta da execução conserva suas métricas, intervalos, previsões, modelos, ZIP de carteiras, auditorias e diagnóstico completos.

## Extensão retrospectiva A/L em 2026

Concluída em **13/11/2026**, execução `b7401a1ee93888219c25`, por solicitação posterior do pesquisador. A já havia sido avaliado em 2026; L ainda não. Reutilizamos **24 redes congeladas**, três A e três L por moeda, sem treinar, reestimar escalas ou escolher checkpoints novamente. Foram avaliadas as mesmas **314 origens de 01/01 a 10/11/2026**, com encerramento em 11/11 às 00:01 UTC. Dados, custos e simulador são os da avaliação anterior de A.

[Protocolo](protocolo_ablacao_linear_2026.md) · [configuração](../configuracoes/ablacao_linear_2026_001.json) · [conferência independente](../registros/ablacao_linear_2026/conferencia_posterior.json) · [tabela de previsões](../registros/ablacao_linear_2026/publicacao/previsoes.csv) · [132 carteiras](../registros/ablacao_linear_2026/publicacao/carteiras.csv) · [resumo verificável](../registros/ablacao_linear_2026/publicacao/resumo.json).

**Exposição:** os resultados A/2026 já eram conhecidos quando esta extensão foi proposta. A comparação de L com A é retrospectiva; não representa um novo holdout intocado, seleção de vencedor ou previsão prospectiva. O fechamento anterior, limitado a 2025, permanece separado.

### O que são A, L e ensemble

A é a adaptação atribuída ao CryptoMamba com 12 blocos residuais `x + Mamba(LayerNorm(x))`, Mamba-1 oficial e estado 64. Cada bloco pode transformar a representação, enquanto a conexão residual permite conservar a entrada. O núcleo projeta larguras 14→16→32→1, com quatro blocos por estágio, e combina os seis canais. Na organização herdada, o Mamba percorre **canais**; os 14 dias são atributos. Isso é distinto da variante temporal investigada anteriormente.

A letra **L significa linear; não é LSTM**. L remove todos esses blocos **antes de treinar**, inclusive as LayerNorms, e aprende do zero as quatro projeções afins restantes, com os mesmos pesos iniciais correspondentes e a mesma receita. Tem 824 parâmetros contra 136.952 de A (99,40% menos). Várias camadas afins sem ativações ainda representam uma função afim; L não é uma nova arquitetura SSM nem a regressão Ridge usada como referência. Sua parametrização fatorada é mais restrita que uma regressão com 84 coeficientes livres. Atribuição ao núcleo CryptoMamba permanece.

Ambos usam OHLCV e timestamp de 14 dias, padronizados com estatísticas do treino, e retornam a variação simples esperada no próximo dia: `0,02` significa +2%; `−0,02`, −2%. Não são probabilidades de alta/queda. São redes separadas por moeda, com treino até 2023 e checkpoint escolhido pelo menor RMSE global de validação em 2024. A equivalência do checkpoint de A com a seleção nas primeiras 200 épocas foi comprovada no fechamento; L foi treinado por 200 épocas. Adam, taxa inicial 0,01, redução pela metade após 100 épocas, lote 32, perda `sqrt(MSE + 1e−8)` e penalização uniforme 0,001 foram preservados.

As seeds 42, 17 e 2026 controlam inicialização e ordem de lotes; não são três períodos distintos e a seed 2026 não se refere ao ano de teste. A média das métricas individuais descreve três redes/carteiras separadas. O ensemble combina as três previsões em uma previsão e só então calcula erros e aplica a política. Logo, seu erro e lucro não são a média dos erros e lucros individuais.

### Previsões no período adicional

RMSE/MAE abaixo estão em **pontos percentuais de retorno diário**, não em percentual de acerto. Menor é melhor. O RMSE dá mais peso a grandes erros; o MAE mede a distância absoluta média. Naive prevê retorno zero. Não comparar moedas por erro bruto sem considerar sua volatilidade.

| Moeda | RMSE médio A / L | RMSE ensemble A / L | RMSE Naive | MAE ensemble A / L | Balanced accuracy ensemble A / L |
|---|---:|---:|---:|---:|---:|
| BTC | 2,3341 / 2,3327 | 2,3328 / 2,3315 | 2,3279 | 1,5946 / 1,5931 | 50,00% / 50,00% |
| ETH | 3,1886 / 3,1875 | 3,1842 / 3,1857 | 3,1791 | 2,1234 / 2,1262 | 52,43% / 51,71% |
| BNB | 2,2967 / 2,3173 | 2,2941 / 2,3030 | 2,3044 | 1,5941 / 1,5918 | 51,51% / 51,73% |
| XRP | 3,4021 / 3,3865 | 3,3886 / 3,3845 | 3,3874 | 2,2013 / 2,1915 | 53,35% / 52,69% |

| Moeda | MSE médio A / L | MSE ensemble A / L | Variação do MSE médio L/A | Variação do MSE ensemble L/A |
|---|---:|---:|---:|---:|
| BTC | 0,000544792 / 0,000544157 | 0,000544186 / 0,000543608 | -0,12% | -0,11% |
| ETH | 0,001016723 / 0,001016003 | 0,001013934 / 0,001014860 | -0,07% | 0,09% |
| BNB | 0,000527497 / 0,000537146 | 0,000526286 / 0,000530400 | 1,83% | 0,78% |
| XRP | 0,001157482 / 0,001146872 | 0,001148242 / 0,001145504 | -0,92% | -0,24% |

O erro médio de L diminuiu em BTC, ETH e XRP e aumentou em BNB. No ensemble, ETH também piorou ligeiramente. **Todos os IC95% principais L−A de MSE incluem zero**, tanto nas médias individuais quanto nos ensembles. Todos os contrastes principais dos ensembles A/L contra Naive também incluem zero. Não demonstramos superioridade preditiva consistente; tampouco demonstramos equivalência formal. Os intervalos completos de 7/14/28 dias estão na publicação original.

Em BTC, ambos os ensembles sempre preveem retorno positivo: balanced accuracy de 50%, embora o filtro selecione apenas parte dos dias. Seu lucro não significa discriminação geral entre altas e quedas. A magnitude prevista importa para decidir quando ficar em caixa.

### Operações e risco

Mesma continuidade: sinal acima de +0,20% compra, abaixo de −0,20% vende, demais sinais ficam em caixa. Mesmo lado conserva a posição e só ajusta o delta para o alvo de 95% do patrimônio liquidável; inversão/caixa/fim encerram. Capital inicial de 10 mil USDT por carteira, comissão 0,05% por lado, slippage provisório 0,01%, funding histórico, latência de um minuto e filtros de execução. Não há stop/take. Retorno é do período completo, sem anualizar. Drawdown é a maior queda desde um pico, com envelope conservador intraminuto.

| Moeda | Retorno médio das seeds A / L | Retorno ensemble A / L | Drawdown ensemble A / L | Comprar/manter no mesmo futuro |
|---|---:|---:|---:|---:|
| BTC | 2,40% / -0,39% | 27,49% / 33,25% | 13,45% / 13,45% | -17,44% |
| ETH | -8,09% / 6,38% | -6,69% / -5,40% | 30,51% / 33,84% | -30,99% |
| BNB | 35,56% / 31,43% | 20,51% / 9,61% | 24,58% / 19,23% | -22,16% |
| XRP | 6,97% / 0,28% | 9,61% / 36,52% | 23,14% / 10,54% | -41,01% |

![Carteiras de 2026](../registros/ablacao_linear_2026/publicacao/carteiras_2026.png)

L-ensemble melhorou o retorno de BTC em 5,76 p.p. e de XRP em 26,90 p.p.; em ETH perdeu 1,28 p.p. menos, mas continuou negativo e teve drawdown maior. Em BNB perdeu 10,90 p.p. de retorno em relação a A, embora o drawdown fosse menor. Os IC95% principais da diferença de crescimento log diário L−A **incluem zero nas quatro moedas**, em médias e ensembles. Esses ICs não estão na unidade do retorno acumulado.

A média dos retornos individuais revela outra história: BTC/L −0,39% apesar do ensemble +33,25%; XRP/L +0,28% apesar do ensemble +36,52%. Em ETH/L, as seeds retornaram +50,40%, −10,96% e −20,31%; a média +6,38% esconde essa instabilidade e não corresponde ao ensemble de −5,40%. Não escolher a seed lucrativa retrospectivamente.

| Moeda | Dias comprados/vendidos A-ensemble | Dias comprados/vendidos L-ensemble | Episódios A / L | Comissões + slippage A / L (USDT) | Funding A / L (USDT) |
|---|---:|---:|---:|---:|---:|
| BTC | 128/0 | 98/0 | 15 / 12 | 205,58 / 165,62 | -81,24 / -47,83 |
| ETH | 116/0 | 136/0 | 6 / 14 | 62,80 / 140,73 | -0,21 / -5,47 |
| BNB | 1/103 | 112/52 | 8 / 55 | 133,11 / 697,48 | 88,26 / -54,11 |
| XRP | 85/1 | 24/0 | 53 / 18 | 707,13 / 285,26 | -15,18 / 4,41 |

BTC/ETH/XRP de L-ensemble não operaram vendidos. XRP/L ficou exposto só em 24 dos 314 dias, divididos em 18 episódios. Assim, +36,52% não comprova previsão generalizada nem exploração consistente dos dois lados do mercado. A maior parte da curva plana significa caixa. A/L diferiram em 30 sinais de BTC, 20 de ETH, 161 de BNB e 66 de XRP; diferenças pequenas na previsão podem cruzar o filtro e mudar toda a trajetória da carteira. Em BNB, L teve mais episódios e custos maiores; em XRP, menos exposição e custos menores. Isso é descrição, não identificação causal isolada do lucro.

Com slippage de 0,03% por lado, os ensembles L retornam +32,60%, −5,91%, +7,34% e +35,61% em BTC/ETH/BNB/XRP. Esses cenários não revertem os sinais de lucro/prejuízo, mas não certificam custos reais. Naive permanece em caixa. O Ridge preservado retorna 0%, +15,74%, +34,61% e +14,15%, respectivamente; não selecionar uma referência por moeda com base neste teste.

### O que o período acrescenta à conclusão

Em 2025, o ensemble L ficou acima de A em BTC/ETH/BNB e abaixo em XRP; em 2026, ficou acima em BTC/ETH/XRP e abaixo em BNB. A magnitude muda bastante e as populações/volatilidades diferem. Não concatenar os números como se fossem uma única carteira, nem chamar um ano mais fácil de evolução do modelo: os checkpoints são os mesmos.

Nas 12 redes A, zerar temporariamente as saídas Mamba em 2026 produziu **diferença exatamente zero em 11** e máximo de **8,38×10⁻⁹** no retorno de ETH/seed17. Nenhum sinal mudou. Isso reforça que os ramos têm contribuição funcional ausente ou desprezível **nesses checkpoints e populações**. Não prova que nunca participaram do treinamento: sondas anteriores mostraram atividade e gradientes iniciais. L é uma ablação treinada separadamente, não o mesmo A com os ramos desligados; os pesos aprendidos das projeções e suas previsões diferem.

A conclusão sustentada para o TCC é que, nesta adaptação e receita, a complexidade adicional dos ramos não apresentou benefício incremental demonstrado. A versão muito mais simples preservou desempenho preditivo próximo e produziu resultados operacionais competitivos, com vantagens dependentes do ativo/período, instabilidade entre seeds e incerteza. Não é evidência de inutilidade universal do Mamba, arquitetura inédita ou garantia de lucro. O estudo de contribuição dos componentes é uma contribuição acadêmica própria, mantendo atribuição ao CryptoMamba.

### Conferências e preservação

As 24 redes reproduziram exatamente validação/teste anteriores; as 12 A reproduziram 2026, todas repetiram inferência exatamente e mantiveram pesos intactos. As janelas foram reconstruídas a partir do OHLCV e escalas anteriores; perturbar o candle-alvo não mudou a entrada correspondente. As 132 carteiras passaram pelo auditor independente, com reprodução das 24 A-ensemble/comprar-manter anteriores. Conferência posterior: 40 séries, 624 intervalos recalculados, reconciliação de movimento/funding/comissões/slippage e 15.201 transições de mesmo lado. Divergência máxima nas métricas: 4,44×10⁻¹⁶. Os 1.449 arquivos de dependências e as fontes congeladas foram preservados antes/depois. Nenhum treinamento novo.

Os manifestos originais dos dois pais também foram conferidos: 937 arquivos do fechamento entre ativos e 103 da avaliação anterior de 2026, conforme [recibo de integridade](../registros/ablacao_linear_2026/integridade_pais.json). Os seis testes de contrato das entradas passaram.

Duas figuras PNG foram inspecionadas, com PDFs correspondentes. [Preservação editorial anterior](../registros/ablacao_linear_2026/editoriais_antes/preservacao.json). Conservar as tabelas extensas como suplemento; incorporar à discussão a ausência de vantagem incremental demonstrada, a diferença entre erro e operação e o caráter retrospectivo da extensão. A etapa experimental solicitada está encerrada, sem nova busca ou promoção automática.
