# Penalização seletiva diária: resultado e interpretação

Execução `26cea089ba0faa9d64dc`, concluída em **12/11/2026 às 13h48 BRT**, aproximadamente 1h35 após o início. [Protocolo](protocolo_penalizacao_seletiva_diaria.md), [fechamento](../registros/penalizacao_seletiva_diaria/fechamento.json) e [conferência posterior](../registros/penalizacao_seletiva_diaria/conferencia_posterior.json).

**Conclusão:** a penalização seletiva S não demonstrou melhoria consistente sobre A. O MSE médio das redes piorou 0,43%; o do ensemble melhorou 0,21%, com intervalo incluindo zero. O lucro médio das três carteiras passou de −0,99% para +1,04%, mas a dispersão aumentou. O ensemble S permaneceu integralmente em caixa em 2025: retorno e drawdown zero por ausência de operações. Não promover S como estratégia superior, nem interpretar esses zeros como proteção de risco demonstrada durante operações.

## O que foi executado e conferido

BTC, contexto de 14 candles diários, seis canais padronizados no treino, retorno simples do próximo dia, Mamba-1 oficial e núcleo derivado do CryptoMamba. A mantém Adam com penalização uniforme 0,001; S isenta marcadores oficiais, LayerNorm e biases e mantém 0,001 nos demais pesos. Mesmos 136.952 parâmetros e inicialização pareada, sendo 33.778 isentos em S. Trata-se de uma política conjunta, sem identificação isolada do efeito de cada isenção.

Treino 2020–2023, seleção 2024 e avaliação retrospectiva 2025; 1.446/351/350 exemplos. A foi herdada com prova de equivalência da seleção nas primeiras 200 épocas. Três ajustes científicos S e dois controles completaram 200 épocas cada, sem early stopping. Controles A42 e S42 passaram com igualdade exata de trajetórias, checkpoints e previsões; estão fora das médias. As épocas selecionadas foram A42/17/2026 = 25/14/44 e S42/17/2026 = 105/199/44. A seleção perto do limite em S17 não autoriza ampliar o orçamento depois de observar o teste.

As 60 carteiras foram concluídas sem violação prudencial, com 30 reproduções financeiras A/Naive aprovadas. Conferência posterior: 315 hashes do fechamento, 1.104 artefatos anteriores preservados, 152 fontes, cinco históricos de 200 épocas, grupos efetivos, 20 séries de métricas recalculadas, quatro ensembles recompostos exatamente e contabilidade agregada das 60 carteiras. Os controles completos de pesos/trajetórias foram reconferidos em WSL, sem novo treino. Divergência máxima do recálculo das métricas: 3,47e−18. Nenhum uso de 2026.

O campo `exit_code` do lançador Windows permaneceu nulo; ele não comprova sucesso isoladamente. O encerramento é sustentado pelo processo inativo, fechamento, cobertura, controles e integridade. A leitura posterior não repetiu forward CUDA, bootstrap ou auditoria financeira por evento; esses resultados pertencem ao executor congelado. Não alterar recibos originais.

## Previsões em 2025

MSE em retorno decimal ao quadrado. RMSE e MAE em **pontos percentuais do retorno diário** (decimal × 100); menor é melhor. Acerto balanceado é a média dos recalls de alta e queda. Naive prevê retorno zero, portanto não recebe acerto direcional de classificador ativo.

| Resultado | MSE | RMSE (p.p.) | MAE (p.p.) | Acerto balanceado |
|---|---:|---:|---:|---:|
| A — média das três redes | 0,000477667 | 2,1856 | 1,5712 | 50,38% |
| S — média das três redes | 0,000479712 | 2,1902 | 1,5788 | 50,76% |
| A — ensemble | 0,000474907 | 2,1792 | 1,5637 | 51,43% |
| S — ensemble | 0,000473901 | 2,1769 | 1,5635 | 50,86% |
| Naive | 0,000475433 | 2,1804 | 1,5633 | Não se aplica |
| Ridge | 0,000477301 | 2,1847 | 1,5726 | 50,00% |

As médias de A e S têm erro maior que Naive. O ensemble S tem MSE 0,32% menor que Naive, mas MAE ligeiramente maior. O erro médio das redes e o erro da média de suas previsões são quantidades distintas: o ensemble reduz diferenças entre os vieses das redes, podendo melhorar MSE mesmo quando as redes individuais pioram. Isso não demonstra capacidade de acertar movimentos negociáveis.

Para S−A, o IC95% principal (bootstrap pareado, blocos de 14 dias) do MSE médio é [−7,498e−6; +8,696e−6]; o do ensemble é [−6,616e−6; +3,246e−6]. Para ensemble S−Naive: [−5,379e−6; +1,944e−6]. Todos incluem zero. O ensemble fixo reamostra dias, não outras redes; três seeds não são três mercados independentes. Intervalos exploratórios, sem correção da busca histórica e com 2025 conhecido.

## Operações em 2025

Mesmo futuro BTC, 350 decisões, capital inicial de 10.000 USDT, filtro ±0,2%, exposição alvo de 95%, comissão de 0,05% e slippage provisório de 0,01% por lado, funding histórico. Mantém posições quando o lado persiste e negocia somente deltas; fecha em caixa/inversão/fim. A leitura dos ledgers confirmou 11.271 transições consecutivas do mesmo lado nas 60 carteiras, sem fechamento/reabertura diária artificial.

| Resultado | Retorno líquido | Drawdown máximo | Capital final (USDT) | Dias posicionado |
|---|---:|---:|---:|---:|
| A — média das três carteiras | −0,99% | 25,39% | 9.901,31 | 142,33 |
| S — média das três carteiras | +1,04% | 24,79% | 10.103,75 | 232,33 |
| A — ensemble | +12,83% | 8,36% | 11.282,53 | 24 |
| S — ensemble | 0,00% | 0,00% | 10.000,00 | 0 |
| Naive — caixa | 0,00% | 0,00% | 10.000,00 | 0 |

