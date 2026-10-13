# Diagnóstico do primeiro piloto Mamba — 13/10/2026

**Situação: em revisão.** Esta análise é posterior à execução `pareado_481b79d054b046fe6b70`. Preserva os resultados desfavoráveis e não altera pesos, limiar, época escolhida ou protocolo. Não houve treinamento adicional.

Fontes: [diagnóstico numérico](2026-10-13_diagnostico_mamba.json), [relatório original do piloto](../../docs/entregas/05_mamba_base/resultados_piloto_BTC_D1_cpu.md) e [registro versionado](../experimentos/pareado_481b79d054b046fe6b70/README.md). O diagnóstico foi calculado por `scripts/diagnosticar_piloto.py`, com o checkpoint já selecionado. O script verifica os artefatos e exige que as fontes originais ainda correspondam ao snapshot antes da inferência.

## 1. O que deu errado no resultado

O teste de desenvolvimento D1 tinha **82 exemplos: 41 altas e 41 não altas**. O Mamba previu alta em **71 exemplos** e não alta em 11. Acertou 32 altas e apenas 2 não altas: **34 acertos de 82**, BA de **41,46%**. Nesta amostra balanceada, accuracy e BA coincidem.

O problema observado é a concentração das previsões em alta, com pouca capacidade de separar as duas classes. Prever alta em 86,59% dos casos não significa atribuir probabilidade de 86,59% a cada caso: a probabilidade mediana de alta no teste foi somente 53,30%.

| Comparação no mesmo teste | BA | Diferença do Mamba |
|---|---:|---:|
| Mamba | 41,46% | — |
| AR(1) | 46,34% | −4,88 pontos percentuais |
| LSTM | 50,00% | −8,54 pontos percentuais |
| Referência de BA | 50,00% | −8,54 pontos percentuais |

A LSTM previu não alta em todos os exemplos; seus 50% também não representam aprendizado direcional útil. O PT do Mamba teve estatística negativa, e a autocorrelação das previsões limita sua interpretação. Nenhuma dessas medidas é uma avaliação de rentabilidade.

## 2. O modelo também separou mal as classes do treino

Reaplicamos o **mesmo checkpoint escolhido na validação** aos três blocos, em modo de avaliação:

| Bloco | Exemplos | Altas reais | Altas previstas | BA | Mediana de p(alta) | Cross-entropy |
|---|---:|---:|---:|---:|---:|---:|
| Treino | 495 | 237 | 175 | 49,68% | 48,34% | 0,6927 |
| Validação | 91 | 39 | 51 | 52,56% | 50,24% | 0,6941 |
| Teste de desenvolvimento | 82 | 41 | 71 | 41,46% | 53,30% | 0,7070 |

Uma previsão constante de probabilidade 0,5 tem cross-entropy aproximadamente 0,6931. O checkpoint ficou perto disso no treino. **Não há, neste checkpoint, o padrão clássico de ótimo acerto no treino e mau acerto fora dele.** Não atribuímos o resultado simplesmente a “decorar os dados”. Pouco sinal direcional nas entradas, dificuldade de otimização e detalhes da implementação permanecem hipóteses.

Essas losses foram recalculadas com os pesos finais selecionados e dropout desativado. Não são a média das losses observadas enquanto os pesos mudavam durante uma época de treinamento.

## 3. Os dados mudaram entre os períodos

As médias abaixo usam somente o último candle de cada janela, transformado pelo scaler ajustado nos **525 candles únicos do treino**. A unidade é o desvio-padrão de treino:

| Bloco | Média do fechamento normalizado | Média do volume normalizado |
|---|---:|---:|
| Treino | −0,055 | 0,014 |
| Validação | −1,662 | 1,948 |
| Teste de desenvolvimento | −1,331 | 2,721 |

