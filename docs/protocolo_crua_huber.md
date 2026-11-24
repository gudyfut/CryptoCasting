# OHLCV cru com Huber: complemento fatorial controlado

Versão1,03/11/2026. ADR0021. O pesquisador autorizou explicitamente iniciar a combinação OHLCV cru+Huber com oito seeds, incluindo referências compatíveis caso faltassem. As três referências já existem nos mesmos quatro blocos e oito seeds; não serão repetidas. Orçamento novo: **32 ajustes principais+1controle real B1/42,total33**, dois ajustes sintéticos de qualificação sem mercado e192simulações novas. Heranças:96ajustes principais, quatro Naive e600simulações, formando128resultados principais e792carteiras comparáveis. Sem novas moedas, arquiteturas, taxas, indicadores, política operacional, busca de delta ou seeds adicionais.

## Pergunta, antecedentes e limites

A combinação de entrada crua e perda Huber melhora a previsão terminal24h do Mamba16? Efeitos individuais favoráveis não garantem combinação favorável: o efeito da perda depende da representação. A rodada Huber `10dac17ea9df2c540c57` encontrou pequena melhora média sem atender seu critério de incerteza; a rodada de entradas `76f6c437e70eaaa605ad` não confirmou vantagem da crua sobre a relativa. Esta hipótese foi formulada após consultar2024/2025 e permanece retrospectiva, sem holdout novo, garantia de significância ou lucro.

Completar o fatorial2×2, sem reexecutar células anteriores:

| Entrada | MSE supervisionada |2×Huber(delta1) |
|---|---|---|
| Relativa/log com zscore de treino |32herdados da ADR0019 |32herdados da ADR0019 |
| OHLCV cru |32herdados da ADR0020 |**32novos** |

São oito seeds por combinação e bloco, não oito treinos no estudo inteiro. A herança exige fontes/publicações íntegras, mesmos calendários, origens/alvos, escalas de alvo, arquitetura e receita efetiva. Referências em divisão antiga única não são usadas no pareamento. Controles reais nunca entram nas médias.

## Dados, fatores fixos e treinamento

BTCUSDT Binance Spot, candles1h,contexto168h, horizonte24h, origens horárias. Na entrada crua: O/H/L/C em USDT e volume base em BTC, sem log, timestamp, indicadores ou zscore de X. Preservar valores e disponibilidade dos artefatos crus já publicados na ADR0020; não recoletar nem gerar dados com outra identidade. O alvo permanece `ln(C[t+24h]/C[t])`, padronizado somente pelo treino. A LayerNorm interna da arquitetura permanece e não deve ser confundida com padronização dos canais de entrada.

Mamba-1 oficial CUDA, largura32, duas camadas, estado16, convolução4, expansão2, dropout0,1, pré-LayerNorm,20.257parâmetros. AdamW constante0,0002,weight_decay0,001 com isenções oficiais A_log/D,batch64,microbatch32,clipping1,máximo100épocas e paciência10. Mesma inicialização/ordem de seed, contratos e função de avaliação das rodadas anteriores. Única mudança científica frente à receita crua/MSE é a perda2×Huber(delta1 no alvo padronizado), usando a função congelada da ADR0018. Seleção e parada sempre pelo menor MSE global real de validação; empate conserva primeira época. Sem seleção por Huber,MAE,teste ou lucro.

Datas UTC semiabertas, treino expansivo iniciado em01/01/2021:

| Bloco | Fim treino/início validação | Fim validação/início teste | Fim teste |
|---|---|---|---|
| B1 |01/10/2023 |01/01/2024 |01/07/2024 |
| B2 |01/04/2024 |01/07/2024 |01/01/2025 |
| B3 |01/10/2024 |01/01/2025 |01/07/2025 |
| B4 |01/04/2025 |01/07/2025 |01/01/2026 |

Pesos novos por bloco/seed; mesmo alvo/escalas de treino dos artefatos anteriores. Purga24h: destino estritamente anterior ao fim de cada partição. Contextos causais podem atravessar o início da partição. Sem interpolação ou seleção pela magnitude futura. Não reaproveitar checkpoint treinado com futuro para datas anteriores.

Seeds17/42/2026/7/123/31415/271828/161803, ordem42→17→2026→7→123→31415→271828→161803. Executar primeiro B1/crua_Huber42 principal e sua repetição real de controle; exigir mesma época,diferença máxima de previsão1e−5 e relativa de MSE de validação1e−4 antes das outras seeds. Cada checkpoint tem recarga exata individual nas três populações. O controle é orçamento adicional separado, não nona seed. Reprovação interrompe; não repetir até passar.

## Qualificação, identidade e preservação

