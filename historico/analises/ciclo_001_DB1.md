# Ciclo 001 — primeiro trimestre, análise parcial

Registro em 18/10/2026 após concluir as 24 células de DB1, com seed 42. Identidade `4e232a796fcda0ea34c3`; dataset `9341610dbb329a858784`. São 48 ajustes neurais e quatro ajustes AR(1), reutilizados entre contextos e prazos. Os outros três trimestres ainda estavam em execução: **este documento não seleciona uma configuração vencedora**.

O teste de DB1 corresponde a janeiro–março de 2023, com purgas e exclusões de observabilidade definidas antes dos treinos. Cada célula preditiva tem 1.812 origens comuns. As mesmas origens reaparecem entre moedas, contextos e prazos; somá-las não cria observações independentes. Os dados completos e hashes de procedência deste resumo estão em [ciclo_001_DB1.json](ciclo_001_DB1.json).

## Evidência de execução

As 24 células passaram pelas auditorias de rótulos, alinhamento, métricas, checkpoints e contabilidade; a auditoria suplementar também conferiu resumos, fontes e ambiente. A recarga reproduziu as probabilidades dos checkpoints. Foram conferidos 72 registros de comprar/manter, correspondentes a quatro trajetórias únicas. Todas as quatro qualificações numéricas AR(1) passaram. Esses controles sustentam a rastreabilidade da execução; não garantem rentabilidade ou validade fora do período estudado.

## Qualidade das probabilidades

Médias com o mesmo peso para as 24 células. Menor é melhor em ambas as métricas.

| Modelo/referência | Log-loss | Brier |
|---|---:|---:|
| Mamba | 1,040225 | 0,625559 |
| LSTM | 1,028929 | 0,617169 |
| AR(1) | 2,403057 | 0,905053 |
| Frequências do treino | 1,070675 | 0,644308 |

Neste trimestre, as duas redes melhoraram a média da referência constante e superaram o AR(1) especificado. A média de Mamba ficou 0,011296 acima da LSTM em log-loss. Isso é uma descrição deste bloco, sem declaração de significância ou superioridade geral. A qualificação de Monte Carlo confirma estabilidade numérica do orçamento do AR(1), não a adequação das suas hipóteses ao mercado.

| Moeda | Mamba | LSTM | AR(1) | Frequências do treino |
|---|---:|---:|---:|---:|
| BTC | 1,062692 | 1,015988 | 1,894152 | 1,086897 |
| ETH | 1,028955 | 1,028166 | 2,222355 | 1,057448 |
| BNB | 1,019899 | 1,033667 | 2,558830 | 1,083563 |
| XRP | 1,049354 | 1,037893 | 2,936891 | 1,054794 |

Cada linha é a média dos seis recortes daquela moeda. BNB favoreceu Mamba em média, enquanto BTC e XRP favoreceram LSTM; ETH ficou próximo. A variação entre moedas é motivo para aguardar os demais blocos, não para eliminar recortes desfavoráveis.

## Efeito do contexto

Diferença de log-loss **W168 menos W24**, pareada por moeda/prazo e depois promediada entre as quatro moedas. Valor positivo indica erro maior com contexto longo. Ambos os contextos recebem o mesmo resumo de volatilidade de sete dias.

| Prazo máximo | Mamba | LSTM |
|---|---:|---:|
| 1 hora | +0,000140 | −0,002301 |
| 24 horas | +0,012488 | +0,002454 |
| 168 horas | +0,001055 | +0,019546 |

Neste bloco, contexto maior não trouxe melhora média consistente. Não extrapolar isso para todo o estudo: a estabilidade entre trimestres e seeds ainda precisa ser examinada. O AR(1) e a referência constante não dependem de W; repeti-los não cria comparadores independentes.

## Operações após custos

Todas as 24 configurações base de cada modelo tiveram percurso financeiro auditável neste trimestre. Mamba operou em sete delas e permaneceu em caixa em 17; LSTM operou em uma e ficou em caixa em 23; AR(1) ficou em caixa nas 24. A duplicação do AR(1) entre contextos é intencional para alinhamento da tabela.

Todos os recortes que efetivamente operaram estão abaixo. As demais configurações tiveram zero operações e retorno zero. São estratégias separadas, que podem operar simultaneamente; **não somar seus retornos ou operações como se fossem uma única carteira**.

| Moeda | Contexto | Prazo | Modelo | Operações | Retorno líquido | Drawdown |
|---|---:|---:|---|---:|---:|---:|
| BTC | 168h | 24h | Mamba | 7 | −0,1500% | 1,9824% |
| ETH | 24h | 24h | Mamba | 9 | +0,9471% | 3,3407% |
| ETH | 168h | 24h | Mamba | 5 | +2,3642% | 1,0187% |
| BNB | 24h | 24h | Mamba | 1 | −1,0000% | 1,1197% |
| BNB | 168h | 24h | Mamba | 4 | −0,3056% | 1,8012% |
| BNB | 24h | 168h | Mamba | 1 | −1,0000% | 1,6796% |
| BNB | 168h | 168h | Mamba | 3 | −1,0253% | 2,9907% |
| BNB | 168h | 168h | LSTM | 2 | +0,2259% | 1,0687% |

Os poucos negócios não estabelecem uma estratégia confiável. Por exemplo, o maior retorno desta tabela veio de cinco operações; escolhê-lo retrospectivamente como vencedor introduziria seleção pelo teste de desenvolvimento. Melhor log-loss e maior retorno também podem apontar para modelos diferentes.

A lacuna durante a interrupção do mercado spot em 24/03/2023 impede uma avaliação integral de comprar/manter neste bloco. Estratégias que não mantiveram posição durante a lacuna podem ser verificáveis, como ocorreu nas políticas base, mas isso não recupera o controle ausente. Consultar também os cenários de custos agravados, ambiguidade e barreiras sem filtro nos artefatos financeiros; a tabela acima é somente o cenário base predefinido.

## Continuação

Nenhum limiar, custo, arquitetura ou checkpoint foi trocado em resposta a esses resultados. Concluir DB2–DB4, comparar estabilidade e incerteza por blocos e somente então registrar uma hipótese concreta para outro ciclo. B1–B4 continuam bloqueados. Este primeiro trimestre integra o desenvolvimento e não constitui avaliação final independente.

## Complemento registrado em 18/10/2026

A revisão da observabilidade permitiu conferir separadamente o retorno de comprar/manter entre seus preços de entrada e saída, ambos conhecidos nas quatro moedas. A curva integral e o drawdown de DB1 continuam indisponíveis; os registros originais acima foram preservados. O [complemento descritivo](complemento_comprar_manter.md) declara a decisão posterior, os valores e os limites. Ele não se aplica às estratégias de barreiras, cujas saídas dependem do caminho.
