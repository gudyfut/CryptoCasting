# Mamba16: MSE e Huber em blocos temporais com oito seeds

Versão1, 03/11/2026. ADR0019. Autorização explícita do pesquisador para desenhar e iniciar a comparação Huber/non-Huber com aproximadamente oito seeds, podendo usar blocos. O orçamento delimitado é **64 ajustes principais e2controles reais, total66**, quatro baselines Naive sem treinamento e408simulações. Não ampliar para novas hipóteses, seeds, moedas ou procura até obter lucro/significância. Há quatro dias para concluir a parte experimental e duas semanas posteriores destinadas ao artigo, conforme informado pelo pesquisador. Planejamento não comprova execução.

## Pergunta e limites de interpretação

Pergunta: a diferença entre treinar Mamba16 por MSE ou2×Huber(delta1 padronizado) permanece ao reestimar modelos em quatro momentos, com oito inicializações pareadas? Mais seeds reduzem a dependência de inicializações específicas, mas **não garantem certeza**, não criam períodos independentes e não anulam seleção adaptativa. A Huber foi escolhida depois de consultar2024/2025; esta é avaliação ampliada retrospectiva, não confirmação intocada. Não chamar inconclusivo de igualdade nem um ganho de MSE de lucro.

A exploração anterior `ed8e55ff978b2742c200`, seus **seis ajustes Huber novos**, seis referências MSE e todos os demais ciclos permanecem preservados. Não somar aquelas seeds às novas: divisões, históricos de treino e validação diferem. Não reaproveitar seus checkpoints para prever datas anteriores. As duas receitas deste ciclo começam do zero em cada bloco/seed. A diferença entre as duas variantes de um mesmo bloco/seed é exclusivamente a perda supervisionada; as mudanças de calendário fazem parte do novo protocolo de avaliação, não uma correção retroativa da execução anterior.

## Desenho congelado antes de mercado

BTCUSDT Binance Spot, candles1h, contexto168h, horizonte24h, previsões a cada hora completa. Mesmos cinco canais causais OHLCV e log1p volume, alvo log-retorno terminal e normalização estática ajustada somente no treino de cada bloco. Mamba-1 oficial CUDA, largura32, dois blocos, estado16, convolução4, expansão2, dropout0,1, pré-LayerNorm,20.257parâmetros. AdamW/taxa constante0,0002, decay0,001 com isenções oficiais A_log/D, batch64/microbatch32, clipping1, máximo100épocas e paciência10. Não aumentar épocas indiscriminadamente ou mudar taxa/normalização para tentar melhorar o placar. Seleção pelo menor MSE global da validação em retorno real, empate conserva a primeira época; teste/operação nunca escolhem a época.

MSE usa a atualização original congelada em `treinamento/neural.py`. Huber usa `experimentos/perda_huber/treino.py`, também congelada:2×Huber(delta1 no alvo padronizado), mesma acumulação/otimizador e identificação correta da perda. O fator2 coincide com MSE em valor/gradiente para resíduos de módulo até1; fora disso a penalidade é linear. Não remover extremos. A Huber pode favorecer outra estimativa que a média condicional; sua utilidade será avaliada mantendo MSE como métrica principal. Reprodução e recarga não são a mesma exigência: treino CUDA tem tolerâncias predefinidas; recarga do mesmo checkpoint deve ser exata.

Seeds17/42/2026/7/123/31415/271828/161803; as duas últimas são fixadas antes dos novos resultados. Oito seeds **por versão e por bloco**, total32ajustes principais por versão, não apenas oito no estudo inteiro. Ordem de seeds42→17→2026→7→123→31415→271828→161803. Intercalar MSE e Huber para cada seed dentro de cada bloco. Sem selecionar ou descartar seed por resultado.

Treino expansivo a partir de01/01/2021, intervalos UTC semiabertos:

