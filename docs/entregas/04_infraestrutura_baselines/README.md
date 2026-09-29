# Entrega 4 — infraestrutura e duas baselines

**Estado em 28/09/2026:** ARIMA(1,0,0) implementado e executado pelo pesquisador em BTCUSDT/D1–D4. O [piloto D1](resultados_piloto_BTC_D1.md) e os [resultados dos quatro folds](resultados_desenvolvimento_BTC_D1_D4.md) estão documentados. A LSTM foi incluída no protocolo 1.6, mas **não está implementada nem foi executada**. Ainda faltam a LSTM e a infraestrutura experimental completa da Entrega 4.

## Trabalho restante desta entrega

Implementar LSTM unidirecional com as duas larguras previstas no [protocolo](../../protocolo_experimental.md), alimentada pelos mesmos tensores e scaler de treino do Mamba. Preparar o treino walk-forward compartilhado, as seeds, os checkpoints e a saída de previsões com timestamps; verificar pareamento de amostras e a ausência de vazamento antes de qualquer comparação. Os ajustes completos ficam a cargo do pesquisador. O AR(1) existente mantém sua configuração e os resultados de BTC já observados.

## O que o teste mede

O [protocolo](../../protocolo_experimental.md) fixa ARIMA(1,0,0) **nos log-retornos**. Nessa série, ele é um AR(1) com intercepto:

```text
r_(t+1) = alfa + phi × r_t + erro
classe prevista = 1 se retorno previsto > 0; senão 0
```

Os parâmetros são estimados por mínimos quadrados ordinários nos pares de retornos de **amostras elegíveis do treino purgado**. Na matriz principal de 24 horas, usam-se fechamentos diários UTC do par. Assim, para a mesma moeda e origem, a baseline terá a mesma previsão diante dos quatro tamanhos de candle do Mamba e dos contextos de 7/14 dias. Ela não usa features do Mamba, scaler nem seed.

O piloto padrão usa BTCUSDT, tarefa principal, fold de desenvolvimento **D1**: treino anterior a 01/10/2022, validação de 2022-T4 e avaliação em 2023-T1, sempre com a purga do término do alvo. O programa bloqueia os folds finais de 2024–2025 enquanto a configuração do Mamba não estiver congelada; consultar esses scores agora poderia orientar escolhas com o teste final.

## Comando para o pesquisador

Na raiz do projeto, com as dependências de `requirements.txt` instaladas:

```powershell
python run_baseline.py --dataset dados/processados/daeec76f001afb50a8fe --par BTCUSDT --fold D1
```

O programa imprime número de pares usados no ajuste, `alfa`, `phi`, balanced accuracy (BA), accuracy e F1 macro na validação e na avaliação de desenvolvimento. O primeiro resultado real está [documentado aqui](resultados_piloto_BTC_D1.md). Para outro par, altere `--par`; os pares permitidos são BTCUSDT, ETHUSDT, BNBUSDT e XRPUSDT. Para outro fold de desenvolvimento, use `--fold D2`, `D3` ou `D4`.

Para testar a tarefa complementar de próximo candle, por exemplo em 1h:

```powershell
python run_baseline.py --dataset dados/processados/daeec76f001afb50a8fe --par BTCUSDT --fold D1 --tarefa proximo_candle --granularidade 1h
```

### Mais histórico: D1–D4 no BTC

Para examinar como a baseline se comporta nos quatro folds de desenvolvimento, com treino expansivo:

```powershell
python run_baseline_desenvolvimento.py --dataset dados/processados/daeec76f001afb50a8fe --par BTCUSDT
```

| Fold | Pares de treino elegíveis | Teste de desenvolvimento |
|---|---:|---:|
| D1 | 495 | 82 amostras, 2023-T1 |
| D2 | 587 | 75 amostras, 2023-T2 |
| D3 | 670 | 91 amostras, 2023-T3 |
| D4 | 745 | 91 amostras, 2023-T4 |

O comando salva cada execução individual e um JSON `dados/experimentos/resumo_ar1_desenvolvimento_{id_dataset}_BTCUSDT.json`, com BA média **não ponderada** dos quatro folds. Também é possível usar `--todos-pares` para incluir ETH, BNB e XRP nos mesmos folds de desenvolvimento. Agentes não executam esses ajustes; o pesquisador roda o script.

O pesquisador executou o comando para BTCUSDT. A [análise dos resultados D1–D4](resultados_desenvolvimento_BTC_D1_D4.md) registra BA média de **49,11%**, matrizes de confusão e o baixo recall de alta.

**Interpretação:** o treino cresce de D1 a D4, mas os trimestres avaliados mudam ao mesmo tempo. Uma diferença de BA pode refletir regime de mercado, distribuição das classes e lacunas, além do tamanho do treino. Esses quatro folds mostram estabilidade temporal com histórico expansivo; isoladamente, não estimam o efeito causal de acrescentar dados. Os folds finais de 2024–2025 continuam bloqueados neste comando.

A célula complementar diária reutiliza a baseline principal. O caminho de saída aparece no terminal, em `dados/experimentos/piloto_ar1_{id}/`. Lá ficam `resultado.json`, `previsoes_validacao.parquet` e `previsoes_teste.parquet`. O JSON registra ID e hash do dataset, hash do código, período, coeficientes, quantidade de pares, versões, métricas, suportes e matriz de confusão. Cada previsão guarda timestamp da origem e do alvo, rótulo, último retorno conhecido e retorno estimado. Os parquets de entrada são verificados contra o manifesto da Entrega 3 antes do ajuste.

## Como interpretar

- BA da baseline responde quanto esse AR(1) acerta em ambas as classes na população e no período escolhidos. Accuracy e F1 macro complementam a leitura; consultar também suportes e a matriz de confusão.
- O patamar de **50% de BA** é uma referência matemática quando as duas classes reais existem. Não é o score observado do AR(1).
- Ainda não há diferenças `BA_Mamba − BA_AR1` ou `BA_Mamba − BA_LSTM`, porque Mamba e LSTM não foram avaliados.
- O teste Pesaran–Timmermann (PT) é outra análise, aplicada conforme o protocolo depois das previsões dos modelos; não testa a diferença Mamba versus qualquer baseline.
- Um resultado do D1 pode orientar desenvolvimento, mas não demonstra desempenho em 2024–2025, rentabilidade ou superioridade do Mamba.

## Verificações feitas pelo agente

O código da baseline foi compilado e testado com dados sintéticos para conferir: alinhamento de retornos consecutivos, rejeição de lacuna/par divergente, decisão de classe com coeficientes congelados, métricas e bloqueio dos folds finais. **Nenhum parâmetro foi ajustado aos dados oficiais pelo agente.** O pesquisador executou o comando acima; os resultados estão no relatório vinculado.
