# Robustez temporal diária A/L em BTC

## Complemento LSTM — 17/11/2026

A execução `59d30a5fe13a627c1f31` acrescentou a receita LSTM aos mesmos quatro blocos, sem substituir as referências A/L. Foram 12 ajustes científicos de 200 épocas e dois controles: reprodução exata do BTC/seed42 da divisão fixa e repetição exata de B1/seed42. Os controles compararam a trajetória inteira, todos os checkpoints de melhoria e as previsões de validação. A [auditoria posterior](../registros/complemento_diario/lstm_walkforward/conferencia_posterior.json) aprovou as populações, seleção, métricas, 288 intervalos e as 48 carteiras novas; não houve falha prudencial.

MSE na unidade 10⁻⁴ de retorno decimal ao quadrado. O ensemble é a média dos preços previstos; a média individual agrega métricas das três seeds. As entradas têm seis canais e 14 dias, mas a LSTM percorre dias e usa Adam inicial 0,001, enquanto A/L usam 0,01. O contraste é entre receitas completas, não uma ablação exclusiva de arquitetura.

| Bloco | LSTM média / ensemble | A ensemble | L ensemble | Naive | Habilidade do ensemble LSTM |
|---|---:|---:|---:|---:|---:|
| B1 | 7,8739 / 7,7600 | 7,6929 | 7,7917 | 7,9084 | +1,88% |
| B2 | 7,5260 / 7,5103 | 7,4985 | 7,4854 | 7,4552 | −0,74% |
| B3 | 6,0602 / 6,0504 | 6,0963 | 6,1186 | 6,0841 | +0,55% |
| B4 | 3,8203 / 3,8167 | 3,8384 | 3,8392 | 3,6105 | −5,71% |

No bootstrap principal de 14 dias, os contrastes LSTM−A e LSTM−L incluem zero em B1, B2 e B4, tanto nas médias individuais quanto nos ensembles. Em B3, os quatro intervalos ficaram abaixo de zero, indicando diferença local favorável à LSTM. Isso não demonstrou superioridade frente ao Naive nesse bloco: os intervalos LSTM−Naive incluem zero. Em B1, somente o ensemble LSTM apresentou intervalo inteiramente abaixo do Naive; em B4, os dois contrastes com o Naive ficaram acima de zero. Os resultados variam entre populações e não sustentam um vencedor geral. Os [resultados integrais](../dados/experimentos/complemento_lstm_walkforward_59d30a5fe13a627c1f31/publicacao/previsao.json) incluem seeds, métricas auxiliares e blocos de reamostragem de 7, 14 e 28 dias, sem atravessar fronteiras dos testes.

| Bloco | Retorno do ensemble LSTM | Drawdown máximo | Dias expostos |
|---|---:|---:|---:|
| B1 | +15,25% | 11,06% | 23,95% |
| B2 | −2,22% | 17,29% | 26,63% |
| B3 | +14,02% | 20,57% | 43,37% |
| B4 | −26,77% | 34,68% | 100,00% |

Operações com filtro ±0,20%, slippage 0,01% e comissão 0,05% por lado, continuidade, funding histórico e as restrições herdadas. Cada bloco é uma carteira independente de 10.000 USDT. Em B4, a LSTM ensemble também permaneceu comprada durante todo o período e reproduziu a carteira dos ensembles A/L: pequenas diferenças de erro não produziram decisões diferentes. Os [resultados operacionais](../dados/experimentos/complemento_lstm_walkforward_59d30a5fe13a627c1f31/publicacao/operacoes.json) preservam indivíduos, médias de carteiras e ensemble, os três custos e os intervalos de crescimento logarítmico diário. Esses intervalos não são intervalos de retorno acumulado.

Esta rodada continua retrospectiva: 2024–2025 já haviam sido consultados. As tabelas abaixo pertencem à execução A/L anterior, preservada; o complemento não reescreve seus recibos nem os transforma em confirmação intocada. O restante do [complemento autorizado](protocolo_complemento_diario.md) é acompanhado na [matriz de requisitos](../registros/complemento_diario/requisitos.json).

