# Resultados do experimento de penalização do Mamba

Execução `7868a4d847c1410fc681`. Referência preservada `1e7c5ed662fba55ddd25`. Relatório gerado em 2026-10-27T20:38:46.003739+00:00 (UTC).

Estudo retrospectivo pareado em períodos já consultados. A única intervenção é retirar weight decay dos parâmetros marcados pelo Mamba. Foram 384 ajustes corrigidos; LSTM, ARIMA, Naive e os Mamba originais são referências herdadas. Dois controles originais foram reexecutados para conferência de reprodução e não contam como novos pares independentes.

A execução e a preservação foram concluídas em 27/10/2026 às 20:39:05 UTC (17:39:05 em São Paulo). A confirmação antes/depois está em `preservacao_depois.json` na pasta desta execução; o estado global está em `progresso.json`. Este texto foi ampliado após a geração automática, sem mudar as publicações científicas congeladas.

Protocolo: [experimento controlado](protocolo_penalizacao_mamba.md). A mudança não garante melhora nem rentabilidade.

## Resposta à pergunta da pesquisa

Retirar a penalização dos quatro tensores marcados pelo Mamba não resolveu sua desvantagem nesta configuração. No desenvolvimento de 2023, o MSE caiu apenas 0,0068%. Na avaliação retrospectiva de 2024–2025, subiu 0,0505%, com intervalo que admite tanto pequena melhora como pequena piora. O Mamba corrigido manteve erro maior que LSTM, Naive e ARIMA. Não há evidência de que essa penalização explique a diferença principal observada entre Mamba e LSTM.

Esses percentuais são mudanças relativas no **erro de previsão**, não pontos percentuais de acurácia nem retorno financeiro. Se o MSE do Naive na avaliação fosse representado pelo índice 100, o corrigido ficaria em aproximadamente 101,27. Quanto menor esse índice, melhor.

Foram preservados os dois ciclos: o original registra o que de fato foi executado; o corrigido registra uma intervenção posterior. A correção respeita a implementação oficial, mesmo sem produzir ganho. Não se deve voltar à configuração anterior apenas porque algum escore foi melhor, nem escolher uma seed favorável depois de ver o teste.

## O que mudou e o que permaneceu igual

O AdamW original aplicava `weight_decay=0.001` a todos os parâmetros. O novo otimizador mantém esse coeficiente nos 17.953 parâmetros não marcados e usa zero nos 2.176 parâmetros de `A_log` e `D`, distribuídos nos dois blocos. Dados, retornos horários, alvo de 24h, contextos, arquitetura, seeds, escalas, loss, aprendizado, batches, validação e parada permanecem iguais. A época escolhida pode mudar como consequência do treinamento; a regra de seleção é a mesma.

O coeficiente era pequeno. Apenas como ilustração da parcela de decaimento, `lr × weight_decay = 0,0000002` por atualização, correspondendo a um fator multiplicativo 0,9999998 nos pesos penalizados. Isso ajuda a compreender por que a intervenção pode ter efeito pequeno, mas não é uma demonstração do mecanismo observado: gradientes, dinâmica não linear e escolha da época também interferem. O experimento mede o efeito final, não isola cada mecanismo interno.

![Efeito da correção e incerteza](figuras/penalizacao_7868a4d847c1410fc681/efeito_principal.png)

O ponto indica a diferença média de MSE; o segmento mostra o intervalo temporal de 95%. Valores negativos favorecem a correção. O painel de 2023 usa outra escala para tornar o efeito muito pequeno legível. Em 2024–2025 o segmento cruza zero: não há distinção clara entre as políticas, o que também não prova equivalência.

## Desenvolvimento de 2023

| Modelo | MSE médio | RMSE × 100 | MAE × 100 |
|---|---:|---:|---:|
| mamba_original | 0.0008363257 | 2.8919 | 1.7755 |
| mamba_corrigido | 0.0008362688 | 2.8918 | 1.7754 |
| lstm | 0.0008268839 | 2.8756 | 1.7624 |
| arima | 0.0008204785 | 2.8644 | 1.7558 |
| naive | 0.0008207934 | 2.8649 | 1.7570 |

