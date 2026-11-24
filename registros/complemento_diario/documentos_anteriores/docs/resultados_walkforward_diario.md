# Robustez temporal diária A/L em BTC

A execução `82659f51435f366ec043` terminou em 13/11/2026, conforme o [protocolo congelado](protocolo_walkforward_diario.md). São 24 ajustes científicos, dois controles repetidos e 108 carteiras; nenhum ajuste de controle integra as médias. As [conferências independentes](../registros/walkforward_diario/conferencia_posterior.json) e [complementar](../registros/walkforward_diario/conferencia_complementar.json) foram aprovadas. A última reconstruiu 7.490 janelas a partir dos candles e das escalas, conferiu 200 épocas e seleção pela validação nos 24 ajustes e reconciliou todas as carteiras, com diferença contábil máxima inferior a 5×10⁻¹¹ USDT. Não houve falha prudencial no simulador.

As receitas A e L foram reestimadas em BTC em quatro blocos semestrais. Cada uma recebeu as mesmas entradas, datas e seeds 42, 17 e 2026; o treino é expansivo e a validação antecede o teste. As datas dos blocos são limites de partição: a primeira previsão em cada teste ocorre 14 dias depois, pois o contexto permanece interno à partição. As populações efetivas são B1: 167 dias, primeiro semestre de 2024; B2: 169, segundo semestre de 2024; B3: 166, primeiro semestre de 2025; B4: 169, segundo semestre de 2025. A última janela possível de cada partição também foi excluída, como na receita herdada.

## Erro e incerteza

MSE em unidades de 10⁻⁴ de retorno decimal ao quadrado; menor é melhor. Média é a média dos três MSEs individuais. Ensemble é a métrica da média das previsões, não outra seed. Os quatro blocos têm durações semelhantes, mas compartilham histórico e representam o mesmo mercado: não são quatro mercados independentes.

| Bloco | A média / ensemble | L média / ensemble | Naive | A − L: IC 95% da média individual | A − L: IC 95% do ensemble |
|---|---:|---:|---:|---:|---:|
| B1 | 8,0009 / 7,6929 | 7,7989 / 7,7917 | 7,9084 | [−0,0520; 0,8949] | [−0,3226; 0,1718] |
| B2 | 7,4986 / 7,4985 | 7,4862 / 7,4854 | 7,4552 | [−0,0104; 0,0464] | [−0,0078; 0,0291] |
| B3 | 6,1053 / 6,0963 | 6,1196 / 6,1186 | 6,0841 | [−0,0814; 0,0190] | [−0,0510; −0,0046] |
| B4 | 3,8404 / 3,8384 | 3,8420 / 3,8392 | 3,6105 | [−0,0145; 0,0098] | [−0,00162; −0,00005] |

Os intervalos são bootstrap pareado em blocos de 14 dias; as médias individuais também reamostram as três seeds. Em cada linha, valores negativos do contraste favorecem A. Os quatro intervalos individuais incluem zero; os de ensemble em B3 e B4 ficaram inteiramente abaixo de zero, com diferenças pequenas. Isso é evidência local condicional à receita e ao recorte, não superioridade geral nem equivalência entre modelos. Em B4, ambos os ensembles tiveram MSE maior que o Naive e seus intervalos de diferença também ficaram acima de zero. Em B1, o ensemble A teve MSE menor que o Naive no intervalo principal. As comparações são exploratórias e não corrigem toda a multiplicidade ou a busca histórica; 2024–2025 já eram conhecidos antes da rodada.

Com peso igual entre blocos, o MSE médio das redes foi 6,3613 para A, 6,3117 para L e 6,2646 para Naive, na unidade da tabela. É uma síntese descritiva dos quatro recortes, não uma nova amostra independente. Os MSEs por seed e intervalos de sensibilidade de 7 e 28 dias estão na [publicação original](../dados/experimentos/walkforward_diario_82659f51435f366ec043/publicacao/previsao.json).

## Operações em futuros

Mesma política de continuidade, filtro fixo ±0,2%, capital inicial 10.000 USDT, taxa 0,05% por lado, funding histórico e slippage provisório de 0,01% por lado. Cada bloco começa com nova carteira; **não somar os percentuais como se fossem uma única trajetória**. A média dos retornos individuais corresponde a três carteiras distintas.

