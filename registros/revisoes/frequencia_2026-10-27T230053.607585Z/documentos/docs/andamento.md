# Andamento do estudo de retorno em 24h

## Revisão de frequência e configurações em 27/10/2026

O pesquisador solicitou procurar erros e melhorias, em particular a possibilidade de emitir previsões a cada 24h. Foi realizada uma revisão de código, literatura primária e artefatos, sem novos treinamentos. O [relatório de diagnóstico](diagnostico_frequencia_e_configuracoes.md) separa candle horário, contexto, horizonte de 24h, frequência das origens e atualização dos pesos. A simulação Spot existente já opera com uma decisão diária.

O [diagnóstico posterior](../registros/revisoes/frequencia_2026-10-27T230053.607585Z/resumo.json) conferiu 1.216 resultados e as épocas dos 1.152 ajustes neurais, recalculou o MSE em todas as origens e em cada horário diário, e estimou intervalos pareados por blocos. O recorte principal foi 00 UTC, previamente usado pela simulação; nenhum horário foi escolhido pelo teste. Em 2024–2025, Naive=100: LSTM passou de 100,005 na avaliação horária para 100,423 na diária; Mamba corrigido, de 101,272 para 101,905. No recorte diário, os intervalos favorecem LSTM/Naive frente ao corrigido; LSTM versus Naive continua inconclusivo. Avaliar diariamente não resolveu a diferença; o efeito de **treinar** com origens diárias continua não testado.

Não foi encontrado novo erro nas verificações de alvo, alinhamento, fronteiras, seleção de época e MSE. Os 17 testes da referência e sete da extensão passaram novamente; três testes do diagnóstico também passaram. A auditoria identificou limitações: forte sobreposição dos alvos horários, queda de aproximadamente 24 vezes na quantidade de exemplos ao usar origens diárias, efeito sobre orçamento por época, sinais compatíveis com sobreajuste e adaptação Mamba com pós-normalização diferente do empilhamento de referência da biblioteca. Essa adaptação está conforme o protocolo executado; seu efeito não foi isolado e não foi classificada como bug comprovado.

Foram preservados código, plano anterior ao cálculo, hashes das fontes lidas, tabelas, intervalos, logs de testes, cópias dos módulos Mamba inspecionados e figura PNG/PDF com inspeção visual. Fechamento em [recibo da revisão](../registros/revisoes/frequencia_2026-10-27T230053.607585Z/fechamento_revisao.json). O catálogo conecta essa revisão aos dois estudos existentes; não a conta como novo treinamento. As propostas de frequência, normalização e entradas no relatório não alteram o protocolo vigente e não constituem nova grade autorizada. B1–B4 permanecem períodos conhecidos e retrospectivos para novas hipóteses.

## Organização e rastreabilidade conferidas em 27/10/2026

A pedido do pesquisador, foi revisada no notebook a reorganização recebida do outro dispositivo, no commit `9af48a933e39b962f0cc789966d096d3387d6e84`. A separação entre guia AGENTS, decisões ADR, cronologia, evidências e artefatos foi mantida. A [ADR 0004](adr/0004-rastreabilidade-de-ciclos.md) documenta o complemento: [catálogo de estudos](../registros/catalogo_estudos.json), [procedimento para mudanças](registro_de_experimentos.md) e [modelo de proposta](modelos/proposta_experimento.md). São registros de organização, não autorização ou execução de uma nova grade.

O catálogo liga o ciclo histórico de barreiras, a referência de retorno24 e a extensão controlada, preservando seus layouts. O ciclo 002 de barreiras permanece classificado como proposta não executada. Para consultar o início da evolução, usar o [relatório arquivado do ciclo 001](../arquivo/estudo_barreiras_2026-10-20/projeto/historico/analises/ciclo_001_resultados.md), sua [proposta posterior](../arquivo/estudo_barreiras_2026-10-20/projeto/historico/ciclos/ciclo_002_proposto.md) e as [decisões de reformulação](decisoes.md); o catálogo não cria retroativamente pré-registro ou aprovação.

