# Baseline AR(1) — BTCUSDT nos quatro folds de desenvolvimento

**Execução pelo pesquisador em 28/09/2026.** Dataset `daeec76f001afb50a8fe`; tarefa principal de direção nas próximas 24 horas. Fonte local: `dados/experimentos/resumo_ar1_desenvolvimento_daeec76f001afb50a8fe_BTCUSDT.json`, que aponta para os quatro `resultado.json` individuais e registra seus hashes. Os blocos avaliados são os quatro trimestres de 2023. Nenhum score final de 2024–2025 foi consultado.

O ARIMA(1,0,0) foi ajustado como AR(1) com intercepto nos log-retornos diários. Em cada fold, o treino expansivo usa somente amostras elegíveis anteriores à fronteira temporal, com purga de rótulos. A decisão é *alta* quando o retorno previsto é positivo; caso contrário, *não alta*. Não há limiar de magnitude da alta.

## Resultados

| Fold | Pares de treino | Dias avaliados | BA | Accuracy | F1 macro | Altas reais | Altas previstas | Altas acertadas | Recall de alta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| D1, 2023-T1 | 495 | 82 | 46,34% | 46,34% | 0,3167 | 41 | 3 | 0 | 0,00% |
| D2, 2023-T2 | 587 | 75 | 50,11% | 52,00% | 0,3656 | 36 | 2 | 1 | 2,78% |
| D3, 2023-T3 | 670 | 91 | 47,06% | 52,75% | 0,3453 | 40 | 3 | 0 | 0,00% |
| D4, 2023-T4 | 745 | 91 | 52,94% | 47,25% | 0,3681 | 51 | 3 | 3 | 5,88% |

**BA média dos folds: 49,11%.** É a média simples das quatro BA, com o mesmo peso para cada trimestre, conforme o protocolo; não é uma nova avaliação sobre observações reunidas. O número de pares de treino aumentou de 495 para 745, cerca de 50,5%, mas as BA oscilaram. Não há melhora consistente conforme cresce o treino.

Nas **339 origens avaliadas**, houve **168 altas reais**. O modelo previu alta só **11 vezes** e acertou **4** dessas 168 altas. Estes totais descrevem o comportamento dos quatro blocos e não substituem a média por fold. As matrizes de confusão abaixo tornam visível a predominância da previsão *não alta*; linhas são classes reais e colunas, previstas.

| Fold | Real 0 → previsto 0 | Real 0 → previsto 1 | Real 1 → previsto 0 | Real 1 → previsto 1 |
|---|---:|---:|---:|---:|
| D1 | 38 | 3 | 41 | 0 |
| D2 | 38 | 1 | 35 | 1 |
| D3 | 48 | 3 | 40 | 0 |
| D4 | 40 | 0 | 48 | 3 |

Em D4, a **BA de 52,94%** convive com **accuracy de 47,25%**: o modelo encontrou todos os 40 dias de não alta, mas apenas 3 dos 51 dias de alta. A BA dá metade do peso ao recall de cada classe: `(40/40 + 3/51)/2 = 52,94%`. A accuracy conta acertos totais: `(40 + 3)/91 = 47,25%`. Portanto, a BA acima de 50% em D4 não significa bom reconhecimento de altas.

## Interpretação e limites

Neste **AR(1) específico para BTCUSDT em 2023**, o resultado médio ficou 0,89 ponto percentual abaixo da referência matemática de 50% de BA. Essa diferença pequena, sem intervalo de incerteza ou teste apropriado, não estabelece inferioridade estatística. O sinal prático mais claro é a raridade das previsões de alta e o recall de alta entre 0% e 5,88% nos folds.

O treino e o trimestre avaliado mudam juntos de D1 a D4. Assim, a oscilação não mede isoladamente o efeito de acrescentar dados. Estes resultados não avaliam outras especificações ARIMA, outras moedas, retorno financeiro, LSTM nem Mamba. O AR(1) permanece a baseline estatística predefinida; não será ajustado retrospectivamente para melhorar estes scores. Na revisão 1.6, depois deste piloto, o pesquisador incluiu LSTM como segunda baseline. Quando houver previsões das duas redes nos **mesmos timestamps**, calcular `BA_Mamba − BA_AR1` e `BA_Mamba − BA_LSTM` por fold. A distância do Mamba a 50% e o teste de Pesaran–Timmermann serão relatados separadamente.
