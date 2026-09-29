# Piloto AR(1) — BTCUSDT, previsão das próximas 24 horas, D1

**Execução pelo pesquisador em 28/09/2026.** Resultado local: `dados/experimentos/piloto_ar1_f39a7dd1df543363b7d0/resultado.json`; dataset de origem: `daeec76f001afb50a8fe`. Trata-se de **avaliação de desenvolvimento**, sem Mamba e sem consulta aos folds finais de 2024–2025.

## O que foi previsto

Às 00:00 UTC de cada dia elegível, o modelo usou o último retorno diário já observado para estimar o retorno das **24 horas seguintes** de BTCUSDT. `retorno previsto > 0` virou classe 1 (*alta*); retorno previsto igual ou menor que zero virou classe 0 (*não alta*). Qualquer alta conta, sem limiar de 5%.

O método é ARIMA(1,0,0) nos log-retornos, equivalente aqui a AR(1) com intercepto estimado por mínimos quadrados:

```text
retorno_previsto_seguinte = −0,002184929 − 0,054793735 × ultimo_retorno_observado
```

O ajuste usou **495 pares** de retornos de amostras elegíveis do treino D1, com término do alvo antes de 01/10/2022. `alfa = −0,002184929` é a previsão de log-retorno quando o último retorno é zero: aproximadamente **−0,218%** em um dia. `phi = −0,054793735` é a inclinação: um último log-retorno de +1% reduz a previsão seguinte em cerca de 0,055 ponto percentual. O coeficiente negativo descreve uma tendência linear fraca de reversão neste ajuste; sozinho não demonstra que tal relação é estatisticamente confiável.

Com esses coeficientes, a previsão só passa para *alta* se o último log-retorno diário for inferior a aproximadamente **−3,988%** (queda simples de cerca de 3,91%). Isso explica por que o AR(1) previu quase sempre classe 0. Os coeficientes foram mantidos fixos na validação e no teste de desenvolvimento; a cada origem mudou apenas o retorno mais recente já conhecido.

## Números exibidos pelo programa

| Resultado | Validação, 2022-T4 | Teste de desenvolvimento, 2023-T1 | Significado |
|---|---:|---:|---|
| Amostras (`n`) | 91 | 82 | Dias com origem e alvo elegíveis após purga e lacunas. |
| Altas reais | 39 | 41 | Dias cujo preço-alvo superou o da origem. |
| Não altas reais | 52 | 41 | Baixas e empates reais; neste piloto não houve empate. |
| Altas previstas | 3 | 3 | Casos em que o retorno estimado foi positivo. |
| Não altas previstas | 88 | 79 | Casos em que o retorno estimado foi zero ou negativo. |
| Balanced accuracy | **0,5160** | **0,4634** | Média do recall das classes 0 e 1; métrica primária. |
| Accuracy | 0,5824 | 0,4634 | Fração total de classes acertadas. |
| F1 macro | 0,4119 | 0,3167 | Média do F1 das classes 0 e 1. |

O bloco chamado `teste` no terminal é **2023-T1, reservado para desenvolvimento**, não o teste final de 2024–2025. Na validação, as origens vão de 01/10 a 30/12/2022; no teste de desenvolvimento, de 01/01 a 23/03/2023. A última origem de março reflete o recorte de qualidade e o alvo disponível antes da lacuna de 24/03.

### Como ler a matriz de confusão

Linhas são a classe **real**; colunas são a classe **prevista**. A diagonal contém acertos.

| Validação | Previu 0 | Previu 1 |
|---|---:|---:|
| Real 0, não alta | **51** | 1 |
| Real 1, alta | 37 | **2** |

| Teste de desenvolvimento | Previu 0 | Previu 1 |
|---|---:|---:|
| Real 0, não alta | **38** | 3 |
| Real 1, alta | 41 | **0** |

Assim, o acerto total da validação é `(51 + 2)/91 = 0,5824`; no teste de desenvolvimento é `(38 + 0)/82 = 0,4634`. A accuracy da validação parece razoável porque havia mais dias de não alta e o modelo quase sempre escolheu essa classe. Ela **não** significa que o modelo reconheceu bem as altas.

### Por que a balanced accuracy e o F1 são menores

**Recall** mede a fração de ocorrências reais de uma classe que foi encontrada:

| Classe | Recall validação | Recall teste de desenvolvimento |
|---|---:|---:|
| Não alta (0) | `51/52 = 98,08%` | `38/41 = 92,68%` |
| Alta (1) | `2/39 = 5,13%` | `0/41 = 0%` |

A balanced accuracy é a média dos dois recalls. Na validação, `(98,08% + 5,13%)/2 = 51,60%`; no teste de desenvolvimento, `(92,68% + 0%)/2 = 46,34%`. Com ambas as classes reais presentes, **50% é a referência matemática** de uma regra que sempre prevê a mesma classe. Aqui ela ajuda a enxergar que o ganho de 1,60 ponto percentual da validação é pequeno e não se repetiu no bloco seguinte. Não é um p-valor.

**Precision** pergunta, entre as previsões de uma classe, quantas estavam certas. Na validação, a precision de alta foi `2/3 = 66,67%`, mas houve só **três** previsões de alta; esse percentual isolado é instável e não compensa o recall de apenas `2/39`. No teste de desenvolvimento, a precision de alta foi `0/3 = 0%`.

O **F1** combina precision e recall; é baixo para a classe alta: **0,0952** na validação e **0** no teste de desenvolvimento. Para não alta, os F1 foram **0,7286** e **0,6333**. O F1 macro exibido é a média simples: `(0,7286 + 0,0952)/2 = 0,4119` e `(0,6333 + 0)/2 = 0,3167`. Isso confirma que o desempenho está concentrado na classe 0.

## O que concluir agora

Este **AR(1) específico, no fold D1 de BTC**, quase sempre previu não alta; ficou pouco acima de 50% de balanced accuracy na validação e abaixo no teste de desenvolvimento. A diferença entre blocos mostra por que não se deve tirar uma conclusão geral de um único trimestre. Os resultados não demonstram que ARIMA em geral é inadequado, que o Mamba é superior ou que uma estratégia teria lucro.

Para a comparação científica, será necessário obter previsões do Mamba **nos mesmos timestamps** e calcular `BA_Mamba − BA_AR1` em cada fold. A distância de `BA_Mamba` a 50% e o teste Pesaran–Timmermann são análises separadas; este piloto não fornece nenhuma das três conclusões sobre o Mamba.

Para verificar o AR(1) com **mais histórico de treino**, executar [D1–D4 em conjunto](README.md#mais-histórico-d1d4-no-btc). O treino cresce de 495 para 745 pares até D4. Como os trimestres de avaliação mudam, diferenças de score entre folds não isolam somente o efeito da quantidade de dados.