MSE menor indica menor erro quadrático. RMSE/MAE ×100 estão em pontos de log-retorno, não em acurácia. As seeds são médias de escores, não um ensemble.

| Comparação do corrigido com | Diferença MSE | Variação relativa | IC 95% de 14 dias |
|---|---:|---:|---|
| mamba_original | -5.691526977e-08 | -0.0068% | [-1.172335376e-07; -1.221849777e-08] |
| lstm | 9.384938437e-06 | +1.1350% | [3.615783005e-06; 1.513396684e-05] |
| naive | 1.547539012e-05 | +1.8854% | [7.059127282e-06; 2.361217789e-05] |
| arima | 1.579031867e-05 | +1.9245% | [7.49070675e-06; 2.387089481e-05] |

O intervalo principal favorece a correção. A diferença é corrigido menos referência: negativa favorece o corrigido. Os contrastes com outras famílias são secundários. Intervalos condicionais aos modelos e períodos, com 2.000 reamostragens de blocos; sensibilidades de sete e 28 dias constam do JSON.

Na simulação Spot com custos base, 48 estratégias tiveram retorno auditável. Mediana corrigida: 0.40%; mediana dos pares originais: 0.40%. Estratégias correlacionadas, sem carteira combinada e sem escolha retrospectiva da vencedora.

Evidências: `dados/experimentos/penalizacao_7868a4d847c1410fc681/analises/desenvolvimento/resumo.json`, `comparacoes_pareadas.csv`, `metricas_por_ajuste.csv`, `financeiro.csv`, `publicacao.json` e `auditoria.json`.

## Avaliação retrospectiva de 2024–2025

| Modelo | MSE médio | RMSE × 100 | MAE × 100 |
|---|---:|---:|---:|
| mamba_original | 0.0011907138 | 3.4507 | 2.3206 |
| mamba_corrigido | 0.0011913154 | 3.4515 | 2.3212 |
| lstm | 0.0011764164 | 3.4299 | 2.3057 |
| arima | 0.0011761429 | 3.4295 | 2.3053 |
| naive | 0.0011763538 | 3.4298 | 2.3061 |

MSE menor indica menor erro quadrático. RMSE/MAE ×100 estão em pontos de log-retorno, não em acurácia. As seeds são médias de escores, não um ensemble.

| Comparação do corrigido com | Diferença MSE | Variação relativa | IC 95% de 14 dias |
|---|---:|---:|---|
| mamba_original | 6.0161949e-07 | +0.0505% | [-3.575148087e-07; 1.809591006e-06] |
| lstm | 1.489907002e-05 | +1.2665% | [3.790738413e-06; 3.333391921e-05] |
| naive | 1.496167177e-05 | +1.2719% | [3.419561143e-06; 3.49287252e-05] |
| arima | 1.517253553e-05 | +1.2900% | [3.633149455e-06; 3.524460753e-05] |

O intervalo principal inclui zero e não distingue claramente as duas políticas. A diferença é corrigido menos referência: negativa favorece o corrigido. Os contrastes com outras famílias são secundários. Intervalos condicionais aos modelos e períodos, com 2.000 reamostragens de blocos; sensibilidades de sete e 28 dias constam do JSON.

Na simulação Spot com custos base, 48 estratégias tiveram retorno auditável. Mediana corrigida: -10.48%; mediana dos pares originais: -10.48%. Estratégias correlacionadas, sem carteira combinada e sem escolha retrospectiva da vencedora.

Evidências: `dados/experimentos/penalizacao_7868a4d847c1410fc681/analises/avaliacao/resumo.json`, `comparacoes_pareadas.csv`, `metricas_por_ajuste.csv`, `financeiro.csv`, `publicacao.json` e `auditoria.json`.

## Incerteza e comparação com as referências

O contraste principal foi definido antes do novo treinamento: Mamba corrigido menos Mamba original na avaliação retrospectiva. Sua diferença foi 6,0162×10⁻⁷ de MSE, com IC95% [−3,5751×10⁻⁷; 1,8096×10⁻⁶]. Dividir esse intervalo pelo MSE original observado, mantido fixo, dá uma escala relativa de aproximadamente −0,0300% a +0,1520%; isso é uma normalização para leitura, não um novo bootstrap da razão.

