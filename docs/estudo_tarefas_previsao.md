# Escolha das tarefas de previsão

**Revisão aberta em 13/10/2026.** Este documento fundamenta as alternativas apresentadas na interface. A escolha do pesquisador e do orientador ainda está pendente. O contrato executável continua sendo o protocolo 1.6: direção em 24h, com origens diárias às 00:00 UTC, e direção do próximo candle, com origens a cada fechamento. Há piloto neural documentado somente para a tarefa diária, BTC/1d/D1, em CPU. Não houve novos treinamentos nesta revisão.

## 1. Como definir um experimento

A interface anterior misturava alvos, horizontes e políticas de resposta em um catálogo A–H. Essa organização foi substituída por **eixos de decisão**, sem criar oito famílias independentes de previsão.

| Escolha | Pergunta | Opções ou exemplos | Estado |
|---|---|---|---|
| Moeda | Qual mercado observar? | BTC, ETH, BNB, XRP, todos em USDT | Definida |
| Candle | Qual detalhe temporal entra no modelo? | 15m, 1h, 4h, 1d | Definida |
| Horizonte | Quanto futuro antecipar? | 15m, 1h, 4h, 24h, 3d, 7d, 14d | Prazos adicionais em discussão |
| Alvo / forma de resposta | O que o modelo deve entregar? | Direção, valor, faixa, volatilidade, primeiro toque | Direção vigente; demais em estudo |
| Contexto | Quanto passado entra em um exemplo? | 7 ou 14 dias | Regras por tarefa no protocolo |
| Origens | Quando produzir uma previsão? | Diariamente, cada candle ou eventos | Diário/próximo candle vigentes |
| Política de resposta | Responder sempre ou selecionar situações? | Todas as origens, abstenção ou gatilho | Seleção em estudo |

Um timestamp identifica um instante. A duração de um candle define sua granularidade. Contexto é uma **janela deslizante de entrada**: seu término avança junto com a origem. A janela de treinamento dos folds, por outro lado, é expansiva. Nenhuma dessas definições exige retreinar a rede a cada candle.

Exemplo: BTC, candles de 1h, contexto de 7 dias (168 candles), horizonte de 24h, direção binária, origens às 00:00 UTC. Trocar apenas o candle para 15m gera 672 candles de entrada, mantendo o mesmo futuro e os mesmos horários. Trocar para “próximo candle” altera o horizonte e a frequência das amostras; essa comparação responde a outra pergunta.

## 2. Pesquisa: o que as fontes sustentam

A busca examinou estudos originais de finanças e cripto, referências metodológicas e documentação de rotulagem financeira. Foram priorizados exemplos com alvo identificável, finalidade clara e publicação/repositório rastreável: IEEE TSP, Applied Soft Computing, Journal of Business & Economic Statistics, International Journal of Forecasting, International Review of Financial Analysis e pesquisa FEDS.

**É uma seleção fundamentada de referências, não uma revisão sistemática nem um ranking bibliométrico.** Não há nesta pesquisa contagem representativa que permita afirmar que determinada tarefa é universalmente “a mais usada”. Estudos publicados também não demonstram, sozinhos, adoção por todas as instituições financeiras. As fontes abaixo justificam a relevância de diferentes perguntas, sem importar automaticamente suas arquiteturas, dados externos ou scores para o TCC.