| Bloco | A média / ensemble / DD ensemble | L média / ensemble / DD ensemble | Dias comprados / vendidos do ensemble A | Dias comprados / vendidos do ensemble L |
|---|---:|---:|---:|---:|
| B1 | +38,12 / +73,45 / 14,21 | +42,88 / +46,01 / 23,57 | 56 / 42 | 145 / 0 |
| B2 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 | 0 / 0 |
| B3 | +11,52 / +9,53 / 31,09 | +9,53 / +9,53 / 31,09 | 166 / 0 | 166 / 0 |
| B4 | −26,77 / −26,77 / 34,68 | −26,77 / −26,77 / 34,68 | 169 / 0 | 169 / 0 |

B2 ficou em caixa sob o filtro; retorno e drawdown nulos não demonstram habilidade ou segurança em outros mercados. Em B3 e B4, os dois ensembles produziram posições e carteiras iguais no período; em B4 a posição comprada em todos os dias veio acompanhada da perda de 26,77%. Em B1, A operou nos dois lados e retornou mais que L no ensemble, mas a média de suas três carteiras foi menor; os intervalos dos contrastes de crescimento log diário A−L incluem zero. O mesmo ocorre nos demais blocos, com intervalos degenerados em zero quando as trajetórias são iguais. Isso não prova igualdade futura, nem transforma o resultado retrospectivo em lucro esperado.

No cenário de slippage 0,03% por lado, os retornos dos ensembles A/L foram respectivamente +71,49/+45,20% em B1, 0/0 em B2, +9,49/+9,49% em B3 e −26,79/−26,79% em B4. Esses três valores de slippage são cenários, não custos de execução históricos certificados. Liquidação oficial completa, fila, impacto de mercado e mudanças de regras não foram reproduzidos.

## Contribuição dos ramos Mamba

A [sondagem posterior](../registros/walkforward_diario/diagnostico_ramos_tentativa_002.json) recarregou os 12 checkpoints A e comparou suas previsões de teste com as da mesma rede após desligar simultaneamente os 12 ramos Mamba, sem retreinar. As diferenças foram [recalculadas independentemente](../registros/walkforward_diario/conferencia_sondagem.json). Em nove redes a diferença foi exatamente zero; em B3/seed 17, no máximo 5,59×10⁻⁹ em retorno decimal, sem mudar decisões. Em B1/seed 42, o máximo foi 6,59×10⁻⁵ e houve uma decisão de sinal alterada.

O caso B1/seed 2026 exige ressalva importante: desligar os ramos mudou a previsão em até 0,0807 de retorno decimal (8,07 pontos percentuais), alterou o lado ou caixa em 134 das 167 origens e elevou o MSE do checkpoint de 8,4338 para 48,5263 na unidade de 10⁻⁴. Essa intervenção mostra contribuição funcional relevante **naquele checkpoint e população**; não identifica causalidade durante o aprendizado, lucro adicional nem vantagem geral sobre L. A conclusão anterior de contribuição final praticamente nula referia-se aos checkpoints da divisão fixa e não se generaliza a todos os retreinamentos.

A primeira tentativa da sondagem foi interrompida antes de produzir previsões porque a variável determinística exigida pelo cuBLAS não estava configurada. O [incidente preservado](../registros/walkforward_diario/diagnostico_ramos.json) contém a tentativa e sua fonte; a segunda tentativa configurou `CUBLAS_WORKSPACE_CONFIG=:4096:8` antes de iniciar o PyTorch. Não houve novo treinamento nem substituição dos artefatos da rodada original.

## Alcance

O walk-forward acrescenta reestimações causais e evidencia variação entre períodos: vantagem local não implica estabilidade operacional, e o comportamento dos ramos depende do checkpoint. A/L foram comparados em BTC; a LSTM das quatro moedas permanece uma comparação de divisão fixa, não uma LSTM reestimada nesses quatro blocos. Os períodos 2024–2025 são retrospectivos, os ativos e seeds não fornecem confirmação independente dos regimes futuros e nenhum resultado certifica operação real.