As sensibilidades de sete, 14 e 28 dias mantiveram a interpretação: efeito pequeno favorável em 2023, inconclusivo em 2024–2025; o corrigido continuou pior que LSTM e Naive nas comparações secundárias. Os intervalos são condicionais aos modelos e às séries observadas. Não incluem toda a incerteza de repetir o treinamento, mudar o mercado ou formular esta hipótese após consultar o primeiro estudo. Contrastes por família/contexto não receberam correção de multiplicidade e devem ser lidos como secundários.

![Comparação com as referências](figuras/penalizacao_7868a4d847c1410fc681/diferencas_pareadas.png)

A LSTM e as baselines foram herdadas, portanto a conclusão original de LSTM versus Naive não mudou: não houve vantagem clara da LSTM sobre a persistência. O pequeno MSE médio do ARIMA frente ao Naive, isoladamente, também não autoriza declarar superioridade robusta.

## Estabilidade entre seeds e tamanho do contexto

Cada seed representa uma inicialização e uma sequência de aleatoriedade do treinamento. São três repetições de cada configuração, não três mercados independentes. O resultado principal inclui todas, sem escolher a melhor e sem formar ensemble.

| Seed | MSE original em 2024–2025 | MSE corrigido | Mudança relativa do erro |
|---|---:|---:|---:|
| 17 | 0,0011766798 | 0,0011762958 | −0,0326% |
| 42 | 0,0012018725 | 0,0012052027 | +0,2771% |
| 2026 | 0,0011935892 | 0,0011924478 | −0,0956% |

Duas seeds melhoraram e uma piorou, mas a piora teve maior magnitude. O desvio padrão dos três MSEs médios foi 1,0484×10⁻⁵ no original, 1,1828×10⁻⁵ no corrigido e 1,4325×10⁻⁶ na LSTM. Neste diagnóstico descritivo, o corrigido variou cerca de 8,26 vezes mais que a LSTM. Três seeds não bastam para caracterizar completamente a distribuição do treinamento. No desenvolvimento, os desvios foram, respectivamente, 4,2406×10⁻⁶, 4,1745×10⁻⁶ e 2,0650×10⁻⁷.

![Estabilidade entre inicializações](figuras/penalizacao_7868a4d847c1410fc681/estabilidade_seeds.png)

O efeito de contexto também depende do período. Em 2023, 14 dias tiveram menor MSE que um dia no Mamba corrigido; em 2024–2025, um dia teve menor erro médio que os contextos maiores. Os contrastes de um contra três e 14 dias favoreceram um dia nessa avaliação; um contra sete dias permaneceu inconclusivo. Isso não demonstra que contexto curto seja sempre melhor: a inversão entre períodos é uma limitação central e não autoriza escolher o contexto pelo teste.

![Erro por contexto](figuras/penalizacao_7868a4d847c1410fc681/contextos.png)

![Efeito descritivo por moeda e contexto](figuras/penalizacao_7868a4d847c1410fc681/efeito_por_moeda.png)

O último gráfico é uma decomposição exploratória das médias, sem intervalos por ponto. Um aumento localizado, como BNB com sete dias, não deve substituir o contraste principal ou ser omitido para melhorar a narrativa.

## Simulação Spot: o que mudou na operação

A política permanece diária, comprado/caixa: decisão às 00:00 UTC, entrada às 00:01, saída 24h depois e capital inicial de 10.000 USDT por estratégia. Só compra quando o retorno previsto supera o limiar dos custos base. Taxa de 0,10% e slippage de 0,05% por lado no cenário base; 0,20% e 0,10% no agravado, mantendo os mesmos sinais. Não há short, alavancagem, stop loss ou take profit. Isso não simula futuros ou liquidação, nem operar em todas as origens horárias.

