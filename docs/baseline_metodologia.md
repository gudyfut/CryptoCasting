# Nota metodológica — baselines para previsão direcional de criptomoedas

**Projeto:** CryptoCasting  
**Data:** 14/09/2026  
**Decisão incorporada ao:** [protocolo experimental](protocolo_experimental.md#7-baselines-e-decisão-de-classe)

## Problema

Uma acurácia isolada não diz se o Mamba aprendeu informação útil. Se 56% dos retornos do teste forem positivos, prever sempre alta já produz 56% de accuracy. Da mesma forma, obter 52% de acerto pode representar ganho real sobre uma baseline de 49%, empate com uma de 52% ou perda para uma regra simples com 55%.

Uma baseline deve estar disponível no instante da previsão, ser treinada apenas no passado quando possuir parâmetros e ser avaliada nas mesmas observações do modelo. Para este TCC, nenhuma referência isolada cobre todos os significados de “sem habilidade”. Por isso, será usada uma hierarquia curta e previamente definida.

## O que a literatura sustenta

Não há uma baseline única e exclusiva de cripto. O benchmark mais tradicional em previsão de preços/retornos financeiros é o **random walk**, geralmente implementado como preço futuro igual ao atual ou retorno previsto igual a zero.

- Gradojevic et al. avaliam retornos horários e diários de Bitcoin contra random walk e ARMAX, encontrando resultados diferentes conforme a frequência. Isso sustenta comparar o Mamba a uma referência random walk e a uma relação estatística simples: [International Journal of Forecasting, DOI 10.1016/j.ijforecast.2021.08.001](https://doi.org/10.1016/j.ijforecast.2021.08.001).
- Liu, Zhang e Zhao estudam previsão fora da amostra de retornos diários de BTC, ETH e XRP e usam explicitamente a previsão de retorno zero como benchmark: [Physica A, DOI 10.1016/j.physa.2022.127379](https://doi.org/10.1016/j.physa.2022.127379).
- Pesaran e Timmermann propõem um teste não paramétrico para verificar se sinais previstos e realizados têm associação direcional: [Journal of Business & Economic Statistics, DOI 10.1080/07350015.1992.10509922](https://doi.org/10.1080/07350015.1992.10509922). A implementação documentada pelo [statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.stats.diagnostic.pesaran_timmermann.html) explicita que a hipótese nula é independência entre os sinais.
- Gneiting e Raftery mostram por que previsões de probabilidade devem ser avaliadas com regras próprias, como o Brier score: [Journal of the American Statistical Association, DOI 10.1198/016214506000001437](https://doi.org/10.1198/016214506000001437).

Esses trabalhos não determinam que momentum seja universalmente a melhor baseline de cripto. Eles mostram que random walk/retorno zero, modelos estatísticos simples e avaliação direcional fora da amostra são referências defensáveis.

## Baselines adotadas

| Código | Referência | Informação utilizada | Pergunta respondida |
|---|---|---|---|
| B0 | Random walk, retorno zero | Preço atual; `p(alta)=0,5` | O modelo supera ausência teórica de previsibilidade? |
| B1 | Prevalência/classe majoritária | Proporção de altas apenas no treino | O score vem apenas do desequilíbrio das classes? |
| B2 | Momentum, principal | Direção do retorno imediatamente anterior com duração `H` | O Mamba supera a regra direcional ingênua mais direta? |
| B3 | AR(1) | Relação linear entre retorno passado e futuro, estimada no treino | A complexidade do Mamba acrescenta algo além de dinâmica linear simples? |

### B0 — random walk

```text
retorno_previsto = 0
p(alta) = 0,5
```

Random walk não é momentum. Na previsão de preço, ele mantém o último preço. Na classificação, retorno exatamente zero precisa seguir a convenção de empate e gera uma classe constante; por isso seu uso mais limpo neste projeto será como probabilidade `0,5` para Brier score e como referência teórica para acurácia direcional.

Não será sorteada uma moeda em cada observação. Essa simulação adicionaria variância desnecessária: a previsão probabilística `0,5` representa diretamente o acaso.

### B1 — prevalência histórica

```text
p_treino = (altas_treino + 1) / (n_treino + 2)
classe = 1 se p_treino > 0,5; senão 0
```

A proporção é congelada para validação/teste do fold. Usar a proporção observada no teste vazaria informação. A suavização de Laplace evita probabilidades extremas em amostras pequenas.

### B2 — momentum

```text
classe = 1 se C_t > C_(t-H); senão 0
```

Se o alvo cobre as próximas 24 horas, a baseline observa as 24 horas anteriores. Para próximo candle, observa o candle anterior. Usar sempre apenas o último candle de 15 minutos para prever 24 horas produziria um benchmark desalinhado.

### B3 — AR(1)

```text
r_futuro(t,H) = alfa + phi * r_passado(t,H) + erro
r_passado(t,H) = ln(C_t / C_(t-H))
classe = 1 se retorno_estimado > 0; senão 0
```

`alfa` e `phi` são ajustados novamente em cada fold, apenas no treino. Não haverá escolha de várias defasagens. Trata-se de uma referência estatística de baixa capacidade, não de uma nova arquitetura neural concorrente.

## Métricas e interpretação

A métrica primária passará a ser **balanced accuracy (BA)**:

```text
BA = (recall_alta + recall_nao_alta) / 2
delta_BA = BA_Mamba - BA_momentum
```

Quando ambas as classes aparecem, um classificador constante obtém BA igual a 0,5. Isso torna o ponto de “sem discriminação” claro, mesmo quando altas e quedas não têm a mesma frequência. Accuracy direcional e F1 macro continuarão reportadas.

Para a probabilidade de alta, será usado:

```text
BS = media((probabilidade_alta - alvo)^2)
BSS = 1 - BS_Mamba / BS_prevalencia
```

No Brier score, menor é melhor. BSS positivo significa que o Mamba melhorou a previsão probabilística em relação à frequência histórica do treino; BSS negativo significa piora.

O teste de Pesaran–Timmermann responderá se há associação entre direção prevista e realizada. Ele não prova que o Mamba é superior ao momentum ou ao AR(1). Essa superioridade será avaliada por diferenças pareadas de BA e intervalos obtidos pelo bootstrap temporal do protocolo.

## Régua de conclusão

| Resultado | Interpretação |
|---|---|
| `delta_BA <= 0` contra momentum, ou `BSS <= 0` | Ruim: não acrescenta habilidade sobre referências simples em uma dimensão essencial |
| Delta positivo, intervalo de 95% contendo zero | Promissor, mas inconclusivo: o ganho pode ser compatível com variação amostral |
| Delta contra momentum positivo com intervalo acima de zero, BSS positivo e BA acima da majoritária | Bom: evidência de ganho direcional e probabilístico fora da amostra |
| Critério bom + supera AR(1) + ganho em todas as moedas e em pelo menos 75% dos folds | Muito forte/robusto neste protocolo |

“Ótimo” não será definido como uma acurácia absoluta escolhida antecipadamente, como 60% ou 70%. O significado depende da classe majoritária, do horizonte, do ativo, da baseline e da incerteza. A régua qualifica força da evidência dentro deste recorte; não garante retorno financeiro nem generalização universal.

## Saída mínima por fold

Salvar uma linha por origem com `timestamp`, retorno realizado, alvo, probabilidade e classe do Mamba, e classes B0–B3. O resumo por moeda/granularidade deve conter BA, accuracy, F1 macro, Brier, BSS, deltas pareados, suportes e intervalos. Baselines determinísticas aparecem uma vez por fold; não são replicadas pelas seeds do Mamba.