| Bloco | Fim treino/início validação | Fim validação/início teste | Fim teste |
|---|---|---|---|
| B1 | 01/10/2023 | 01/01/2024 | 01/07/2024 |
| B2 | 01/04/2024 | 01/07/2024 | 01/01/2025 |
| B3 | 01/10/2024 | 01/01/2025 | 01/07/2025 |
| B4 | 01/04/2025 | 01/07/2025 | 01/01/2026 |

Purga: destino do alvo estritamente anterior ao fim da partição. Contexto usa somente passado conhecido, podendo atravessar o início da partição. Reestimar scalers e pesos em cada bloco. Os testes anteriores podem integrar treino/validação posteriores por serem passado disponível, sem mudar o algoritmo. Não fatiar previsões de um checkpoint único como se fossem walk-forward. Dados OHLCV/candles existentes são reutilizados; quatro novos artefatos de entradas têm versões e identidades próprias, sem recoleta ou alteração da representação.

Não há novos LSTM/ARIMA nesta rodada focada nas duas perdas. Suas comparações anteriores continuam disponíveis como evidências auxiliares; não transplantar resultados ou pesos de calendários incompatíveis. Naive zero é gerado nas mesmas origens de cada bloco e não treina.

## Qualificação e controles

Código `experimentos/huber_blocos/`, testes `tests_huber_blocos/`, configuração `configuracoes/huber_blocos_001.json`, registros `registros/huber_blocos/`, entrada `python -m experimentos.huber_blocos`. Nenhum módulo/executor encerrado é editado. Leitura/checagem de artefatos deduplica arquivos e dependências apenas dentro de uma mesma conferência, sem aceitar hashes novos ou confiar em cache de conferência anterior. Cada nova fase cria um verificador fresco. Contratos dos consumidores continuam validando janelas, dimensões, alvo, origens e purga.

Antes de mercado: qualificação CUDA oficial, testes do fator único/grade, datas/scalers e invariância ao futuro, verificação de hashes/ciclos/caminhos, inferência/atualização, bootstrap pareado, separação de calendário operacional e alvo observado, publicação com dados artificiais e contabilidade do motor existente. Quatro ajustes sintéticos de duas épocas: duas repetições MSE e duas Huber; mesma época selecionada, diferença máxima de previsão1e−5 e relativa de MSE1e−4, conforme limites anteriores. Recarga individual exata nas três populações. Esses ensaios não são treinos de mercado.

No B1, executar primeiro MSE42 e Huber42 principais, depois repetir cada um como **dois controles reais adicionais**. Exigir mesmos limites de reprodução antes de liberar outras seeds/blocos. Os controles não entram nas médias nem contam como nona seed. Falha interrompe e fica preservada; não repetir até passar. Pilotos principais integram os64ajustes, sem duplicação extra. Grade total66:64principais+2controles. Cada tentativa mantém fontes/vínculo/log/épocas/checkpoints/seleção/previsões/conclusão próprios; recarga exata antes da avaliação.

Congelar quatro blocos, duas receitas, fontes, artefatos de entrada, ambiente, qualificação, grade, regras operacionais e preservação. Só então vincular a autorização humana à identidade concreta e iniciar. Conferir processos/locks/host antes de iniciar ou retomar. Um processo vivo não se duplica. Retomada exige processo encerrado/investigado e fontes íntegras; preservar tentativas incompletas e reiniciar somente a célula incompleta da mesma seed. Ciclo encerrado nunca chama treinamento para regenerar tabelas. Pós-processamento tem lock/recibo próprio.

## Métricas, agregação e critério principal

Seleção de checkpoint: MSE real da validação anterior ao teste, separada por bloco/seed. **Critério principal desta avaliação ampliada:** diferença do MSE de teste Huber−MSE, com peso igual entre quatro blocos e média das oito seeds dentro de cada bloco. Não reabrir o critério de validação da exploração anterior nem substituir seus recibos. Reportar todas as médias por bloco/seed, RMSE,MAE, habilidade Naive, viés,direção balanceada, associação, erros extremos e diagnóstico diário; não selecionar a métrica/população favorável. Médias individuais, não ensemble; RMSE médio não é automaticamente a raiz de outro agregado de MSE. A habilidade global é1−MSEglobal/MSEglobalNaive sob os mesmos pesos de bloco.