Foi executada `python manutencao/auditar_catalogo.py --integridade --exigir-completo`, com [recibo próprio](../registros/revisoes/catalogo_2026-10-27T224713.066988Z/resumo.json): **8.743 hashes conferidos, sem divergências ou ausências no escopo**. A cobertura foi exata: 832 resultados auditados da referência, 384 corrigidos e dois controles da extensão, sem células inesperadas ou duplicadas. As duas tentativas interrompidas permanecem contabilizadas. Foram verificadas fontes atuais/congeladas, identidade/configuração, dataset e arquivos das quatro publicações (216 por fase da referência; 101 por fase da extensão). Esta revisão não repetiu inferência ou cálculo de métricas, nem reauditou integralmente brutos e legado; a auditoria científica anterior continua sendo a fonte dessas verificações. Sete testes do novo verificador passaram, incluindo duplicidade, herança incorreta, ausência parcial e divergência CRLF/LF.

As 30 fontes científicas atuais conferem com seus hashes congelados. Destas, 28 coincidem em bytes com HEAD; `previsao24/coleta.py` e `experimento_penalizacao/treino.py` diferem do blob do commit apenas por finais de linha. O achado é local e não certifica o checkout do desktop. `.gitattributes` passou a preservar bytes de fontes, registros e arquivo histórico, sem renormalização, alteração de fontes ou atualização de hashes antigos. As regras anteriores de converter os registros para LF foram substituídas, pois os snapshots podem conter CRLF original.

Antes da revisão textual, foram preservados e conferidos os oito documentos vinculados por hash ao fechamento da extensão em [snapshot anterior](../registros/revisoes/organizacao_2026-10-27T223818/inicio.json). O fechamento antigo não foi sobrescrito. O [recibo desta organização](../registros/revisoes/organizacao_2026-10-27T223818/resumo.json) relaciona as verificações e as versões documentais posteriores.

O [inventário local](../registros/revisoes/organizacao_2026-10-27T223818/volumes_locais.json) mediu 518.553.824 bytes no dataset processado, 438.401.967 na referência, 230.780.121 na extensão e 169.714.342 no portal: cerca de 1,36 GB, sem incluir os brutos ou o arquivo histórico. No instante da auditoria havia 6.449 arquivos elegíveis ainda não rastreados, somando 27.767.463 bytes; esse número aumenta com os próprios recibos novos. Elegibilidade não significa commit, envio ou backup. Nenhum commit/push/Release foi feito nesta revisão. A preservação externa e a restauração no outro dispositivo continuam pendentes, conforme a [política](armazenamento_e_reproducao.md).

O acompanhamento agendado da penalização foi encerrado após a entrega final, conforme [recibo](../registros/penalizacao/acompanhamento_encerrado.json). O próximo ciclo científico deve partir de pergunta e configuração próprias, com registro dos resultados já conhecidos e autorização correspondente. A organização permite evoluir dados, entradas e parâmetros sem substituir o passado; não transforma a exploração de B1–B4 em confirmação independente.

## Extensão concluída e conferida em 27/10/2026

A execução `7868a4d847c1410fc681` terminou os treinamentos às 20:33:49 UTC e a consolidação/preservação às 20:39:05 UTC (17:39:05 em São Paulo). Foram 384 ajustes corrigidos completos e dois controles aprovados. As duas tentativas interrompidas continuam no histórico; houve 388 tentativas de mercado e 386 conclusões auditadas, sem escolha pelo resultado. As duas publicações contêm, cada uma, 192 ajustes novos, 416 resultados herdados, 192 pares e 96 cenários financeiros. O recibo `preservacao_depois.json` confirma os 7.082 arquivos da referência.

