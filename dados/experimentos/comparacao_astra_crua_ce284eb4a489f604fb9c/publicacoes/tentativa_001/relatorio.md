# Candidata Astra versus OHLCV cru + Huber

Execução `ce284eb4a489f604fb9c`. Mesmos dados, executor científico e oito seeds/quatro blocos.32Astra herdados;32crus novos;dois controles excluídos das médias.

| Versão | MSE médio teste | RMSE médio | MAE médio |
|---|---:|---:|---:|
| astra | 0.0006122753 | 0.0245987 | 0.0177640 |
| crua | 0.0006114371 | 0.0245711 | 0.0177258 |
| naive | 0.0006092954 | 0.0245283 | 0.0176953 |

## Incerteza

Diferença negativa favorece o primeiro modelo. IC98,333% ajustado para três contrastes; bootstrap pareado de seeds/dias14.

| Contraste | Diferença MSE | IC ajustado |
|---|---:|---|
| astra_menos_crua | 8.38188425e-07 | [-7.266237654168076e-06, 9.532796518630295e-06] |
| astra_menos_naive | 2.97989583e-06 | [-4.88912043592503e-06, 1.2208151581791196e-05] |
| crua_menos_naive | 2.1417074e-06 | [-1.2490747545031659e-06, 5.897950261652832e-06] |

## Operação: média das oito seeds, custos base

| Bloco | Smart Astra | Smart crua | Diária Astra | Diária crua |
|---|---:|---:|---:|---:|
| B1 | +36.01% | +6.06% | +3.17% | +0.00% |
| B2 | +21.06% | +0.00% | -3.55% | +0.00% |
| B3 | +10.50% | +13.38% | +0.63% | +0.00% |
| B4 | -18.97% | -21.78% | -12.42% | +0.00% |

192carteiras novas,216herdadas; custos e políticas inalterados. Smart mantém posição; parâmetro2% não é stop-loss. Naive mantém caixa nessas políticas.

2024/2025 conhecidos; comparacao retrospectiva, sem novo holdout.
Duas mudancas simultaneas: representacao e contexto. Nao isola efeito individual.
Medias de oito modelos individuais por bloco; nao ensemble.
Carteiras independentes, sem compor retornos dos quatro blocos.
Intervalos condicionais nao corrigem a selecao previa de receitas.
Sem novas consultas Astra, busca de configuracoes ou promocao automatica.

[Dados completos](../dados/experimentos/comparacao_astra_crua_ce284eb4a489f604fb9c/publicacoes/tentativa_001/resultados.json).