| Referência primária | Mercado e tarefa observados | Por que é pertinente | Limite da transferência |
|---|---|---|---|
| [Zhang, Zohren e Roberts, DeepLOB, IEEE TSP, 2019](https://arxiv.org/abs/1808.03668) | Movimentos de preço de ações usando livro de ofertas, incluindo dados da Bolsa de Londres | Exemplo de classificação direcional em pesquisa de microestrutura | Livro de ofertas e horizontes por atualizações diferem de candles OHLCV; não extrapolar desempenho |
| [Mallqui e Fernandes, Applied Soft Computing, 2019](https://doi.org/10.1016/j.asoc.2018.11.038) | Direção e níveis diários de máximo, mínimo e fechamento do Bitcoin | Distingue antecipar o sentido de estimar valores | Fonte consultada: resumo e trechos públicos da editora; não foi auditada toda a avaliação do artigo |
| [Engle e Manganelli, CAViaR, JBES, 2004](https://doi.org/10.1198/073500104000000370) | Quantis condicionais e Value at Risk em séries financeiras | Referência consolidada de previsão de cauda para gestão de risco | VaR é um quantil de perda; não equivale a intervalo simétrico ou previsão de alta |
| [Lim et al., TFT, IJF, 2021](https://arxiv.org/html/1912.09363v3) | Quantis 10/50/90; inclui volatilidade diária de 31 índices, previsão de cinco dias úteis com contexto de 252 dias úteis | Mostra previsão probabilística e múltiplos horizontes na mesma formulação | O alvo financeiro é volatilidade; não é evidência de faixa de preço cripto nem motivo para incluir Transformers |
| [Wang, Andreeva e Martin-Barragan, IRFA, 2023](https://doi.org/10.1016/j.irfa.2023.102914) — [texto no repositório dos autores](https://www.pure.ed.ac.uk/ws/files/381945597/WangEtal2023IRFAMachineLearningApproaches.pdf) | Previsões de volatilidade de cripto diária, semanal e mensal | Evidência direta de que risco e prazo constituem tarefas próprias em cripto | Usa determinantes internos e externos; o TCC permanece restrito a OHLCV e derivados |
| [Kilic, FEDS 2025-061, revisão de setembro/2026](https://www.federalreserve.gov/econres/feds/linear-and-nonlinear-econometric-models-against-machine-learning-models.htm) | Volatilidade realizada do S&P 500 e de 40 ações, com comparação entre horizontes | Conecta avaliação estatística de risco a utilidade, VaR e expected shortfall | Working paper; os resultados não representam posição institucional nem demonstram melhor tarefa para cripto |
| [López de Prado, Advances in Financial Machine Learning, 2018, cap. 3](https://www.oreilly.com/library/view/advances-in-financial/9781119482086/) e [documentação Mlfin.py](https://mlfinpy.readthedocs.io/en/latest/Labelling.html) | Rotulagem por horizonte fixo e primeiro toque em barreiras | Oferece uma formulação dependente do caminho percorrido pelo preço | Livro/método/documentação; não é levantamento empírico de popularidade nem garantia de rentabilidade |

Busca/consulta: 13/10/2026. Exemplos de termos: “cryptocurrency direction maximum minimum closing prices”, “DeepLOB price movements”, “financial quantile forecasting CAViaR”, “cryptocurrency volatility daily weekly monthly”, “triple barrier labeling”. A interface permite consultar as fontes junto a cada opção; nomes de modelos dos artigos identificam evidências, não novos concorrentes no experimento.

## 3. Opções e razões de uso

### 3.1 Direção

Pergunta: o fechamento futuro será maior que o atual? Classificação reduz a resposta ao sentido do retorno. Serve diretamente ao objetivo atual do TCC. A versão vigente é **alta versus não alta**, com empate na segunda classe, sem excluir movimentos pequenos. Uma classificação alta/neutro/baixa seria outra tarefa: limiares definidos no desenvolvimento e retenção da classe neutra, sem filtrar o teste pelo futuro.

Avaliar BA, F1 macro, recalls, confusão e diferenças pareadas frente a AR(1) e LSTM. A probabilidade de alta também pode ser avaliada por calibração e escores próprios. Direção correta não informa magnitude nem lucro.

### 3.2 Retorno ou preço

Pergunta: qual será o valor futuro ou sua variação? Regressão mede o tamanho esperado do movimento; máximo e mínimo futuros também são alvos possíveis, diferentes do fechamento. Para comparar ativos, retorno oferece escala relativa mais interpretável que preço nominal. Retorno simples e log-retorno devem ser identificados; o desenho didático 100 → 103 usa retorno simples de 3%.

Requer saída numérica, perda de regressão e métricas como MAE/RMSE. Comparar com persistência/retorno zero e adaptar os comparadores escolhidos. Pequeno erro de nível pode resultar da persistência de preços, mesmo sem capacidade útil de antecipar mudanças. Essa é uma extensão de escopo, não uma configuração pronta do classificador atual.

### 3.3 Faixa provável / quantis

Pergunta: qual distribuição ou intervalo é previsto para o resultado? Quantis permitem expressar incerteza e caudas. A faixa q10–q90 tem cobertura nominal de 80%; sua cobertura real precisa ser verificada fora do treino, junto com largura e perda de quantis. Uma faixa muito larga pode cobrir muitos valores e ainda ser pouco informativa.

Essa opção é um **formato de previsão probabilística**, combinável com retorno, preço ou volatilidade. Os cartões visuais são formas de formular perguntas, não uma taxonomia de classes mutuamente exclusivas. CAViaR fundamenta risco de cauda; TFT ilustra múltiplos quantis/horizontes, inclusive para volatilidade. Nenhum deles obriga a adicionar sua arquitetura ao trabalho.

### 3.4 Volatilidade

Pergunta: qual será a intensidade das oscilações futuras? É relevante para gestão de risco e dimensionamento de exposição. Não determina o sinal do retorno: movimentos intensos podem terminar perto do preço inicial.

Exige definir precisamente a medida futura (por exemplo, variância realizada a partir de retornos intradiários), escala e horizonte. Métricas como MAE e QLIKE dependem da definição e domínio da medida. Exige comparadores de risco adequados; **o AR(1) direcional atual não passa automaticamente a ser uma baseline de volatilidade**. Não foi adotado nenhum novo comparador nesta revisão.

### 3.5 Primeiro limite atingido / barreiras

Pergunta: o preço atinge primeiro o limite superior, o inferior ou o prazo final? O caminho importa, aproximando a rotulagem de regras de saída. Um ativo pode tocar a barreira inferior antes de terminar o horizonte em alta.

As barreiras devem ser fixadas com informação disponível na origem, eventualmente escaladas pela volatilidade passada. Precisam de definição de três classes, tratamento do vencimento sem toque e métricas por classe. Se a máxima e a mínima do mesmo candle cruzarem as duas barreiras, a ordem é desconhecida com OHLCV; definir antes do teste uma política auditável ou usar dados mais finos. Não escolher retrospectivamente o toque favorável. Rotular toques não demonstra execução real, especialmente com custos e slippage.

## 4. Estilos de trading e prazos candidatos

O estilo é um contexto de uso; o experimento deve armazenar **horizonte exato e agenda**. A [descrição profissional da Schwab](https://www.schwab.com/learn/story/swing-trading-strategies) distingue day trading com entrada/saída no mesmo dia de swing com manutenção por dias ou semanas. Não há uma fronteira universal na qual sete dias deixem de ser swing. Essa referência conceitual não transfere regras regulatórias de ações para cripto.

| Grupo visual para discussão | Prazos candidatos no explorador | Relação com uso |
|---|---|---|
| Dentro do dia | 15m, 1h, 4h | Contextualiza previsões intradiárias; um trade só é day trade se respeitar o fechamento no dia definido |
| Entre dias | 24h, 3 dias | Movimentos que podem atravessar dias; referência a swing |
| Uma semana ou mais | 7 e 14 dias | Swing mais longo ou posições; nome depende também das regras da estratégia |

Esses números são **propostas do projeto**, não extraídos como “prazos ótimos” das referências. 24h não implica origem às 00:00, e um candle diário não obriga horizonte de um dia. É possível usar candles de 1h para prever sete dias. Se o alvo tiver resolução menor que o candle de entrada, os dados mais finos precisam sustentá-lo. Cripto funciona continuamente; análises semanais usam dias corridos, sem copiar os cinco dias úteis dos estudos de índices.

Quanto maior H em relação ao intervalo entre origens, maior a sobreposição dos desfechos. Exemplos sobrepostos não são observações independentes. Purga temporal, tratamento de dependência, quantidade efetiva de amostras e inferência devem ser revistos antes da adoção.

## 5. Quando prever e quando responder

- **Próximo candle:** define horizonte relativo ao candle e, no nosso protocolo, agenda a cada fechamento. Não é outro tipo de alvo.
- **Vários horizontes:** pode usar modelos separados ou saída conjunta. Essa decisão e orçamento ainda precisam ser fixados; não inferir que há suporte multi-output atual.
- **Gatilho:** regra causal de seleção de origens, como volume observado acima de um limiar aprendido no desenvolvimento. Não escolher origens pelo movimento futuro.
- **Abstenção:** produzir uma previsão somente quando um critério de confiança for satisfeito. Publicar cobertura (fração respondida), erro/BA nos casos selecionados, suporte por classe e comportamento temporal; se uma classe desaparecer, BA pode ficar indefinida. Comparar modelos na mesma população ou separar explicitamente o efeito da seleção.

[SelectiveNet, Geifman e El-Yaniv, 2019](https://proceedings.mlr.press/v97/geifman19a.html) fundamenta o compromisso entre risco e cobertura em classificação geral. [Guo et al., 2017](https://proceedings.mlr.press/v70/guo17a.html) fundamenta a necessidade de avaliar calibração; confiança numérica de uma rede não é garantia de acerto. Esses trabalhos não demonstram ganho em cripto. Limiar/calibração não podem ser escolhidos pelo teste final.

## 6. Recomendação para a decisão com o orientador

1. Manter **direção** como núcleo: combina com a pergunta do TCC e com as duas baselines já implementadas.
2. Definir uma grade pequena de prazos para representar intradia, entre dias e uma semana ou mais. O explorador permite discutir 15m/1h/4h/24h/3d/7d/14d, mas isso não autoriza executar o produto cartesiano inteiro.
3. Separar dois objetivos: comparar candles para o mesmo futuro; comparar tarefas operacionais com futuros diferentes. Preservar população comum quando o contraste exigir.
4. Se houver tempo e motivação científica, escolher uma extensão com hipótese explícita: abstenção ou barreiras mantêm proximidade com decisão direcional, mas ainda exigem protocolo próprio. Retorno, quantis e volatilidade ampliam mais o problema e não devem entrar apenas para aumentar o número de testes.
5. Após a escolha: versionar alvo/agenda, construir amostras, definir comparadores/métricas, ajustar purga, dimensionar orçamento, qualificar o Mamba e só então executar desenvolvimento. Congelar antes de liberar F1–F8.

O resultado esperado é conhecer onde há sinal preditivo, sua estabilidade e sua diferença frente aos comparadores. Um resultado sem ganho do Mamba também é científico. PT permanece uma análise de associação direcional com pressupostos; não é certificado de treinamento correto nem teste de rentabilidade.

## 7. Contrato da interface

O explorador é um rascunho em memória: suas combinações persistem ao mudar de seção e são apagadas ao recarregar. Não escreve configurações nem gera ordens, amostras ou treinos. Os gráficos são ilustrações fictícias identificadas, sem pretensão de refletir cotação, previsão ou resultado. Resultados reais ficam na seção de andamento, acompanhados de contexto e links para os relatórios. O piloto CPU em revisão foi preservado.
