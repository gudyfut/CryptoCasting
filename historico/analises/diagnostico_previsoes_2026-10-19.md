# Investigação das probabilidades, do AR(1) e das classes não escolhidas

Data: 19/10/2026. Diagnóstico retrospectivo do ciclo `4e232a796fcda0ea34c3`, dataset `9341610dbb329a858784`. Não executa outro treinamento, não muda checkpoints, protocolo, rótulos ou a proposta 002. B1–B4 permanecem bloqueados. Os números são de desenvolvimento e não descobertas confirmatórias.

## Síntese

O mau resultado do AR(1) foi reproduzido e há forte evidência de inadequação da sua escala de volatilidade. A ausência de algumas classes no argmax das redes também foi reproduzida, mas nenhuma probabilidade salva de teste era zero. Não foi detectada troca de rótulos na exportação, erro nas matrizes ou seleção de época pelo teste nas verificações realizadas. Isso não certifica ausência de todo viés ou adequação do desenho para operar.

A recomendação é preservar o AR(1) e seus resultados como referência limitada do ciclo inicial. Retirá-lo apenas por perder ocultaria uma tentativa. Vencer esse baseline não demonstra superioridade contra modelos estatísticos em geral. A força da evidência deve ser avaliada principalmente também contra as frequências do treino e entre as redes, apresentando cada prazo separadamente. Uma mudança formal do papel dos comparadores pertence ao protocolo de um ciclo futuro.

## 1. O que foi conferido

- As 1.353 fontes do relatório fechado continuam com os hashes originais.
- 288 séries de teste (96 células × três modelos): probabilidades válidas, rótulos e timestamps alinhados ao dataset, matrizes e log-loss recalculadas. As três classes reais estão presentes em todas essas células.
- Nenhuma probabilidade exatamente zero nessas séries. Não há saída de classe ausente no vetor; isso difere de uma coluna vazia na matriz de confusão.
- As 192 épocas selecionadas correspondem ao mínimo registrado de log-loss de validação, com a primeira época nos empates.
- As fronteiras de treino/validação/teste respeitam a purga pela expiração máxima planejada. Revisados código de normalização, entrada auxiliar, softmax, loss sem pesos e acumulação de gradientes. Esta investigação não repete os 192 treinamentos.
- Os 16 ajustes AR(1) foram reproduzidos por fórmulas escalares independentes de mínimos quadrados; limites temporais e variância residual conferidos.
- Uma implementação NumPy independente foi confrontada com a simulação AR(1) em três cenários sintéticos de uma hora, com média zero e phi zero. Maior diferença de probabilidade: 0,004676, abaixo da tolerância pré-especificada 0,03. Esse teste não valida empiricamente o mercado nem todos os regimes de parâmetros.

Arquivos: [resumo e proveniência](diagnostico_2026-10-19/resumo.json), [diagnóstico por célula](diagnostico_2026-10-19/diagnostico_por_celula.csv), [ajustes e volatilidade](diagnostico_2026-10-19/volatilidade_ar1.csv), [teste sintético](diagnostico_2026-10-19/simulacao_sintetica.json). Scripts: `scripts/diagnosticar_previsoes.py` e `scripts/verificar_simulacao_ar1.py`.

## 2. Qual ARIMA foi efetivamente avaliado?

AR(1), equivalente a ARIMA(1,0,0) nos log-retornos horários, com intercepto, ajuste por mínimos quadrados e inovações gaussianas de variância fixa por moeda/fold. Não houve seleção entre várias ordens ARIMA, GARCH, caudas pesadas ou atualização da variância a cada origem.

