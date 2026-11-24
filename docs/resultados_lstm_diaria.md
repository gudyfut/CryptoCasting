# LSTM diária em comparação com A e L

**Complemento temporal de 17/11/2026:** a LSTM foi reestimada nos quatro blocos BTC do walk-forward, com 12 ajustes, dois controles exatos e 48 carteiras auditadas. A [comparação temporal e seus limites](resultados_walkforward_diario.md#complemento-lstm--17112026) tem população e checkpoints próprios; não deve ser fundida às tabelas da divisão fixa abaixo. Sensibilidade operacional e diagnóstico de exposição também foram concluídos e auditados no [complemento](protocolo_complemento_diario.md). A [publicação final](../dados/experimentos/complemento_sintese_complemento_revisada_ffa868ab3bbb3314d61d/publicacao/consulta.json) reúne tabelas e figuras, e a [matriz de requisitos](../registros/complemento_diario/requisitos.json) registra a cobertura.

Execução `f08eef4cc3371f5fc2e2`, concluída em 13/11/2026. [Protocolo](protocolo_lstm_diaria.md), [estado](../registros/lstm_diaria/estado.json), [fechamento](../registros/lstm_diaria/fechamento.json), [controles independentes](../registros/lstm_diaria/controles_independentes.json) e [conferência posterior](../registros/lstm_diaria/conferencia_posterior.json). As tabelas extensas e intervalos estão na [publicação](../dados/experimentos/lstm_diaria_f08eef4cc3371f5fc2e2/publicacao/); este documento sintetiza, sem substituir os artefatos.

## Pergunta e alcance

A comparação examina uma LSTM unidirecional de duas camadas e 32 unidades, com **13.601 parâmetros**, contra A, L, Naive e Ridge. Ela recebe os mesmos seis canais e 14 dias, mas percorre dias; A percorre canais. A LSTM foi ajustada com Adam inicial 0,001; A e L usaram 0,01. Portanto, não se atribuem diferenças exclusivamente à arquitetura ou à sua capacidade. Cada família usa três seeds e seleção pela validação. L e LSTM foram treinadas por 200 épocas; a equivalência da seleção de A dentro das primeiras 200 épocas foi comprovada, embora seus ajustes originais tenham executado 1.000. As médias individuais e o ensemble são objetos diferentes.

Quatro ativos, 350 origens em 2025 e 314 em 01/01–10/11/2026; 2024 seleciona checkpoints. A referência diária A foi escolhida após observação de 2025, e A/2026 já era conhecido antes desta comparação. Ambos os períodos são **retrospectivos**; a nova comparação não é confirmação intocada. As taxas, moedas, filtros e seeds não foram escolhidos pelos novos resultados.

Foram concluídos 12 ajustes científicos e quatro controles, excluídos das médias. A conferência independente verificou exatamente 200 épocas e todos os checkpoints de melhoria dos quatro controles. As 96 carteiras novas passaram por auditoria contábil; houve zero falhas prudenciais no cenário implementado. A conferência posterior recalculou 160 valores preditivos e financeiros e os contrastes de crescimento logarítmico. Uma [conferência adicional independente](../registros/lstm_diaria/metricas_adicionais.json) recalculou 64 medidas de RMSE e acurácia balanceada; outra [reconciliou as 96 identidades contábeis agregadas](../registros/lstm_diaria/conferencia_financeira_adicional.json), com divergência máxima inferior a $5\times10^{-11}$ USDT. Isso não certifica execução real.

## Previsões

RMSE em **pontos percentuais de retorno**; menor é melhor. A coluna média é a média dos RMSEs das três redes, não o RMSE da previsão média. O ensemble primeiro combina as previsões. ARIMA diário foi reaproveitado somente em 2025, após conferência das 350 origens, alvos e fechamentos. Seu modelo é univariado; a informação disponível difere dos seis canais das redes.

| Ano | Ativo | A média / ensemble | L média / ensemble | LSTM média / ensemble | Naive | ARIMA |
|---|---|---:|---:|---:|---:|---:|
| 2025 | BTC | 2,1856 / 2,1792 | 2,1845 / 2,1785 | 2,1785 / 2,1775 | 2,1804 | 2,1868 |
| 2025 | ETH | 3,9454 / 3,9445 | 3,9439 / 3,9423 | 3,9459 / 3,9446 | 3,9542 | 3,9542 |
| 2025 | BNB | 2,8022 / 2,7987 | 2,8283 / 2,8082 | 2,8383 / 2,8228 | 2,7638 | 2,7638 |
| 2025 | XRP | 4,4065 / 4,3453 | 4,3511 / 4,3439 | 4,4981 / 4,4904 | 4,3441 | 4,3441 |
| 2026 | BTC | 2,3341 / 2,3328 | 2,3327 / 2,3315 | 2,3250 / 2,3244 | 2,3279 | — |
| 2026 | ETH | 3,1886 / 3,1842 | 3,1875 / 3,1857 | 3,1863 / 3,1837 | 3,1791 | — |
| 2026 | BNB | 2,2967 / 2,2941 | 2,3173 / 2,3030 | 2,3326 / 2,3163 | 2,3044 | — |
| 2026 | XRP | 3,4021 / 3,3886 | 3,3865 / 3,3845 | 3,4165 / 3,3795 | 3,3874 | — |

As diferenças são pequenas em vários casos, mas não em todos: o ensemble LSTM em XRP/2025 teve RMSE 4,4904 contra 4,3453 de A e 4,3441 de Naive. No contraste de MSE LSTM−A, os intervalos principais para médias individuais incluem zero em todos os casos; alguns contrastes de ensembles não incluem zero. São intervalos exploratórios por ativo/período, sem correção para todas as comparações ou para a seleção histórica: não provam uma ordenação geral. Não incluir zero não transforma esses períodos em confirmação reservada. A inclusão de zero também não prova equivalência.

O MSE médio individual de LSTM/A em BTC foi, respectivamente, 4,7458/4,7767 em 2025 e 5,4057/5,4479 em 2026, na unidade de $10^{-4}$ de retorno decimal ao quadrado. O menor erro em BTC não se repete em todas as moedas; BNB e XRP de 2025 tiveram maior MSE médio para LSTM. Detalhes por seed, MAE, direção, MSE, sensibilidades de bloco e ICs estão na publicação.

Para comparar com uma referência na escala de cada ativo, a habilidade $1-\mathrm{MSE}_{\mathrm{LSTM}}/\mathrm{MSE}_{\mathrm{Naive}}$ foi calculada usando a **média dos MSEs das três seeds**. Em 2025, foi +0,18% em BTC, +0,42% em ETH, −5,51% em BNB e −7,23% em XRP. Em 2026, foi +0,25%, −0,46%, −2,48% e −1,74%, respectivamente. Valor positivo significa menor MSE que retorno zero; esses percentuais não são taxas de acerto nem lucro e são comparações descritivas, não garantia de superioridade.

## Operações em futuros

Mesma política de continuidade, capital e custos da referência: comissão 0,05%, slippage provisório 0,01% por lado, funding histórico e filtro fixo ±0,2%. Retornos e drawdowns em porcentagem; cada média individual corresponde a três carteiras independentes. **A média não é o resultado do ensemble.**

Extensão definida antes de executá-la: comparar em 2026, para as quatro moedas e três custos preservados, posições permanentemente compradas e permanentemente vendidas, com o mesmo simulador de continuidade e alvo diário de 95% do patrimônio liquidável. Reproduzir também a carteira A-ensemble anterior como controle em cada moeda. Essas referências são reavaliadas retrospectivamente após conhecer os resultados da LSTM; sua exposição não é necessariamente igual à do modelo, e não se escolhe o lado vencedor como estratégia. Fontes, entradas, regras, controle e auditorias estão na [execução identificada](../registros/lstm_diaria/referencias_constantes_2026.json), com [conferência posterior](../registros/lstm_diaria/conferencia_referencias_constantes_2026.json): 24 carteiras, quatro reproduções de A e nenhuma falha prudencial.

| Ano | Ativo | LSTM: média / ensemble / DD ensemble | A: média / ensemble / DD ensemble | Dias comprados / vendidos LSTM ensemble |
|---|---|---:|---:|---:|
| 2025 | BTC | +10,03 / +16,66 / 9,77 | −0,99 / +12,83 / 8,36 | 0 / 51 |
| 2025 | ETH | +41,21 / −1,00 / 46,55 | +60,76 / +39,81 / 48,35 | 133 / 83 |
| 2025 | BNB | −7,28 / −20,35 / 58,74 | −25,50 / −20,51 / 54,56 | 0 / 256 |
| 2025 | XRP | −24,58 / −24,58 / 62,20 | −18,76 / +41,15 / 44,47 | 0 / 350 |
| 2026 | BTC | +15,23 / +9,99 / 5,04 | +2,40 / +27,49 / 13,45 | 16 / 0 |
| 2026 | ETH | −7,31 / +16,01 / 33,26 | −8,09 / −6,69 / 30,51 | 177 / 0 |
| 2026 | BNB | +11,93 / +13,50 / 31,43 | +35,56 / +20,51 / 24,58 | 0 / 277 |
| 2026 | XRP | +32,46 / +72,49 / 35,16 | +6,97 / +9,61 / 23,14 | 0 / 237 |

O ensemble LSTM lucrou nos quatro ativos no recorte de 2026, mas a diferença entre média de redes e ensemble pode ser grande, como em ETH/2025. O ganho de XRP/2026 veio de 237 dias vendidos e nenhum comprado; sua acurácia balanceada foi 50%. Comprar/manter no mesmo futuro perdeu 41,01% no período. A posição vendida em mercado de queda ajuda a interpretar o lucro, sem demonstrar que o modelo antecipa consistentemente altas e quedas ou que o resultado é reproduzível. Seu drawdown de 35,16% também precisa acompanhar o retorno de 72,49%.

As três carteiras LSTM individuais de XRP/2026 retornaram +84,87%, −8,41% e +20,92% nas seeds 42, 17 e 2026; sua média foi +32,46%, distinta dos +72,49% do ensemble. Essa dispersão decorre das previsões e da regra operacional não linear, sem autorizar escolher a seed lucrativa após o período. Em XRP/2025, as três carteiras registraram −24,58%; isso não prova que suas previsões fossem idênticas, pois sinais diferentes podem produzir a mesma posição.

Os intervalos principais dos contrastes operacionais LSTM−A de crescimento logarítmico diário incluem zero em todos os ativos e períodos, tanto para médias individuais como ensembles. Isso não é intervalo para retorno acumulado e não demonstra igualdade. Com slippage de 0,03% por lado, BTC/2025 passa de +16,66% a +16,49% e XRP/2026 de +72,49% a +72,02%; nenhum dos oito retornos do ensemble muda de sinal nesses cenários. A sensibilidade aos três valores provisórios não certifica custos reais, e as demais métricas permanecem na publicação, sem escolha retrospectiva de custo.

Uma [análise posterior contra caixa](../registros/lstm_diaria/contrastes_caixa.json), sem nova simulação, reamostrou o crescimento log diário das 24 combinações de ativo, ano e custo. Com 0,01% de slippage, apenas BTC/2025 teve intervalo do ensemble inteiramente acima de zero; os outros sete incluem zero, inclusive XRP/2026. Esses intervalos são exploratórios, sem correção por multiplicidade ou seleção histórica, e não quantificam certeza sobre lucro futuro. A presença de vários dias em caixa também pode levar o limite inferior exatamente a zero.

Em 2026, as referências sempre compradas tiveram retornos de −16,93%, −30,45%, −21,94% e −40,88% em BTC/ETH/BNB/XRP; sempre vendidas, +2,85%, +7,34%, +9,29% e +20,92%, respectivamente. Em XRP, a LSTM (+72,49%; drawdown 35,16%) excedeu descritivamente o sempre vendido (+20,92%; drawdown 45,44%), mas ficou vendida por 237 dias contra 314 da referência. O intervalo exploratório de 95% da diferença de crescimento log diário inclui zero nas quatro moedas; isso não prova igualdade nem vantagem futura da seleção de dias. As referências rebalanceiam para o alvo diariamente e diferem de comprar/manter quantidade fixa.

Em 2025, o ARIMA diário selecionado para BTC retornou +2,13%, com drawdown de 21,81%; nos outros três ativos, a ordem selecionada equivalia ao Naive sem deriva e permaneceu em caixa sob o filtro. São referências existentes, não novos ajustes nesta execução. ARIMA não foi extrapolado a 2026 neste ciclo.

## Interpretação para o artigo

A LSTM enriquece a comparação com outra família, mas esta receita não supera consistentemente A, L e Naive em moedas e períodos. Menor erro pode coexistir com menor retorno de uma carteira, e médias individuais não representam a operação do ensemble. A contribuição pequena dos ramos de A observada anteriormente é uma constatação sobre aqueles checkpoints, não prova de superioridade da LSTM ou inutilidade geral de Mamba. Comparações mais amplas exigem outras configurações e períodos independentes; intervalos e diferenças descritivas atuais não dão garantia de lucro.

## Sensibilidade operacional ao filtro — 17/11/2026

A execução `31bc62dadbc41d1d8f82` cruzou filtros ±0,15%, ±0,20% e ±0,25% com slippage de 0,01%, 0,02% e 0,03% por lado. Foram 324 carteiras: 24 ensembles fixos (A/L/LSTM × quatro ativos × 2025/recorte conhecido de 2026) e 12 ensembles walk-forward BTC, com nove cenários por caso. As previsões, mercados, funding e regras de continuidade permaneceram fixos. Os 108 cenários do filtro original foram reproduzidos com igualdade exata de ledger, curva e métricas; a [auditoria posterior](../registros/complemento_diario/sensibilidade_filtro/conferencia_posterior.json) recalculou todas as carteiras, sem falhas prudenciais. [Matriz completa](../dados/experimentos/complemento_sensibilidade_filtro_31bc62dadbc41d1d8f82/publicacao/carteiras.csv) e [índice com recibos](../dados/experimentos/complemento_sensibilidade_filtro_31bc62dadbc41d1d8f82/publicacao/resultados.json).

A tabela resume somente slippage de 0,01% por lado, sempre contra o mesmo caso com filtro ±0,20%. Cada linha agrega 12 casos; os grupos têm populações diferentes. A mediana e a faixa são descrições, não intervalos de confiança, retornos de uma carteira agregada ou uma regra para escolher filtro.

| População | Filtro alternativo | Casos sem mudança de decisão | Maior fração de decisões alteradas | Diferença de retorno: mínimo / mediana / máximo (p.p.) |
|---|---:|---:|---:|---:|
| Divisão fixa 2025 | ±0,15% | 1/12 | 20,00% | −23,64 / −1,09 / +66,15 |
| Divisão fixa 2025 | ±0,25% | 1/12 | 17,43% | −33,24 / −10,90 / +25,31 |
| Recorte fixo 2026 | ±0,15% | 0/12 | 33,76% | −27,10 / −0,32 / +17,56 |
| Recorte fixo 2026 | ±0,25% | 0/12 | 38,54% | −37,30 / −2,00 / +22,88 |
| Walk-forward BTC | ±0,15% | 7/12 | 17,37% | −6,31 / 0,00 / +42,04 |
| Walk-forward BTC | ±0,25% | 5/12 | 27,71% | −8,85 / 0,00 / +7,01 |

Uma alteração de 0,05 ponto percentual no filtro produziu mudanças materialmente diferentes entre os casos. Algumas carteiras permaneceram idênticas; outras alteraram muitos dias de exposição e seu retorno. Assim, estabilidade nos três custos não implica estabilidade à regra de decisão. As métricas preditivas não mudaram: o contraste isola a transformação das previsões congeladas em decisões e sua execução. Nenhum filtro foi promovido, e a faixa de lucros não representa uma oportunidade previamente identificável.

Os recibos individuais registram compra/venda/caixa desejados e executados, episódios, reversões diretas, ordens, giro, custos e funding. Episódios não equivalem a número de ordens: continuidade negocia somente a diferença necessária, com encerramento da posição quando previsto. Os recortes semestrais usam o patrimônio contínuo da mesma carteira; seus retornos não são somados. O drawdown principal considera o envelope intraminuto; o dos recortes semestrais considera fechamentos diários. A concentração nos três maiores episódios é medida sobre os ganhos positivos de movimento do contrato, não como participação no lucro líquido após custos e funding.

Para contextualizar o diagnóstico de exposição, a execução `1ab5479ffd34e6079659` herdou e [conferiu independentemente](../registros/complemento_diario/referencias_exposicao/conferencia_posterior.json) 32 referências: caixa, comprar/manter quantidade fixa, sempre comprado e sempre vendido para os oito pares ativo/período. Todas as referências foram mantidas, sem escolher retrospectivamente o lado mais lucrativo. A [tabela completa](../dados/experimentos/complemento_referencias_exposicao_1ab5479ffd34e6079659/publicacao/referencias.csv) conserva origem e membro dos ledgers. Comprar/manter e posição constante rebalanceada têm regras e exposições diferentes; nenhuma delas constitui um pareamento exato de risco com os modelos.

## Momentos de exposição: diagnóstico circular — 17/11/2026

A execução `84c7ba4175b45ea36f25` avaliou os 24 ensembles fixos, com filtro ±0,20% e slippage 0,01% por lado. Para cada caso, foram aplicados 99 deslocamentos circulares distintos à sequência de decisões −1/0/+1, mantendo preços, funding e datas nas posições cronológicas reais. Os offsets foram registrados antes das simulações, usando seed 2026111705, intervalo inclusivo de 14 a n−14 e a mesma lista entre casos com o mesmo n. Houve 2.376 carteiras deslocadas e 24 controles zero; estes reproduziram os ledgers, curvas e métricas originais exatamente. A [auditoria posterior](../registros/complemento_diario/deslocamento_exposicao/conferencia_posterior.json) aprovou a cobertura completa, a contabilidade, os offsets e os resumos, sem falhas prudenciais.

O percentil abaixo é descritivo: 100 × (alternativas com valor inferior + metade dos empates) / 99. Valores altos indicam que o retorno original ficou acima de muitas alternativas deste diagnóstico. Não são p-valores nem probabilidades de habilidade ou de lucro futuro. A tabela cobre todos os casos, sem escolher modelos ou períodos pelo percentil.

| Período | Ativo | A: percentil do retorno | L: percentil do retorno | LSTM: percentil do retorno |
|---|---|---:|---:|---:|
| 2025 | BTC | 94,95 | 98,99 | 90,91 |
| 2025 | ETH | 66,67 | 71,72 | 55,56 |
| 2025 | BNB | 51,52 | 51,52 | 70,71 |
| 2025 | XRP | 93,94 | 73,74 | 50,00* |
| 2026 conhecido | BTC | 89,90 | 97,98 | 90,91 |
| 2026 conhecido | ETH | 59,60 | 64,65 | 88,89 |
| 2026 conhecido | BNB | 74,75 | 80,81 | 65,66 |
| 2026 conhecido | XRP | 81,82 | 98,99 | 92,93 |

\* A sequência LSTM/XRP de 2025 é constante. Os 99 deslocamentos resultam na mesma sequência e carteira, com retorno −24,58% e drawdown 62,20%. O percentil 50 decorre integralmente de empates; esse caso não fornece informação sobre a escolha dos momentos de exposição pelo método. As 99 multiplicidades foram preservadas. Nos outros 23 casos, as 99 sequências alternativas foram distintas.

Vários resultados originais ficaram na parte superior de suas distribuições condicionais. Isso fornece contexto descritivo para os momentos de exposição, mas não remove a seleção histórica: modelos, receitas e períodos já eram conhecidos. Um percentil elevado pode coexistir com perda; por exemplo, BNB/LSTM de 2025 teve retorno −20,35% e percentil 70,71. Em XRP/LSTM de 2026, o retorno original de +72,49% ficou no percentil 92,93, com drawdown de 35,16%; esse resultado não transforma a sequência observada em estratégia causal confirmada. O deslocamento circular pode atravessar regimes e depende da sequência que já ocorreu.

Nesta grade, as contagens de dias efetivamente comprados, vendidos e em caixa coincidiram com as originais em todos os deslocamentos. Isso é uma observação verificada, não uma garantia geral do procedimento nem equivalência de risco. O número de episódios variou em até um por causa das bordas; o número de ordens mudou entre −36 e +55. A diferença de giro em relação ao caso original variou de aproximadamente −1,239 milhão a +1,003 milhão de USDT, e a de comissões de −619,56 a +501,44 USDT. Quantidades, evolução do patrimônio, preços encontrados e custos não ficaram pareados.

As [distribuições e resumos completos](../dados/experimentos/complemento_deslocamento_exposicao_84c7ba4175b45ea36f25/publicacao/resultados.json) incluem retorno, crescimento logarítmico diário e drawdown. No drawdown, valores menores são preferíveis; seu percentil também segue a ordem crescente dos valores, não uma escala de desempenho com “maior é melhor”. A [tabela das 2.376 alternativas](../dados/experimentos/complemento_deslocamento_exposicao_84c7ba4175b45ea36f25/publicacao/carteiras.csv) preserva offsets, resultados e diferenças operacionais. O diagnóstico usa o simulador completo, incluindo continuidade, funding, custos e encerramento, sem aproximar lucro por sinais multiplicados por retornos.
