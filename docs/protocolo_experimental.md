# Protocolo experimental — versão 2.1: barreiras e pesquisa iterativa

**Ciclo inicial definido em 18/10/2026. Implementação, qualificação e execução autorizadas pelo pesquisador.**

A pesquisa começa com uma grade de referência e prossegue por ciclos documentados de melhoria, inclusive de configurações internas do Mamba. Cada ciclo é fixado antes de ser executado; todas as tentativas e resultados do estudo são registrados. O desenvolvimento pode orientar mudanças futuras, mas não pode produzir uma alegação de teste final independente quando seus resultados foram consultados para decidir.

O estado factual de execução fica em [andamento](andamento.md) e nos registros em `historico/`. A especificação não substitui evidência de testes, recarga de checkpoints e auditoria.

## 1. Pergunta científica e limites da conclusão

Investigar se Mamba prevê qual limite de preço será atingido primeiro — superior, inferior ou nenhum até um prazo máximo — melhor que LSTM e AR(1), e se essas probabilidades melhoram uma política fixa de compra à vista. Examinar diferenças entre quatro moedas, dois comprimentos de sequência e três prazos máximos.

A avaliação tem dois eixos separados: **qualidade probabilística** e **utilidade econômica após custos**. Um resultado negativo em qualquer eixo é resultado científico válido. Não exigir lucro nem superioridade de Mamba como condição de publicação.

A aplicação operacional desta versão é Binance Spot, posição comprada ou caixa, sem empréstimo, venda a descoberto ou alavancagem. Há risco de perda de capital, mas não liquidação por margem. A tarefa pode informar decisões de exposição e risco; os resultados não demonstram adequação a derivativos nem investimento de meses/anos. Uma semana continua sendo um prazo curto. Stop não garante execução exatamente no limite.

