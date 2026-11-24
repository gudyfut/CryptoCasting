# Entradas relativas, cruas e níveis padronizados

Execução `76f6c437e70eaaa605ad`. Oito seeds por versão/bloco; quatro blocos,64ajustes novos+2controles e32referências MSE herdadas.

[Protocolo](protocolo_entradas_niveis.md), [estado](../registros/entradas_niveis/estado.json).

## Médias das oito seeds por bloco

| Bloco | Parte | Atual MSE | Crua MSE | Níveis padronizados MSE |
|---|---|---:|---:|---:|
| B1 | validacao | 0.0004902856 | 0.0004829695 | 0.0004755522 |
| B1 | teste | 0.0007282770 | 0.0007370560 | 0.0007538854 |
| B2 | validacao | 0.0005728364 | 0.0005695012 | 0.0005637781 |
| B2 | teste | 0.0007225947 | 0.0007265668 | 0.0007473749 |
| B3 | validacao | 0.0006032542 | 0.0006118555 | 0.0006285818 |
| B3 | teste | 0.0005934036 | 0.0005905105 | 0.0006008048 |
| B4 | validacao | 0.0003938712 | 0.0004089005 | 0.0004037976 |
| B4 | teste | 0.0004299033 | 0.0004046596 | 0.0004070954 |

## Médias com peso igual entre os quatro blocos

| Parte | Variante | MSE | RMSE×100 | MAE×100 | Habilidade Naive |
|---|---|---:|---:|---:|---:|
| validacao | atual | 0.0005150618 | 2.2621 | 1.6341 | +1.186% |
| validacao | crua | 0.0005183067 | 2.2699 | 1.6351 | +0.564% |
| validacao | niveis_padronizados | 0.0005179274 | 2.2679 | 1.6372 | +0.637% |
| teste | atual | 0.0006185446 | 2.4739 | 1.7887 | -1.518% |
| teste | crua | 0.0006146982 | 2.4630 | 1.7805 | -0.887% |
| teste | niveis_padronizados | 0.0006272901 | 2.4869 | 1.8056 | -2.953% |

## Contrastes predefinidos de teste

| Contraste | Diferença MSE | IC98,333% principal | Interpretação |
|---|---:|---|---|
| crua_menos_atual | -3.846424975e-06 | [-1.4694647142589576e-05, 6.26758151591911e-06] | inconclusivo |
| niveis_padronizados_menos_atual | 8.745481403e-06 | [-7.940046060175639e-06, 2.8263334973567554e-05] | inconclusivo |
| crua_menos_niveis_padronizados | -1.259190638e-05 | [-2.6389028440722705e-05, -2.8019662280540813e-06] | melhora |

## Smart com custos base: média de oito carteiras independentes

| Bloco | Atual | Crua | Níveis padronizados |
|---|---:|---:|---:|
| B1 | +14.19% | +0.73% | +8.32% |
| B2 | +25.11% | +0.00% | +10.48% |
| B3 | +4.62% | +3.91% | -0.01% |
| B4 | -19.87% | -12.02% | -14.88% |

Todos os resultados por seed, dispersões, decisões, sensibilidades7/28, custos, risco e referências operacionais estão na publicação estruturada. Controles reais não entram nas médias.

Retrospectivo2024/2025; oito seeds não garantem certeza.
Três contrastes fixos; IC98,333% principal Bonferroni,14dias; sensibilidades7/28.
Mesmas origens, alvo e cinco canais; sem timestamp, indicadores ou novas buscas.
Comparação de entradas sob receita fixa; não demonstra desempenho ótimo de cada representação.
Médias de modelos individuais, não ensemble; carteiras independentes por bloco.
Não há retomada automática após falha nem repetição até passar/lucrar.