A conferência posterior independente foi aprovada em `registros/revisoes/penalizacao_2026-10-27T210853.776756_0000/resumo.json`: cobertura exata, fontes, dataset, artefatos, populações, métricas, escalas/configurações de todos os checkpoints corrigidos, grupos do otimizador, 60 intervalos temporais e 9.022 registros de operações nos dois cenários de custos. Esses registros financeiros repetem os sinais nos cenários base/agravado; não representam 9.022 operações independentes. O verificador não repetiu inferência neural; a recarga exata de cada ajuste consta da auditoria original por tentativa. A primeira tentativa dessa revisão falhou apenas ao salvar o recibo, por conflito de variável; código e diagnóstico preservados em `registros/revisoes/penalizacao_2026-10-27T210425.386923_0000/`. Somente o verificador foi corrigido e repetido.

Resultado: a correção diminuiu o MSE em 0,0068% no desenvolvimento de 2023; na avaliação retrospectiva de 2024–2025 aumentou 0,0505%, com intervalo incluindo zero. O corrigido permaneceu com MSE 1,2665% maior que LSTM e 1,2719% maior que Naive. Não houve solução para a desvantagem do Mamba nem evidência de rentabilidade consistente. A mediana da política Spot ficou em −10,48% na avaliação, embora alguns sinais e resultados individuais tenham mudado. Os períodos já eram conhecidos; não são novo holdout intocado.

O [relatório final da extensão](resultados_penalizacao_mamba.md) contém interpretação, seeds, contextos, simulação, sete entregas da extensão e limitações. Foram geradas e inspecionadas cinco figuras PNG/PDF em `docs/figuras/penalizacao_7868a4d847c1410fc681/`, com manifesto. README, guia AGENTS, plano, auditoria e roteiro de redação foram atualizados. O portal continua apresentando o ciclo original; a extensão está documentada separadamente. Não reexecutar o executor concluído para regenerar relatórios. Redação acadêmica, aceite do orientador, preservação externa e eventual integração da extensão na interface são trabalhos distintos deste fechamento; nenhum novo treinamento foi autorizado por seus resultados.

## Segunda retomada operacional em 27/10/2026

Após novo reinício informado pelo pesquisador, a verificação encontrou o executor encerrado e 299 ajustes corrigidos concluídos, além dos dois controles. O último progresso era de 11:23:40 UTC; a tentativa BTC/B3/W336/seed2026 tinha log até 11:26:14 UTC, sem conclusão auditada. O Windows informou início da sessão atual às 15:15:51 UTC. Foram preservados os eventos de desligamento inesperado e reinício por atualização; seus horários não permitem atribuir com certeza a causa exata da parada do treinamento.

A auditoria de retomada terminou aprovada às 15:28:47 UTC: 299 resultados corrigidos e dois controles íntegros, dataset verificado, fontes atuais e congeladas conferidas, 7.082 arquivos da referência preservados, nenhum executor ativo e trava livre. Evidências em `registros/incidentes/penalizacao_retomada_2026-10-27T152403.256870_0000/verificacao.json`, com os eventos em `eventos_windows.json` e cópia dos registros e da tentativa incompleta. O verificador operacional passou a receber a evidência de cada incidente como argumento, evitando reutilizar a descrição do primeiro reinício; nenhuma fonte científica foi alterada.

A execução foi retomada pela mesma entrada congelada. Os resultados auditados são revalidados e reaproveitados; somente a tentativa incompleta é repetida com a mesma seed/configuração, mantendo a tentativa anterior no histórico. Restavam 85 ajustes corrigidos na conferência. A conclusão da grade e a comparação científica final ainda estavam pendentes.

## Retomada operacional em 27/10/2026

Às 04:05 UTC, a verificação encontrou o executor anterior encerrado, com 56 ajustes corrigidos e dois controles concluídos. O último log da tentativa incompleta era de 27/10 às 00:43:34 UTC; o Windows informou início da sessão atual em 27/10 às 00:50:47 UTC. Isso evidencia um reinício posterior ao último log, sem estabelecer a causa exata do encerramento do treino. Não houve exceção final registrada pelo executor.

