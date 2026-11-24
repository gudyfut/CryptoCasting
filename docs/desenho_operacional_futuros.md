# Pesquisa operacional em futuros — desenho de trabalho

Proposta `operacional_futuros_001`, iniciada em04/11/2026 (Brasília), vinculada à [ADR0028](adr/0028-pesquisa-operacional-futuros.md). **Goal de execução autorizado em05/11/2026, início06:05:40UTC e prazo18:05:40UTC. Executor integrado implementado e em qualificação; início de mercado depende do recibo aprovado e congelamento.** [Estado](../registros/operacional_futuros/estado.json) e [configuração proposta v2](../configuracoes/operacional_futuros_001_proposta.json). A seção10 fecha os detalhes para o goal noturno; o envio do prompt pelo pesquisador será a autorização de execução, não sua simples existência em arquivo.

## 1. Pergunta e separação dos estudos anteriores

Queremos encontrar, dentro de um orçamento limitado, uma combinação de **Mamba, informação de entrada, alvo e política operacional** que produza crescimento líquido do patrimônio com uma relação favorável entre retorno e perdas no caminho. Instrumento: BTCUSDT perpétuo USDⓈ-M da Binance; posições compradas, vendidas ou em caixa. A unidade de comparação é a estratégia completa, não somente o checkpoint neural.

Isso muda o critério da busca: o MSE deixa de ser a barreira de promoção econômica. Os estudos OHLCV e Astra001/002 mantêm seus objetivos, métricas, conclusões e caminhos; a F03 mantém seu motor e resultados. Não reescrever o passado como se tivesse sido selecionado por lucro. O [desenho acadêmico anterior](desenho_ohlcv24.md) continua sendo sua referência. A incorporação desta nova linha ao artigo precisa ser explicitada como ampliação de escopo, sem presumir aprovação do orientador ou alterar o PDF.

A busca Astra002 terminou sem finalista segundo seus critérios preditivos. A [F03](resultados_revisao_operacional.md) mostrou que transferir sinais treinados em Spot para uma estratégia bilateral não assegurou ganho; em vários braços, vendas prejudicaram o resultado. Essas evidências motivam a nova pergunta, mas não fornecem uma candidata operacional já comprovada.

## 2. O que significa melhor: patrimônio, crescimento e drawdown

Usar patrimônio marcado a mercado, incluindo lucro/prejuízo das posições abertas, e descontar comissão, deslizamento e funding. Não medir apenas saldo disponível, operações encerradas ou pico de dinheiro. Sem aportes/retiradas; resultados antes de tributos. Saques ou encerramento após atingir um valor seriam políticas próprias, definidas antes do teste.

Para cada carteira, com duração `D` em dias e patrimônio `E`:

- Retorno líquido: `R = E_final / E_inicial - 1`.
- Crescimento logarítmico diário: `g = log(E_final / E_inicial) / D`; equivalente à média dos log-retornos diários do patrimônio.
- Taxa composta anualizada: `CAGR = exp(365 × g) - 1`. É uma transformação para comparação, não previsão de rendimento anual. Sempre exibir o retorno efetivo e a duração; anualizar trimestres pode amplificar resultados transitórios.
- Drawdown máximo: `MDD = max_t(1 - E_t / max_{u≤t} E_u)`.
- **Calmar no período:** `CAGR / MDD`, com ambos em frações. Usa o mesmo período para numerador e denominador. É uma adaptação por bloco, não a alegação de possuir uma janela convencional de 36 meses.

**Recomendação de seleção operacional: Calmar como compromisso principal, acompanhado obrigatoriamente de crescimento composto e estabilidade.** O escore de uma receita será a mediana dos Calmar das carteiras bloco×seed elegíveis, com cobertura balanceada. A mediana reduz o domínio de um único quociente extremo; também publicar médias, medianas, dispersão e cada célula. Calmar indefinido, empate, carteira sem operações ou drawdown nulo não recebe infinito nem vira vencedora; é caso separado. Empates numéricos usam maior crescimento logarítmico médio e depois menor giro. A precisão do empate será congelada no executor.

Calmar permite que uma estratégia mais arriscada vença se o retorno compensar proporcionalmente: no mesmo ano, 120% de retorno/40% de drawdown = 3, contra 30%/15% = 2. Mas não prova que 40% de queda seja aceitável para uma pessoa. Também pode favorecer uma carteira de lucro pequeno e drawdown muito pequeno. Por isso preservar a **fronteira retorno–drawdown**: mostrar as alternativas que não são simultaneamente piores em retorno e risco, incluindo a de maior crescimento. Não esconder o compromisso em uma nota única.