| Fase e modelo | Mediana do retorno líquido: base | Custos agravados | Estratégias positivas: base |
|---|---:|---:|---:|
| 2023 — Mamba original | +0,40% | −0,74% | 25/48 |
| 2023 — Mamba corrigido | +0,40% | −0,74% | 25/48 |
| 2023 — LSTM | +1,56% | +1,25% | 24/48 |
| 2024–2025 — Mamba original | −10,48% | −28,48% | 21/48 |
| 2024–2025 — Mamba corrigido | −10,48% | −28,48% | 23/48 |
| 2024–2025 — LSTM | −0,16% | −4,82% | 24/48 |
| Ambas as fases — Naive | 0,00% | 0,00% | 0/4 por fase |

As 48 estratégias correspondem a quatro moedas × quatro contextos × três seeds, cada uma encadeando os quatro blocos de sua fase. São estratégias correlacionadas, não uma carteira de 48 posições nem 48 experimentos financeiros independentes. Os retornos são acumulados na fase, não diários nem anualizados. O Naive fica em caixa porque sua previsão zero não supera os custos; não é uma estratégia lucrativa descoberta pelo modelo. LSTM e original são referências herdadas.

Medianas idênticas não significam todas as operações idênticas. O total de entradas, somado entre estratégias, passou de 397 para 399 em 2023 e de 4.173 para 4.112 em 2024–2025. Esses totais contam sinais compartilhados por estratégias diferentes e não representam operações de uma carteira real. Na avaliação, o drawdown mediano do corrigido foi 38,97% com custos base e 44,20% com custos agravados, contra 21,61% e 23,44% na LSTM. O drawdown considera os fechamentos de minuto; não garante o pior movimento intraminuto.

A conferência contou dois sinais diferentes em 2023 e 219 em 2024–2025, somando inclusões e exclusões entre os pares de estratégias. O retorno mudou em duas das 48 estratégias de desenvolvimento e em 20 das 48 de avaliação, em cada cenário de custos. Nenhuma época selecionada mudou nos 192 pares de desenvolvimento; oito mudaram nos 192 pares de avaliação. São diagnósticos descritivos, não testes adicionais de superioridade.

Não há demonstração de rentabilidade consistente. Melhorar ou piorar pouco o MSE pode alterar uma operação quando a previsão fica próxima ao limiar de entrada, mas a correção não mudou a conclusão econômica global. Não foram escolhidas a posteriori as estratégias que lucraram.

## Cobertura, controles, incidentes e entregas

Cada fase contém 192 ajustes corrigidos e 416 resultados herdados: 192 Mamba originais, 192 LSTM, 16 Naive e 16 seleções ARIMA. Há 192 pares original/corrigido por fase e 96 cenários financeiros (48 estratégias × dois custos). Isso totaliza 384 novos ajustes corrigidos, não 1.216 novos treinamentos. Os dois controles de reprodução adicionais ficaram fora das estimativas científicas.

Os controles BTC/DB1/seed42 em W24 e W336 mantiveram a época selecionada. As diferenças máximas de previsão foram inferiores a 1,25×10⁻⁸ de log-retorno e as variações relativas de MSE inferiores a 1,19×10⁻⁸, dentro dos limites predefinidos de 10⁻⁵ e 10⁻⁴. Eles verificam a reprodução de duas células, não demonstram determinismo absoluto de toda a grade.

Houve duas interrupções operacionais, após 56 e 299 ajustes concluídos. Os resultados auditados foram reaproveitados após conferência de integridade; as duas tentativas incompletas foram preservadas e repetidas com os mesmos parâmetros e seeds. Assim, a extensão tem 386 conclusões auditadas de mercado (384 corrigidos + dois controles) e duas tentativas interrompidas adicionais, total de 388 tentativas. A seleção das tentativas não foi feita pelo desempenho.

| Entrega da extensão | Evidência |
|---|---|
| Correção isolada e testes | `experimento_penalizacao/otimizador.py`, comparação estrutural do treinador e sete testes específicos, além dos 17 contratos anteriores |
| Qualificação e congelamento | 12 casos CUDA, teste de equivalência do agrupamento e fontes/ambiente vinculados à identidade da execução |
| Controles e piloto | Dois controles reproduzidos; dois pilotos corrigidos incluídos na grade, sem dupla contagem |
| Grade completa | 384 ajustes corrigidos, 192 por fase; recarga e auditoria por tentativa |
| Comparação e simulação | Duas publicações, diferenças pareadas, intervalos, seeds e 96 cenários por fase |
| Preservação | 7.082 arquivos comparados antes/depois, com aprovação do recibo final |
| Documentação e figuras | Este relatório, andamento, roteiro de redação e cinco figuras PNG/PDF com manifesto |

