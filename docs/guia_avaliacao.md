# Guia de leitura da avaliação do ciclo 001

Complemento didático de 19/10/2026. Não modifica o método executado. Valores e conclusões do experimento permanecem em `historico/analises/ciclo_001_resultados.md`.

## Da sequência ao resultado

Uma origem é um instante em que a previsão é emitida. A rede recebe 24 ou 168 candles horários e uma variável auxiliar de distância. Produz três probabilidades, na ordem inferior, expiração, superior. Elas não são garantias. As barreiras são definidas pela regra de volatilidade; não são otimizadas livremente pelo modelo. O primeiro evento determina a classe histórica. Expiração pode produzir retorno positivo ou negativo.

Mamba/LSTM ajustam pesos no treino por cross-entropy, equivalente à log-loss multiclasse das probabilidades. Retropropagação calcula gradientes e AdamW atualiza os pesos. Batch efetivo 32; até 100 épocas, parada após dez sem melhora de validação. Uma época é uma passagem pelo treino. A menor log-loss de validação seleciona o checkpoint; teste não escolhe retrospectivamente a época. Normalização usa somente treino; as fronteiras são purgadas pela expiração máxima planejada.

DB1–DB4 são testes cronológicos de desenvolvimento em 2023. Consultá-los para decidir mudanças torna-os parte da busca. Não equivalem ao teste final independente. Uma seed e um ano limitam a generalização.

## Medidas preditivas

### Log-loss

Para cada origem, tomar a probabilidade atribuída à classe real e calcular `−ln(p_real)`; depois calcular a média. Se o evento ocorrido recebeu 90%, a penalidade é aproximadamente 0,105; 50% dá 0,693; 10% dá 2,303; 1% dá 4,605. Erros confiantes recebem penalidade alta. Zero é ideal, sem teto teórico; o código limita a probabilidade inferiormente a 10⁻⁷ para o cálculo.

0,9, 1,0 e 2,7 não são porcentagens de acerto, erro ou retorno. Comparar sempre o mesmo alvo/população com referências. Probabilidade uniforme de um terço produz log-loss 1,099, mas as frequências de treino são uma referência mais informativa quando as classes não são equilibradas. `exp(−média)` é média geométrica das probabilidades reais, não taxa de acerto.

### Brier

Somar, nas três classes, `(p_classe − indicador_do_evento_real)²`, e tirar a média das observações. No contrato do projeto, o escore está entre 0 e 2, sem dividir por dois ou por três. `[inferior=0,2; expiração=0,2; superior=0,6]`, quando superior acontece, produz 0,24. Uniforme produz 2/3. Menor é melhor; 0,60 não representa 60% de erro.

### Classe escolhida, recall, precisão, F1 e acerto balanceado

A classe escolhida é a de maior probabilidade; empate segue o primeiro índice, como no código auditado. Acurácia comum é a fração de classes corretas. Recall de superior pergunta: entre os superiores reais, quantos foram identificados? Precisão de superior pergunta: entre os anúncios de superior, quantos eram superiores reais? F1 é a média harmônica de precisão e recall; macro-F1 dá peso igual às classes.

Acerto balanceado é a média dos três recalls. Um modelo que anuncia sempre expiração pode ter acurácia comum alta quando expiração é frequente, mas acerto balanceado de 33,33%, com as três classes presentes. A matriz de confusão mostra linhas reais e colunas previstas; a diagonal são acertos. Nenhuma dessas métricas é taxa de operações lucrativas.

No pós-processamento das 96 células, com pesos iguais:

| Classe real / recall | LSTM | Mamba |
|---|---:|---:|
| Inferior | 38,15% | 39,81% |
| Expiração | 66,71% | 65,68% |
| Superior | 12,70% | 10,93% |

Esses valores não são precisões dos sinais de compra. O recibo do explorador registra os valores completos. Eles reproduzem os acertos balanceados publicados, sem alterar métricas do ciclo.

### Calibração e incerteza

Entre muitas previsões que anunciam aproximadamente 70% para um evento, espera-se frequência observada próxima de 70% se houver boa calibração nessa faixa. Uma ocorrência isolada não avalia calibração; grupos pequenos têm incerteza. Coincidência da média global não prova calibração condicional.

As médias principais dão peso igual por célula/fold. Origens vizinhas têm rótulos sobrepostos, moedas são correlacionadas, AR(1) reutilizado entre contextos não é novo ajuste. Intervalos por blocos temporais de 14 dias (sensibilidades 7/28) preservam parte dessa dependência. Mamba menos LSTM na log-loss: +0,000923, intervalo de 95% [−0,006171; +0,004971]; sem superioridade demonstrada, sem provar equivalência.

## Da previsão à política

O modelo não determina sozinho posição, capital ou custos. O ciclo usa compra Spot/caixa, probabilidade superior ≥60%, viabilidade nominal após custos e uma posição por estratégia. Risco nominal de até 1% no stop, limitado ao capital disponível. Gaps podem exceder essa perda. Expiração encerra pelo preço observado; não é lucro zero.

Exemplo fictício: 55 operações com ganho bruto de 100, 45 com perda bruta de 100 e custo de 12 por operação dão `5500 − 4500 − 1200 = −200`, apesar de 55% de acertos. Por isso avaliação econômica exige retorno líquido, drawdown, exposição, número de operações, ganhos e perdas médios e incerteza.

Drawdown é a queda em relação ao pico anterior do patrimônio, não apenas a perda em relação ao capital inicial. Zero operações com retorno zero significa caixa. Controle com lacuna impeditiva tem resultado indisponível, não zero. Somar retornos de estratégias sobrepostas não cria uma carteira válida.

Futuros exigiriam dados e regras específicos, incluindo posições vendidas, margem, funding, preço de referência e liquidação. Multiplicar retorno Spot por alavancagem não executa esse teste. A presente documentação preserva essa pergunta como não respondida.

## Como usar o explorador

1. Escolher moeda, contexto, prazo e trimestre. Todas as previsões de teste daquela célula ficam disponíveis.
2. Escolher o modelo da análise; os cartões mantêm a comparação dos três modelos na mesma origem.
3. Navegar por origem, localizar uma data ou selecionar uma linha do registro. Os filtros não refazem treinos ou resultados.
4. Examinar candles, entrada, limites e evento real. O gráfico tem zoom, cursor e panes separados de preço, volume e probabilidades.
5. Usar inspeção de saída em 1 minuto para verificar máximas/mínimas. O timestamp intraminuto não recupera segundo exato nem ordem desconhecida.
6. Ler log-loss/Brier individuais junto da probabilidade do evento real. Consultar matriz de confusão e métricas do recorte completo; filtros da lista não mudam esses agregados.

Os candles do gráfico podem ter 1/5/15/60 minutos, sem alterar o candle de 1h usado no treinamento. Janela de contexto visual limitada a 48h não significa que o modelo W168 recebeu apenas 48h. Pacotes de preços incluem os dias finais de 2022 apenas para contexto; não são previsões de teste adicionais. Lacunas permanecem vazias.