A [ablação do timestamp](resultados_ablacao_linear_diaria.md#ablacao-timestamp) também foi concluída nos quatro blocos, com 24 ajustes e quatro controles: sem melhora consistente nem recuperação de contribuição operacional dos ramos. A [publicação final](../dados/experimentos/complemento_sintese_complemento_revisada_ffa868ab3bbb3314d61d/publicacao/consulta.json) reúne as 18 tabelas e oito figuras do complemento, incluindo [habilidade por bloco](../dados/experimentos/complemento_sintese_complemento_revisada_ffa868ab3bbb3314d61d/publicacao/lstm_habilidade_por_bloco.png) e [contrastes LSTM](../dados/experimentos/complemento_sintese_complemento_revisada_ffa868ab3bbb3314d61d/publicacao/lstm_contrastes_mse.png). A [inspeção visual](../registros/complemento_diario/sintese_complemento/inspecao_visual.json) identifica os arquivos finais.

## Execução A/L anterior, preservada

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

O walk-forward acrescenta reestimações causais e evidencia variação entre períodos: vantagem local não implica estabilidade operacional, e o comportamento dos ramos depende do checkpoint. A execução original comparou A/L em BTC; a reestimação LSTM foi acrescentada no complemento de 17/11 descrito no início deste documento. A comparação das quatro moedas continua sendo uma divisão fixa distinta. Os períodos 2024–2025 são retrospectivos, os ativos e seeds não fornecem confirmação independente dos regimes futuros e nenhum resultado certifica operação real.

## Consulta e reprodução do complemento

Os ponteiros de `registros/complemento_diario/<etapa>/execucao.json` identificam a pasta de cada execução em `dados/experimentos`. Cada pasta conserva `congelamento.json`, fontes, dependências e qualificação; os ajustes guardam 200 épocas, seleção e checkpoints de melhoria. `publicacao/previsao.json` distingue indivíduos, médias e ensemble. Cada carteira nova tem `recibo.json` e um ZIP com ledger e curva; o ZIP consolidado da LSTM usa os mesmos membros publicados no índice operacional. O recibo de auditoria posterior aponta para a conferência e sua fonte preservada.

O ambiente científico foi o Python `/home/murilorfm/.venvs/cc/bin/python` do Ubuntu/WSL, PyTorch 2.6.0+cu118, CUDA 11.8, cuDNN 90100 e NumPy 2.2.6, na RTX 4050 Laptop. Os recibos de qualificação e início guardam os detalhes efetivos. A sequência implementada no namespace `experimentos.complemento_diario` é: `treinar` (qualificação, preparação e grade LSTM), `avaliar_lstm` (inferência e operações), `auditar`; `diagnosticos` (qualificação, preparação e grades de filtros/deslocamentos), `auditar`; `referencias` para a herança contábil; `timestamp` (decisão condicional, qualificação, preparação e grade), `avaliar_timestamp`, `auditar_timestamp`; e `publicacao_final`, `revisar_publicacao` e `encerramento_final` para a entrega. `publicacao_final` reutiliza o publicador preservado e explicita exposição por lado, eventuais linhas indisponíveis e as colunas anualizadas herdadas do motor nos CSVs; as figuras e a síntese usam os períodos efetivamente observados. As dependências são verificadas antes de liberar as etapas. A revisão de apresentação tem identidade própria e mantém as 18 tabelas e sete figuras byte a byte; somente a escala da figura dos ramos e os metadados de consulta mudaram. O ponteiro `registros/complemento_diario/sintese_complemento/versao_final.json` identifica ambas as versões. O encerramento final verifica a preservação da primeira e a integridade da revisão, sem sobrescrever fontes ou fechamentos anteriores.

Essa ordem descreve a execução autorizada, não uma instrução para repetir identidades encerradas. Para reproduzir, restaurar as fontes congeladas em cópia isolada, usar o ambiente qualificado, conferir os hashes e registrar uma identidade própria, preservando controles e orçamento. Não atualizar hashes para acomodar divergências, reutilizar pastas incompletas silenciosamente ou iniciar novo treino apenas para consultar resultados.

Após o encerramento global, a verificação somente de leitura pode ser executada na raiz do repositório, pelo ambiente Windows existente:

```powershell
.venv/Scripts/python.exe -B -m experimentos.complemento_diario.encerramento_final conferir
```

Ela verifica os arquivos das referências, o artigo preservado, os fechamentos e as auditorias, a cobertura das matrizes, as figuras inspecionadas e a documentação final. Antes de todas essas etapas estarem concluídas, deve recusar a confirmação global; o acompanhamento parcial é a matriz de requisitos.
