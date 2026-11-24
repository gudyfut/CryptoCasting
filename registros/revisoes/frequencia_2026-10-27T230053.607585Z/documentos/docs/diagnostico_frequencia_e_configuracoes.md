# Diagnóstico de frequência, configurações e generalização

Revisão solicitada pelo pesquisador em 27/10/2026, após conhecer os resultados dos dois ciclos. É uma análise retrospectiva, sem novo treinamento, busca de hiperparâmetros ou mudança das publicações congeladas. Referência: `1e7c5ed662fba55ddd25`; Mamba corrigido: `7868a4d847c1410fc681`.

**Conclusão:** não foi encontrado novo erro de alvo, população, seleção de época ou cálculo de MSE nas verificações desta revisão. Avaliar apenas uma previsão por dia não resolveu a desvantagem dos modelos existentes. Há limitações de informação, generalização, orçamento e adaptação arquitetural que justificam experiências controladas; não há evidência de um parâmetro isolado cuja alteração garanta superar Naive.

## Os quatro relógios do estudo

| Conceito | Execução existente | Significado |
|---|---|---|
| Resolução da entrada | Candle de 1h | Cada valor de entrada é um retorno horário |
| Contexto | 24/72/168/336 retornos | Quanto passado a rede recebe em cada exemplo |
| Horizonte | 24h | Distância entre o preço de origem e o preço terminal previsto |
| Frequência das origens | 1h | Uma nova previsão de 24h é produzida a cada hora |

Às 10h prevê-se o retorno entre 10h de hoje e 10h de amanhã; às 11h, entre 11h de hoje e 11h de amanhã. Não são previsões de apenas uma hora. As duas respostas futuras compartilham 23 das 24 horas de variação. O contexto pode continuar com candles de 1h mesmo que a previsão seja emitida uma vez ao dia.

Produzir uma previsão nova não significa retreinar. Cada ajuste usa treino/validação anteriores ao bloco e mantém seus pesos durante o teste. O ARIMA atualiza o estado filtrado com observações reveladas, sem reestimar os parâmetros a cada origem. A política Spot **já decide diariamente às 00:00 UTC**, executa às 00:01 e sai 24h depois. Não há 24 posições sobrepostas por dia nessa política.

