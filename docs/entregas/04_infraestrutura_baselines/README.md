# Entrega 4 — infraestrutura e duas baselines

**Estado em 13/10/2026:** ARIMA(1,0,0) implementado e executado pelo pesquisador em BTCUSDT/D1–D4. O [piloto D1](resultados_piloto_BTC_D1.md) e os [resultados dos quatro folds](resultados_desenvolvimento_BTC_D1_D4.md) estão documentados. LSTM, infraestrutura de desenvolvimento, métricas, PT e pareamento foram validados no [piloto neural BTCUSDT/1d/D1 em CPU](../05_mamba_base/resultados_piloto_BTC_D1_cpu.md), executado com autorização do usuário. **Aceite funcional da infraestrutura no piloto CPU concluído; a grade completa pertence às entregas posteriores.**

## Infraestrutura implementada

A LSTM unidirecional possui as duas larguras do [protocolo](../../protocolo_experimental.md) e usa os mesmos tensores e scaler do Mamba. A execução compartilhada inclui folds D1–D4, seed 42, checkpoints, probabilidades, comparação por timestamps, BA/accuracy/F1/matriz de confusão e teste PT. Os [comandos, artefatos e critérios de aceite estão na Entrega 5](../05_mamba_base/README.md). O AR(1) mantém sua especificação e os resultados de BTC já observados.

O PT usa a formulação clássica de Pesaran–Timmermann (1992), com correção de amostra finita na variância e p-valor normal bicaudal; séries constantes ou variância não positiva retornam indisponibilidade. A autocorrelação de lag 1 de rótulos e previsões é registrada por fold (entre observações consecutivas disponíveis). Nesta etapa os p-valores são **exploratórios**, não provas confirmatórias de previsibilidade. PT não testa a diferença Mamba menos AR(1) ou LSTM. [Fonte original](https://doi.org/10.1080/07350015.1992.10509922).

As quatro leituras são campos distintos: ganho sobre AR(1), ganho sobre LSTM, distância da BA a 50% e PT por modelo. A consolidação pode juntar D1–D4 para descrever o desenvolvimento, com pesos iguais por fold e cobertura explícita. As execuções finais de 2024–2025 continuam bloqueadas até o congelamento.

Na revisão técnica, a consolidação passou a recalcular as métricas dos parquets e rejeitar resumos inconsistentes, arquivos obrigatórios ausentes, datas fora dos folds e metadados divergentes. Código e protocolo efetivos são preservados junto das novas execuções. A [matriz de configurações](../05_mamba_base/matriz_experimental.md) detalha como moedas, janelas e períodos se combinam.

## Execução e aceite do piloto

O agente executou AR(1), LSTM e Mamba em BTCUSDT/1d/D1 após autorização explícita. A auditoria recalculou métricas e a recarga independente dos checkpoints reproduziu exatamente as probabilidades salvas. Os testes sintéticos continuam separados dessa execução real.

### Condição para concluir a Entrega 4

| Parte | Situação | Evidência necessária para fechar |
|---|---|---|
| AR(1) e piloto BTC/D1–D4 | Implementado e executado | Relatórios históricos já vinculados nesta entrega |
| LSTM, separação temporal e normalização | Validados no piloto CPU | Piloto `481b79d054b046fe6b70` concluído: histórico, checkpoint e previsões da LSTM preservados |
| Métricas, PT, pareamento e registros | Validados no piloto CPU | Auditoria por `run_avaliacao.py` aprovada; interpretação registrada no relatório |

O mesmo piloto BTCUSDT/1d/D1 produz as evidências de LSTM da Entrega 4 e de Mamba da Entrega 5. Os comandos e a lista de conferência estão na [Entrega 5](../05_mamba_base/README.md#aceite-das-entregas-4-e-5). Fechar esta entrega não exige executar toda a grade das Entregas 6–9 nem obter uma BA acima de 50%; exige funcionamento verificável e resultados corretamente registrados.

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

O comando salva cada execução individual e um JSON `dados/experimentos/resumo_ar1_desenvolvimento_{id_dataset}_BTCUSDT.json`, com BA média **não ponderada** dos quatro folds. Também é possível usar `--todos-pares` para incluir ETH, BNB e XRP nos mesmos folds de desenvolvimento. A execução histórica D1–D4 foi feita pelo pesquisador; a exceção posterior autorizou o piloto pareado D1 pelo agente.

O pesquisador executou o comando para BTCUSDT. A [análise dos resultados D1–D4](resultados_desenvolvimento_BTC_D1_D4.md) registra BA média de **49,11%**, matrizes de confusão e o baixo recall de alta.

**Interpretação:** o treino cresce de D1 a D4, mas os trimestres avaliados mudam ao mesmo tempo. Uma diferença de BA pode refletir regime de mercado, distribuição das classes e lacunas, além do tamanho do treino. Esses quatro folds mostram estabilidade temporal com histórico expansivo; isoladamente, não estimam o efeito causal de acrescentar dados. Os folds finais de 2024–2025 continuam bloqueados neste comando.

A célula complementar diária reutiliza a baseline principal. O caminho de saída aparece no terminal, em `dados/experimentos/piloto_ar1_{id}/`. Lá ficam `resultado.json`, `previsoes_validacao.parquet` e `previsoes_teste.parquet`. O JSON registra ID e hash do dataset, hash do código, período, coeficientes, quantidade de pares, versões, métricas, suportes e matriz de confusão. Cada previsão guarda timestamp da origem e do alvo, rótulo, último retorno conhecido e retorno estimado. Os parquets de entrada são verificados contra o manifesto da Entrega 3 antes do ajuste.

## Como interpretar

- BA da baseline responde quanto esse AR(1) acerta em ambas as classes na população e no período escolhidos. Accuracy e F1 macro complementam a leitura; consultar também suportes e a matriz de confusão.
- O patamar de **50% de BA** é uma referência matemática quando as duas classes reais existem. Não é o score observado do AR(1).
- No piloto pareado D1/CPU, `BA_Mamba − BA_AR1 = −4,88 p.p.` e `BA_Mamba − BA_LSTM = −8,54 p.p.`. As demais células neurais ainda não foram avaliadas.
- O teste Pesaran–Timmermann (PT) é outra análise, aplicada conforme o protocolo depois das previsões dos modelos; não testa a diferença Mamba versus qualquer baseline.
- Um resultado do D1 pode orientar desenvolvimento, mas não demonstra desempenho em 2024–2025, rentabilidade ou superioridade do Mamba.

## Verificações feitas pelo agente

O código da baseline foi compilado e testado com dados sintéticos para conferir: alinhamento de retornos consecutivos, rejeição de lacuna/par divergente, decisão de classe com coeficientes congelados, métricas e bloqueio dos folds finais. O pesquisador executou o AR(1) histórico D1–D4. Posteriormente, em 13/10/2026, autorizou o piloto pareado D1 pelo agente; essa execução e sua auditoria estão documentadas separadamente na Entrega 5.
