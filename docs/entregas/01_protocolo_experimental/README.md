# Entrega 1 — protocolo experimental

**Entrega esperada:** documento curto com as decisões que orientam o estudo.  
**Estado:** fundação metodológica revisada em 28/09/2026 (protocolo 1.6). O AR(1) foi executado em BTCUSDT/D1–D4; LSTM e Mamba ainda não foram executados, e não há resultados finais.

## Pergunta científica

O Mamba consegue prever a direção futura de BTC, ETH, BNB e XRP usando somente OHLCV, com desempenho superior ao AR(1) estatístico e a uma LSTM que recebe as mesmas entradas, além de evidência de associação direcional?

## Decisões fechadas

| Item | Decisão |
|---|---|
| Moedas | BTCUSDT, ETHUSDT, BNBUSDT e XRPUSDT |
| Fonte | Binance Spot Public Data |
| Período | 01/01/2021 a 01/01/2026, UTC, fim exclusivo |
| Candles | 15m, 1h, 4h e 1d |
| Dados | OHLCV e indicadores derivados somente do passado |
| Alvo | Alta (`1`) se o retorno futuro for positivo; não alta (`0`) caso contrário |
| Comparação principal | Prever as próximas 24 horas nas quatro granularidades, com contexto de 7 dias |
| Comparação de contexto | Repetir a previsão de 24 horas com 7 e 14 dias de passado |
| Comparação de horizonte | Comparar próximas 24 horas com próximo candle, mantendo o contexto de referência |
| Baseline estatística | ARIMA(1,0,0) dos log-retornos, equivalente a AR(1) com intercepto |
| Baseline neural | LSTM unidirecional de duas camadas, com largura 32 ou 64 escolhida somente no desenvolvimento; mesmas entradas e amostras do Mamba |
| Métrica principal | Balanced accuracy |
| Referência matemática | 50% de BA, quando ambas as classes reais estão presentes |
| Teste direcional | Pesaran–Timmermann, nível de 5%; não testa a diferença para as baselines |
| Validação | Walk-forward expansivo, sem embaralhar validação/teste |

## Por que estas baselines

A [pesquisa metodológica](../../baseline_metodologia.md) distingue referências de **preço** (passeio aleatório), de **retorno numérico** (média histórica), de **rentabilidade** (buy-and-hold) e de **direção**. O *random walk* sem deriva é uma referência clássica em previsão financeira. Porém, ao prever preço inalterado e converter pelo alvo deste TCC, ele sempre prevê `não alta`: sua BA é 50% se ambas as classes aparecem. ARIMA aparece como comparador estatístico explícito em estudos de direção de Bitcoin; a especificação ARIMA(1,0,0) nos retornos foi fixada **antes do piloto de desenvolvimento**. A LSTM foi adicionada **depois** de observar a BA do AR(1) em BTCUSDT/D1–D4, para comparar o Mamba com uma rede sequencial alimentada pelos mesmos dados. Essa sequência de decisões está registrada no [protocolo 1.6](../../protocolo_experimental.md); nenhuma delas foi escolhida por scores finais de 2024–2025.

```text
r_t = ln(C_t / C_(t-1))
r_previsto_(t+1|t) = alfa_estimado + phi_estimado * r_t
prever alta se r_previsto_(t+1|t) > 0; caso contrário, prever não alta
```

Na análise principal de 24 horas, estimar `alfa` e `phi` apenas com retornos de treino de dias UTC completos, por moeda e fold. Para a mesma moeda e origem, a previsão é igual nas quatro granularidades. Na análise de próximo candle, ajustar o AR(1) separadamente para cada granularidade; a célula diária é reutilizada. Em validação e teste, os coeficientes ficam congelados, mas o último retorno **já observado** pode atualizar a previsão de um passo. O AR(1) não recebe seeds nem consulta o candle a prever. A amostra elegível será a mesma das redes, sem os 20 dias extras antes exigidos pela SMA.

A LSTM receberá as janelas de 7 ou 14 dias em resolução 15m, 1h, 4h ou 1d, com as mesmas features, normalização de treino, origens, rótulos e horizontes do Mamba. Ambas usarão o mesmo orçamento de treino e serão avaliadas nos mesmos folds e seeds; cada arquitetura terá pesos próprios. O AR(1) continua com sua entrada simples baseada em fechamentos. Assim, as duas diferenças de BA respondem a perguntas distintas.