Antes da retomada, foram preservados os registros de processo, progresso, aprovação dos pilotos e todos os arquivos da tentativa incompleta. A conferência de 27/10 às 04:07:54 UTC aprovou as fontes atuais e congeladas, o dataset, os 7.082 arquivos da referência, os 56 resultados corrigidos e os dois controles. Não havia executor ativo e a trava estava livre. Evidências em `registros/incidentes/penalizacao_retomada_2026-10-27T040636.095845_0000/verificacao.json`.

A retomada usa a mesma entrada e identidade congelada, reutiliza os resultados auditados e repete somente o ajuste incompleto com a mesma seed e configuração. A tentativa anterior permanece preservada; não houve alteração científica ou seleção pelo desempenho. O acompanhamento agendado verifica o estado a cada meia hora, mas depende do computador e do aplicativo disponíveis; não substitui o programa de treinamento.

## Extensão iniciada em 26/10/2026

O pesquisador autorizou corrigir a penalização do Mamba e executar a grade original de Mamba novamente, mantendo os demais fatores. O protocolo separado está em [penalização do Mamba](protocolo_penalizacao_mamba.md); a revisão das estruturas está em [auditoria de configuração](auditoria_configuracao_penalizacao.md).

O código da correção e sete testes específicos foram implementados e aprovados. A execução foi iniciada com preservação, verificação das referências, repetição dos 17 contratos, qualificação CUDA e congelamento antes do treinamento de mercado. O estado exato deve ser consultado em `registros/penalizacao/execucao.json` e no `progresso.json` da execução apontada; antes de existir esse ponteiro, a preparação é registrada em `registros/penalizacao/preparacao_*/estado.json`.

São planejados 384 treinamentos corrigidos e dois controles de reprodução. Não se afirma conclusão da nova grade nesta entrada. Os resultados e a cronologia abaixo pertencem ao ciclo original, concluído em 21/10. As referências antigas não serão apagadas nem substituídas. A extensão usa períodos já consultados e é retrospectiva.

Congelamento da extensão: `7868a4d847c1410fc681`, com treinamento de mercado iniciado em 26/10 às 23:43:29 UTC. A preparação verificou as referências, passou nos 17 testes existentes e sete específicos, qualificou 12 combinações de modelo/contexto/política e comprovou equivalência exata da atualização em um teste de agrupamento com penalização uniforme. O manifesto inicial contém 7.082 arquivos preservados. Evidências em `registros/penalizacao/preparacao_2026-10-26T233400.168859_0000/`; o recibo final de preservação será emitido somente após execução e conferência.

Os dois controles reais BTC/DB1/seed42, W24 e W336, e os dois pilotos corrigidos foram aprovados. A reprodução dos controles manteve a época escolhida, com diferenças máximas de previsões abaixo de 1,25e-8 de log-retorno e variação relativa de MSE abaixo de 1,19e-8. Esses controles não são uma nova avaliação científica independente. A grade corrigida segue em execução; `piloto_aprovado.json` e os recibos `controles/celulas/*/tentativa_001/reproducao.json` preservam a evidência.

Foi configurado acompanhamento local para verificar a conclusão, executar as figuras científicas, revisar a documentação e entregar a interpretação final no chat. Registro: `registros/penalizacao/acompanhamento.json`. Não reiniciar um executor vivo; o acompanhamento não autoriza novo experimento além deste protocolo.

Atualização: 21/10/2026. Os horários desta página são UTC.

## Situação do ciclo de referência em 21/10/2026

As oito entregas computacionais estão concluídas e verificadas. Execução `1e7c5ed662fba55ddd25`; dataset `d25f6a93a9900725f51e`. A exportação final terminou às 18:36:54 UTC: **832 resultados auditados em 384 séries**, com os quatro modelos disponíveis. A conferência global e a inspeção da interface foram aprovadas; recibos `registros/auditorias/1e7c5ed662fba55ddd25/fechamento.json` e `registros/interface/aceite_final.json`.

São **768 ajustes neurais** (384 em cada fase), **32 referências Naive** e **32 seleções ARIMA**. Todos os **288 candidatos internos ARIMA** foram válidos. Referências compartilhadas entre contextos e seeds não contam como novos treinamentos. Duas publicações auditadas contêm **424 cenários financeiros e 16.284 registros de operações**; cenários correlacionados não são observações independentes nem uma carteira.

