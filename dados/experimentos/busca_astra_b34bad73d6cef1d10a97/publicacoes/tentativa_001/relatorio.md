# Busca adaptativa assistida por Astra — resultados

Execucao `b34bad73d6cef1d10a97`. Comparacao retrospectiva apos congelar finalista.

| Versao | MSE teste medio | MAE teste medio |
|---|---:|---:|
| referencia | 0.0006212451997 | 0.0179585 |
| candidata | 0.0006122753212 | 0.017764 |
| naive | 0.0006092954253 | 0.0176953 |

Intervalos, seeds e todas as carteiras em `publicacao/resultados.json` da execucao.

2024/2025 ja consultados; retrospectivo, nao holdout intocado.
Busca adaptativa: comparacao de receitas, nao ablacao de um fator.
Referencia nova usa o mesmo aquecimento336 e implementacao; nao substituir resultados anteriores.
Cada carteira inicia10000USDT por bloco; nao compor retornos entre blocos.
MSE e lucro distintos; nenhuma promocao automatica.