Uma previsão pontual ARIMA não determina qual barreira vem primeiro. O projeto acrescenta uma distribuição de trajetórias: 60 incrementos intrahorários, minuto de latência, limites conhecidos na origem e contagem dos primeiros eventos em 4.096 percursos. Essa transformação é possível, mas depende de hipóteses sobre o caminho, além da média prevista. Referências: [ARIMA — Hyndman e Athanasopoulos](https://otexts.com/fpp3/arima.html) e [previsão por simulação e hipóteses dos erros](https://otexts.com/fpp2/prediction-intervals.html).

Portanto, não é correto concluir que ARIMA seja inaplicável a barreiras. É correto concluir que esta especificação teve probabilidades muito inadequadas neste desenvolvimento.

## 3. Por que o AR(1) errou tanto?

As barreiras usam volatilidade recente de 168 horas. A simulação usa desvio residual estimado em todo o treino expansivo. Nos 16 pares moeda/fold, a mediana da razão `sigma_residual / sigma_recente` variou de **1,6999 a 3,1359**. Exemplo BNB/DB3: aproximadamente 1,0949% de desvio horário na simulação contra 0,3492% de volatilidade recente mediana usada nas barreiras.

Assim, em muitos instantes o modelo imagina oscilação muito maior que a escala dos limites: simula saídas rápidas e quase elimina a expiração. Essa razão é evidência de desajuste entre escalas passadas; a volatilidade recente não é a verdadeira volatilidade futura. A subestimação observada da expiração confirma a falha preditiva, mas não identifica uma causa única.

Médias com pesos iguais por célula/fold, preservando a agregação principal:

| Prazo | Expiração observada | Probabilidade média AR(1) | Log-loss AR(1) |
|---|---:|---:|---:|
| 1 hora | 59,95% | 5,49% | 3,018582 |
| 24 horas | 48,62% | 3,89% | 2,898042 |
| 168 horas | 42,69% | 3,69% | 2,389945 |

Log-loss usa a probabilidade de cada evento real. Penalizar fortemente um modelo que dá probabilidade muito baixa a algo frequente é o comportamento esperado da métrica. A convergência de 4.096 para 16.384 trajetórias qualifica a precisão numérica da simulação; não corrige as hipóteses que ela simula.

O teste sintético isolou o mecanismo, sem dados de mercado: mantendo limites em ±1% de log-preço e prazo de uma hora, a probabilidade simulada de expiração foi 92,34%, 43,36% e 2,99% ao usar desvio horário de 0,5%, 1% e 2%, respectivamente. Não são configurações concorrentes treinadas nem resultados de operação. Mostram por que multiplicar a escala da oscilação reduz drasticamente a sobrevivência entre limites.

Resíduos também apresentam caudas e dependência nos quadrados, registradas no CSV. Volatilidade condicional e distribuições alternativas são hipóteses para outro comparador, não correções retroativas do AR(1). [A documentação do arch](https://arch.readthedocs.io/en/latest/univariate/univariate_volatility_modeling.html) distingue explicitamente modelo da média, volatilidade e distribuição dos erros.

## 4. O que significa uma classe nunca escolhida?

Exemplo: probabilidades `[31%, 40%, 29%]` significam inferior, expiração e superior. O argmax escolhe expiração. Superior recebeu 29%, não zero. A rede pode variar essas três probabilidades ao longo do trimestre e, ainda assim, manter sempre uma delas abaixo das outras.

Contagens por prazo; cada linha tem 32 células (quatro moedas × dois contextos × quatro folds):

| Modelo / prazo | Células sem escolher inferior | Sem escolher expiração | Sem escolher superior |
|---|---:|---:|---:|
| LSTM / H1 | 0 | 0 | 0 |
| LSTM / H24 | 4 | 0 | 1 |
| LSTM / H168 | 0 | 0 | 4 |
| Mamba / H1 | 0 | 0 | 0 |
| Mamba / H24 | 0 | 0 | 0 |
| Mamba / H168 | 0 | 0 | 2 |

As contagens por classe se sobrepõem: são **8 células LSTM** e **2 células Mamba** com pelo menos uma classe nunca escolhida. Não são réplicas independentes.

Caso extremo: LSTM, BNB, W168, H24, DB2 (`ff71c0cb6ba4ac8e33bc`) escolheu expiração nas 2.016 origens. Houve 616 inferiores, 991 expirações e 409 superiores reais. A probabilidade de superior variou entre 17,5% e 30,6%, mas nunca foi a maior. Seu acerto comum é 49,16% e seu acerto balanceado é 1/3 porque só o recall de expiração é 1; os recalls dos dois limites são zero. Isso é uma limitação séria como classificador, não prova automática de código quebrado.

Mamba nunca escolheu superior nos dois contextos BTC/H168/DB1. Por exemplo, em BTC/W24, 08/01/2023 07:00 UTC, atribuiu 51,83% a inferior, 14,83% a expiração e 33,35% a superior; superior aconteceu. O erro permanece registrado. A interface permite abrir o caso e o recorte inteiro.

Log-loss avalia probabilidades, enquanto argmax/recall avaliam a escolha de uma classe. Não maximizar as duas coisas da mesma forma é esperado: a métrica principal do protocolo é probabilística. [A documentação de avaliação do scikit-learn](https://scikit-learn.org/stable/modules/model_evaluation.html) distingue estimação da distribuição e tomada de decisão.

Não é correto solucionar isso forçando um terço das previsões em cada classe. Pesos de classe e oversampling alteram a distribuição efetiva otimizada; podem ajudar recall e prejudicar probabilidades na frequência natural. Mudanças exigem hipótese, validação temporal e nova identidade. Uma etapa de calibração deve ser ajustada fora do teste e avaliada em dados separados; [calibração de probabilidades](https://scikit-learn.org/stable/modules/calibration.html).

## 5. Problemas de interpretação que precisam ser evitados

1. **Um adversário fraco não certifica redes fortes.** O AR(1) usa informação e hipóteses diferentes das redes; a comparação neural controla as entradas. A conclusão não deve ser “deep learning venceu métodos estatísticos”.
2. **O semanal permanece fraco mesmo sem AR(1).** Log-loss H168: frequências de treino 1,102181; LSTM 1,114676; Mamba 1,117845. As duas redes perdem para a referência constante. Expiração semanal observada 42,69%; probabilidades médias LSTM 29,84% e Mamba 30,36%.
3. **Desbalanceamento não explica tudo.** No semanal, a frequência média de expiração foi 40,95% no treino, 46,29% na validação e 42,69% no teste. É uma classe comum, que as redes subestimaram no agregado. Há mudança temporal; não se demonstrou que um ajuste de pesos ou de capacidade resolva o problema.
4. **Não confundir boa probabilidade com boa operação.** Argmax não é sinal econômico, expiração não é retorno zero, e superar um baseline não demonstra lucro após custos.
5. **População comum é condicionada à observabilidade.** Exigir futuro íntegro para comparar rótulos permite avaliar a população preditiva definida, mas restringe generalização a todos os instantes. O painel não é uma lista causal de operações. A população financeira foi construída separadamente. O CSV novo inclui uma sensibilidade descritiva para as origens operacionais com desfecho conhecido e mantém a contagem de desconhecidos; não preenche seus resultados nem altera o placar principal.
6. **Uma seed, um ano e testes reutilizados.** Sobreposição de horizontes e dependência entre moedas reduzem a informação independente. DB1–DB4 consultados para decidir mudanças são desenvolvimento, nunca confirmação final intocada.
7. **Qualificação funcional não é adequação estatística.** Recargas exatas, código causal e métricas consistentes não provam que as features, a distribuição dos erros ou os modelos são suficientes para a tarefa.
8. **Ambiguidade precisa ser identificada, mas não explica o padrão global.** O relatório fechado registrou seis origens ambíguas em H1 somadas entre moedas, antes de repetir contextos/modelos, e nenhuma em H24/H168 na população comum de teste. O exemplo visual de uma dessas origens não representa a frequência do problema na grade. As sensibilidades documentadas são muito menores que a diferença entre AR(1) e redes.

### Sensibilidade da população preditiva

Como conferência retrospectiva adicional, usando as previsões já salvas, a log-loss foi recalculada em todas as origens operacionais com desfecho conhecido. Os desconhecidos permanecem contados nos CSVs e não recebem resultado inventado. Esta sensibilidade não modifica as regras financeiras nem substitui a comparação principal.

| Modelo | H1: comum → observável operacional | H24 | H168 |
|---|---:|---:|---:|
| AR(1) | 3,018582 → 2,982436 | 2,898042 → 2,846558 | 2,389945 → 2,381285 |
| LSTM | 0,866459 → 0,871113 | 1,047167 → 1,048820 | 1,114676 → 1,115008 |
| Mamba | 0,868270 → 0,873412 | 1,044955 → 1,046691 | 1,117845 → 1,118223 |

O mau resultado do AR(1) persiste. Isso reduz a plausibilidade de que a máscara comum seja a explicação central dessa diferença, sem recuperar o desempenho nos desfechos desconhecidos ou demonstrar ausência de viés de seleção.

## 6. Recomendação para prosseguir, ainda não executada

Preservar o ciclo inicial e seu AR(1), inclusive os resultados ruins. Antes de executar uma ablação de tamanho de estado como se a causa já fosse capacidade do Mamba, discutir um ciclo delimitado de diagnóstico de probabilidades e referências:

- Manter frequências do treino, resultados por classe e por prazo como controles obrigatórios.
- Considerar um classificador probabilístico simples, como regressão logística multinomial, com features causais predefinidas. Uma ablação usando apenas a distância/volatilidade auxiliar ajuda a verificar quanto do ganho vem desse resumo, em vez de aprendizagem temporal complexa.
- Se a comparação com modelos de trajetórias for central ao TCC, formular uma única variante de volatilidade condicional (por exemplo, AR com GARCH ou uma escala causal previamente fixada), com qualificação própria. Não escolher a variante que melhor reproduz 2023 e chamá-la de validação independente.
- Avaliar frequências, dispersão, recall e calibração no treino/validação; escolher alterações e calibração sem consultar B1–B4, e confirmar candidatos com outras sementes de desenvolvimento.

Isso é uma recomendação de prioridade, não uma nova grade autorizada automaticamente nem alteração do protocolo 2.1. Se o orientador preferir reduzir escopo, é defensável manter AR(1) como experiência inicial secundária e concentrar a próxima comparação em Mamba, LSTM e controles probabilísticos mais diretamente ligados ao alvo. O motivo deve ser adequação científica e custo, não apagar o resultado desfavorável.