Médias individuais são estatísticas de três carteiras independentes, não uma carteira executada nem o drawdown de uma curva média. O ensemble calcula primeiro a média das previsões e aplica o filtro a esse sinal único. Seu resultado não é a média dos lucros das seeds.

**Por que S não operou?** Em 2025, o retorno previsto pelo ensemble variou de −0,187505% a +0,147873%; nenhuma previsão ultrapassou ±0,2%. Os sinais divergentes das redes se compensaram. A inferência produziu previsões normalmente e a regra operacional decidiu ficar em caixa. Não é falha de execução nem ausência de simulação. Diminuir o filtro agora seria outra hipótese, não correção deste resultado.

| Seed | MSE A | MSE S | Retorno A | Retorno S | Drawdown S |
|---|---:|---:|---:|---:|---:|
| 42 | 0,000478476 | 0,000482546 | +10,25% | −11,97% | 34,76% |
| 17 | 0,000478824 | 0,000481297 | −13,32% | +15,94% | 22,72% |
| 2026 | 0,000475700 | 0,000475293 | +0,11% | −0,86% | 16,90% |

S melhora MSE em apenas um dos três pares e lucro em apenas um. O desvio entre seeds do retorno aumenta de 11,82 para 14,05 pontos percentuais. S42 prevê sempre +0,265534% no teste e fica comprado nos 350 dias; S17 opera vendido em 224 dias; S2026 opera vendido em 123. Não usar lucro de uma seed como prova de boa previsão bidirecional.

Na média, a diferença de lucro S−A é +202,44 USDT (+2,02 p.p.): aproximadamente +51,55 de movimento de preço, +41,58 de funding e +109,32 de economia em comissão/slippage. A mudança operacional não deriva apenas da qualidade do erro preditivo. O IC95% principal da diferença de crescimento log diário inclui zero, tanto nas médias [−0,00112094; +0,00157893] quanto nos ensembles [−0,00091612; +0,00003563]. Esses intervalos são de crescimento log diário, não de retorno total em porcentagem.

Sensibilidade ao slippage por lado:

| Slippage | A médio | S médio | A ensemble | S ensemble |
|---|---:|---:|---:|---:|
| 0,01% | −0,99% | +1,04% | +12,83% | 0,00% |
| 0,02% | −1,18% | +0,96% | +12,70% | 0,00% |
| 0,03% | −1,44% | +0,84% | +12,54% | 0,00% |

Essa sensibilidade não certifica custos históricos reais da Binance. Resultado financeiro condicionado ao instrumento, período, funding e política especificados.

## Validação de 2024 e contribuição do SSM

Em 2024, o MSE médio de S caiu 0,079% contra A (0,000751793 versus 0,000752385); no ensemble caiu 0,149% (0,000750956 versus 0,000752079). Os lucros médios foram +83,96% em S e +95,13% em A; os ensembles, +90,81% e +95,53%, respectivamente. S ensemble ficou comprado em 304 dias, A em 312, ambos com drawdown 34,58%. É o período usado para selecionar checkpoints, não confirmação independente; lucros majoritariamente comprados não comprovam informação preditiva além da exposição ao mercado.

As isenções foram aplicadas corretamente e preservaram as normas de LayerNorm, A_log e D. Entretanto, nas 32 janelas fixas de treino, retirar os ramos Mamba ainda mudou a previsão em RMS exatamente zero em S42 e S2026; em S17, o efeito foi 0,00076563 de retorno (0,07656 p.p.). Em A, foi zero nas três seeds. A preservação desses grupos não garantiu contribuição funcional em todas as redes. Outros pesos continuaram próximos de zero; atribuir a supressão a uma matriz específica exigiria diagnóstico adicional.

S42 também produziu previsão constante em todos os exemplos de validação e teste; sua correlação é indefinida e não foi preenchida com zero. As correlações dos ensembles em 2025 são pequenas: A 0,0562 e S 0,0637. Há contribuição funcional parcial em uma seed, sem superioridade preditiva ou operacional estabelecida. A sonda cobre uma população fixa de treino, não prova ausência global de contribuição em todas as entradas possíveis.

## Conclusão para o TCC

Esta ablação mostra que preservar grupos específicos de parâmetros é insuficiente, nesta receita, para garantir uso efetivo do SSM, menor erro médio ou uma estratégia de ensemble ativa e superior. O estudo separa regularização, agregação das previsões e decisão operacional; diferenças nessas camadas explicam por que rankings de MSE e lucro não coincidem.

Manter A como referência preservada, sem promover S nem apresentar o lucro de A em 24 dias de exposição como robustez comprovada. O ciclo está encerrado; não ampliar épocas, escolher outra seed ou ajustar o filtro retrospectivamente dentro desta identidade.

Evidências: [métricas e contrastes](../dados/experimentos/penalizacao_seletiva_diaria_26cea089ba0faa9d64dc/publicacao/previsao.json), [operações](../dados/experimentos/penalizacao_seletiva_diaria_26cea089ba0faa9d64dc/publicacao/operacoes.json), [controles](../dados/experimentos/penalizacao_seletiva_diaria_26cea089ba0faa9d64dc/controles.json), [conferência do executor](../dados/experimentos/penalizacao_seletiva_diaria_26cea089ba0faa9d64dc/publicacao/conferencia.json) e [modelos](../dados/experimentos/penalizacao_seletiva_diaria_26cea089ba0faa9d64dc/modelos.json). Fontes, checkpoints, observações, previsões e ledgers permanecem na execução congelada.