São sete entregas da extensão, além das oito entregas computacionais do ciclo original. Essa organização não equivale a quinze entregas formais aprovadas pelo orientador. Redação, revisão bibliográfica, formato acadêmico, defesa e eventual integração da extensão na interface continuam separados do fechamento computacional.

As fontes científicas e recibos antigos não foram reescritos. Os controles e pilotos foram aprovados antes da grade. A primeira conferência posterior encontrou um conflito de nome de variável ao salvar o relatório; o código e o diagnóstico dessa falha foram preservados em `registros/revisoes/penalizacao_2026-10-27T210425.386923_0000/`. O defeito estava apenas na ferramenta de revisão e não exigiu novo treinamento, mudança de dados ou alteração das publicações.

A nova conferência terminou aprovada: [recibo independente](../registros/revisoes/penalizacao_2026-10-27T210853.776756_0000/resumo.json). Foram verificados cobertura exata, fontes, dataset, artefatos, alinhamento das três populações novas, métricas recalculadas, escalas/configurações dos 384 checkpoints, grupos do otimizador, 60 intervalos temporais com implementação própria da reamostragem e 9.022 registros de operações (798 em desenvolvimento e 8.224 em avaliação, somando os dois cenários). Foram conferidos sinais, horários, preços, custos, capital e drawdown. A revisão não repetiu treino ou inferência neural; a recarga exata já é requisito de cada ajuste auditado. Verificação aprovada reduz riscos identificáveis, mas não constitui prova de ausência de qualquer defeito.

Preservação antes/depois: [recibo](../dados/experimentos/penalizacao_7868a4d847c1410fc681/preservacao_depois.json). Figuras: [manifesto](figuras/penalizacao_7868a4d847c1410fc681/manifesto.json). O arquivamento verificado aqui é local; nenhuma publicação externa ou restauração em outra máquina é afirmada por esses recibos.

## Implicações para o TCC e próximos passos

A contribuição do estudo é uma comparação rastreável sob um contrato claro, incluindo a avaliação explícita de uma possível falha de implementação. O resultado negativo é informativo: respeitar a marcação do otimizador não foi suficiente para tornar esta configuração Mamba superior às referências. Não se conclui que Mamba seja inadequado para todas as séries financeiras ou que nenhuma entrada consiga prever retornos.

Para a redação, apresentar primeiro o ciclo original, depois a identificação do problema, a intervenção única e seus resultados retrospectivos. Usar o Mamba corrigido como implementação tecnicamente ajustada, mantendo o original como controle histórico. Explicar que a comparação usa redes compactas e configurações fixas, e não uma otimização exaustiva de cada arquitetura.

Se o orientador aprovar novas hipóteses, definir antecipadamente o orçamento de ajustes, o critério de escolha e uma avaliação realmente nova. Indicadores, outras granularidades ou ajuste de capacidade seriam novos ciclos. Não usar os mesmos testes repetidamente para escolher variantes até Mamba vencer. Nenhuma dessas buscas foi iniciada neste fechamento. Ver [roteiro de redação](roteiro_redacao_tcc.md).

## Limites da conclusão

A correção mantém arquitetura, entrada, dados, partições, seeds e regra de seleção de época. A época selecionada pode mudar como consequência do tratamento. Não houve busca adicional. Comparações por moeda, contexto e seed são exploratórias e estão integralmente reportadas nos arquivos, sem seleção de subconjuntos favoráveis.

Os resultados de 2024–2025 já haviam sido vistos quando esta hipótese foi definida. Congelar a extensão não desfaz essa exposição; uma nova alegação confirmatória requer dados não usados nas decisões. Este experimento não mede a melhor configuração possível de Mamba/LSTM nem certifica execução financeira real.