O método de três barreiras associa dois limites de preço a um limite de tempo e permite distância ajustada à volatilidade; isso motiva o alvo, sem implicar rentabilidade. [Referência metodológica: mlfinpy](https://mlfinpy.readthedocs.io/en/latest/Labelling.html).

## 2. Fatores que variam e escolhas fixas

| Elemento | Definição do ciclo inicial |
|---|---|
| Moedas | BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT |
| Candle de entrada | 1 hora, UTC, fixo |
| Contexto sequencial W | 24 ou 168 candles: 1 ou 7 dias |
| Prazo máximo H | 1, 24 ou 168 horas |
| Alvo | Superior primeiro; inferior primeiro; prazo esgotado |
| Modelos | Mamba, LSTM unidirecional, ARIMA(1,0,0) nos log-retornos horários |
| Origem de previsão | A cada hora, imediatamente após fechar o candle |
| Distância dos limites | Uma unidade de volatilidade horária histórica multiplicada por √H |
| Histórico para volatilidade | Últimos 168 retornos horários, igual em todas as células |
| Dados para execução/rótulo | OHLCV de 1 minuto; convenção explícita para ordem desconhecida |
| Arquiteturas neurais | Largura 32, duas camadas; demais parâmetros fixados na seção 8 |
| Entrada operacional | Probabilidade superior ≥ 0,60 e teste de viabilidade nominal após custos |

São **4 × 2 × 3 = 24 células científicas** no ciclo inicial. Frequência de candle, features, scaler, largura, multiplicador das barreiras e limiar de entrada ficam fixos neste ciclo. Ciclos posteriores podem modificar escolhas e configurações internas das redes conforme a seção 13, sem reescrever os resultados já obtidos. A origem horária é frequência de decisão, não autorização para acumular posições a cada hora.

Os contextos são o passado visto em cada amostra; não são o número de anos usados para ajustar os pesos. O conjunto de treinamento cresce por datas em todos os casos. Há um modelo neural distinto por moeda, W, H, fold e seed; sem pré-treino conjunto entre moedas.

**Interpretação do efeito de contexto:** ambos os contextos recebem o mesmo resumo de risco calculado com sete dias. Portanto, comparamos 1 versus 7 dias de sequência detalhada, condicionados a esse resumo comum. Não afirmar que o modelo curto desconhece toda informação anterior a um dia.

## 3. Tempo, volatilidade e posição das barreiras

Seja t o instante UTC de fechamento de um candle horário completo. Somente observações anteriores ou iguais a esse fechamento podem entrar na previsão. O candle seguinte não está disponível.

1. Calcular retornos horários `r_j = ln(C_j / C_(j-1))`.
2. Calcular `sigma_t = desvio_padrao_amostral(r_(t-167), ..., r_t)`, com 168 retornos e divisor 167.
3. Para H em horas, calcular `d_(t,H) = sigma_t × sqrt(H)`. Multiplicadores superior e inferior: ambos **1,0**.
4. A decisão emitida em t é executada no **open do minuto iniciado em e = t + 1 minuto**. Esse atraso fixo evita assumir execução retroativa no fechamento observado.
5. Seja A esse preço bruto de entrada. Fixar `U = A × exp(d)` e `L = A × exp(-d)` até a saída. Não mover limites com volatilidade futura.
6. O prazo máximo vence em `v = e + H horas`. Não é obrigatório permanecer até v: o primeiro limite encerra a operação.

A é desconhecido na origem e só ancora o rótulo e a execução posteriormente. Não é feature. A distância relativa d já é conhecida em t. O orçamento da ordem pode ser determinado em t e convertido em quantidade ao preencher a ordem.

Exemplo **ilustrativo, não estimativa dos dados**: com sigma horário de 0,3%, os limites ficam aproximadamente em +0,30%/−0,30% para 1h; +1,48%/−1,46% para 24h; +3,96%/−3,81% para 168h. São simétricos em log-preço, não exatamente em percentual simples. No mesmo instante, a distância logarítmica semanal é √7 ≈ 2,65 vezes a diária.

O escalonamento √H é uma **regra de desenho fixa**, não uma previsão de volatilidade futura, intervalo de confiança ou garantia de probabilidades iguais de toque. Dependência temporal, saltos e volatilidade variável limitam essa aproximação. Não recalibrar o multiplicador para obter classes equilibradas. Reportar largura efetiva, frequência das classes e tempo até saída por moeda e prazo. A literatura mostra, por exemplo, limitações de usar essa regra para escalar quantis de risco sob saltos; isso impede interpretá-la aqui como garantia de cobertura. [Daníelsson e Zigrand, On time-scaling of risk](https://eprints.lse.ac.uk/24827/1/dp439.pdf).

Como H e a distância crescem juntos, o efeito de prazo representa uma operação mais longa com limites proporcionalmente mais largos. Não atribuir as diferenças exclusivamente ao tempo mantendo todo o restante constante.

Sigma nulo, não finito ou impossível de calcular gera origem inelegível por informação passada, registrada como tal. Não excluir retornos futuros pequenos, prejuízos, operações sem toque ou episódios adversos.

## 4. Rótulos, preços de saída e ambiguidade

Classes, nesta ordem fixa: `0 = inferior_primeiro`, `1 = prazo_esgotado`, `2 = superior_primeiro`. A classe de prazo esgotado não significa retorno zero nem ausência de oscilação.

Examinar cronologicamente os minutos com início em `[e, v)`, usando o mesmo A, U e L para todos os modelos e ambos os contextos:

1. Se o open do minuto já está em U/acima ou em L/abaixo, registrar o respectivo toque no open. O preço bruto de saída é esse open, incorporando o salto observado.
2. Com open entre os limites: se apenas o high alcança U, saída superior em U; se apenas o low alcança L, saída inferior em L. Igualdade conta como toque.
3. Se high alcança U e low alcança L no mesmo primeiro minuto de toque, a ordem é desconhecida em OHLCV. A convenção principal é **inferior primeiro para a posição comprada**, com `toque_ambiguo = true`. Isso é uma convenção conservadora, não uma reconstrução factual da ordem.
4. Sem toque antes de v: classe prazo esgotado e saída no open do minuto v, com seu retorno efetivo. A expiração tem prioridade em v; não reclassificar como toque só porque esse open está fora dos limites.

O timestamp de um toque dentro do minuto indica o minuto de ocorrência, sem inventar segundo exato. Para controle de posição e nova decisão, tratar a saída intraminuto como conhecida no fim desse minuto. Toque no open tem timestamp exato do open.

Não descartar amostras ambíguas. Reportar sua proporção entre todas as origens e entre as origens com toque, por moeda, H e fold. **Gate de resolução:** se exceder 1% de todas as origens ou 5% das origens com toque em qualquer partição avaliada, não liberar sua comparação principal antes de obter trades da mesma fonte para resolver a ordem em todos os minutos ambíguos daquela partição. Se não for possível, registrar bloqueio de qualidade. Esses limites são tolerâncias administrativas predefinidas, não um teste estatístico. O diagnóstico do gate usa apenas contagem de qualidade, não desempenho dos modelos.

Mesmo abaixo do gate, publicar sensibilidade superior-primeiro nos casos ambíguos, mantendo previsões e configurações. Para log-loss e Brier, calcular também limites de incerteza de rotulagem escolhendo, em cada origem ambígua, o menor/maior erro entre os dois rótulos possíveis e depois agregando. Apenas comparar todos-inferior com todos-superior não fornece esses limites. Reexecutar a contabilidade completa da política sob a convenção alternativa, pois saídas podem alterar entradas posteriores; isso é sensibilidade econômica, não limite matemático global de retorno. Não escolher a convenção que favorece o modelo. A regra principal de treino permanece inferior-primeiro; refinamentos com trades geram outra identidade de dataset e exigem tratamento consistente nas partições.

A regra de preenchimento em U/L é uma aproximação de execução. Gaps observáveis usam open; taxas, slippage e cenário de custos agravados são obrigatórios. Não interpretar o stop nominal como teto garantido de perda.

## 5. Dados e elegibilidade

Fonte: arquivos públicos Binance Spot de **1 minuto**, quatro pares, período `[2021-01-01 00:00 UTC, 2026-01-01 00:00 UTC)`. São 240 arquivos mensais esperados e 10.517.760 minutos teóricos somados nos quatro pares, antes de falhas. Os candles horários serão agregados destes mesmos minutos: primeiro open, máximo high, mínimo low, último close, soma de volume base.

Verificar checksums, duplicatas, timestamps, OHLC válido, volume, calendário completo e unidade de tempo. Os arquivos Spot a partir de 2025 usam microssegundos; normalizar explicitamente, sem inferir a unidade a partir de um único arquivo. [Fonte e especificação: Binance Public Data](https://github.com/binance/binance-public-data).

Só agregar hora com 60 minutos válidos. Não interpolar preços ou fabricar candles em lacunas. O cálculo dos 168 retornos requer 169 closes consecutivos; os primeiros instantes sem histórico suficiente são aquecimento. Preservar o início e fim de cada candle e distinguir timestamp de fechamento exclusivo da convenção de close_time da fonte.

Criar uma identidade de dataset com manifestos, hashes dos arquivos brutos e do código de transformação, convenções, contagens e causas de exclusão. Verificar arquivos já disponíveis antes de reutilizá-los.

O desenvolvimento inicial coleta e processa somente 2021–2023: 144 arquivos mensais. Os anos 2024–2025 não são necessários para construir ou escolher a primeira configuração e ficam bloqueados para avaliação. A base completa terá 240 meses somados entre moedas quando a avaliação final for liberada.

Alguns arquivos públicos têm um candle cujo close_time é anterior ao fim normal do minuto. Esses registros são minutos interrompidos: preservar o dado bruto, registrar sua contagem e tratá-los como lacunas na série regular; não completar os preços nem fingir cobertura integral.

### 5.1 Amostras para avaliação preditiva pareada

Construir uma máscara comum aos quatro pares, ambos os contextos e três prazos: passado necessário válido e futuro completo até a expiração máxima de 168h, incluindo seu open. A qualidade futura é usada somente para determinar se o rótulo é observável, nunca como feature. Isso dá às comparações preditivas a mesma população. Publicar exclusões por motivo e por período; uma lacuna em XRP pode retirar uma origem da comparação comum, por exemplo.

Antes de qualquer fronteira entre partições, purgar origens cuja expiração **máxima planejada**, `e + 168h`, seja maior ou igual à fronteira. Aplicar a mesma purga aos três H, mesmo quando a operação teria saído antes. Não usar o toque futuro para permitir uma amostra que cruzaria a fronteira. Janelas de entrada de validação/teste podem usar passado anterior à fronteira; seus rótulos não entram no ajuste.

### 5.2 Simulação econômica sem conhecimento antecipado das lacunas

A política usa elegibilidade **causal**: histórico válido, modelo disponível, ausência de posição/ordem e calendário conhecido. Não utilizar a máscara de completude futura para decidir entrar. Gerar probabilidades também nas origens causalmente elegíveis sem rótulo avaliável.

Não abrir se `e + H >= fim_do_bloco_de_teste`, pois o fim do bloco é conhecido de antemão. Essa restrição usa o H real da estratégia, não 168h para todos. Por isso a amostra econômica pode diferir da amostra preditiva comum; publicar ambas as contagens.

Se uma lacuna durante posição aberta impedir decidir a primeira saída ou seu preço, a trajetória financeira fica **não auditável** a partir dela. Isso inclui ordem de entrada/saída sem preço de negociação observável: preservar volume e contagem de negócios da fonte para auditoria, sem assumir execução em preço carregado de minuto sem negócios. Não fechar retrospectivamente antes da lacuna, preencher lucro zero, ignorar a operação ou compor uma curva com os trechos convenientes. Recuperar os dados da mesma fonte; sem recuperação, não publicar resultado econômico integral daquele fold como válido. A liberação final exige cobertura suficiente para auditar as estratégias, sem escolher folds pelo resultado financeiro.

## 6. Calendário walk-forward e congelamento

Datas são limites UTC, intervalos semiabertos. Treino expansivo começa em 01/01/2021, descontando aquecimento/purgas. Cada ajuste parte de pesos novos; não carregar checkpoint de outro fold. Validação serve a early stopping; teste do bloco não escolhe época ou parâmetros.

| Fold | Fim exclusivo do treino / início da validação | Fim da validação / início do teste | Fim exclusivo do teste |
|---|---|---|---|
| DB1 | 2022-10-01 | 2023-01-01 | 2023-04-01 |
| DB2 | 2023-01-01 | 2023-04-01 | 2023-07-01 |
| DB3 | 2023-04-01 | 2023-07-01 | 2023-10-01 |
| DB4 | 2023-07-01 | 2023-10-01 | 2024-01-01 |
| B1 | 2023-10-01 | 2024-01-01 | 2024-07-01 |
| B2 | 2024-04-01 | 2024-07-01 | 2025-01-01 |
| B3 | 2024-10-01 | 2025-01-01 | 2025-07-01 |
| B4 | 2025-04-01 | 2025-07-01 | 2026-01-01 |

DB1–DB4 são desenvolvimento em 2023, seed 42. B1–B4 são avaliação final semestral em 2024–2025, seeds **17, 42 e 2026**. O semestre reduz o número de ajustes; não implica estabilidade do mercado por seis meses. As validações finais são janelas anteriores de três meses. No walk-forward, dados de um teste antigo podem fazer parte do treino/validação de um bloco posterior, como ocorreria na implantação; não voltar atrás e alterar previsões já emitidas.

Antes de B1, congelar commit, protocolo, dataset, ambiente, backend, parâmetros, regras de seleção e simulação. Congelar também os quatro folds como um único plano de avaliação: resultados de B1 não autorizam ajustes discricionários antes de B2. Bloquear B1–B4 na CLI até esse registro.

Registrar declaração do pesquisador sobre exposição prévia a resultados de 2024–2025, inclusive experimentos removidos. Não presumir que o período nunca foi consultado. Se houve uso de seus resultados para orientar escolhas, descrever a avaliação como retrospectiva, sem alegar holdout intocado; uma confirmação prospectiva precisará de outro período, definida em revisão separada.

### Quantidade de execuções

- Por fold e seed: 24 células × 2 redes = **48 ajustes neurais**.
- Desenvolvimento: 48 × 4 × 1 = **192 ajustes**.
- Final: 48 × 4 × 3 = **576 ajustes**.
- Total planejado: **768 ajustes neurais**, além de qualificações e tentativas registradas. Um piloto só conta na grade se sua identidade e todos os parâmetros coincidirem com a execução definitiva.
- AR(1): um ajuste por moeda/fold = **32 ajustes**; previsões para três H = 96 séries moeda/fold/H. Reutilizá-las nos dois W e nas seeds neurais, sem contá-las como novas evidências independentes.

É uma grade menor em fatores, mas não um experimento trivial em custo. Medir tempo/memória e custo das simulações do AR(1) no piloto antes da grade completa. Se inviável, revisar o orçamento antes da avaliação final, preservando o registro; não remover células por desempenho desfavorável.

## 7. Entradas e transformações

Para cada candle horário j, usar cinco variáveis causais:

`[ln(O_j/C_(j-1)), ln(H_j/C_(j-1)), ln(L_j/C_(j-1)), ln(C_j/C_(j-1)), ln(1+V_j)]`.

V é volume na moeda base. O close anterior é necessário também no primeiro candle da sequência. Essa representação evita obrigar a rede a interpretar níveis absolutos de preço de anos distintos, sem acrescentar indicadores ou informação externa.

Aplicar StandardScaler por moeda e fold, ajustado apenas aos vetores horários únicos que integram as entradas W=168 das origens de treino elegíveis. Reutilizar esse ajuste em ambos W, nos três H e nas duas redes; não contar repetições das janelas como observações adicionais no ajuste do scaler. Dimensão sequencial: **5**.

Acrescentar à cabeça de classificação o escalar `ln(d_(t,H))`, padronizado por moeda/fold/H apenas nas origens de treino. Ele informa a distância efetivamente prevista. Dimensão auxiliar: **1**. Concatenar com o último estado da sequência e produzir três logits. A documentação/identidade deve distinguir cinco features por candle de uma feature auxiliar por origem.

Não ajustar scalers na validação/teste, não recomputar seus parâmetros ao emitir uma previsão e não compartilhar estatísticas entre moedas. Colunas constantes no treino recebem escala 1, com registro. Rejeitar valores não finitos e inputs fora do contrato; não corrigir silenciosamente com dados futuros.

## 8. Modelos e treinamento

### 8.1 Comparação neural controlada

Mamba: bloco Mamba-1, `d_model=32`, duas camadas, `d_state=16`, `d_conv=4`, `expand=2`, dropout 0,1. Preservar o encadeamento atual do classificador: projeção linear 5→32; em cada bloco `x = LayerNorm(x + Mamba(x))`; depois dropout 0,1 e LayerNorm final; selecionar último estado, concatenar a variável auxiliar e aplicar linear 33→3. LSTM: unidirecional, duas camadas, hidden size 32, dropout 0,1 entre camadas; último estado de saída concatenado à variável auxiliar, linear 33→3, sem acrescentar normalização ou residual. Estado recorrente começa em zero em cada janela. Mesmo número de camadas/largura não significa mesmo número de parâmetros; publicar contagem, tempo e memória, com snapshot do código e versões.

Ambas usam entradas, origens, folds, loss, otimização e regra de seleção iguais. Saída softmax com três classes. AdamW: learning rate 0,0002, weight decay 0,001, betas (0,9; 0,999), epsilon 1e-8, batch efetivo 32, clipping de norma de gradiente 1,0, máximo 100 épocas, patience 10. Cross-entropy sem pesos de classe, sem oversampling. Não introduzir scheduler, busca de hiperparâmetros ou calibração posterior dentro do ciclo inicial; mudanças posteriores exigem outro ciclo predefinido.

Selecionar checkpoint pela **menor log-loss de validação**; empate exato mantém a primeira época. Acurácia não seleciona checkpoint. Só treino pode embaralhar; validação/teste preservam a ordem. Microbatch pode dividir 32 por necessidade de memória, com acumulação e normalização corretas, registrado na identidade. Fixar seeds de inicialização/ordenação e documentar limites de determinismo do ambiente. Sem mixed precision na referência inicial; qualquer mudança numérica exige qualificação e outra identidade.

O backend de referência da nova grade será **Mamba oficial/CUDA, após qualificação**. O fallback PyTorch continua disponível e deve ser preservado; não substituir o backend silenciosamente se CUDA faltar. Não misturar implementações na mesma comparação científica. Se o backend de referência não estiver disponível, a execução fica pendente ou requer revisão documentada antes da grade.

A qualificação inclui forward/backward finitos, inicialização, causalidade, consistência de recarga e comparação da implementação oficial com sua rotina de referência em entradas sintéticas. Registre divergências numéricas e de ambiente. Uma qualificação funcional não certifica qualidade de previsão financeira.

### 8.2 AR(1) como previsão probabilística de trajetórias

O AR(1) atual de próximo retorno não basta para três barreiras. Implementar um comparador explicitamente probabilístico:

`r_(j+1) = c + phi × r_j + epsilon_(j+1)`, com inovação gaussiana independente, média zero e variância residual estimada no treino.

Ajustar intercepto e coeficiente por mínimos quadrados em retornos horários consecutivos do treino, encerrados antes do limite purgado comum. Estimar variância por SSE/(n−2). Não ajustar em validação/teste. Usar todos os retornos horários válidos nesse intervalo, sem duplicação por janelas. Se o ajuste for singular, variância inválida ou `abs(phi) >= 1`, registrar falha e bloquear a execução dessa configuração; não truncar phi para obter resultado desejado.

Para prever o percurso intrahora, adotar esta **hipótese adicional do baseline**, predefinida: durante uma hora simulada, cada um de seus 60 incrementos de log-preço tem média `(c + phi × retorno_da_hora_anterior)/60` e desvio padrão `sigma_residual/sqrt(60)`, com ruídos independentes. A soma da hora obedece ao AR(1). Atualizar a média condicional apenas na próxima hora simulada. Interpolar linearmente entre preços simulados de minutos consecutivos para determinar toques. A origem usa o último retorno horário observado.

Simular o minuto de latência até e; ancorar os limites no preço simulado de e e seguir até e+H. As barreiras usam o d observado na origem, igual ao das redes. Produzir **4.096 trajetórias por origem**, compartilhando prefixos entre os três H; contar superior, inferior e expiração conforme o primeiro evento. Probabilidade: `(contagem_classe + 0,5)/(4096 + 1,5)`. Semente base de simulação 20261018, derivada por hash estável de moeda/fold/origem; não depende de W ou seed neural.

Essa interpolação não reproduz extremos dentro de cada minuto, saltos, caudas pesadas ou volatilidade futura variável. É uma hipótese simplificadora do modelo de previsão; **não substituir por ela o rótulo observado de OHLCV**. Avaliar as probabilidades contra o mesmo alvo real, com a mesma convenção de ambiguidade. Qualidade de calibração e erro refletem também essa limitação. AR(1) é um comparador simples; Mamba versus LSTM é a comparação que controla as entradas detalhadas e o treinamento neural.

Qualificação numérica: em 32 origens de desenvolvimento igualmente espaçadas por moeda, escolhidas por índice temporal antes de observar escores, comparar 4.096 contra 16.384 trajetórias aninhadas, nos três H. Exigir diferença absoluta ≤ 0,03 em pelo menos 95% das combinações origem/classe/H. Falha bloqueia o aceite numérico e exige revisão registrada, sem escolher o orçamento que maximiza desempenho. Medir custo, processar em lotes e interromper cada percurso após resolver todos os H; Monte Carlo não é gratuito e não entra na contagem de ajustes neurais.

Simular trajetórias é uma forma de transformar um modelo estocástico em distribuição preditiva; as hipóteses acima são escolhas deste projeto, não uma propriedade universal de AR(1). [Referência sobre previsão por simulação e hipóteses dos resíduos](https://otexts.com/fpp2/prediction-intervals.html).

## 9. Política econômica fixa

Avaliar cada moeda/modelo/W/H/seed como estratégia separada. Capital inicial ilustrativo de **10.000 USDT**, sem juros sobre caixa. Uma posição por vez, sem pirâmide, sem reaproveitar capital já comprometido e sem somar retornos de estratégias sobrepostas como se fossem uma única carteira.

Custos convencionais de referência, **não cotação da tarifa atual de uma conta**: taxa `f = 0,001` por lado (10 bps) e slippage adverso `s = 0,0005` por lado (5 bps). Sem desconto por token. Compra: `A × (1+s)`; venda: `B × (1−s)`, com taxa em cada lado. B é o preço bruto de saída da seção 4.

Definir retorno líquido nominal de um limite b, incluindo aquisição e venda:

`R_b = (b/A) × (1−s) × (1−f) / [(1+s) × (1+f)] − 1`.

Na origem, entrar somente se estiver em caixa e:

1. `p_superior >= 0,60`;
2. `p_superior × R_U + (1−p_superior) × R_L > 0`;
3. demais requisitos causais/de calendário forem atendidos.

O segundo critério trata nominalmente todo resultado que não seja superior como stop. Evita operar um alvo estreito cujo ganho seria consumido pelos custos e dispensa inventar retorno esperado da expiração. É um **filtro nominal conservador**, não prova de esperança matemática positiva: probabilidades podem estar erradas, gaps podem ultrapassar o stop e preenchimentos são aproximados. Não calibrar 0,60 olhando resultados de teste. O prazo de 1h pode gerar poucas ou nenhuma entrada após custos; publicar esse resultado, sem alargar barreiras ou reduzir taxas retrospectivamente para forçar operações.

Com patrimônio E em caixa, o desembolso total de entrada é:

`N = E × min(1, 0,01 / (−R_L))`; quantidade `q = N / [A × (1+s) × (1+f)]`.

Assim o risco de stop nominal é de até 1% do patrimônio, com investimento limitado a 100% e sem empréstimo. Barreiras mais largas levam a posições menores; risco não é comparado usando alavancagem oculta. Gaps e execução pior podem exceder 1%. O saldo não investido permanece em caixa. Após a venda, somar ao caixa `q × B × (1−s) × (1−f)`.

Abrir apenas em uma origem estritamente posterior ao instante em que a saída anterior é conhecida; não reentrar retroativamente na mesma origem. Uma ordem pendente também ocupa a vaga. Operações ignoradas enquanto há posição não desaparecem da avaliação preditiva, apenas não são transações da estratégia.

Concatenar folds em ordem cronológica, mantendo o capital acumulado e trocando o modelo nas fronteiras; as regras de expiração impedem posições atravessando fronteiras. Mostrar resultados individuais e concatenados. Cada seed produz sua curva; não selecionar a melhor nem transformar três seeds em ensemble não planejado.

**Sensibilidade de custos:** taxa 0,002/lado e slippage 0,001/lado, mantendo previsões, regra de sinal e frações de exposição calculadas no cenário base. Aplicar a mesma fração ao patrimônio corrente do cenário agravado e recalcular q com seus custos de compra, sem gastar mais caixa que o disponível. Recontabilizar com os custos agravados; não recalibrar limiar ou fração de risco para recuperar lucro. Custos alteram patrimônio, mas não os limites brutos ou horários de toque. Identificar este cenário como sensibilidade, não segunda estratégia otimizada.

Controles econômicos: (a) aplicar a mesma regra de barreiras, calendário e dimensionamento sem filtro preditivo, entrando quando estiver em caixa; (b) comprar com todo o capital na primeira origem causalmente elegível de cada bloco e manter até o open do último minuto antes do fim do bloco, com custos de entrada/saída; (c) caixa, retorno zero. Concatenar também os capitais dos controles entre blocos. Não são novas arquiteturas. O controle (a) identifica se filtrar entradas acrescenta valor à própria regra de saídas; as exposições diferentes devem ser reportadas.

A simulação mantém quantidades fracionárias e taxas descontadas em USDT. Não reconstrói livro de ofertas, impacto dependente de tamanho, fila, mínimos de ordem ou regras históricas de arredondamento da corretora. Portanto, avalia utilidade sob um modelo de custos declarado, não certifica que cada ordem seria executável com esse preenchimento. O valor de 10.000 USDT é uma escala da simulação, não recomendação de capital. Não converter retorno em USDT automaticamente em retorno em USD ou BRL.

## 10. Métricas e análise sem seleção de vencedores

### 10.1 Previsão

Métrica principal: **log-loss multiclasse**, menor é melhor. Métricas secundárias: Brier (soma dos três erros quadráticos por origem), balanced accuracy multiclasse, macro-F1, precisão/recall por classe, matriz de confusão e calibração com dez faixas de probabilidade de largura 0,1. Mostrar quantidade de observações e frequência de cada classe. Para log-loss, usar `max(p_classe_verdadeira, 1e-7)` somente no cálculo do log, sem mudar a decisão.

Classificação por argmax; empate exato resolve pela ordem fixa 0, 1, 2. Se uma classe não ocorrer em um recorte, marcar sua métrica e a BA completa como indisponíveis, sem alterar silenciosamente o conjunto de classes. Frequências de treino com suavização 0,5 por classe servem como referência probabilística constante, sem outra arquitetura.

Uma referência de 1/3 para balanced accuracy requer as três classes presentes e não substitui log-loss ou comparação pareada. Acurácia isolada não demonstra calibração ou utilidade econômica.

Comparações principais: Mamba menos LSTM e Mamba menos AR(1), sempre nas mesmas origens. Para resumir efeitos de W, comparar 24 versus 168 dentro da mesma moeda/H/fold/seed. Apresentar cada H separadamente antes de agregar: ele muda tanto a duração como a largura. Não pressupor uma ordem de volatilidade das quatro moedas; descrevê-la com os dados.

Resumo global: primeiro média entre seeds para cada célula/fold, depois média com pesos iguais entre 24 células e folds. Também fornecer escores por origem e tamanho dos recortes para permitir outras leituras, sem substituir a análise principal depois de ver o resultado. AR(1) repetido entre W/seeds não gera réplicas independentes.

### 10.2 Operações

Retorno líquido e curva de patrimônio; custos acumulados; número de entradas; percentual de origens aproveitadas; tempo exposto; duração realizada; proporção de saídas por cada motivo; ganho/perda médios; taxa de acerto econômico; profit factor (indisponível se denominador zero); drawdown. A classe superior não equivale automaticamente a ganho líquido positivo.

Marcar posições a mercado em cada fechamento de minuto, com valor de liquidação após custos. Reportar máximo drawdown dessa série e uma medida conservadora de pior marca intraminuto com o low observado enquanto a posição estava aberta. No minuto da saída, não incluir extremos que possam ter ocorrido depois dela: usar o preço de saída e marcar a incerteza de ordenação; não afirmar que OHLCV recupera drawdown contínuo exato. Curvas somente de operações encerradas não bastam para medir risco durante a posição.

### 10.3 Dependência e incerteza

Origens horárias com prazo semanal compartilham grande parte do futuro; não tratá-las como ensaios independentes. Para intervalos descritivos de diferenças médias, bootstrap por blocos temporais de **14 dias**, 2.000 réplicas, dentro de cada fold, mantendo os mesmos dias para moedas/modelos/contextos/seeds. Usar blocos móveis contíguos de dias UTC completos, amostrados com reposição e truncados ao número de dias original; não atravessar fronteiras entre folds. Intervalos percentis de 95%: quantis 2,5% e 97,5% das réplicas. Semente 20261018.

Para log-loss/Brier, calcular a média dos escores entre seeds e reagrupar por dia de origem, preservando contagens para recomputar médias. Para finanças, reamostrar retornos diários de cada estratégia/seed já simulada com os mesmos blocos, calcular as métricas por seed e então tirar sua média. Não compor uma curva a partir da média diária de retornos entre seeds, pois isso introduziria uma carteira não planejada; não inventar novos sinais reordenando operações. Reportar sensibilidades com blocos de 7 e 28 dias e todas as estimativas, sem escolher o intervalo favorável. São intervalos condicionais ao conjunto de previsões e ao período observado; não capturam toda a incerteza de reestimar modelos ou mudar de regime. [Bootstrap de séries temporais: documentação arch](https://arch.readthedocs.io/en/stable/bootstrap/bootstrap_examples.html).

Publicar tabelas completas e gráficos dos efeitos de contexto, prazo e moeda, inclusive ausências e falhas. Não declarar cada célula uma descoberta confirmatória a partir de dezenas de testes isolados. A grade explora padrões predefinidos; não procurar a combinação de maior retorno final e apresentá-la como uma estratégia validada sem outra avaliação. [Risco de seleção em backtests: Bailey e coautores](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf).

## 11. Contrato executável e evidências

A configuração de referência é `configuracoes/ciclo_001.json`. O pacote `barreiras/` concentra coleta, transformação, rotulagem, folds, treino, AR(1), operações, métricas e auditoria. As CLIs devem validar versão e configuração e rejeitar campos desconhecidos. Não aceitar um argumento e ignorá-lo silenciosamente.

Cada tentativa possui identidade do ciclo/configuração/célula/dataset/código/ambiente, snapshot do protocolo, scalers, épocas, checkpoint, previsões com timestamps, probabilidades das três classes, rótulos observados, ordens e resultados. Arquivos parciais não contam como execução concluída. Falhas geram registro com causa; a repetição corrigida tem nova identidade. Os modelos das duas redes começam com pesos novos em cada fold.

O dataset é independente do modelo: suas features são causais e não normalizadas globalmente. Scalers são artefatos do ajuste de cada fold. A origem, entrada, expiração máxima, saída observada e limite do ajuste ficam preservados para auditoria.

## 12. Ordem de execução e aceite

1. Validar os contratos com testes de casos-limite e testes de vazamento por perturbação do futuro. Testar toques isolados/duplos, latência, expiração, gaps, custos, caixa e sobreposição.
2. Coletar/reutilizar dados 1m, auditar checksums e cobertura, executar a pipeline e gerar contagens comuns às quatro moedas.
3. Qualificar ambiente Mamba oficial/CUDA e AR(1); registrar versões, opções numéricas, recursos e resultados dos testes.
4. Executar primeiro BTCUSDT/W24/H24/DB1/seed42 pareado e o caso longo BTCUSDT/W168/H168/DB1. Usar configuração real do ciclo, sem reduzir épocas ou amostras para chamar um teste rápido de avaliação científica.
5. Recarregar checkpoints, reproduzir previsões, recalcular métricas e auditar simulador e cortes temporais. Só promover a execução a auditada quando as verificações correspondentes passarem.
6. Executar a grade inicial DB1–DB4; comparar moedas/contextos/prazos e documentar padrões, limitações e custo. Publicar também células desfavoráveis, falhas e situações sem operação.
7. Formular os próximos ciclos de melhoria com o desenvolvimento; reservar a avaliação final para o fim da pesquisa.

O pesquisador autorizou o agente a executar essas etapas nesta sessão. Não é necessário pedir confirmação repetida. Isso não elimina os gates científicos nem autoriza abrir B1–B4 antes de congelar o estudo.

## 13. Ciclos de melhoria e configurações do Mamba

A primeira grade estabelece uma referência, não o encerramento do trabalho. O objetivo é buscar uma configuração melhor e documentar como cada decisão foi tomada.

Antes de cada ciclo, registrar em `historico/ciclos/`: identificador, hipótese, motivo, configuração completa, ciclo de referência, fator alterado, orçamento, períodos/seeds, critério de comparação e regra de parada. Configurações executadas são imutáveis. Registrar tentativas interrompidas e desfavoráveis junto às bem-sucedidas.

Sequência recomendada, sem executar automaticamente um produto cartesiano:
- Contexto e prazo: examinar as 24 células iniciais e sua estabilidade entre os quatro folds.
- Capacidade do Mamba: estudar largura, quantidade de camadas e tamanho do estado; por exemplo 32/64, 1/2/4 camadas ou estados 8/16/32, alterando primeiro um fator por ciclo.
- Dinâmica local: kernel convolucional e expansão; declarar efeito em parâmetros, memória e tempo.
- Otimização/regularização: learning rate e dropout, com orçamento igual e seleção pela validação.
- Confirmação no desenvolvimento: repetir candidatos selecionados nas seeds 17/42/2026, mantendo todas, antes de congelar a escolha final.

Esses valores são um catálogo de hipóteses futuras, não configurações já executadas nem autorização para procurar indefinidamente. Mamba/LSTM seguem pareados quando a hipótese requer mesma entrada ou regra de treino. Alterar apenas um parâmetro interno do Mamba constitui ablação dessa arquitetura; declarar a mudança de capacidade, sem afirmar orçamento ou quantidade de parâmetros idênticos à LSTM.

Critério principal inicial: menor log-loss média nos folds de desenvolvimento, com métricas econômicas e risco como segundo eixo. Ganho em acurácia sem melhora probabilística ou econômica não constitui vitória universal. Reportar troca entre qualidade, risco e custo computacional. Não mudar a métrica de seleção depois de conhecer o resultado de um ciclo.

Os testes DB são fora do treino de seus folds, mas fazem parte do **desenvolvimento consultado repetidamente**. Walk-forward evita olhar o futuro ao ajustar cada modelo; sozinho não remove viés de seleção acumulado entre dezenas de tentativas. Quantidade de tentativas e escolhas deve aparecer no relatório final.

B1–B4 ficam fechados durante essa busca. Depois de abertos, uma alteração guiada por seus resultados é um novo estudo retrospectivo e precisa de outro período para confirmação independente. A remoção de arquivos não apaga exposição humana anterior aos dados; a situação de exposição deve ser declarada sem reconstituir relatórios removidos.

Se aparecer vazamento ou defeito, marcar a tentativa como inválida, explicar o impacto e gerar execução corrigida. Não editar previsões ou trocar o checkpoint retrospectivamente para melhorar o placar.