Código `experimentos/crua_huber/`,testes `tests_crua_huber/`,configuração `configuracoes/crua_huber_001.json`,registros `registros/crua_huber/`,entrada `python -m experimentos.crua_huber`. Ler os dois fechamentos originais, host/processos/logs e conferir hashes antes de executar. Qualificação exige Mamba oficial/CUDA, forward/backward/atualização com entrada crua de escala realista, dois ajustes sintéticos reproduzidos, recarga, testes da diferença única/grade/contrastes/seleção/contabilidade/publicação completa artificial. Dados reais são conferidos sem treinar nessa etapa.

Preparar não treina. Depois da qualificação, congelar fontes, configuração, protocolo, ambiente, dados herdados, orçamento, grade e qualificação com ID próprio. Vincular ao ID a autorização literal deste pedido; não solicitar novo aceite já concedido. Não editar treinadores, representações ou executores encerrados. Preservar fontes atuais e copiadas, todos os checkpoints/resultados/tentativas, publicações e relatórios das duas rodadas. Conferência nova usa verificador novo; sem regenerar hashes para aceitar divergência.

Lock exclusivo/host/boot/PID impedem duplicação; processo vivo não se duplica. Falhas preservam tentativa/logs e interrompem. Não existe retomada automática. Uma futura retomada exige investigação explícita, integridade e preservação, sem ampliar escopo. Executor iniciado/concluído não é chamado para refazer relatório. Publicação possui ação/lock/processo/recibos separados e nunca chama treinador.

## Métricas e quatro contrastes fixados antes dos novos resultados

Primário: MSE de teste no contraste crua/Huber−crua/MSE, isolando a perda na entrada crua. Peso igual nos quatro blocos e média das oito seeds dentro de cada um. Reportar também validação,RMSE,MAE,viés,acerto direcional/balanceado,habilidadeNaive,erros extremos e associação diária. Todas as seeds são mantidas. Médias de modelos individuais, não ensemble.

Família fixa de quatro contrastes:

1. `huber_na_crua`:crua/Huber−crua/MSE, principal.
2. `crua_na_huber`:crua/Huber−relativa/Huber.
3. `combinacao_menos_referencia`:crua/Huber−relativa/MSE.
4. `interacao`:(crua/Huber−crua/MSE)−(relativa/Huber−relativa/MSE).

Interação negativa significa benefício além da soma dos efeitos na escala aditiva de MSE; positiva significa efeito combinado menos favorável que essa soma. Não prova mecanismo universal ou lucro. Não somar melhorias percentuais dos estudos anteriores para prever o novo resultado.

Bootstrap pareado de seeds/dias,2.000réplicas,seed20261105,sequências circulares14dias, sensibilidades7/28. Mesmos índices de seeds sorteados para todas as combinações e quatro blocos; dias amostrados dentro de cada bloco, sem atravessar fronteiras; blocos não são sorteados como mercados independentes. Publicar IC95% descritivo e **IC98,75% Bonferroni** para quatro contrastes. Decisão negativa exige média<0 e limite superior corrigido<0; positiva exige média>0 e limite inferior>0; demais inconclusivas. Inconclusivo não demonstra igualdade. Resultado claramente superior às três referências exige os três contrastes simples corrigidos inteiramente negativos, sem promoção automática. Magnitude e consistência importam além do sinal estatístico; não redefinir “expressivo” pelo resultado observado.

Intervalos condicionais a estes períodos/modelos não cobrem integralmente histórico compartilhado de treino, seleção adaptativa ou regimes futuros. Oito seeds não garantem certeza. Comparações anteriores mantêm seus recibos/critérios e não são reescritas com o novo ajuste de multiplicidade.

## Simulações secundárias e fechamento

Mesmo motor Spot congelado `backtest_carteira/` da execução8ec8a66648313caa48e3,Smart2% e diária24,cenários ideal/base/agravado,decisão00UTC e execução00:01. Capital10.000USDT independente por bloco;sem alavancagem,short,stop,funding ou alterações de limiares/custos. Usar somente população operacional/colunas conhecidas; máscara de calendário origem+24h<fim do bloco, igual à ADR0019. Não selecionar dias pelo alvo. Preservar regra da última sessão excluída e liquidação terminal+1minuto.

32modelos novos×2políticas×3custos=192carteiras novas. Herdar384carteiras das duas versões relativas,192crua/MSE e24benchmarks comprar/manter/caixa, total600herdadas e792comparáveis. Não repetir simulações ou treinos herdados. Lançamentos novos são reconstruídos pelo auditor independente; risco por minuto e custos/exposição separados de erro de previsão. Carteiras não compõem uma série contínua de dois anos.

Fechamento exige32principais novos,1controle aprovado,96herdados,128resultados principais,192simulações novas+600herdadas,mesmas populações,seleção/recarga/hashes/métricas/contrastes e preservação antes/depois. Relatório único `docs/resultados_crua_huber.md`,cronologia em `docs/andamento.md`,catálogo/estado atualizados. Arquivos locais não certificam backup remoto. Não comprar computação ou executar ordens reais. A autorização termina neste complemento, sem nova busca ou promoção automática.