Picos maiores, isoladamente, não constituem vantagem: 100 → 200 → 80 perdeu 20%; 100 → 110 → 121 ganhou 21%. A segunda teve pico menor. Em contrapartida, aceitar maior oscilação pode compensar quando melhora o crescimento sustentado e a sobrevivência. “Quase nunca zera” não basta para estimar a perda rara que pode destruir muitos ganhos.

O crescimento logarítmico tem fundamento na literatura de crescimento de capital, mas **não penaliza sozinho a trajetória**: dois caminhos com início/fim iguais têm o mesmo `g`, mesmo com drawdowns distintos. Não usar uma fórmula de Kelly alimentada por probabilidades não calibradas para dimensionar posições. A literatura explicita o compromisso adicional entre crescimento e risco de drawdown: [Busseti, Ryu e Boyd](https://web.stanford.edu/~boyd/papers/kelly.html). Definição de Calmar: [Morningstar](https://admainnew.morningstar.com/directhelp/Glossary/Custom_Statistics/Calmar_Ratio.htm).

O pesquisador solicitou uma métrica que balanceie risco e retorno, em vez de escolher o limite sugerido de 25%. **Nenhum teto de drawdown de 20%, 25% ou 30% foi aprovado.** A pesquisa mostrará quedas, duração abaixo do pico, perdas extremas e comprometimento de margem. Seleção acadêmica não autoriza colocar a estratégia em uma conta real.

## 3. Mercado, entradas e tarefas a comparar

O conjunto anterior em `registros/mercado_futuros/estado.json`, identidade `979c54995465216ea020`, tem contrato de **01/01/2024 até 01/01/2026 exclusivo** e permanece intacto. A preparação do goal publicou o complemento2021–2023 `7535d44ba23eb371fe4d`, em [estado próprio de dados](../registros/operacional_futuros/dados/estado.json):1.576.800minutos de negociação/marcação,26.280candles1h e3.285eventos de funding. Arquivos/checksums e complementos oficiais foram preservados, sem interpolar lacunas. [Dados públicos oficiais](https://github.com/binance/binance-public-data) e [API de futuros](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data).

A API não informa markPrice exato em3.100dos3.285eventos de funding do complemento. O dado ausente permaneceNaN, com open/high/low do minuto em colunas separadas. O motor usará marca adversa do intervalo (high se paga,low se recebe), identificada como aproximação em todos os cenários, nunca como preço de settlement exato. A estratégia não recebe esses extremos futuros para decidir entrada/tamanho. Duas tentativas de coleta interrompidas foram preservadas: lacunas de julho2021 recuperadas pela API; cobertura de funding corrigida para aceitar offsets reais de milissegundos sem mudar timestamps originais.

Primeira rodada: BTC, candles de 1h completos, prazo máximo de 24h e contexto inicial de 168h. Contextos candidatos de 24/72/168h; população comum com aquecimento de 336h, incluindo indicadores. Dados para execução e marcação em 1min. Escalas ajustadas somente em T; nenhuma normalização pelo período inteiro. Funding só entra como característica quando seu valor já estava publicado; o funding realizado futuro pertence ao alvo/contabilidade, nunca à entrada.

Comparar duas famílias inicialmente, mantendo a mesma base Mamba oficial CUDA, estado16/AdamW/taxa0,0002 e receita de treinamento identificada:

| Receita inicial | O que a rede estima | Treino/seleção de época | Uso operacional |
|---|---|---|---|
| R0 terminal | Log-retorno do contrato futuro nas próximas 24h | Huber de treino; MSE de V, como a referência anterior | Sinal terminal convertido em decisão por regra explícita |
| P0 resultado da operação | Dois valores: resultado líquido por unidade de nocional de abrir uma compra ou uma venda com saída definida | MSE dos dois alvos padronizados; MSE real médio dos dois canais em V | Escolher o lado com maior resultado previsto positivo, acima da margem de entrada |

R0 herda a **receita**, não pesos nem números de Spot. Reestimá-la no mesmo instrumento, datas e executor da candidata. A mudança R0→P0 é uma comparação de abordagem (alvo, cabeça de saída e perda), não ablação causal de um único fator. MSE de tarefas diferentes não pode decidir qual estratégia ganhou.

P0 usa como rótulo o resultado de uma operação hipotética unitária, executada após o sinal, incluindo saída por stop/take/tempo, preços de execução, comissão e funding até a saída. Não é previsão infalível nem garantia de lucro. O resultado de expirar pode ser positivo ou negativo. Guardar também motivo e tempo da saída. Operações hipotéticas sobrepostas servem de exemplos supervisionados; **a carteira real simulada continua com uma posição por vez**, sujeita a capital, margem e filtros. Custos dependentes de tamanho e arredondamento pertencem à carteira, não podem ser tratados como idênticos ao rótulo unitário.

Barreiras iniciais propostas: volatilidade conhecida `σ24 = std(log-retornos horários das últimas 168h, ddof=1) × sqrt(24)`; distância logarítmica do stop `max(σ24, 0,005)` e take `1,5 × distância_stop`, fixadas na entrada. O piso de 0,5% evita distância nula e é uma escolha de pesquisa, não parâmetro ideal demonstrado. Preços das barreiras são exponenciais dessas distâncias em torno do preço preenchido, invertidos para venda. Prazo termina 24h após a entrada. Não ajustar a volatilidade pela trajetória futura.

**Se stop, take ou horizonte do P0 mudar, o alvo muda:** gerar outra identidade e retreinar. Não reutilizar suas previsões para afirmar que estimavam o payoff de outra regra. Já uma mudança apenas de limiar ou tamanho pode reutilizar as previsões, respeitados os custos do tamanho. Testes de custos estressados mantêm o modelo treinado no cenário base e mudam a execução; não corrigem os rótulos depois de observar o teste.

## 4. Política variável e execução fixa

Astra propõe receitas permitidas; o avaliador continua fechado. A estratégia pode alterar informações causais, contexto, parâmetros permitidos, alvo identificado e política. Não pode alterar datas, métricas, custos, resolução de execução ou regras de preenchimento para melhorar artificialmente o placar.

Primeiro ciclo sem busca de alavancagem: capital inicial 10.000 USDT por carteira independente; nocional de entrada limitado a 95% do patrimônio; uma posição líquida comprada/vendida, sem martingale, pirâmide ou simultaneidade de hedge. Nocional inicial inferior ao patrimônio **não elimina risco de margem**, especialmente em uma venda cujo preço sobe. Não simular futuros como uma venda de moedas já possuídas.

Grade interna proposta: margem adicional de entrada de 0/10/20 pontos-base; risco nominal ao stop de 0,5%/1% do patrimônio; decisão a cada 1h/4h UTC, total **12 políticas por receita**. Tamanho aproximado resulta do orçamento de perda dividido pela distância percentual ao stop, limitado pelo nocional/margem/filtros. Acrescentar custos estimados ao risco antes de arredondar para baixo; gaps podem exceder esse orçamento. R0 usa `exp(previsao)-1` para compra e seu oposto para venda, descontando estimativas causais de comissão/deslizamento/funding; é um escore heurístico terminal, não a esperança exata da operação com barreiras. P0 já estima resultado líquido: não descontar comissão duas vezes. Estimador de funding deve usar apenas taxas publicadas no passado e ficar fixado antes do treino.

Sem posição, abrir o lado com maior escore que supere o limiar; empate entre lados não abre. Com posição, aguardar stop, take ou tempo; sinais novos não abrem operações sobrepostas. Saída pelo sinal oposto, trailing stop ou realização parcial exigem receita/política explícitas posteriores. Uma regra sem operações é resultado real, não motivo para reduzir limiar depois do teste.

Motor novo deve qualificar: disponibilidade do candle antes da decisão; latência de pelo menos 1min; ordem executada no primeiro preço posterior permitido; stops com gap e deslizamento; funding pelo lado/nocional/horário; comissão em cada preenchimento; margem, manutenção e liquidação; filtros de quantidade/preço/nocional; fechamento e taxas no fim do bloco. A reserva F03 não equivale à liquidação oficial. Tabelas históricas indisponíveis precisam ser assumidas e testadas conservadoramente, com limitação explícita, sem certificação de fidelidade exata à exchange.

Base proposta: comissão taker de 0,05% por lado, deslizamento de 0,05% por preenchimento e funding histórico. São hipóteses de pesquisa, não tarifa verificada da conta do pesquisador. Sensibilidades com deslizamento de 0,10% e 0,15%; não usar desconto BNB/VIP sem evidência. Comissões/slippage não podem ser escolhidos pela rentabilidade. Custos da execução e unidade do alvo precisam reconciliar para não duplicar cobranças.

Se stop e take ocorrerem no mesmo minuto sem ordem intraminuto conhecida, assumir stop primeiro e registrar ambiguidade. Não usar o close para inventar o caminho; não escolher preenchimento favorável. Take também usa execução conservadora, sem presumir fila maker. Drawdown usa marcação de 1min, extremos adversos e eventos, além da curva diária; revelar a limitação intraminuto. Não apagar perdas, intervalos ruins ou incidentes. Patrimônio não positivo/liquidação reprova a estratégia e permanece no relatório.

## 5. Separar aprender, parar, escolher política e comparar

Quatro papéis em ordem temporal, limites finais exclusivos:

| Recorte | T: pesos/escalas desde 01/01/2021 até | V: seleção de época | C: seleção da política | S: comparação de receitas |
|---|---|---|---|---|
| D1 | 01/10/2022 | 2022 T4 | 2023 T1 | 2023 T2 |
| D2 | 01/01/2023 | 2023 T1 | 2023 T2 | 2023 T3 |
| D3 | 01/04/2023 | 2023 T2 | 2023 T3 | 2023 T4 |

Reestimar do zero por recorte. V escolhe somente checkpoint; C escolhe uma política por receita/recorte a partir do conjunto de seeds disponíveis, antes de S. As seeds não recebem políticas escolhidas individualmente pelo seu lucro. **Não calibrar uma política conjunta com C de recortes posteriores para avaliar S anteriores.** Ao ampliar de três para oito seeds, recalibrar em C e publicar nova versão de avaliação das oito, preservando a etapa de três.

Purga pelo maior instante de realização dos alvos, incluindo entrada/latência e saída máxima; 24h cravadas podem ser insuficientes quando a entrada ocorre depois da origem. Nenhum rótulo de T atravessa V, de V atravessa C ou de C atravessa S. Contexto anterior pode ser usado por ser passado conhecido. Calendário comum, sem interpolação e sem filtrar exemplos por retorno futuro. Não abrir operações que o calendário já informa não caberem no fim do segmento; intervalo com execução desconhecida invalida a cobertura e exige incidente, não exclusão silenciosa.

Astra recebe somente resumos do desenvolvimento e histórico de suas tentativas. Ver S repetidamente torna S parte da busca, não teste independente. Finalista, procedimento de calibração e motor são congelados antes de quatro blocos retrospectivos:

| Bloco final | T até | V | C | Avaliação |
|---|---|---|---|---|
| B1 | 01/07/2023 | 2023 T3 | 2023 T4 | 2024 S1 |
| B2 | 01/01/2024 | 2024 T1 | 2024 T2 | 2024 S2 |
| B3 | 01/07/2024 | 2024 T3 | 2024 T4 | 2025 S1 |
| B4 | 01/01/2025 | 2025 T1 | 2025 T2 | 2025 S2 |

T começa em 2021 em todos os casos. O algoritmo de recalibração em C permanece fixo; ele pode aprender do passado permitido de um bloco anterior, mas não mudar a receita após seus resultados. Carteiras reiniciadas por bloco; não somar ou compor médias como se fossem uma conta contínua. **2023–2025 já foram consultados.** Nem novos alvos nem novas seeds tornam esses anos intocados. Uma confirmação mais forte exigirá período comprovadamente não usado ou acompanhamento prospectivo com decisões registradas antes de cada resultado.

## 6. Busca limitada, métricas e critérios propostos

Até oito receitas: R0/P0 iniciais e seis propostas locais do Astra. Cada proposta identifica a receita-mãe e a alteração: contexto 24/72/168h; canais OHLCV crus/relativos/padronizados e grupos causais de momentum, volatilidade ou volume; estado16/32; taxa0,0001/0,0002; ou par stop/take de uma lista finita. Fórmulas completas e pares permitidos devem ser enumerados **antes da qualificação**, sem gerar novos graus de liberdade após ver S. Candles15min/4h, horizonte6h, saídas adaptativas e alavancagem ficam para outro ciclo, não combinados silenciosamente nesta primeira busca. A ampliação posterior é possível; cada etapa terá orçamento e identidade.

Todos os resultados, inclusive falhas e regras sem operação, ficam registrados. Inicialmente três seeds pareadas:42/17/2026. Até duas candidatas mais R0 recebem as cinco seeds adicionais7/123/31415/271828/161803. Seleção de receita pelo Calmar mediano em S; curvas completas e fronteira de retorno/drawdown permanecem visíveis. O escore não é uma probabilidade de lucro.

Elegibilidade proposta para promoção: cobertura completa; nenhuma insolvência/liquidação; crescimento logarítmico médio positivo no cenário base e no deslizamento2×; crescimento médio positivo em pelo menos dois dos três S; pelo menos20 operações encerradas por carteira S. São limites de pesquisa predefinidos, não teoremas. Atividade insuficiente recebe esse diagnóstico, sem forçar mais operações. O reforço exige crescimento médio por seed positivo em pelo menos seis das oito seeds; nunca apagar as demais. Se não houver candidata elegível melhor que R0 no escore, encerrar sem nova campeã. A referência pode ser negativa; não inventar uma melhoria por comparação de duas perdas.

Em C, aplicar cobertura, não insolvência, pelo menos20 operações e crescimento médio positivo entre seeds; ordenar as políticas pelo Calmar mediano. Se nenhuma passar, a receita permanece em caixa nesse S e não satisfaz a atividade para promoção. Cenários de estresse são aplicados depois, sem recalibrar o limiar no próprio S. O cenário3× é sensibilidade severa, não nova oportunidade de selecionar política. Na final, reportar tudo, inclusive perda dos critérios que justificaram a promoção; não voltar à busca dentro do mesmo ciclo.

Métricas obrigatórias: retorno líquido efetivo, crescimento composto, Calmar, MDD e tempo de recuperação, quantis das perdas diárias/Expected Shortfall95%, pior bloco/seed, exposição, operações e giro, custos/funding, fração de seeds e blocos positivos. Sortino e Sharpe são diagnósticos secundários, com frequência e autocorrelação explícitas. MSE/MAE/correlação permanecem por tarefa; classificação/calibração só quando a saída realmente permitir. Não chamar escore de retorno de probabilidade.

Médias de oito carteiras não são uma carteira que combina oito modelos. Um ensemble precisa de regra anterior ao teste e simulação própria. Intervalos devem parear seeds e datas, com bootstrap de blocos de dias14 e sensibilidades7/28; preservar retornos diários e extremos intradiários associados aos dias para reconstruir drawdowns coerentemente. Relatar incerteza do crescimento/retorno e do contraste, não somente do quociente. Bootstrap condicional e oito seeds não corrigem automaticamente a busca adaptativa, mudanças de regime ou eventos ausentes. A literatura sobre [sobreajuste de backtests](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) fundamenta a limitação, não uma garantia de eliminá-la.

## 7. Como distinguir habilidade bilateral de uma aposta na alta

Usar sempre o mesmo contrato futuro. Comparações mínimas: estratégia bilateral, somente comprada e somente vendida com regras correspondentes; baselines em caixa, sempre comprado, sempre vendido e tendência causal simples. Baselines passivas têm exposição própria explícita; não são pareamento de risco perfeito. A regra de tendência e seu tamanho serão congelados e não ajustados por S. Naive de retorno zero é diagnóstico preditivo de R0 e equivale a caixa sob a regra de entrada; não exige treino nem uma simulação duplicada.

Publicar a contribuição em USDT e pontos do patrimônio inicial de compras/vendas: preço bruto, comissão, deslizamento e funding. A soma deve reconciliar com o patrimônio final. A contribuição contábil não basta para atribuição causal: remover shorts muda capital, oportunidades e trajetória. Mostrar também retornos por unidade de exposição e diagnósticos de previsão em todas as origens, inclusive as sem operação.

Avaliar lucro, quantidade, exposição e estabilidade do lado vendido separadamente. Uma estratégia pode ser lucrativa e ainda não demonstrar habilidade em quedas. Não impor operações artificiais ou 50% para cada lado; ausência de vendas é falta de evidência bilateral. Não declarar melhoria bilateral apenas porque o resultado total ou o Calmar cresceu. Regimes de alta/baixa são descrição posterior; uma classificação que usa o futuro não pode decidir operações.

## 8. Orçamento proposto, sem autorização de execução

| Etapa | Máximo de ajustes novos |
|---|---:|
| Oito receitas × três recortes × três seeds | 72 |
| Dois controles reais D1/42, R0 e P0 | 2 |
| Duas candidatas + R0 × três recortes × cinco seeds adicionais | 45 |
| Uma candidata + R0 × quatro blocos × oito seeds | 64 |
| Dois controles reais finais B1/42 | 2 |
| **Teto condicional** | **185** |

Controle não entra nas médias. Não repetir R0 se coincidir com a candidata; sem elegível, etapas condicionais não ocorrem. Até oito chamadas ao proponente: uma qualificação técnica, seis receitas aceitas e uma tentativa técnica adicional; falha/cota esgota a etapa, sem API paga. Teto de24h para exploração/reforço proposto; a final tem orçamento separado e estimativa baseada em benchmark. Não prometer185ajustes em um dia. Só comparar coortes completas ao atingir o prazo, sem favorecer a receita cujo treino acabou primeiro.

Avaliações lógicas máximas: por carteira neural,12 políticas em C e5 avaliações em S/B (bilateral base, bilateral deslizamento2×/3×, somente compra base, somente venda base). Exploração:72×17=1.224; reforço, recalibrando as oito seeds:72×17=1.224; final:64×17=1.088; quatro baselines × sete segmentos × três custos=84. **Total3.620 avaliações lógicas**; reaproveitamento de C idêntico pode reduzir execuções físicas, com herança registrada. Controles verificam reprodução, sem carteiras adicionais. Reamostragens estatísticas não são novas operações de mercado. Grade detalhada, fórmulas restantes, testes e benchmark ainda precisam fechar o protocolo executivo antes de treinamento.

## 9. Organização, contratos e condições para implementar

Separação lógica no catálogo e nos caminhos, sem mover ou copiar os grandes artefatos encerrados:

| Responsabilidade | Base existente | Trabalho necessário para esta linha |
|---|---|---|
| Observações públicas de futuros | `mercado_futuros/` | Coleta2021–2023 e contratos históricos; nova identidade |
| Canais, alvos e divisões | `entradas_modelo/` | Contrato de dois alvos de payoff e disponibilidade temporal |
| Rede | `modelos/` | Adaptador de saída por tarefa, sem editar núcleos congelados |
| Treino/checkpoints | `treinamento/` | Seleção por V, máscaras/purga corretas e recarga |
| Contabilidade/políticas | `simulacao_operacoes/` | Nova versão com barreiras/margem; F03 permanece imutável |
| Coordenação | `experimentos/operacional_futuros/` | Apenas verificador de proposta/dados implementado; executor, fila e isolamento ainda pendentes |
| Evidências | `registros/operacional_futuros/` | Estado de proposta, preservação e futura qualificação/autorização |
| Artefatos científicos | Futuro `dados/experimentos/operacional_futuros_<id>/` | Só criar identidade executiva após qualificação/congelamento |

Identificar separadamente `dataset_id`, `entrada_id`, `alvo_id`, `receita_id`, `politica_id`, `motor_id` e `ciclo_id`. Mudança de alvo não pode se esconder sob alteração de política. Astra não recebe acesso a editar o motor, dados finais ou recibos; propostas rejeitadas e mensagens ficam registradas. Pesos são ajustados pelo treinamento, não editados arbitrariamente pelo agente.

Antes de qualquer treino: completar as fórmulas/grade e custo estimado; conferir dados; testar causalidade com perturbação do futuro, purga e disponibilidade; verificar equivalência entre rótulo unitário e operação isolada; testar caminhos conhecidos para compra/venda, stops/gaps/funding, arredondamento e margem; conferir patrimônio independentemente; qualificar CUDA, atualização, repetição e recarga; conferir fontes/PID/locks; congelar identidade e vincular autorização compatível. Não chamar executor encerrado para reutilizar resultados. A autorização atual cobre organizar e desenhar, não iniciar este orçamento.

Esta proposta busca um resultado economicamente melhor entre alternativas examinadas. Pode terminar sem estratégia aprovada. Não transforma retrospectiva em garantia de lucro, não prova risco de ruína baixo pela ausência de quebras observadas e não promete encontrar o melhor modelo possível.

## 10. Preparação do goal noturno

Pedido posterior: preparar o necessário e fornecer um prompt de goal para o pesquisador enviar. [Prompt pronto](../registros/operacional_futuros/goal_noturno.txt); sua redação não ativa goal, autorização de treino ou automação. A [configuração v2](../configuracoes/operacional_futuros_001_proposta.json) enumera os detalhes abaixo antes de consultar novos resultados. A versão1 está preservada em `registros/operacional_futuros/preparacao_goal/antes/`. Não transformar essa proposta em configuração executiva alterando seu campo de autorização; criar a receita de execução e vincular o pedido efetivamente recebido à identidade congelada.

**Janela de uma noite:** até12h desde o recebimento do goal, incluindo implementação restante, qualificação, ajustes e fechamento. É mais restrita que o teto geral24h da proposta; não se soma a ele. Reservar30min para conferência/relatório e não iniciar ajuste que não caiba no tempo restante, considerando seu limite máximo45min. Coortes incompletas permanecem parciais, sem ranking ou promoção. Prazo não reinicia após reinicialização. Teto185ajustes/3.620avaliações continua condicional; não é meta de gasto nem promessa de conclusão em12h. Ao fim da janela, a entrega pode conter a grade parcialmente realizada, claramente identificada, ou um impedimento técnico concreto; nunca chamar o estudo completo quando faltarem células.

**Receita base fechada:** Mamba oficialCUDA, largura32,dois blocos,estado16,d_conv4,expand2,pré-LayerNorm,dropout0,1,poolingúltimo. AdamW0,0002,decay0,001 respeitando `_no_weight_decay`,betas0,9/0,999,eps1e-8,100épocas máximas,paciência10,batch64,microbatch32,clipping1,float32 semAMP,sem scheduler. Perda média por elemento/canal, acumulada corretamente; escolha de checkpoint somente emV. `modelos/mamba_operacional.py` mantém o núcleo anterior intacto, com uma ou duas saídas; smoke testsCUDA não qualificam ainda o treinador inteiro.

**Grade finita de representações:** crua =O/H/L/C/V sem escala da base; relativa =log(O/H/L/C sobre C_anterior)+log1p(V); log_niveis =log(O/H/L/C)+log1p(V). Bases relativa/log_niveis padronizadas emT. Grupos opcionais: momentum log(C/C_lag) em24/72/168h; volatilidade dos retornos horários em24/168h,ddof1; volume log1p(V) menos sua média em24/168h. Extras sempre padronizados emT, inclusive com base crua. Escalas por canal,ddof0; escala constante vira1. Todos os cálculos usam apenas candles completos e aquecimento comum336h; escalas do alvo também próprias por canal,estimadas só emT.

**Demais fatores locais:** contexto24/72/168h,estado16/32,taxa0,0001/0,0002,ativação individual dos três grupos. Pares de barreiras do payoff `[k_stop,razão_take_stop]`, em notação JSON: `[1.0,1.0]`, `[1.0,1.5]`, `[1.0,2.0]`, `[1.5,1.5]`. Stop log=max(k_stop×σ24,0,005);take=razão×stop. R0 mantém barreiras iniciais; P0 muda alvo/identidade/treino junto com barreiras. Uma proposta muda um fator identificado e tem pai; R0/P0 iniciais continuam comparação de abordagem. Nenhuma abertura de grade durante o teste final.

**Detalhes operacionais fechados como hipóteses de pesquisa:** teto adicional50.000USDT por posição,passo0,001BTC,tick0,1USDT,mínimo100USDT; não são filtros históricos certificados. Funding esperado de R0 usa última taxa já publicada com atraso de1min,24/intervalo conhecido e sinal do lado; não usa a taxa futura realizada. Baseline de tendência usaEMA24/EMA168 causal,adjust=False,min_periods168,decisão1h e posição retida,invertendo somente na mudança de sinal. Carteiras passivas não realavancam a cada candle. Entrada/tamanho usam preço conhecido antes do fill; gaps não autorizam redimensionar retrospectivamente. Purga mínima1442min, além da conferência de timestamps reais dos alvos; mesmos limites entre famílias.

**Margem e funding incertos:** fechamento prudencial em patrimônio/nocional≤2%,com custos,tentativa preservada e candidata reprovada. Essa é uma regra da estratégia simulada, não liquidação oficial Binance. Não impor que o simulador certifique tiers históricos indisponíveis nem fingir que os certificou; registrar a hipótese e o alcance. Eventos sem ordem intraminuto conhecida: stop primeiro; se saída coincidir com settlement, não conceder receita de funding ambígua e contabilizar débito possível, explicitando a convenção. Evitar novas entradas em minuto de settlement pela regra fixada; não usar uma escolha posterior favorável.

**Ranking:** exigir também Calmar mediano positivo para promoção; empate absoluto≤1e-10, depois crescimento médio e menor giro. Calmar indefinido em uma célula impede omiti-la da agregação. Se R0 for inelegível ou tiver Calmar indefinido, candidata ainda precisa cumprir todos os critérios positivos; referência negativa/indefinida não é pontuada artificialmente com infinito e não exige relaxar gates. Publicar o motivo da ausência do contraste. Não continuar buscando até encontrar lucro.

**Marcos do goal:** reconferir preparação/host/PID/fontes; implementar adaptador de entradas/alvos,treinador,motor e auditor independente; testes causais/contábeis eCUDA; benchmark e fila/prazos/locks; congelar/vincular autorização recebida; controles reais antes das demais seeds; explorar/reforçar; congelar candidata e avaliar retrospectiva somente se elegível e houver tempo; fechar recibos/relatório. Não parar só porque foi criado um plano ou iniciado um processo. Não modificar fontes históricas ou o coletor já publicado; extensões novas têm fontes próprias.

Verificação disponível agora: `python -B -m experimentos.operacional_futuros conferir --integridade`. Testes: `python -B -m unittest discover -s tests_operacional_futuros -v`; executar noWSL comCUDA para que os testes neurais não sejam ignorados. Métricas genéricas estão em `avaliacao/metricas_operacionais.py`. A integração, motor, auditor e bootstrap estão implementados; sua qualificação completa e identidade são verificadas pelos recibos da sessão, sem inferir conclusão a partir deste texto.

## 11. Fechamento técnico antes do mercado

A mensagem que ativou o goal autoriza implementar, qualificar, congelar e executar sem novo pedido de confirmação. O relógio único da sessão está em `registros/operacional_futuros/sessao_goal.json`; não reinicia após preparar a identidade. A proposta v2 continua identificada como proposta: a autorização efetiva fica no congelamento e no ponteiro de execução, não pela edição retroativa de seu JSON.

Entradas/escalas estão em `entradas_modelo/operacional_futuros.py`, adaptador em `modelos/mamba_operacional.py`, ajuste em `treinamento/operacional_futuros.py`, motor e auditor em `simulacao_operacoes/operacional/`, coordenação em `experimentos/operacional_futuros/`. O coletor já publicado e os executores anteriores não foram alterados. Os alvos de payoff são exemplos unitários sobrepostos, com tempo/motivo de realização; as carteiras têm somente uma posição.

A quantidade usa o último fechamento conhecido ajustado pelo deslizamento/tick **estimados**, antes de conhecer o fill. A quantidade não é recalculada após o gap: entrada que violar teto/filtros é rejeitada e registrada. O cenário de custo muda o fill e sua estimativa causal para dimensionamento, mantendo previsões, limiar e regra; portanto também pode mudar quantidades e rejeições. Não é promessa de posições idênticas entre cenários de custo. Tick de preço é arredondado contra cada ordem, quantidade para baixo. Take é preenchido com custo taker, sem bônus por gap favorável; não há suposição de execução maker grátis.

O patrimônio incorpora comissão de entrada, funding e marcação de posições abertas. Com OHLC de minuto, a ordem intraminuto de extremos não é observada: para o drawdown, registra-se pico favorável e depois extremo adverso como **envelope conservador**, inclusive no minuto de saída protetiva. Isso pode superestimar a queda ocorrida antes do stop, e é explicitado nos resultados. O fechamento prudencial usa esse envelope; não é certificação de liquidação da exchange. A aproximação permanece igual entre receitas. Bootstrap comprime cada dia em fator final, máximo, mínimo e drawdown interno, suficientes para reconstruir o drawdown sem perder a ordem relevante entre picos e vales.

A regra de atividade de pelo menos20 operações em cada carteira S é aplicada aos cinco cenários predefinidos, inclusive os diagnósticos de compra/venda isoladas. Esses diagnósticos alteram oportunidades e capital; não identificam causalmente a qualidade de previsão de quedas. A atribuição de PnL comprado/vendido dentro da carteira bilateral também é publicada. Caixa e Calmar indefinido não recebem score artificial.

Controles de mercado usam tolerância absoluta1e-5 nas previsões reais e mesma época selecionada, fixadas antes do primeiro ajuste, como a tolerância de reprodução histórica. A repetição sintética usa1e-7; recarregar um checkpoint individual exige previsões exatamente iguais. A qualificação preservou um incidente de unidade temporal do fixture pandas3 e a constatação de diferenças CUDA de ordem1e-10 entre repetições; nenhum incidente desses envolveu treino de mercado. O recibo final deve aprovar as fontes exatas que serão congeladas.

Fechamento posterior usa `python -B -m experimentos.operacional_futuros publicar`, somente após encerramento. Recalcula MSE, confere arquivos/checkpoints e reconcilia cada ledger sem treinar outra vez. A publicação preserva coortes incompletas, separa controles, médias de carteiras e baselines e calcula IC condicional pareado de seeds/dias14 com sensibilidades7/28. Qualquer correção após congelamento exige outra identidade, não atualização dos hashes para aceitar divergência.
