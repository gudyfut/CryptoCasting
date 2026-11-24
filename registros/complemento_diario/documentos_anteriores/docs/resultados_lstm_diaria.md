# LSTM diária em comparação com A e L

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