Uma origem deslizante com horizonte maior que o passo é uma avaliação possível; o cuidado é não contar erros sobrepostos como observações independentes. A literatura distingue origem e horizonte na [avaliação temporal com origens móveis](https://otexts.com/fpp3/toolbox.html#time-series-cross-validation). Aqui a purga temporal evita rótulos cruzando treino/validação/teste e a análise usa bootstrap por blocos de dias. Isso não torna as observações independentes, nem elimina toda a incerteza.

## O que foi executado nesta revisão

O [recibo do diagnóstico](../registros/revisoes/frequencia_2026-10-27T230053.607585Z/resumo.json), acompanhado de código e [plano registrado antes do cálculo](../registros/revisoes/frequencia_2026-10-27T230053.607585Z/plano.json), preserva:

- Recálculo de 1.216 resultados: 384 LSTM, 384 Mamba originais, 384 corrigidos, 32 Naive e 32 ARIMA. Controles de reprodução não foram duplicados nesse placar.
- Verificação das fontes atuais/congeladas e hashes das previsões de teste; reconstrução de retornos/alvos a partir dos closes horários e das populações por fronteira, com comparação de todas as origens salvas.
- Verificação da melhor época, finitude dos logs, limite e paciência nos 1.152 ajustes neurais. Cada MSE horário recalculado coincide com o resultado por ajuste.
- Métricas com todas as origens horárias e, separadamente, uma origem diária em cada um dos 24 horários UTC. **00 UTC é o recorte principal por já ser o horário da política**, não porque apresentou o melhor escore.
- Médias de escores com pesos iguais por moeda/contexto/bloco/seed; baselines compartilhadas, sem multiplicá-las como réplicas independentes. Sem ensemble de previsões.
- Bootstrap pareado de diferenças diárias, 2.000 réplicas, blocos de 14 dias e sensibilidades 7/28, seed 20261020. Dias sem observação permanecem no calendário; os blocos não atravessam folds. As mesmas reamostragens preservam o pareamento de moedas, modelos, contextos e seeds.

Os 17 testes existentes da referência e os sete da penalização passaram novamente no WSL científico. Três testes adicionais conferiram o bootstrap com lacunas contra somas/contagens, pesos iguais entre folds e decomposição do MSE. Evidências complementares e aceite da figura constam do [fechamento desta revisão](../registros/revisoes/frequencia_2026-10-27T230053.607585Z/fechamento_revisao.json).

Não houve nova coleta, recarga de todos os checkpoints, repetição dos treinos ou simulação financeira nesta revisão. A reconstrução integral desde os minutos e a auditoria de escalas/checkpoints permanecem sustentadas pelas revisões de 24/10 e pelo fechamento da extensão. A revisão de organização anterior conferiu 8.743 hashes; integridade de arquivos e validade científica são verificações diferentes.

## Resultado de usar somente a previsão diária

Índice de erro = `100 × MSE do modelo / MSE do Naive` **na mesma população e fase**. Um índice 101,90 significa erro quadrático 1,90% maior que Naive; não significa 1,90% de perda financeira ou de diferença na acurácia. Menor é melhor.

| Modelo | 2023: origens horárias | 2023: diária 00 UTC | 2024–2025: horárias | 2024–2025: diária 00 UTC |
|---|---:|---:|---:|---:|
| Naive | 100,000 | 100,000 | 100,000 | 100,000 |
| ARIMA | 99,962 | 99,985 | 99,982 | 99,982 |
| LSTM | 100,742 | 100,567 | 100,005 | 100,423 |
| Mamba original | 101,892 | 101,861 | 101,221 | 101,862 |
| Mamba corrigido | 101,885 | 101,854 | 101,272 | 101,905 |

Os denominadores diferem entre os recortes: não atribuir causalmente a diferença de MSE absoluto à frequência. A tabela compara cada modelo com Naive sob a mesma regra de amostragem. A amostra diária tem 348 origens temporais comuns em 2023 e 727 em 2024–2025, repetidas entre moedas/configurações; não são milhares de dias independentes.

![Avaliação horária e diária](../registros/revisoes/frequencia_2026-10-27T230053.607585Z/figuras/frequencia_avaliacao.png)

Na avaliação diária de 2024–2025, os contrastes de MSE e IC95% principal foram:

| Diferença | Estimativa | IC95% por blocos de 14 dias | Leitura |
|---|---:|---:|---|
| Mamba corrigido − LSTM | 0,000017116 | [0,000002702; 0,000036705] | Favorece LSTM |
| Mamba corrigido − Naive | 0,000021997 | [0,000007147; 0,000043209] | Favorece Naive |
| LSTM − Naive | 0,000004881 | [−0,000000939; 0,000012242] | Não separa claramente os dois |
| Mamba corrigido − original | 0,000000499 | [−0,000000906; 0,000001958] | Não demonstra benefício da correção nesse recorte |

As sensibilidades 7/28 dias mantêm essas leituras. Intervalos condicionais aos modelos e períodos, exploratórios, sem correção por multiplicidade; não constituem nova confirmação independente. A pequena vantagem descritiva de ARIMA não foi submetida aqui a um contraste próprio com Naive.

Na sensibilidade dos 24 horários, o Mamba corrigido teve índice agregado acima de 100 em todos eles, nas duas fases. Na avaliação, variou de 100,075 a 102,500. A LSTM variou de 99,550 a 100,484 e ficou abaixo de 100 em 12 dos 24 horários. Isso não autoriza escolher o horário de melhor teste; os recortes compartilham o mesmo mercado e não são 24 experimentos independentes. Tampouco significa que toda célula individual do Mamba perdeu.

**Esta análise responde a “e se eu utilizasse apenas uma previsão diária destes modelos?”. Não responde a “e se eu treinasse modelos novos usando apenas um exemplo por dia?”.** A segunda pergunta exige novo experimento.

## Sobreposição: um cuidado real, mas não um erro automático

As correlações descritivas dos alvos de 24h em origens separadas por uma hora ficaram entre 0,952 e 0,961 nas moedas/fases. Isso é esperado quando 23 das 24 variações horárias são compartilhadas; não significa que o modelo sabe antecipadamente o resultado. Com origens diárias às 00 UTC, a correlação entre alvos consecutivos ficou entre −0,206 e 0,024. São descrições desses períodos, não garantias de independência ou estimativas completas de tamanho efetivo da amostra.

Ao treinar só com origens diárias, a quantidade de exemplos cai aproximadamente 24 vezes. Na população comum:

| Bloco | Treino com origem horária | Treino apenas 00 UTC | Validação horária / diária |
|---|---:|---:|---:|
| DB1 | 12.779 | 533 | 2.184 / 91 |
| DB4 | 18.991 | 792 | 2.184 / 91 |
| B1 | 21.199 | 884 | 2.184 / 91 |
| B4 | 34.351 | 1.432 | 2.160 / 90 |

A perda de exemplos não equivale à perda de 24 vezes mais informação independente, pois havia redundância. Ainda assim, 533–1.432 exemplos são poucos para redes de aproximadamente 13 mil/20 mil parâmetros. Reduzir redundância pode ajudar ou prejudicar; não se pode deduzir o sinal do efeito apenas dessa contagem.

Com batch 64, B4 tem 537 atualizações por época na grade horária e 23 na diária. Portanto manter “100 épocas e paciência 10” não mantém o mesmo orçamento de otimização. Um teste que altere só a lista de origens e ignore isso mistura amostragem, número de atualizações e frequência de seleção. A validação diária também fornece menos alvos distintos, podendo tornar a escolha de época mais variável.

## Configurações e implementação: achados e limites

| Item | Achado | Consequência |
|---|---|---|
| Alvo, deslocamento e tempo | Retorno entre closes separados por 24h; relógio e origens conferem | Não se encontrou erro “prevê 1h em vez de 24h” |
| Entradas e janelas | Retornos até a origem, sem alvo futuro na janela; W mede horas de retorno | Apenas retorno entra na rede; OHLCV no dataset não significa OHLCV como feature |
| Ausências/população | Causalidade exige 336 retornos; pontas observáveis definem avaliação; origem operacional usa passado | Controle de comparabilidade já definido; não filtrar operação pela existência de alvo futuro |
| Separação | Treino expansivo, validação seguinte, teste posterior, destino estritamente anterior à fronteira | Não foi encontrado split aleatório ou rótulo atravessando partição |
| Escalas | Ajustadas no treino e desfeitas na previsão; já conferidas em checkpoints nas revisões anteriores | Zero na escala padronizada representa a média do treino, não necessariamente retorno zero |
| Gradiente | MSE somado nos microbatches, dividido pelo tamanho efetivo do lote, clipping antes do passo | Inspeção não encontrou multiplicação indevida da perda por microbatch |
| Validação e parada | Melhor MSE estrita, primeira época em empate; todas as épocas selecionadas conferiram | Aumentar o teto de épocas sozinho não resolve o quadro observado |
| Penalização | Exceção `_no_weight_decay` incorporada no ciclo corrigido | Problema conhecido já isolado; efeito insuficiente para explicar a desvantagem |
| Precisão/inicialização | FP32, sem reinicialização genérica que apague `dt_proj.bias`; núcleo oficial CUDA | Não foi encontrada a falha de inicialização/precisão alertada no repositório oficial |
| Capacidade | Mamba 20.129 parâmetros e LSTM 12.961 | Mesma largura não equivale a mesma capacidade ou custo |
| Dropout | LSTM entre camadas recorrentes; Mamba no final da sequência, antes da norma final | Ambos usam 0,1, mas regularizam posições diferentes; não são tratamentos idênticos |
| Adaptação Mamba | Código local usa `norma(x + bloco(x))`, seguido de dropout/norma final/saída | O núcleo é oficial; o empilhamento para regressão é uma adaptação do projeto |
| Referência oficial de empilhamento | `Block` da biblioteca instalada aplica normalização antes do mixer e mantém caminho residual separado | Pré-normalização é hipótese legítima de comparação, não correção comprovada de um bug |
| Baselines | Naive é retorno zero; ARIMA trabalha em log-preço integrado, sem deriva e com estado filtrado causal | Referências válidas para o alvo; não remover porque são difíceis de superar |
| Atualização | Pesos neurais fixos durante cada teste, que chega a seis meses | Pode haver mudança de regime; atualizar mais frequentemente seria outro fator/custo |
| Configuração executável | O carregador aceita apenas o contrato congelado; diversas constantes refletem 24h/336h/1h | Editar `origem_minutos` para 1440 sozinho não implementa uma variante; exige novo ciclo e seleção explícita de origens |

A cópia inspecionada da biblioteca é `mamba-ssm 2.2.6.post3`; os módulos foram preservados com hashes em [biblioteca_mamba](../registros/revisoes/frequencia_2026-10-27T230053.607585Z/biblioteca_mamba/manifesto.json). A [estrutura oficial do Block](https://github.com/state-spaces/mamba/blob/main/mamba_ssm/modules/block.py) e as [orientações de precisão/inicialização](https://github.com/state-spaces/mamba#troubleshooting) ajudam a contextualizar a comparação; a versão local registrada é a evidência de reprodução. Não afirmar que trocar pós-normalização por pré-normalização necessariamente melhorará séries financeiras.

## O que os históricos de treinamento sugerem

Na avaliação 2024–2025:

- Mamba corrigido: época escolhida mediana 9; 19 épocas executadas na mediana. Em 150/192 ajustes o erro de treino caiu entre a primeira e a última época, enquanto a validação final ficou pior que a primeira. Na mediana, a razão de perda de treino final/inicial foi 0,855.
- LSTM: época escolhida mediana 4; 14 executadas na mediana. O mesmo padrão ocorreu em 120/192 ajustes; razão mediana 0,983.
- Nenhuma das 1.152 redes dos dois períodos atingiu o teto de 100 épocas. O término ocorreu pela paciência. As perdas de treino são padronizadas e observadas durante atualização com dropout; não comparar seu valor bruto diretamente com MSE de validação em unidades originais.

Esse padrão é **compatível com sobreajuste e dificuldade de generalização**, não uma identificação causal única. Mudanças de regime, pouca informação preditiva, seleção ruidosa e escolhas arquiteturais também podem contribuir. Mais épocas, capacidade ou paciência podem aumentar esse problema em vez de resolver.

Na validação da avaliação, 169/192 Mamba corrigidos e 164/192 LSTM tiveram melhor MSE que Naive. Isso não se transformou em vantagem agregada no teste seguinte. As combinações são correlacionadas: não usar a contagem como teste de significância. O contraste mostra por que melhorar validação é necessário para selecionar, mas insuficiente para provar generalização.

A decomposição exata `MSE(modelo) − MSE(Naive) = média(previsão²) − 2 × média(alvo × previsão)` ajuda a ler a desvantagem. Nas origens horárias de 2024–2025, o corrigido acrescentou 0,000031086 pelo tamanho das suas previsões e compensou 0,000016124 por alinhamento com o alvo; sobrou 0,000014962 de erro extra. Para LSTM, as parcelas foram 0,000004517 e 0,000004454, quase se compensando. O Mamba oscilou mais sem alinhamento suficiente. Isso descreve as previsões; não demonstra qual camada causou o efeito.

Previsões próximas de zero não são automaticamente defeito: MSE favorece a média condicional, que pode ficar próxima de zero quando há pouco sinal na entrada. Naive pode ser forte mesmo quando os preços variam bastante. Prever magnitude grande sem informação suficiente aumenta o erro quadrático.

## Como prosseguir — propostas, não novos experimentos executados

1. **Definir a decisão diária como objetivo operacional**, mantendo candles horários e horizonte 24h. Para um novo ciclo, pode-se fixar avaliação e seleção de época às 00 UTC para todas as alternativas, com diagnóstico horário secundário. Isso muda a seleção em relação ao estudo antigo e precisa de uma nova referência comparável; as épocas antigas não foram escolhidas por validação diária.
2. **Testar a frequência do treino de forma isolada:** origens 1h versus 24h, com mesma população de avaliação diária, dados, contextos, seeds, arquitetura, loss e política de seleção. Fixar orçamento e cadência de validação em atualizações do otimizador, além do custo computacional registrado; não supor que épocas iguais controlam esse fator. Outra comparação possível é custo reduzido com épocas iguais, mas seria uma comparação conjunta de política e orçamento, explicitamente diferente.
3. **Antes de ampliar a grade, qualificar a adaptação Mamba para regressão.** Testes sintéticos de recuperação de sinal conhecido e de memória de defasagens, seguidos de comparação controlada de pré/pós-normalização e regularização, podem localizar problemas de otimização. O núcleo oficial já passou em testes de atualização/recarga; isso não prova que toda a adaptação é ideal. Não mudar arquitetura, frequência, entradas e taxa de aprendizado ao mesmo tempo.
4. **Só depois investigar novas entradas.** Retorno acumulado e volatilidade calculados dentro do contexto podem facilitar a representação, mas são transformações da informação já disponível; volume acrescenta outro tipo de informação. Registrar fórmulas, aquecimento, ausência e normalização causal. Um indicador de 30 dias usado em W24 introduziria histórico adicional e confundiria a pergunta sobre contexto.

Uma busca neural limitada por validação, com orçamento comparável nas duas famílias, pode ser uma etapa futura. Aumentar épocas, mudar loss, escolher a melhor seed, trocar horário pelo melhor teste ou remover Naive não são correções justificadas pelos achados. Alterar MSE para uma loss robusta também muda o objetivo da estimação e exige justificativa.

Minha recomendação é manter os dois ciclos como referência, adotar a perspectiva de decisão diária no próximo desenho e fazer primeiro uma comparação pequena e controlada de frequência/seleção antes de uma nova grade completa. O número de combinações, orçamento e critério de encerramento devem ser definidos na proposta correspondente. O acervo atual permite avaliar a hipótese sem recoletar; uma nova preparação identificada pode ser necessária para materializar o novo conjunto de origens, mesmo reutilizando os brutos.

B1–B4 foram consultados, inclusive nesta revisão. Novas escolhas nesses períodos são retrospectivas. Trabalhar primeiro no desenvolvimento e reservar dados realmente novos ou avaliação prospectiva para confirmação não apaga essa exposição anterior. O objetivo continua sendo explicar o desempenho de configurações identificadas, com conclusão negativa admissível, e não procurar indefinidamente até obter um placar favorável.

## Artefatos para consulta

- [Resumo de frequência](../registros/revisoes/frequencia_2026-10-27T230053.607585Z/resumo_frequencias.csv): médias por fase/modelo/hora; `hora_utc=-1` significa todas as origens horárias.
- [Resultados por ajuste e horário](../registros/revisoes/frequencia_2026-10-27T230053.607585Z/metricas_por_origem_e_ajuste.csv).
- [Populações](../registros/revisoes/frequencia_2026-10-27T230053.607585Z/populacoes.csv), [dependência dos alvos](../registros/revisoes/frequencia_2026-10-27T230053.607585Z/dependencia_alvos.csv) e [históricos por ajuste](../registros/revisoes/frequencia_2026-10-27T230053.607585Z/diagnostico_epocas.csv).
- [Figura PDF](../registros/revisoes/frequencia_2026-10-27T230053.607585Z/figuras/frequencia_avaliacao.pdf) e [manifesto da figura](../registros/revisoes/frequencia_2026-10-27T230053.607585Z/figuras/manifesto.json).

Fontes e recibos do estudo anterior permanecem inalterados. Este documento e seus artefatos são evidência de uma revisão posterior, não uma substituição dos relatórios originais.