A conclusão da avaliação é: LSTM teve menor MSE que Mamba; a diferença LSTM–Naive foi inconclusiva. Mamba teve erro maior que LSTM, Naive e ARIMA no procedimento predefinido. Mais contexto não trouxe melhoria geral, e a simulação não demonstrou rentabilidade consistente. Ler [avaliação de 2024–2025](resultados_avaliacao.md) e, separadamente, [desenvolvimento de 2023](resultados_desenvolvimento.md).

## Cronologia da execução

| Marco | Evidência e resultado |
|---|---|
| Reformulação em 20/10 | Horizonte fixo de 24h; entradas exclusivamente retornos horários; quatro moedas; contextos 24/72/168/336h; Mamba/LSTM com seeds 17/42/2026; Naive e ARIMA. Fontes e configuração vinculadas à identidade antes do piloto. |
| Preservação histórica | 9.790 arquivos movimentados, 3.031.966.371 bytes, com hashes antes/depois. Recibo `arquivo/estudo_barreiras_2026-10-20/verificacao.json`. Git não foi reescrito. |
| Ambiente e qualificação | RTX 4050 6 GB, WSL, PyTorch CUDA e Mamba oficial; statsmodels 0.14.6. Oito casos CUDA (duas redes × quatro contextos), forward/backward, repetição e recarga aprovados. 17 testes de contrato aprovados, com recibos congelados em `registros/qualificacao/`. |
| Coleta e preparação | 240 arquivos mensais oficiais 1m, 2021–2025, verificados. Lacunas preservadas, sem interpolação; populações causal e observada distintas. Ponteiro `registros/dataset_atual.json`. |
| Piloto real | Quatro ajustes curto/longo auditados e integrados à grade, sem duplicação. Não confundir com os testes sintéticos. |
| Desenvolvimento completo, 21/10 às 06:41:03 | 192 LSTM, 192 Mamba, 16 Naive e 16 ARIMA auditados. Cobertura dos 96 ajustes neurais de cada DB conferida nos recibos `DB1_neurais.json` a `DB4_neurais.json`. |
| Publicação de desenvolvimento, 06:43:59 | 416 resultados, 144 candidatos ARIMA válidos, 212 cenários financeiros e 2.418 registros de operações conferidos. Manifesto e auditoria em `registros/analises/1e7c5ed662fba55ddd25/desenvolvimento/`. |
| Congelamento, 06:47:38 | Configuração, fontes, dataset, qualificações, declaração humana e auditorias de desenvolvimento fixados em `congelamento.json`. Avaliação iniciada em seguida, sem revisão pelo placar de desenvolvimento. |
| B1, auditoria às 08:46:57 | 96 ajustes neurais, cobertura exata e integridade aprovadas; recibo `B1_neurais.json`. |
| B2, auditoria às 11:05:22 | Outros 96 ajustes neurais aprovados; recibo `B2_neurais.json`. |
| Interrupção, 12:09:37 | Depois de auditar o ajuste 220 da avaliação, ocorreu `PermissionError` ao substituir o arquivo de progresso. Executor/coordenador terminaram com falha. Causa exata não identificada; contenção transitória Windows/WSL é hipótese. |
| Retomada explícita, 12:14:39 | Processos encerrados confirmados. Fontes, grade e hashes dos 416 resultados DB e 220 ajustes B existentes conferidos. Logs/estados da falha preservados no diretório do incidente. Código científico original reutilizou resultados íntegros e executou somente os restantes. |
| Continuidade, 12:16:58 | Os 636 registros anteriores, suas auditorias e o congelamento mantiveram os hashes. Recibo `continuidade.json` no diretório do incidente. Releitura de checkpoints não representa novo treinamento. |
| B3, conclusão 14:12:24; auditoria 14:13:47 | 96 ajustes neurais, cobertura exata e integridade aprovadas; recibo `B3_neurais.json`. |
| B4, conclusão 18:21:49; auditoria 18:22:56 | Últimos 96 ajustes neurais aprovados; recibo `B4_neurais.json`. Total de 768 ajustes neurais nas duas fases. |
| Avaliação completa, 18:25:01 | 384 ajustes neurais e 32 referências; todos os 144 candidatos ARIMA válidos. Recibo `avaliacao_concluido.json`. |
| Publicação da avaliação, 18:28:46 | 416 resultados, 212 cenários financeiros e 13.866 registros de operações conferidos. Manifesto/auditoria em `registros/analises/1e7c5ed662fba55ddd25/avaliacao/`. |
| Exportação final, 18:36:54 | 832 resultados, 384 séries com Mamba/LSTM/Naive/ARIMA; ambas as fases completas. A continuação sequencial terminou. Exportação não substitui o aceite visual. |
| Interface e aceite | Placar global e filtrado, intervalos 7/14/28 dias, contextos, seeds, ARIMA e simulações conferidos. Gráficos reais em desktop/celular, busca de data, navegação e recarga verificados. Build/lint, dois testes das séries e dois da API aprovados. Fechamento final confirmou 832 resultados, 288 candidatos e 9.790 arquivos históricos íntegros; aceite final registrado. |