As entradas contêm níveis OHLCV. Os preços e volumes dos períodos posteriores estão em faixas diferentes das observadas no treino. Isso pode contribuir para uma resposta diferente da rede. **A tabela comprova a mudança de distribuição, não comprova que ela causou a queda de BA.** O scaler deve continuar ajustado somente no treino; ajustar com dados futuros para aproximar essas médias seria vazamento.

O piloto também é limitado: uma moeda, um fold, uma seed, janelas de sete candles diários e 495 exemplos de treino. Janelas vizinhas compartilham candles; não são 495 sequências independentes. Isso impede generalizar o resultado para toda a arquitetura ou para a matriz intradiária. Não há demonstração de que apenas aumentar a quantidade de dados resolverá o problema.

## 4. Diferença concreta na inicialização do Mamba local

A implementação preservada em `modelo/mamba_minimal.py` deixa o bias de `dt_proj` com a inicialização padrão de `nn.Linear`. A implementação oficial Mamba v2.2.4 inicializa esse bias especialmente para que seu softplus esteja inicialmente entre **0,001 e 0,1**. Fonte primária: [código oficial, inicialização de dt_proj](https://github.com/state-spaces/mamba/blob/v2.2.4/mamba_ssm/modules/mamba_simple.py).

Reconstruindo somente a inicialização do piloto com seed 42, observamos:

| Camada local | Mínimo de softplus(bias) | Máximo de softplus(bias) |
|---|---:|---:|
| 1 | 0,4009 | 1,1037 |
| 2 | 0,4095 | 1,0798 |

Esse parâmetro participa do passo usado para atualizar a memória. Pela recorrência `exp(delta * A)`, com `A` negativo, um delta maior acelera o decaimento do estado. **Essa é uma explicação do mecanismo, não uma prova da causa do resultado:** o delta completo também depende da entrada projetada, e a tabela mostra apenas o termo de bias antes do treinamento.

Portanto, há uma diferença real que precisa ser qualificada antes de usar este piloto como evidência sobre o Mamba de referência. Não foi executada uma comparação numérica com o backend oficial. Rodar em CPU, por si só, não explica uma BA menor; a questão identificada é a implementação/inicialização utilizada.

## 5. O que as auditorias confirmam — e seu limite

- As previsões de validação e teste são reproduzidas exatamente ao recarregar os checkpoints.
- Pesos foram atualizados, as épocas foram escolhidas pela validação e as métricas foram recalculadas dos parquets.
- Timestamps, classes, purga, cobertura comum e ajuste do scaler foram conferidos.
- O AR(1) pareado reproduziu as classes do piloto histórico D1.

Essas verificações sustentam o **aceite funcional do fluxo**. Não demonstram equivalência com a implementação oficial, ausência de qualquer defeito ou capacidade preditiva do modelo. A classificação científica deste piloto permanece **em revisão**, e seus valores originais continuam preservados.

## 6. Próxima sequência recomendada

1. Verificar a recorrência e a inicialização do fallback contra a referência oficial, com verificações numéricas pequenas e sem escolher alterações pela BA de teste.
2. Documentar qualquer correção como nova versão do código, preservando esta execução. Não reescrever o resultado antigo como se a correção já estivesse nele.
3. Antes de novos treinos, declarar uma comparação controlada de desenvolvimento com entradas, fold, seed e regras de treino mantidos. Uma eventual melhora isolada continua sendo exploratória.
4. Depois da qualificação da implementação, completar D1–D4 e seguir a matriz de entradas/contextos do protocolo com as mesmas regras para LSTM e Mamba. Não procurar uma seed favorável nem inverter previsões após ver o teste.
5. Manter os folds finais de 2024–2025 bloqueados até o congelamento metodológico.

**Conclusão atual:** o piloto apresentou baixa discriminação e viés para alta no teste. Encontramos mudança de distribuição e uma diferença de inicialização que merecem investigação, mas ainda não isolamos uma causa. O registro serve como evidência do desenvolvimento, sem sustentar uma conclusão geral de que “Mamba é ruim para criptomoedas”.