IC95% principal: bootstrap pareado de **seeds e dias**,2.000réplicas, seed20261103, blocos circulares14dias; sensibilidades7/28. Em cada réplica, sortear oito índices de seeds com reposição e usar os mesmos índices para as duas perdas e os quatro blocos. Dentro de cada bloco, reamostrar sequências de dias sem atravessar fronteiras, preservando contagens horárias; calcular o MSE médio das seeds sorteadas e depois a média igual dos quatro blocos. Não sortear blocos como mercados independentes. Publicar também o intervalo temporal condicional às oito seeds fixas, como análise secundária. Critério favorável exige média menor e limite superior do IC95% principal14dias abaixo de zero. Sem promoção automática ou repetição para obter significância. Contrastes por bloco e sensibilidades são diagnósticos, não quatro oportunidades independentes de declarar vitória.

Os intervalos continuam condicionais a quatro períodos escolhidos e redes ajustadas; não representam integralmente dependência entre históricos de treino, novos regimes ou busca adaptativa anterior. Oito seeds não eliminam essas limitações. Magnitude, heterogeneidade temporal e utilidade econômica serão discutidas separadamente do critério estatístico. Nenhuma obrigação de vencer, provar igualdade ou obter lucro.

## Simulação operacional secundária, orçamento408

Mesmo motor congelado `backtest_carteira/` da execução8ec8a66648313caa48e3, vinculada por contrato/hash. Spot long/caixa, capital10.000USDT, decisões00UTC, execução00:01, quantidade/filtros/custos anteriores; sem futuros, short, funding, stop ou garantia de fills reais. Políticas **Smart2% e diaria24** no mesmo motor, com custos ideal/base/agravado. Smart2% não é stop nem probabilidade. O controle diaria24 encerra/reabre diariamente conforme regra fixa. Não apresentar essa contabilização como idêntica ao SpotR0 histórico, que permanece preservado e não é reexecutado.

64modelos×2políticas×3custos=384carteiras. Comprar/manter e caixa, quatro blocos×2benchmarks×3custos=24. Total408. Sem novas políticas, limiares, controle constante adicional ou busca de retorno. Comparar as duas perdas dentro de cada bloco/política/custo. Não usar capital, custos ou estratégia para selecionar época/configuração.

Entradas de simulação vêm da população operacional e só incluem colunas conhecidas na origem mais destino programado/previsão. Calendário fixo: origem+24h estritamente anterior ao fim do bloco. A máscara não usa alvo observado ou preço futuro. Por isso, a última sessão completa de cada semestre fica excluída; o motor termina24h após a última decisão mais a latência de1minuto. Calendário real deve constar de cada resumo. Isso evita inventar minutos de2026 não coletados e mantém a mesma regra em todos os blocos. Falta de preços ou negócios interrompe a simulação, sem interpolar/pular dias.

Carteiras **independentes por bloco**, com reset10.000USDT; não somar ou compor seus retornos como se fossem um histórico contínuo de dois anos. Reportar resultados de cada bloco, médias entre seeds, custos/exposição/drawdown e benchmarks. Saldos/lançamentos são reconstruídos pelo verificador independente. Retorno financeiro é secundário e não comprova generalização ou execução de conta real.

## Fechamento e preservação

Preservar integralmente execuções anteriores e suas revisões. Artefatos novos em `dados/experimentos/huber_blocos_<id>/`, receitas/copias congeladas por identidade e ponteiro próprio. Conferir66conclusões,64principais sem controles nas médias, dois controles aprovados,4Naive e408simulações, fontes, recargas/checkpoints/métricas/contrastes, lançamentos e preservação antes/depois. Relatório único `docs/resultados_huber_blocos.md`, cronologia `docs/andamento.md`, catálogo/índices atualizados com estado real. Nenhum treino futuro é autorizado pelo fechamento. Arquivos locais não equivalem a backup externo ou publicação remota. Não comprar computação nem executar ordens reais.