## Dimensões que não devem ser confundidas

| Dimensão | Pergunta | Valores do estudo |
|---|---|---|
| Moeda | O comportamento muda entre ativos? | BTC, ETH, BNB e XRP |
| Candle | Com que nível de detalhe o passado é representado? | 15m, 1h, 4h e 1d |
| Contexto | Quanto passado o modelo recebe? | 7 e 14 dias |
| Horizonte | Quão longe no futuro tentamos prever? | Próximo candle e próximas 24h |

Os resultados serão mantidos separados por configuração. Isso permite, por exemplo, encontrar capacidade preditiva em horizontes curtos e não em 24 horas, ou o contrário. Também permite verificar se mais contexto ajuda ou apenas acrescenta ruído.

Para reduzir a mistura de causas, as comparações serão organizadas assim:

1. **Candles:** contexto de 7 dias e horizonte de 24 horas ficam fixos.
2. **Contexto:** horizonte de 24 horas fica fixo; comparar 7 contra 14 dias.
3. **Horizonte:** contexto de 7 dias fica fixo; comparar próximo candle contra 24 horas em tabelas separadas.

A terceira comparação é operacional, não perfeitamente controlada: prever a cada candle gera mais origens e amostras do que prever uma vez por dia. Por isso, uma diferença nessa tabela pode refletir tanto o horizonte quanto a frequência da tarefa e será interpretada com essa limitação.

A expressão “trade curto ou longo” será tratada como **horizonte de previsão curto ou longo**. Rentabilidade de trading exigiria outro protocolo com taxas, slippage, posições e risco.

## Quatro verificações independentes

| Verificação | Pergunta | Leitura correta |
|---|---|---|
| `BA_Mamba − BA_AR1` | O Mamba teve BA observada maior que este modelo estatístico, nas mesmas origens? | Ganho em p.p., com estabilidade por fold; as entradas dos métodos diferem. |
| `BA_Mamba − BA_LSTM` | O Mamba supera outra rede sequencial nas mesmas entradas e origens? | Diferença observada em p.p.; capacidade e hiperparâmetros internos ainda podem diferir. |
| `BA_Mamba − 50%` | O Mamba ficou acima do nível matemático de ausência de discriminação? | Exige as duas classes reais. O random walk sem deriva cai nesse patamar para este alvo, sem criar outra evidência independente. 50% não é a BA medida do AR(1) e não fornece p-valor. |
| PT | Há evidência de associação direcional favorável além do esperado pelas proporções de altas previstas e reais? | Exigir estatística positiva e `p < 0,05` nas três seeds do Mamba. PT não compara modelos. |

Uma leitura favorável do TCC precisa discutir as quatro verificações e a estabilidade entre períodos e ativos. Não haverá um único rótulo de "ruim" a "excelente" que misture seus significados. Nenhuma dessas verificações prova rentabilidade ou, isoladamente, superioridade estatística entre modelos.

## Forma dos resultados

Serão apresentadas **quatro matrizes paralelas** com as mesmas moedas e candles:

1. **Mamba versus AR(1):** BA de cada método e ganho Mamba menos AR(1) em p.p.
2. **Mamba versus LSTM:** BA de cada rede e ganho Mamba menos LSTM em p.p.
3. **Mamba versus 50%:** BA do Mamba, distância a 50% em p.p. e suporte das classes.
4. **PT:** estatística e p-valor por seed para cada rede; AR(1) uma vez por célula.

O PT é calculado uma vez por seed sobre os oito períodos fora da amostra. O resumo exige estatísticas positivas e mostra qualquer caso em que a inferência fique indisponível ou limitada pela dependência serial.

| Moeda / candle | 15m | 1h | 4h | 1d |
|---|---|---|---|---|
| BTC | A calcular | A calcular | A calcular | A calcular |
| ETH | A calcular | A calcular | A calcular | A calcular |
| BNB | A calcular | A calcular | A calcular | A calcular |
| XRP | A calcular | A calcular | A calcular | A calcular |

Essa matriz será apresentada separadamente para cada análise. Não será feita uma média única que esconda diferenças entre moedas, candles, contextos ou horizontes. O resumo global será apenas complementar.

## Materiais relacionados

- [Mapa visual do estudo e das comparações](visao_visual.md)
- [Nota metodológica completa](../../baseline_metodologia.md)
- [Protocolo experimental detalhado](../../protocolo_experimental.md)