Os oito recibos de cobertura neural estão em `registros/auditorias/1e7c5ed662fba55ddd25/`. O incidente completo está em `registros/incidentes/retomada_1e7c5ed662fba55ddd25_2026-10-21T121439.243349_0000/`. Não houve revisão metodológica entre B1 e B4, nem exclusão de uma tentativa por resultado ruim.

## Publicações parciais preservadas

A interface foi conferida durante a execução, sem alterar modelos ou regras científicas. Os recibos em `registros/interface/` preservam cada versão: DB2 (194 resultados/97 séries), DB3 (289/145), desenvolvimento completo (416/192), B1 (513/241), B2 (609/289) e B3 (705/337). As primeiras versões identificavam modelos ainda ausentes; nenhuma ausência foi preenchida como previsão zero. Contagens antigas são das respectivas exportações, não do estado final.

Os exemplos reais XRP/DB4, XRP/B2 e XRP/B3 foram conferidos numericamente em desktop/celular. Na conferência completa, XRP/B4/336h/seed2026 apresentou previsões de +0,68% LSTM, +0,17% Mamba, 0,00% Naive e +0,07% ARIMA, para retorno observado −2,87% na origem de 01/07/2025 às 00:00 UTC. O explorador diferencia erro de log-retorno de diferença de retorno simples.

## Convenções de publicação e limites

O auditor financeiro confere horários e cotações diretamente nos minutos do dataset, recalcula quantidades/contas e rejeita operações observáveis descartadas como desconhecidas. Testes suplementares usam dados sintéticos separados e verificam ausências, corrupção e uma alteração proporcional das duas cotações que preservaria o retorno aparente. Esses dados nunca integram o portal ou inventário de mercado.

As curvas financeiras publicadas usam liquidações às 00:01 UTC. Marcas de caixa emitidas às 00:00 pelo simulador, após contabilizar a saída anterior às 00:01, são deslocadas para 00:01 e deduplicadas na apresentação. Nenhuma decisão, quantidade ou retorno muda. O gráfico diário de capital não substitui o percurso de minuto usado no drawdown; fechamentos de minuto não certificam movimentos intraminuto.

O pesquisador declarou que não usou resultados de 2024–2025 para decidir o estudo. A declaração permanece como evidência humana, sem alegação de auditoria universal de exposição histórica. Depois da abertura desses resultados, novas hipóteses nos mesmos períodos são desenvolvimento; precisam de confirmação independente para novas conclusões. Indicadores, candles menores e busca de parâmetros são extensões futuras, sem execução automática.

As oito entregas são operacionais deste protocolo. O prazo acadêmico e o aceite pelo orientador não foram reconfirmados nesta reformulação; não se presume aprovação acadêmica pela conclusão computacional. O cronograma original permanece no arquivo histórico.
