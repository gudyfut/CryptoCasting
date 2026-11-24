# Andamento do CryptoCasting

## Huber em blocos concluído e conferido

Execução `10dac17ea9df2c540c57`:64ajustes principais e2controles reais,4Naive e408simulações. [Relatório](resultados_huber_blocos.md), [estado](../registros/huber_blocos/estado.json). Sem nova rodada automática;2024/2025 retrospectivos.


## MSE/Huber em blocos e oito seeds autorizado e qualificado em03/11/2026

Treino real confirmado noB1/MSE/seed42: primeira época em 03/11/2026 02:18:33 de Brasília, PIDLinux319. Evidência em `registros/huber_blocos/inicio_confirmado.json`; grade em andamento, não resultado final. Os dois controles reais ainda são etapas seguintes antes das outras seeds.

Execução `10dac17ea9df2c540c57`,85fontes atuais/copiadas e6.082arquivos anteriores conferidos. Autorização vinculada à identidade em `registros/huber_blocos/autorizacao.json`. Lançamento em 03/11/2026 02:15:58 de Brasília, com logs em `registros/huber_blocos/lancador.*.log`. A checagem inicial precede lock e primeira época; lançamento não é prova de início real. Processo de segundo plano, sem tarefa agendada.

O pesquisador autorizou ampliar as duas versões para aproximadamente oito seeds, podendo usar blocos, e iniciar após o desenho. ADR0019 delimita quatro blocos expansivos de2024/2025, oito seeds por versão/bloco,64ajustes principais+2controles reais B1/42, total66; quatro Naive e408simulações. Sem novos LSTM/ARIMA, indicadores ou outras hipóteses. Oito seeds não garantem certeza. [Protocolo](protocolo_huber_blocos.md), [estado](../registros/huber_blocos/estado.json).

Quatro artefatos novos de entradas em `registros/huber_blocos/entradas.json`, com scalers ajustados a cada treino. Qualificação `a1048044401c4a6393ab66b8d071b5b8`:27testes sem skips, quatro ajustes sintéticos MSE/Huber, reprodução nos limites anteriores e recarga exata. Fórmulas, alvos, scalers e matrizes reais reproduzidos independentemente nos quatro blocos, com igualdade exata das matrizesfloat32. Fontes encerradas/receitas anteriores permanecem intactas. Preparação/congelamento em andamento; ainda não comprova treino real. Quatro dias experimentais e duas semanas de artigo, conforme prazo informado pelo pesquisador.


## Perda Huber Mamba16 concluída e conferida

Revisão independente em03/11/2026: 76fontes atuais/copiadas,350arquivos publicados e5.533anteriores preservados; métricas59séries/intervalos recalculados e saldos54carteiras reconstruídos sem treinar ou simular novamente. [Recibo](../registros/perda_huber/entrega/20261103/conferencia.json). MSE médio−0,483% na validação e−0,058% no teste; IC95% principal inclui zero. Seis seeds melhoraram na validação e cinco no teste. SpotR0 base−18,46%→−10,34%; Smart−8,79%→−8,65%, com drawdown/exposição maiores e nenhuma seed Smart lucrativa. Referência MSE mantida; Huber é candidata para avaliação temporal futura, sem nova rodada automática. Interpretação/figura no relatório único, versão automática anterior preservada.

Execução `ed8e55ff978b2742c200`: seis ajustes e53referências herdadas,54carteiras Smart. Taxa constante, perda supervisionada, seleção por MSE, checkpoint/recarga, métricas, ordens e preservação conferidos. [Resultados](resultados_perda_huber.md), [estado](../registros/perda_huber/estado.json). Sem promoção automática ou novos treinos;2024/2025 retrospectivos.


## Perda Huber Mamba16 autorizada e qualificada em 02/11/2026

Treinamento real confirmado: processo LinuxPID472, primeira época registrada em 2026-11-03T02:29:33.032535+00:00 (02/11,23h29 de Brasília), seed42, perda Huber e taxa constante0,0002. Evidência em `registros/perda_huber/inicio_confirmado.json`. Esta observação não é conclusão da grade; o processo segue em segundo plano com seis ajustes delimitados e publicação posterior automática.

Execução congelada `ed8e55ff978b2742c200`, com76fontes atuais/copiadas e5.533arquivos anteriores conferidos. Autorização vinculada em `registros/perda_huber/autorizacao.json`. Lançamento local em 2026-11-03T02:20:03.9076251Z (02/11,23h20 de Brasília), com logs em `registros/perda_huber/lancador.*.log`. O executor confere integridade antes de adquirir lock e iniciar épocas; lançamento não comprova a primeira atualização. Sem tarefa agendada.

O pesquisador autorizou seis ajustes com 2×Huber(delta1 no alvo padronizado), contra as seis referências MSE existentes. Dados, arquitetura, AdamW/taxa constante0,0002, lotes, clipping e parada mantidos; seleção/primário continuam MSE real de validação. [ADR0018](adr/0018-perda-huber-mamba16.md), [protocolo](protocolo_perda_huber.md), [estado](../registros/perda_huber/estado.json). Código em `experimentos/perda_huber/`, entrada própria por módulo para preservar os lançadores congelados.

Qualificação `f3ce78930c9f471ba0458c9f2f65ebb3`: 19 testes aprovados, sem skips, quatro ajustes sintéticos com reprodução/controle quadrático nos limites e recarga individual exata. Igualdade das demais instruções conferida por AST. Uma falha de pré-checagem foi preservada em `registros/perda_huber/incidentes/`: o comparador identificou a mudança no texto de uma exceção; a mensagem original foi restaurada antes da qualificação, sem ajuste de mercado. Preparação/congelamento em andamento; qualificação não comprova início real. Nenhuma referência ou scheduler encerrado foi reaberto.2024/2025 seguem retrospectivos.


## Taxa dinâmica Mamba16 concluída e conferida

Execução `99884456ac71fedfd9b0`: seis ajustes e53referências herdadas,54carteiras Smart. Taxas por época,seleção,checkpoint/recarga,métricas,ordens e preservação conferidos. [Resultados](resultados_taxa_dinamica.md), [estado](../registros/taxa_dinamica/estado.json). Sem promoção automática ou novos treinos;2024/2025retrospectivos.

Conferência independente posterior em 02/11/2026: 74 fontes atuais/copiadas, 350 arquivos publicados e 4.998 anteriores preservados; métricas das 59 séries, médias, intervalos por blocos e trajetória de taxa/seleção recalculados sem repetir o executor. [Recibo](../registros/taxa_dinamica/entrega/20261102/conferencia.json). MSE médio da candidata +0,292% na validação e +0,226% no teste; intervalos incluem zero. Seis seeds pioraram na validação, três melhoraram no teste. Manter a referência 16/0,0002; nenhuma nova rodada iniciada. O relatório único recebeu a interpretação, preservando a versão automática anterior. Smart teste −8,49% contra −8,79% da referência; nenhuma candidata Smart lucrativa. SpotR0 −8,77% contra −18,46%, com giro/custos menores, sem inferir melhoria preditiva ou promover por esse resultado secundário.


## Organização e taxa dinâmica Mamba16 em30/10/2026

Lançamento local confirmado em2026-10-30T09:19:27.5667233Z, com saídas em `registros/taxa_dinamica/lancador.*.log`; processo/progresso distinguem a conferência prévia da primeira época real. Sem tarefa agendada ou duplicação de outro treinamento.

Navegação consolidada em README/plano/índice documental, com versões anteriores em `registros/taxa_dinamica/organizacao/antes/`. Códigos/artefatos encerrados permaneceram nos caminhos originais. Novos ciclos usam `experimentos/`, análises em `analises/`. Caches descartáveis inventariados; exclusão bloqueada por política automática, nenhum arquivo científico removido.

Diagnóstico de53séries concluído sem treino: [relatório](diagnostico_previsoes.md), [fontes e resultados](../registros/diagnosticos_previsoes/atual.json). Mamba16/seis seeds: no teste00UTC, Spearman médio0,0014 e47,62%de erros menores que Naive, sem alegação de significância. Não mudou a hipótese ou critério depois deste achado.

Execução `99884456ac71fedfd9b0` qualificada e preparada:18testes e três ajustes sintéticos (duas repetições da candidata e controle sem redução contra treinador anterior). Recarga individual exata e reprodução dentro dos limites. 4998arquivos anteriores conferidos; 74fontes atuais/copied congeladas. Autorização vinculada para seis ajustes,53referências herdadas e54carteiras Smart secundárias. [Protocolo](protocolo_taxa_dinamica.md), [estado](../registros/taxa_dinamica/estado.json). Preparação não comprova início/resultado de mercado; processo/progresso/logs são a evidência.2024/2025 conhecidos; sem nova grade automática.


## Otimizador CryptoMamba concluído e conferido

Execução `6829c5fa076dc8c0e0ac`: seis AdamW novos e59referências herdadas; 54simulações Smart na política anterior, sem nova busca. [Resultados](resultados_otimizador_cryptomamba.md), [estado](../registros/otimizador/estado.json). Fontes/configurações/checkpoints/recarga/métricas e preservação conferidos; Adam original e Mamba16 continuam intactos.2024/2025 retrospectivos; sem promoção automática.


## Ablação Adam→AdamW autorizada, qualificada e preparada em30/10/2026

Lançador local confirmado em2026-10-30T06:38:25Z (03:38:25 de Brasília), com saídas redirecionadas em `registros/otimizador/`. A conferência inicial do executor precede a primeira época; o lançamento por si só não comprova treino concluído ou gradiente já aplicado. Processo/progresso e logs por seed são a evidência dinâmica.

Execução `6829c5fa076dc8c0e0ac`: somente o otimizador do CryptoMamba adaptado muda; seis ajustes e59heranças, com54avaliações Smart secundárias nas regras anteriores.18testes aprovados e duas repetições sintéticas dentro dos limites; recarga individual exata. Conferidos 4405arquivos anteriores e as19fontes do backtest precedente. [Protocolo](protocolo_otimizador_cryptomamba.md), [estado](../registros/otimizador/estado.json) e ADR0016. Duas falhas de preparação sintética foram preservadas (expectativa numérica do teste e seleção indevida da partição treino no novo publicador); correções anteriores ao congelamento, sem treinamento real/alteração da receita.

Autorização humana registrada e vinculada à identidade. Preparação não comprova início de mercado; consultar processo/progresso. Adam original, Mamba16, estudos de taxa/estados e369simulações antigas permanecem intactos. Não ampliar orçamento por resultados, selecionar seed por lucro ou chamar2025de holdout novo.


## Backtest de carteira concluído e conferido em 30/10/2026

Grade `8ec8a66648313caa48e3` concluída às 02:44:15 de Brasília: 369 simulações, 17 séries herdadas e zero treinamentos/inferências novas. Smart, Vanilla, controle de saída diária, caixa, comprar/manter e controle de previsão constante foram mantidos no orçamento original. As 369 carteiras têm verificador de lançamentos independente. Conferência posterior de 19 fontes atuais/copiadas, 84 insumos, 2.585 arquivos publicados e 1.163 anteriores preservados; médias e três contrastes bootstrap recalculados sem repetir o executor. [Relatório único](resultados_backtest_carteira.md), [estado](../registros/backtest_carteira/estado.json) e [recibo posterior](../registros/backtest_carteira/entrega/fechamento_20261030/conferencia.json).

Mamba16/seis seeds no teste: Smart −8,79%, saída diária no mesmo motor −18,47%, Vanilla −0,80%; controle Smart constante −8,66%, comprar/manter −5,80% e caixa 0%. Nenhuma seed Mamba16/Smart foi lucrativa; IC95% do contraste com viés inclui zero. Smart aumenta exposição/drawdown frente à saída diária; não atribuir toda diferença ao custo. Vanilla/LSTM +1,58% em três seeds, porém duas carteiras fizeram a mesma única compra e uma não operou. Em 2024, desenvolvimento, Smart/Mamba16 +81,45% contra comprar/manter +118,69%. Não promover por lucro isolado ou tratar como holdout novo/walk-forward.

A tentativa inicial interrompida antes da primeira simulação permanece intacta. O novo leitor alterou apenas a cópia da matriz pandas; o protocolo congelado, a correção, as fontes antigas e os testes sintéticos estão identificados nos registros. Relatório automático e figuras originais preservados; revisão de apresentação usa os mesmos dados. Fonte/receita/modelos/previsões dos ciclos anteriores não mudaram. Não há novo treinamento autorizado por este fechamento.


## Backtest de carteira retida autorizado e iniciado em30/10/2026

O pesquisador solicitou investigar as estratégias do CryptoMamba e avaliar lucro com nossos modelos. [ADR0015](adr/0015-backtest-carteira.md) e [protocolo](protocolo_backtest_carteira.md) fixaram Smart2%/Vanilla1%,controle diária24,17séries e369simulações com custos,sem novos treinos/busca.12testes sintéticos aprovados na revisão. A tentativa `b9fce5ae0300ce91ba69` falhou na leitura antes de qualquer simulação; a cópia explícita da matriz foi implementada em nova camada, mantendo todas as fontes antigas. Execução atual `8ec8a66648313caa48e3`, com fontes/configuração/previsões/preços congelados, em [registros próprios](../registros/backtest_carteira/estado.json). Não houve mudança das políticas por resultados;2024/2025seguem retrospectivos.


## Interpretação independente do CryptoMamba adaptado

Fechamento científico em30/10/2026: MSE médio de validação −0,279% e de teste +0,280% frente a16/0,0002, sem IC95% primário inteiramente favorável. Cinco checkpoints deram retorno exatamente constante no teste; o sexto teve oscilação reduzida. Seis seeds com zero operações/retorno Spot zero. Referência16mantida; Adam→AdamW na adaptação é hipótese proposta, não nova execução. Fontes/dados/checkpoints/publicações anteriores e53resultados preditivos/financeiros herdados conferidos sem alteração.

Conferidas59séries por somas independentes; médias3/6seeds, seis diagnósticos inicial/checkpoint, figuras PNG/PDF e análise externa de Naive preservados. [Relatório único](resultados_cryptomamba_adaptado.md) e [análise com verificador](../registros/cryptomamba/revisoes/3dbd58da46d148dfb6371934ed7f6acf/analise.json). Nenhum novo ajuste, seleção, alteração de receita ou promoção automática. Encerramento da revisão em2026-10-30T03:30:27.034847+00:00.


## CryptoMamba adaptado concluído e conferido

Execução `35dd98141ee20d9b8885`:6novos ajustes e53referências herdadas; métricas de retorno/preço,contraste primário,pesos e preservação conferidos. [Resultados e análise](resultados_cryptomamba_adaptado.md), [recibos](../registros/cryptomamba/estado.json). Arquitetura/receita foram adaptadas conforme protocolo; não é reprodução literal do artigo.2024/2025retrospectivos; sem nova promoção automática.


## CryptoMamba adaptado preparado e executor lançado em29/10/2026

Diagnóstico externo paralelo, sem treino: persistência nos splits públicos do CryptoMamba foi calculada por dois procedimentos, incluindo as classes originais emfloat32, com350alvos de teste. RMSE1568,50USD/MAE1091,90USD/MAPE1,973%, numericamente abaixo de1598,1/1120,7/2,034%da tabela do artigo. Isso não certifica igualdade da população exata/checkpoints publicados nem diferença significativa; não misturar com a rodada Binance. [Fontes, fórmulas e conferência](../registros/cryptomamba/diagnostico_naive_publico.json). A receita local não foi alterada após esse achado.

Treinamento de mercado efetivamente iniciado às23:03:20de Brasília após conferência de integridade, com PID318/hostMuriloRFM e lock exclusivos; seed42primeira na ordem congelada. O estado e o catálogo foram atualizados a partir dos artefatos, sem alterar fonte/receita.

Execução `35dd98141ee20d9b8885`, fontes117/configuração/protocolo/qualificação/contratos/53heranças congelados. Autorização vinculada para seis ajustes, sem repetição das referências. Lançador WSL iniciado às23:00:20de Brasília; verifica integridade antes de obter lock e ajustar seed42. Progresso/PID/logs em [estado](../registros/cryptomamba/estado.json); lançamento não equivale a treinamento concluído.670arquivos anteriores conferidos sem alteração. Publicação/comparação e auditoria são executadas automaticamente após seis conclusões; falha fica preservada e interrompe o ciclo.


## CryptoMamba adaptado autorizado e qualificado em29/10/2026

A pedido do pesquisador, os resultados da taxa foram preservados e as fontes do CryptoMamba estudadas/fixadas por commit. [ADR0014](adr/0014-cryptomamba-adaptado.md) e [protocolo](protocolo_cryptomamba_adaptado.md) delimitam uma abordagem composta, seis ajustes, mantendo dados/alvo/Spot. Qualificação sintética aprovada: núcleo equivalente com pesos iguais, eixos/dimensões, dois ajustes sintéticos reproduzidos e cinco testes sem skips.139.317parâmetros, contra20.257da referência. Preparação congela fontes, configuração, qualificação e53heranças; estado operacional em [registros próprios](../registros/cryptomamba/estado.json). Ainda sem ajuste de mercado nesta etapa.


## Análise posterior da taxa encerrada em29/10/2026

Conferidos novamente os53resultados e as métricas por origem, fontes/manifestos e433arquivos anteriores.24ajustes reais concluídos às20:46:49 de Brasília e pós-conferência final às20:51:48, sem incidentes na grade; não houve reexecução. O [relatório da taxa](resultados_taxa_aprendizado.md) recebeu interpretação,dispersão entre seeds,diagnóstico de concentração,recorte secundário de três seeds e figura científica PNG/PDF; o texto automático anterior foi preservado. [Análise e verificador](../registros/taxa_aprendizado/revisoes/85bd9dd338ac4ad0b83aec9f1d7d1e38/analise.json).

A taxa0,0001 piorou a média de validação nos quatro estados (+0,147%/+0,182%/+0,083%/+0,312% em8/16/32/64); nenhum contraste satisfez o critério pré-fixado. No teste, MSE mudou−0,190%/+0,403%/−0,089%/−0,872%, com dispersão menor em todos. Não promover candidata por teste/Spot. Retornos líquidos médios0,0001:−14,29%/−11,77%/−11,88%/−7,90%, todos negativos, com menos operações/exposição. Recomenda-se manter16/lr0,0002 como referência; nenhuma configuração ou peso foi alterado. A interpretação é retrospectiva e não comprova ótimo universal ou operação lucrativa.


## Taxa0,0001 nos quatro estados concluída e conferida

Grade `1af0a64e83d472ac533e` encerrada com24ajustes novos e29herdados; fontes/checkpoints/métricas/contrastes/preservação conferidos. [Relatório](resultados_taxa_aprendizado.md), [estado e recibos](../registros/taxa_aprendizado/estado.json). Mesmas seis seeds por estado; efeitos de taxa medidos dentro de cada arquitetura. Sem promoção automática, alteração Spot ou nova busca.2024/2025 permanecem retrospectivos.


## Redução da taxa autorizada nos quatro estados em29/10/2026

O pesquisador autorizou seguir a proposta0,0002→0,0001 e ampliá-la aos estados8/16/32/64, seis seeds em cada,24novos ajustes. [ADR0013](adr/0013-taxa-aprendizado-quatro-estados.md) e [protocolo](protocolo_taxa_aprendizado.md) delimitam fatores,ordem,controles e quatro contrastes primários com ajuste de multiplicidade. As24referências Mamba,LSTM/Naive/ARIMA são herdadas; a investigação anterior continua encerrada e16é referência de trabalho, sem promoção automática.2024/2025 permanecem retrospectivos.

O início real foi confirmado às2026-10-29T22:23:02.619825+00:00 no estado8/seed42; único processo identificado e lock ativo. Todas as quatro receitas foram congeladas antes desse início; nenhum resultado parcial altera as outras arquiteturas.

A qualificação CUDA foi aprovada nos quatro estados: oito ajustes sintéticos, reprodução nos limites definidos e recarga exata, cinco testes sem skips. As quatro receitas e29referências foram congeladas juntas sob `1af0a64e83d472ac533e` antes de mercado. O executor foi lançado com autorização vinculada; o estado real deriva de `progresso.json`/`processo.json` na pasta da execução.

Novo executor separado, sem editar fontes científicas encerradas. Os cinco testes de orçamento,autorização,fator único,parada em falha,53resultados e pós-relatório passaram com fixtures artificiais. Qualificação CUDA/sintética dos quatro estados em andamento; não conta como treino real. [Estado verificável](../registros/taxa_aprendizado/estado.json). Congelamento/IDs e início de mercado só são declarados pelos artefatos. Versões editoriais anteriores e433arquivos científicos guardados em `registros/taxa_aprendizado/`.


## Investigação de estados encerrada e referência16 adotada em29/10/2026

O pesquisador solicitou separar o resultado das quatro variantes e seguir com16estados. A [ADR0012](adr/0012-referencia16-e-proxima-hipotese.md) registra a decisão. O bloco está [indexado separadamente](../registros/investigacoes/estados_internos_001/fechamento.json), com24tentativas Mamba principais (quatro estados×seis seeds), vinculadas a cinco execuções existentes. Controles e referências auxiliares permanecem nas publicações originais; esse índice não é nova execução ou contagem de24treinos adicionais. A [referência de trabalho16](../registros/referencias/mamba16_ohlcv24_001.json) liga suas seis seeds, configuração, contrato, checkpoints e hashes. Não houve mudança de pesos, publicação, dados, fonte científica ou métrica dos ciclos fechados.

A próxima hipótese recomendada é reduzir somente a taxa AdamW0,0002→0,0001. Está **proposta**, sem treinamento/qualificação/congelamento, conforme a seção11 do [desenho](desenho_ohlcv24.md#11-referência-adotada-e-próxima-hipótese-proposta). Orçamento proposto de seis novos Mamba16; seis referências herdadas. Motivo: curvas existentes selecionam épocas9–13, depois treino online cai e validação piora. Isso motiva contraste limitado de otimização, sem diagnosticar taxa incorreta ou garantir ganho. Restante da receita, seis seeds, política Spot e seleção por validação ficam fixos; política operacional/novas entradas não mudam simultaneamente.

A seleção16 é retrospectiva e não demonstra vantagem sobre8/32, lucro ou ótimo universal. A proposta nova usa MSE de validação para decidir, com incerteza e manutenção da referência em caso inconclusivo;2025 não dirige ajustes dentro da rodada. Versões editoriais anteriores e diagnóstico das curvas foram preservados em `registros/revisoes/selecao_estado16_*/`. Nenhum treino novo foi iniciado nesta decisão.

## Complemento estado16 concluído e comparação dos quatro em seis seeds

Em29/10/2026, o complemento `cc0b166fe42a3ed1678d` encerrou às19:50:24UTC (16:50:24 de Brasília), com três novos ajustes7/123/31415, seleção nas épocas12/11/9 e parada nas épocas22/21/19. As três seeds17/42/2026 vieram de R0 intactas. [Estado e evidências](../registros/complemento_estado16/estado.json), [protocolo](protocolo_complemento_estado16.md). A conferência posterior foi aprovada: cobertura, fontes/manifestos, capacidade20.257 e A_log[64,16] em duas camadas, mínimo de validação, checkpoints e métricas por origem. Recarga preditiva exata foi verificada pelo executor em cada ajuste. Não houve novo LSTM/Naive/ARIMA nem repetição de seeds existentes.

A publicação contém3novos+26herdados. Uma consolidação independente de métricas/contrastes preserva a anterior, em [ponteiro próprio](../registros/complemento_estado16/comparacao_atual.json); médias aritméticas por seed, inclusive RMSE, não ensemble. O [relatório único](resultados_estados32_64.md) e a figura/PDF foram atualizados, preservando seus bytes anteriores em `registros/complemento_estado16/documentos_antes/`. Os301 arquivos anteriores da guarda de preservação ficaram intactos. A ocorrência de preparação descrita abaixo não iniciou treino real e foi corrigida antes do congelamento.

Nas seis seeds, MSE teste8/16/32/64 =0,000498745/0,000496570/0,000499044/0,000503767; habilidade contra Naive−0,712%/−0,272%/−0,772%/−1,726%. Estado16 mantém a menor média observada, mas os contrastes16/8 e16/32 incluem zero no IC14 (também7/28);16/64 favorece16 nas três sensibilidades. Contra Naive, o IC também inclui zero: não se demonstrou ganho. A habilidade média16 passou de−0,135% nas três seeds para−0,272% nas seis, sem mudar qualquer resultado antigo.

Retornos líquidos médios Spot8/16/32/64 =−14,52%/−18,46%/−14,46%/−18,85%, mesma política/custos R0; média negativa em todos. O menor MSE do16 não foi o melhor retorno operacional. Desvios do MSE entre seeds (×10⁻⁶):1,75/4,10/3,07/8,49. Todos os pares e resultados individuais permanecem no recibo. Intervalos exploratórios condicionais, sem ajuste global de multiplicidade;2024/2025 conhecidos e divisão fixa, não walk-forward. Nenhum novo ciclo fica autorizado pelo fechamento.

## Complemento estado16 autorizado em29/10/2026

Após a comparação dos estados, o pesquisador solicitou completar o16 para seis seeds e atualizar a média/tabela. O [protocolo](protocolo_complemento_estado16.md) fixa três ajustes novos7/123/31415, somados às três seeds17/42/2026 preservadas de R0, sem mudar dados/configuração/política. Fonte de estado e progresso: [registros próprios](../registros/complemento_estado16/estado.json). A nova identidade é `cc0b166fe42a3ed1678d`; R0 e8/32/64 permanecem separados e intactos.

Houve uma falha de integração na preparação (verificador64 chamado sem argumento); foi corrigida antes do congelamento e de qualquer ajuste real, com teste adicional e nova qualificação. Ambos os ensaios e a [ocorrência](../registros/complemento_estado16/ocorrencias_preparacao.json) foram preservados. Qualificação final: quatro testes sem skips, dois ajustes curtos sintéticos reproduzidos e recarga exata,20.257 parâmetros. O executor foi iniciado com autorização vinculada; consultar artefatos para distinguir execução/conclusão.2024/2025 continuam retrospectivos.



## Fechamento32/64 e comparação consolidada em29/10/2026

A sequência terminou às19:01:21UTC (16:01:21 de Brasília), com12 ajustes novos e auditorias automáticas aprovadas. Estado32 encerrou às18:39:56UTC e64 às19:01:06UTC; conferências posteriores completaram a fila. [Estado/ponteiros](../registros/estados_ampliados/estado.json). Progresso operacional, estados individuais e catálogo agora identificam ambas como concluídas/conferidas.

A pedido do pesquisador, foram calculadas médias aritméticas de métricas por seed, separando17/42/2026 para os quatro estados e17/42/2026/7/123/31415 para8/32/64. Essa consolidação inclui RMSE médio por seed; não é ensemble nem raiz do MSE médio. Foram verificados manifestos, fontes, tentativas, origens e métricas; todos os pares temporais solicitados foram refeitos em análise posterior exploratória, sem novos treinos. [Dados e verificador](../registros/estados_ampliados/comparacao_atual.json), [relatório](resultados_estados32_64.md) e figura/PDF preservam a interpretação e limites.

Três seeds: MSE teste8/16/32/64 de0,000498582/0,000495890/0,000501114/0,000507149; habilidades contra Naive−0,679%/−0,135%/−1,190%/−2,409%. Seis seeds: MSE8/32/64 de0,000498745/0,000499044/0,000503767; habilidades−0,712%/−0,772%/−1,726%. Estado16 teve a menor média observada no grupo de três;8/32 ficaram próximos no grupo de seis, com diferença inconclusiva. Estado64 teve maior MSE que8/32 nas seis, com ICs temporais exploratórios7/14/28 inteiramente desfavoráveis. Intervalos não corrigem toda seleção/multiplicidade nem transformam2024/2025 em holdout novo.

Retornos líquidos médios base nas três seeds8/16/32/64:−9,56%/−18,85%/−20,57%/−16,93%; nas seis8/32/64:−14,52%/−14,46%/−18,85%. Nenhuma configuração teve média líquida positiva. O32 teve pequena vantagem numérica líquida sobre8 no grupo de seis, de apenas0,067ponto percentual; não se demonstrou significância financeira. Maior capacidade não melhorou consistentemente previsão ou operação no desenho estudado. As médias não representam carteira e o drawdown médio não é risco de carteira média.

As fontes/publicações anteriores permaneceram íntegras. O relatório estado8 segue como fechamento específico daquela extensão; o novo relatório fecha32/64 e consolida os quatro tamanhos, sem alterar resultados congelados. Nenhum novo experimento foi iniciado na análise.


## Sequência Mamba32→64 autorizada, qualificada e congelada em29/10/2026

Após o fechamento comparativo16/8, o pesquisador autorizou explicitamente duas novas rodadas, primeiro32 e depois64, seis seeds cada. A [ADR0011](adr/0011-estados32-64.md) e o [protocolo](protocolo_estados32_64.md) fixam12 ajustes reais, seeds17/42/2026/7/123/31415, mesmas entradas/escalas/datas/arquitetura restante/otimização/políticaR0. Não há novos baselines ou complemento de estado16. Comparações:8/32/64 nas seis seeds; os quatro estados nas três comuns17/42/2026. Não se identifica estado ótimo universal com essa exploração retrospectiva.

As duas arquiteturas passaram em qualificação com Mamba oficial/CUDA:26.401 parâmetros para32 e38.689 para64. Para cada uma, dois ajustes curtos artificiais seed42 reproduzidos nos limites previstos e recarga exata; os mesmos cinco testes de orçamento/fila/publicação passaram, sem skips. Nenhum ajuste de mercado ocorreu durante qualificação. Um comando de teste anterior falhou por erro de sintaxe no próprio teste, corrigido antes das qualificações; a ocorrência permanece registrada. Fontes/configurações/protocolos/qualificações das duas foram congelados **antes do primeiro treino**.

- Estado32: **23c2ba54349bcc1b0ee1**, em `dados/experimentos/estados_ampliados_32_23c2ba54349bcc1b0ee1`.
- Estado64: **42cb667ea43df563e3ac**, em `dados/experimentos/estados_ampliados_64_42cb667ea43df563e3ac`.

A dependência64 liga o hash do congelamento32, não um resultado escolhido depois. O coordenador local exige32 concluído, publicação íntegra e auditoria de fechamento antes de64. Em falha, interrompe e preserva o incidente; não ajusta parâmetros nem continua silenciosamente. Não chama novamente um executor encerrado para refazer relatórios. O lançamento da fila ocorreu às18:21:38UTC (15:21:38 de Brasília), após ausência de outros treinamentos no WSL e autorização vinculada às duas identidades. [Índice](../registros/estados_ampliados/estado.json), [fila](../registros/estados_ampliados/fila/progresso.json) e `registros/estados_ampliados/fila/lancamento.json` indicam as evidências; um índice/plano não substitui progresso operacional.

A preservação conferiu92 fontes/ponteiros/protocolos/recibos anteriores antes/depois da preparação. Resultados16/8 permanecem em suas pastas, sem mudança. Novos pesos, previsões e publicações serão separados por estado e identidade; heranças identificadas não contam como novos ajustes. Esse registro confirma preparação/lançamento da sequência, não resultados das novas rodadas.


O primeiro ajuste real da sequência, estado32/seed42, iniciou às18:23:22UTC (15:23:22 de Brasília), após a verificação completa. Épocas e checkpoint confirmados; estado64 permanece preparado. [Confirmação](../registros/estados_ampliados/fila/inicio_confirmado.json). A fila local avança automaticamente a64 somente após fechamento/conferência de32, sem tarefa agendada do aplicativo ou novo ajuste de parâmetros.


## Extensão estado8 encerrada, conferida e comparada em29/10/2026

A execução **dcf4b0ed9012f7247bce** terminou às16:19:57UTC (13:19:57 de Brasília), com seis ajustes Mamba estado8 completos. A [conferência posterior](../registros/estado_mamba/conferencias/c041b9a06cdc4a99a3d10f3faa6cf0e2/conclusao.json) aprovou cobertura, fontes/protocolos/publicações, seis checkpoints novos e referências herdadas. Inspeção em CPU confirmou duas matrizes A_log64×8 nos novos modelos e64×16 nos anteriores,17.185/20.257 parâmetros, identidade comum dos dados e seleção de época. Refez métricas, médias e contrastes bootstrap, além de sinais/horários/pontas/quantidades/custos/capital nos minutos. Não repetiu treino ou recarga preditivaCUDA; esta foi atestada pelo executor. Drawdown permanece atestado pela publicação, sem recálculo independente nessa conferência.

Nas seeds pareadas17/42/2026, reduzir o estado aumentou o MSE em0,235% na validação e0,543% no teste. O IC principal14dias da diferença de MSE inclui zero. Todas as seis seeds da candidata tiveram MSE pior que Naive no teste; a média das seis foi0,712% pior. O desvio do MSE entre as três seeds pareadas diminuiu, mas não houve melhora preditiva demonstrada. A média líquida Spot das três melhorou de−18,85% para−9,56%, ainda negativa; a média bruta foi de−0,94% para−1,50% e a média de entradas caiu de69,3 para28,3. Não confundir menor perda/custo/exposição com melhor previsão.

Desenhos congelados, configurações de modelos, checkpoints por seed, previsões e publicações das duas rodadas permanecem em pastas/identidades distintas. O dataset é compartilhado intencionalmente. O catálogo ganhou a seção `rodadas_ohlcv`, distinguindo6novos+8herdados na publicação da extensão. O estado desatualizado “executando” dos índices foi corrigido; os recibos e dados congelados permaneceram intactos. [Relatório comparativo](resultados_estado_mamba.md), figura/PDF e recibos próprios apontam todas as fontes. Auditoria Binance/manutenção de posição permanece separada da política R0 usada nesta comparação. Nenhum próximo ciclo foi iniciado.


## Auditoria OHLCV/custos e extensão Mamba em29/10/2026

O pesquisador solicitou conferir as transformações OHLCV e a correspondência da simulação com a Binance, e prosseguir com uma alteração Mamba/seis seeds. Escolheu seis ajustes novos, com comparação pareada limitada às três seeds já existentes. A [ADR0010](adr/0010-estado-interno-mamba.md) e o [protocolo](protocolo_estado_mamba.md) delimitam somente d_state16→8, seeds17/42/2026/7/123/31415, mesmas entradas/configurações restantes e política R0. A média das seis da candidata não é tratada como pareamento contra três da referência. Não há sétimo ajuste real de controle; reprodução sintética antes da grade e recarga exata são exigidas e essa limitação é explícita.

A [auditoria](../registros/treinamento/auditoria_representacao_atual.json) refez as fórmulas, matrizfloat32 e scalers exatamente; alvos/purga e geometria relativa foram conferidos. Oito candles horários nativos coincidiram com a agregação, em quatro datas de2021/2023/2024/2025. Há extremos/mudança de escala na abertura e deslocamento de volume; isso é diagnóstico de distribuição, não evidência causal de prejuízo ou erro de implementação. Não houve recoleta nem alteração das entradas publicadas.

A tabela pública Spot consultada mostra0,10% por lado para usuário comum e0,075% com BNB aplicável. Slippage0,05% é hipótese. A contabilização de compra em R0 aproxima a taxa reservando caixa, enquanto o caso sem BNB descrito pela Binance desconta BTC recebido. Corrigir somente essa contabilidade muda o retorno aproximadamente0,003–0,012 ponto percentual entre os ajustes que operaram, sem mudar a conclusão. Mantendo os mesmos sinais, até taxa0,075% e slippagezero deixa negativas todas as redes que operaram. Não se simulou carteira BNB; filtros públicos atuais e tarifas atuais não certificam execução/condições históricas2025. R0 permaneceu intacta.

A qualificação da variante confirmou17.185 parâmetros contra20.257 de R0, dois ajustes curtos sintéticos reproduzidos e recarga exata. Foram acrescentados dois testes de orquestração: orçamento/herança/pareamento/publicação e rejeição de segunda alteração. Uma tentativa falhou porque a fixture de janeiro tinha trimestres vazios e a publicação tentava serializar NaN; foi corrigida antes do congelamento para n0/métricasnull. A falha e fontes intermediárias foram preservadas. A qualificação final passou. Estado/identidade próprios em [registros/estado_mamba/estado.json](../registros/estado_mamba/estado.json); preparação em andamento, ainda sem ajuste real da variante neste registro.


A extensão foi congelada como **dcf4b0ed9012f7247bce**, em `dados/experimentos/estado_mamba_dcf4b0ed9012f7247bce`, com [ponteiro próprio](../registros/estado_mamba/execucao.json), [autorização vinculada](../registros/estado_mamba/autorizacao.json) e qualificação final9db95c713e5c481b8cd06a90bd465b2c. O lançamento ocorreu às16:01:48UTC (13:01:48 de Brasília); o executor verifica a cadeia antes dos seis ajustes. LSTM/Naive/ARIMA e três Mamba estado16 são referências herdadas, sem novos ajustes. Não foi alterado o executor encerrado de R0.


O primeiro ajuste real da extensão (Mamba estado8,seed42) iniciou às16:03:29UTC (13:03:29 de Brasília), após a verificação completa. Processo ativo e épocas/checkpoints confirmados em [recibo](../registros/estado_mamba/inicio_confirmado.json). Nenhum resultado parcial orienta mudanças na grade congelada.

Um diagnóstico operacional posterior adicional manteve os mesmos dias de exposição, mas uniu dias compradores consecutivos para evitar vender/recomprar na fronteira. Com taxa/slippage base e contabilização no ativo recebido, o Mamba42 passou de−7,99% publicado para−5,19%, Mamba2026 de−33,32% para−18,24% e LSTM2026 de−32,03% para−6,87%. O efeito isolado da correção contábil é inferior a0,013 ponto percentual; o efeito predominante é giro. Um cenário combinado de taxa0,075%/slippage0,01% e posição mantida gerou+2,41% na LSTM2026; é sensibilidade posterior em teste conhecido, sem prova de lucro futuro ou carteiraBNB modelada. [Dados](../registros/estado_mamba/sensibilidade_giro_sinais_fixos.json) e [conferência reproduzível](../registros/estado_mamba/conferencia_sensibilidade_giro.json). Isso altera a política operacional, não a capacidade preditiva; não substitui R0 nem entra como mudança simultânea na extensão de estado.


## Rodada modular concluída e conferida em29/10/2026

A execução **ab5baf3eab3a2e66d8b2** terminou em29/10 às07:26:53UTC (**04:26:53, horário de Brasília**). Foram concluídas as dez células previstas: seis ajustes principais (Mamba/LSTM, seeds17/42/2026), dois controles de reprodução seed42, Naive e ARIMA. Todos os nove candidatos ARIMA foram válidos. O processo encerrou normalmente e não há treinamento Python ativo no WSL na conferência posterior.

A [conferência posterior](../registros/treinamento/conferencias/bbe308fe56c54c2d879b85fc7f1b7105/conclusao.json), realizada sem reexecutar o estudo, aprovou cobertura exata, hashes das fontes/checkpoints/tentativas/publicação, seleção da época pelo menor MSE de validação, alinhamento das populações e recálculo independente das métricas. Os dois controles passaram: LSTM reproduziu exatamente; Mamba teve diferença máxima de previsão de aproximadamente2,33×10⁻⁸, mesma época e diferença relativa de MSE de aproximadamente1,41×10⁻⁹, dentro dos limites definidos. Os recibos de cada ajuste atestam recarga exata do próprio checkpoint; essa recarga CUDA não foi repetida na conferência posterior.

A publicação está em `dados/experimentos/ohlcv_modular_ab5baf3eab3a2e66d8b2/publicacoes/tentativa_001`: previsões e métricas de validação/teste, contrastes temporais, simulações Spot e referências econômicas. [Estado atual](../registros/treinamento/estado.json). Esta conferência confirma conclusão e consistência técnica; interpretação científica dos resultados e seus limites deve usar a publicação. A divisão permanece fixa e retrospectiva. Não reexecutar o executor encerrado para produzir relatórios.


## Rodada modular autorizada em29/10/2026

O pesquisador respondeu “ok” ao pedido explícito para iniciar treinamento, validação e testes da rodada preparada. A autorização foi vinculada à execução **ab5baf3eab3a2e66d8b2**, suas dez células e orçamento em [recibo próprio](../registros/treinamento/autorizacao.json). Não autoriza mudanças de parâmetros ou novos ciclos.

O lançamento ocorreu em29/10 às07:02:56UTC, no WSL/Ubuntu com o Python qualificado. Antes dele foram conferidas as56 fontes congeladas, o protocolo, a identidade, a ausência de outro treinamento no WSL e a disponibilidade da RTX4050. O executor faz novamente a verificação completa dos dados e do ambiente antes de ajustar parâmetros. [Lançamento](../registros/treinamento/lancamento_2026-10-29.json), logs em `registros/treinamento/executor_2026-10-29.*.log` e [estado atual](../registros/treinamento/estado.json). Autorização e processo lançado ainda não significam ajuste concluído ou resultado disponível.


O início efetivo do primeiro ajuste, **Mamba seed42**, foi confirmado após a verificação completa, às07:05:47UTC. O processo WSL está ativo e já produziu épocas e checkpoint de validação. A execução seguirá a grade congelada, com controles antes das demais seeds e avaliação/publicação ao final. [Confirmação de início](../registros/treinamento/inicio_confirmado_2026-10-29.json). Estes registros comprovam início, não conclusão ou qualidade preditiva.


## Cadeia modular qualificada em29/10/2026; aguarda “Ok”

O pesquisador solicitou organizar treinamento, seleção e checkpoints, integrar dados/modelos e verificar o caminho até os resultados, sem iniciar mercado antes de novo “Ok”. A [ADR0009](adr/0009-treinamento-modular.md) e a [arquitetura](arquitetura_treinamento.md) descrevem `treinamento/`, `avaliacao/` e `run_treinamento.py`. A configuração mantém R0: BTC/1h/contexto168h/alvo24h, cinco canais, mesma divisão e hiperparâmetros, seis ajustes neurais principais e dois controles. A referência preparada92e3eb82e3f6adf99994 permanece intacta.

A nova identidade **ab5baf3eab3a2e66d8b2** está congelada em `dados/experimentos/ohlcv_modular_ab5baf3eab3a2e66d8b2`, com ponteiro em [registros/treinamento/execucao.json](../registros/treinamento/execucao.json). Estado: **aguardando_ok; zero treinamentos de mercado**. Preparação/qualificação não autorizam execução, novas hipóteses ou aceitação acadêmica. O [estado verificável](../registros/treinamento/estado.json) liga fontes, configuração, qualificação e preservação.

Passaram **68 testes sem skips**, no WSL/CUDA/Mamba oficial, cobrindo as camadas de dados, consumo e treinamento/avaliação. O ensaio integral usou exclusivamente mercado artificial: oito ajustes neurais curtos, Naive, nove candidatos ARIMA, recarga, controles, métricas independentes, contrastes e simulação. Uma interrupção artificial depois do primeiro ajuste confirmou retomada sem alterar seu manifesto; a tentativa falha permaneceu guardada e somente a incompleta recomeçou. Os checkpoints recarregados reproduziram previsões exatamente. Testes também conferiram ausência de acesso ao teste durante seleção, peso do último microbatch, isenções de decay, corrupção, bloqueio concorrente e outro host. Evidência: [qualificação final](../registros/treinamento/qualificacoes/09524ec9434041e7805053d7c507987c/qualificacao.json).

A conferência real verificou24.751 janelas de treino,8.760 de validação,8.736 de teste e8.760 operacionais, com as populações e escalas publicadas. O adaptador financeiro preservou exatamente **2.629.440 minutos×6 campos**, incluindo ausências, frente à base auditada anterior. Isso foi leitura/comparação, não previsão ou simulação de mercado. A política econômica e as métricas foram migradas para módulos próprios; a publicação acrescenta dispersão entre seeds e distribuição das operações observáveis, sem alterar critérios de seleção ou sinais.

A primeira tentativa de qualificação falhou na descoberta das suítes antigas pelo unittest; a descoberta foi corrigida sem alterar esses testes. Uma versão intermediária passou67 testes; após reforçar retomada, bloqueio de controle reprovado e fronteira explícita do avaliador, a versão final passou68. Recibos e falhas não foram sobrescritos; [ocorrências](../registros/revisoes/treinamento_modular_2026-10-29/ocorrencias.json) identificam cada versão. Nenhuma dessas tentativas é treinamento de mercado.

Preservação antes/depois confirmou74 fontes/configurações/ponteiros anteriores inalterados. A auditoria dos estudos preliminares conferiu12.090 hashes, sem erro ou arquivo ausente, em [recibo próprio](../registros/revisoes/catalogo_2026-10-29T064426.996705Z/resumo.json). Esses checks não são comprovação de backup externo. O portal permanece com os resultados preliminares. Próximo passo: autorização humana vinculada à execução, conferência de processo/ambiente/integridade e execução somente da rodada delimitada.


## Consumo pelos modelos organizado e conferido em 29/10/2026

A pedido do pesquisador, a revisão avançou das camadas de dados para a forma como Mamba, LSTM, Naive e ARIMA recebem informação. Foi criado `modelos/`, com contratos, ponte de consumo, arquivos por família, inferência e conferência, conforme a [ADR 0008](adr/0008-consumo-de-dados-pelos-modelos.md) e a [arquitetura dos modelos](arquitetura_modelos.md). O comando `run_modelos.py conferir` não possui ação de treinamento. As configurações neurais foram separadas, conservando os valores de R0.

Mamba/LSTM recebem as mesmas janelas causais `[lote,168,5]`, com quantidade/ordem de canais vinculadas ao contrato, em vez de um cinco fixo na implementação. O alvo fica fora do pedido de previsão; a conversão entre saída normalizada e log-retorno real é explícita. Naive retorna zero real. ARIMA continua univariado, com histórico de log-fechamentos, lacunas mantidas no calendário e parâmetros fixos durante filtragem; não foi transformado em modelo com janela OHLCV. O prefixo permitido para um futuro ajuste termina no índice26.278, antes da validação, conservando a regra anterior.

Passaram **21 testes sem skips**, executados no WSL com PyTorch2.6.0+cu118, Mamba oficial2.2.6.post3, statsmodels0.14.6 e RTX4050 Laptop. Conferiram janelas/alvos, purga, ausência de futuro nos pedidos, escala de Naive, causalidade ARIMA, shapes, ordem dos canais, contextos24/168 e1/2/5 canais em fixtures. Para as nove ordens ARIMA, projeções filtradas foram comparadas a `get_forecast(24)` em prefixos sintéticos, sem `fit`. As redes produziram **forward e recarga exatos** frente às implementações preservadas sob pesos iguais; pesos permaneceram inalterados e gradientes ausentes. Isso não é reprodução de treinamento. Mamba/LSTM mantêm20.257/13.473 parâmetros no contrato de cinco canais; marcas de isenção de penalização foram conservadas. Classe Mamba e três arquivos/extensões instalados coincidiram por hash com a qualificação anterior.

A [conferência real](../registros/modelos/conferencias/daeb16b0af2440f4a49d85f82b948e07/resumo.json) verificou todas as24.751 janelas de treino,8.760 de validação,8.736 de teste e8.760 operacionais do conjunto `0420879c2afc454c7754`, inclusive conversão do alvo e igualdade de origens entre consumidores. Populações de teste/operação se sobrepõem; não contar como amostras independentes. Não houve treinamento neural, backward, ajuste ARIMA, seleção de ordem, inferência neural de mercado, cálculo de placar ou simulação.

Evidências e inventário de preservação em [registros/modelos/estado.json](../registros/modelos/estado.json) e `registros/revisoes/consumo_modelos_2026-10-29T054622.136468+0000/`. Camadas de dados, executores anteriores e preparação congelada de R0 permaneceram intactos. Próxima revisão: separar treinamento/seleção/checkpoints e, depois, avaliação/simulação; integrar sob nova identidade e qualificação. Nenhuma autorização de treinamento foi inferida desta revisão.

## Camadas de dados separadas e conferidas em 28/10/2026

O pesquisador mudou a prioridade: antes de treinar, revisar a modularização módulo a módulo, começando pela Binance e pela preparação das entradas. A [ADR 0007](adr/0007-modulos-de-dados.md) registra essa decisão; a [arquitetura](arquitetura_dados.md) define contratos, etapas e manutenção. Foram implementados `mercado_binance/` (coleta pública, validação e candles), `entradas_modelo/` (receita causal, alvo, contexto, divisões e escalas), `infraestrutura/` (preservação) e `run_dados.py`, com configurações distintas de mercado e entradas.

Os 240 ZIPs mensais existentes de BTC/ETH/BNB/XRP em 2021–2025 foram revalidados por CHECKSUM e processados em artefatos novos. Cada par tem calendário de 2.629.440 minutos e 43.824 horas. BTC/ETH/BNB apresentam 1.073 minutos ausentes na fonte e cinco interrompidos, afetando 23 horas por par; XRP tem 1.072 ausentes e quatro interrompidos, afetando 22 horas. Essas indisponibilidades já existiam; foram conservadas sem interpolação. OHLCV/número de negócios por minuto, OHLCV horário e tempos coincidem exatamente com a base preservada.

A preparação modular de BTC reproduziu a matriz float32 de R0 integralmente: 24.751 origens de treino, 8.760 de validação, 8.736 de teste e 8.760 operacionais. Um cálculo independente refez canais, contextos, purga, alvos e ajuste das escalas. A diferença máxima dos alvos para o artefato anterior foi 2,78e−17, compatível com ponto flutuante e abaixo da tolerância registrada; índices e matriz de entrada coincidem exatamente. Artefatos: mercado `449aab6c79dbf88aa625`, candles `93509a1b06b19103ac1c`, entradas `0420879c2afc454c7754`.

Passaram 30 testes locais, incluindo fluxo completo, causalidade, independência das escalas frente ao futuro, lacunas, candles interrompidos, unidades ms/us, paginação, limites de requisições, falhas sem publicação, integridade ancestral e compatibilidade. A aquisição real foi verificada com cinco minutos de BTC em janeiro/2024 e janeiro/2025, usando páginas de dois registros: os valores coincidiram com o arquivo histórico. Um download novo de janeiro/2025 passou no CHECKSUM e reproduziu o hash do ZIP antigo. Não houve recoleta integral, treino, inferência neural nem simulação.

Ocorrências de desenvolvimento: as primeiras verificações identificaram unidade interna de timestamps e arrays somente leitura do pandas3; corrigidas antes da publicação dos artefatos. Uma chamada de conferência usou caminho de entradas incorreto e falhou antes de comparar; o erro e log foram preservados, e a chamada com o caminho efetivo passou. Esses eventos não são tentativas de treinamento. Evidências, limitações e fontes estão no [estado dos dados](../registros/dados/estado.json) e em `registros/revisoes/modularizacao_dados_2026-10-28T222751.152378Z/`.

R0 `92e3eb82e3f6adf99994` permanece preparada e separada; fontes, configurações e recibos anteriores não foram substituídos. O novo módulo não redireciona o executor congelado. A revisão das demais superfícies identificou redes com cinco canais fixos, orquestração/configuração acopladas e simulação herdada com array de minutos de seis colunas. Próxima etapa: revisar os consumidores, integrar por nova identidade e qualificar antes de treinar. O portal continua representando o estudo preliminar. Artefatos locais e hashes não comprovam backup externo.

## Referência OHLCV preparada em28/10/2026, sem treinamento de mercado

Após o pedido de limpeza e fechamento técnico, a documentação atual foi reduzida: dez relatórios/diagnósticos saíram de `docs/` para `arquivo/estudos_preliminares_2026-10-28/documentacao/`. Links e catálogo foram atualizados. README/plano passaram a resumir orientação e etapas, remetendo ao arquivo para números antigos. Os originais dos documentos movidos estão preservados no snapshot desta revisão. Protocolos, fontes, configurações, checkpoints, previsões e recibos dos ciclos encerrados permaneceram intactos; o PDF acadêmico também.

R0 foi delimitada a BTC/1h/contexto168h/alvo24h, cinco canais OHLCV, treino2021–2023, validação2024 e avaliação retrospectiva2025. Redes Mamba/LSTM com seeds17/42/2026: seis ajustes principais mais dois controles. Naive zero e ARIMA com nove candidatos/uma seleção. Retirada de volume, indicadores e mudanças de configuração ficam para ciclos posteriores, uma variável por vez. Os quatro preços relativos e log-volume foram mantidos como representação motivada, sem alegação de necessidade ou superioridade. CryptoMamba utiliza outra representação; não é replicação.

Implementação nova `estudo_ohlcv/`, comando `run_ohlcv.py`, configuração `configuracoes/ohlcv24_001.json`. O dataset **00c15349ce0e28a543a6** reutiliza BTC horário/minutos íntegros, sem recoleta ou interpolação. São **24.751 origens de treino,8.760 de validação e8.736 de teste**;8.760 origens causais operacionais, das quais somente as decisões diárias com saída dentro do período podem operar. São43.824 horas, com23 horas OHLCV ausentes preservadas. Máscaras de336h/quatro moedas do dataset antigo não entram na nova população.

A [conferência independente dos dados](../registros/ohlcv/conferencias/2026-10-28T213844.690511_0000/resumo.json) reagrupou todos os minutos e reconstruiu horários, alvos, origens e escalas por outro cálculo. OHLCV/índices/contagens são exatos; a matriz float32 coincide integralmente. Diferença máxima de alvo Windows/WSL de2,78e−17, dentro da tolerância explícita de ponto flutuante. Estatísticas de preço/volume são ajustadas na união de horas únicas dos contextos de treino; não em validação/teste. Amostras de alvo sem destino observado não integram erro preditivo, mas não removem retrospectivamente decisões operacionais.

[Qualificação atual](../registros/ohlcv/qualificacoes/2026-10-28T213745.525127_0000/qualificacao.json): **31 testes automatizados aprovados** (14 novos e17 contratos anteriores), mais forward/backward/atualização, gradientes dos cinco canais, treino sintético curto e recarga das duas redes. Mamba oficial CUDA com20.257 parâmetros; LSTM com13.473. Recarga do mesmo checkpoint exata; controles sintéticos de repetição dentro dos limites predefinidos, com mesma época. Implementações instaladas e extensões CUDA identificadas por SHA-256. O primeiro ensaio de igualdade bit a bit entre treinos falhou com diferença numérica muito pequena e foi preservado; os controles passaram a usar os limites já existentes de1e−5 de log-retorno/1e−4 de MSE relativo, sem consultar resultados de mercado. Ocorrências em `registros/revisoes/limpeza_preparacao_ohlcv_2026-10-28T211713.614472Z/ocorrencias_preparacao.json`.

Identidade preparada/congelada: **92e3eb82e3f6adf99994**. Ponteiro [execução OHLCV](../registros/ohlcv/execucao.json); estado `preparado_sem_treinamento`. O congelamento inclui configuração, fontes, dataset, protocolo e qualificação; **nenhum ajuste de mercado, resultado preditivo ou simulação de mercado dessa nova etapa foi executado**. Testes sintéticos não são contados como resultados do TCC. Próximo passo operacional: executar somente R0 e seus controles no ambiente qualificado, sem abrir a busca de configurações.

A [auditoria integral posterior dos ciclos preliminares](../registros/revisoes/catalogo_2026-10-28T212727.147106Z/resumo.json) passou sem divergências/ausências. Ela verifica hashes, fontes, cobertura e publicações; não repete treino, não é nova auditoria matemática de todos os escores e não certifica backup externo. A nova preparação tem auditoria própria; não depende de o auditor histórico reconhecer seu layout.

Evidências da organização em `registros/revisoes/limpeza_preparacao_ohlcv_2026-10-28T211713.614472Z/`; versão anterior da preparação `d13d7fe5765c6213f11f` e qualificações superadas permanecem como tentativas técnicas sem treino de mercado. Documentação de conversa não será criada automaticamente. O portal segue exibindo a fase preliminar. Nenhum commit/push, alteração do PDF ou aceite do orientador foi presumido.


## Reorganização e desenho OHLCV em 28/10/2026

O pesquisador solicitou conferir o encerramento da normalização, separar os estudos anteriores e realinhar o próximo desenho ao TCC escrito. Forneceu `docs/TCC_1_MuriloRFM.pdf` durante a revisão e pediu reduzir a criação de documentos por interação. O PDF foi identificado por hash, extraído e lido nas seções relevantes; a página de posicionamento foi inspecionada visualmente. O original permanece intacto.

A leitura do resumo, introdução e seção 2.7 confirmou a orientação de investigação iterativa do próprio Mamba, entradas OHLCV/indicadores e avaliação walk-forward, com crítica à equivalência entre erro baixo e utilidade operacional. Isso difere da prioridade do plano operacional anterior, centrado em contextos e comparação entre famílias. Os ciclos de retorno24 usaram só retornos de fechamento; a coleta OHLCV não os torna modelos multivariados. A ablação pré/pós-LayerNorm concluída também não equivale ao estudo estático/adaptativo de normalização dos dados mencionado no PDF. Não foram identificados nesta revisão motivos para invalidar todos os resultados anteriores, nem foi auditada integralmente a bibliografia do TCC1.

O catálogo foi reconferido com integridade completa e exigência de disponibilidade, sem divergências nem ausências: [recibo](../registros/revisoes/catalogo_2026-10-28T204312.995454Z/resumo.json). O ciclo de normalização está concluído, sem processo PID425 ativo no WSL, com 384 ajustes e dois controles, publicações e fechamento já existentes. A revisão não chamou seu executor nem repetiu inferência.

Foi criado o [bloco de estudos preliminares](../arquivo/estudos_preliminares_2026-10-28/README.md), com índice dos quatro estudos e cópias verificadas de 22 documentos anteriores. Artefatos, fontes e protocolos científicos permanecem nos caminhos originais. O [índice documental](README.md) separa trabalho atual e histórico. AGENTS, plano, README, roteiro, catálogo e procedimento de registro passaram a distinguir a etapa OHLCV proposta dos ciclos encerrados e a evitar documentos para perguntas explicativas. A [ADR 0006](adr/0006-reorganizacao-e-desenho-ohlcv.md) registra esta mudança material.

O [desenho OHLCV](desenho_ohlcv24.md) concentra recomendações sobre cinco canais causais, alvo de24h, BTC/contexto168h/três seeds, exploração limitada, avaliação ampliada walk-forward, métricas pareadas e política Spot fixa com custos. Reorganização e direção OHLCV foram solicitadas; escolhas concretas permanecem propostas, sem implementação ou treinamento novo. Não se presumiu aceite do orientador. Períodos2023–2025 continuam conhecidos; a figura do PDF atéjunho/2026 impede presumir todo2026 desconhecido sem apurar exposição.

Evidências desta organização em `registros/revisoes/reestruturacao_ohlcv_2026-10-28T204537.973691Z/`. Nenhum commit, publicação externa, movimentação de checkpoints ou apagamento de histórico foi feito. O portal ainda representa o estudo preliminar; preservação externa continua pendente de recibos próprios.

Conferência de encerramento: catálogo posterior novamente conferido; 173 links locais sem quebra, 22 cópias documentais verificadas e PDF original inalterado. [Verificação documental](../registros/revisoes/reestruturacao_ohlcv_2026-10-28T204537.973691Z/verificacao_documental.json). O hash integral anterior cobriu 12.090 arquivos/entradas verificadas; a conferência posterior verificou fontes/manifestos/cobertura, sem repetir todos os binários ou recalcular métricas.

## Pré-normalização concluída e conferida em 28/10/2026

A execução `9e03af2150cbb7b1068d` terminou os treinos às 19:32:35 UTC e a consolidação às 19:38:35 UTC (16:38:35 em São Paulo): 384 novos ajustes Mamba e dois controles auditados, sem tentativas interrompidas neste ciclo. As duas publicações têm 192 novos resultados, 416 referências herdadas e 192 pares diretos cada. O comparador é o Mamba com penalização corrigida; LSTM, Naive e ARIMA não foram retreinados.

A [conferência posterior independente](../registros/revisoes/normalizacao_2026-10-28T200441.557811_0000/resumo.json), concluída às 20:10:35 UTC, aprovou cobertura exata, fontes, dataset, populações, escalas/configurações dos checkpoints, seleção de época, grupos de penalização, métricas, 60 intervalos temporais e 10.296 registros de ordens nos dois cenários de custo. Foram reconferidos 11.243 arquivos preservados dos ciclos anteriores. Não refez inferência neural: recargas exatas constam dos recibos dos treinos. Não foram alterados fontes, configurações ou recibos congelados, nem chamado novamente o executor.

Resultado principal de 2024–2025: MSE de 0,0011913154 para 0,0011817236, redução de 0,8051%; IC95% da diferença [−2,66815e−5; +2,73487e−6], incluindo zero. Melhora numérica, sem evidência conclusiva de ganho e sem superioridade demonstrada sobre LSTM/Naive. Duas seeds melhoraram e uma piorou; 90 de 192 pares de ajustes melhoraram. A mediana Spot base passou de −10,48% para −11,03%; mediana das diferenças pareadas −9,72 p.p., estatística distinta da diferença entre medianas. Em 2023, o MSE caiu 0,5065%, com intervalo excluindo zero. As fases permanecem separadas e os períodos já eram conhecidos.

O [relatório interpretativo](../arquivo/estudos_preliminares_2026-10-28/documentacao/resultados_normalizacao_mamba.md) detalha métricas, intervalos, seeds, moedas, contextos e simulação; figura PNG/PDF com manifesto em `docs/figuras/normalizacao_9e03af2150cbb7b1068d/`, inspecionada visualmente. O [fechamento](../registros/auditorias/9e03af2150cbb7b1068d/fechamento_normalizacao.json) vincula as publicações e a revisão. Foram preservadas versões anteriores/finais dos documentos na pasta da conferência, atualizados o catálogo, README, ADR e roteiro de redação. Nenhuma nova hipótese ou grade foi iniciada. Preservação externa e restauração em outra máquina ainda dependem de recibos próprios.

## Estudo dos fundamentos e resultados do CryptoMamba em 28/10/2026

A pedido do pesquisador, foi elaborado um [material de estudo de SSM/Mamba e leitura crítica do CryptoMamba](../arquivo/estudos_preliminares_2026-10-28/documentacao/fundamentos_mamba_e_leitura_critica_criptomamba.md), distinguindo fatos publicados de motivos plausíveis das escolhas. A inspeção ampliada documentou que a rotina financeira pública não desconta custos explicitamente e que a faixa de risco heurística não é um intervalo probabilístico calibrado.

Foi calculada somente a persistência nos dados públicos externos, sem treino ou inferência neural:365 linhas de teste,350 exemplos conforme os índices do dataset publicado com W14, RMSE1.568,50USD, MAE1.091,90USD e MAPE1,97323%. Os valores são numericamente menores que os publicados para CryptoMamba com volume, mas a conta não reproduz os checkpoints nem comprova igualdade com a população da tabela do artigo; não representa teste pareado ou conclusão de significância. Evidências em [métricas e limites](../registros/revisoes/fundamentos_mamba_2026-10-28T151138.942559Z/persistencia.json), com escopo prévio, fontes, cálculo por origem e segunda conferência independente. Esses resultados externos não pertencem à grade do CryptoCasting. Nenhum código científico, configuração ou artefato do ciclo de pré-normalização foi alterado.

## Conferência de progresso às11h09 de 28/10/2026

A execução de pré-normalização alcançou301/384 ajustes treinados, testados e auditados (78,4%), além dos dois controles aprovados. Desenvolvimento DB1–DB4 completo; B1/B2 completos e B3 em andamento. Processo PID425 ativo em CUDA, log recente e sem tentativas falhas/interrompidas observadas. A conferência verificou82 hashes de fontes/cópias e2.408 artefatos das tentativas auditadas, sem divergências; não repetiu inferência. Evidência em [conferência posterior](../registros/revisoes/progresso_normalizacao_2026-10-28T140736.296023Z/conferencia.json).

A estimativa operacional naquela consulta foi de aproximadamente5–8h restantes para os treinos/testes, sem garantia e sem incluir a conferência final independente. Ela considera tempos recentes B2/B3 e crescimento do número de exemplos até B4. As primeiras12 células de B3 levaram em média294s e34,2 épocas, contra144s e19,3 épocas em B2; ainda são populações distintas, não comparação controlada de velocidade. Tempos por ajuste, método e limites da estimativa estão preservados na mesma pasta. A previsão de horário não declara conclusão antecipada nem altera a grade.

## Diagnóstico de duração e GPU em 28/10/2026

A pedido do pesquisador, foi verificado o uso real da GPU durante a execução de pré-normalização, sem alterar fontes ou treinamento. O PID425 estava ativo como processo CUDA na RTX4050 Laptop. Uma amostra de 31 leituras em aproximadamente30s mediu utilização média34,97%, entre24% e44%, com357MiB ocupados. A consulta de energia indicou alimentação externa e ausência de flags ativas de limitação térmica/potência naquele instante. A GPU está sendo usada, mas a amostra não demonstra saturação nem eficiência máxima.

Nos89 ajustes auditados lidos para os tempos, a mediana da rotina completa ficou entre60,15 e68,77s conforme o contexto, incluindo treino/validação/previsões/recarga; as médias de épocas ficaram entre17,3 e19,6. O retrato seguinte registrou90/384 novos ajustes concluídos e dois controles. A leitura do treinador identificou sincronizações CPU/GPU por microbatch e baixo volume de cálculo por rede; são candidatos a limitar throughput, não gargalos quantificados por profiler. A grade executa384 ajustes separados, não um único modelo; o scan paralelo não elimina atualizações sequenciais do otimizador. O diagnóstico não mede vantagem de velocidade frente à LSTM. Evidências e limites em [parecer de desempenho](../registros/revisoes/desempenho_normalizacao_2026-10-28T065710.587327Z/parecer.md), `tempos.json`, `amostra_gpu.csv` e `resumo.json` na mesma pasta. Nenhuma otimização foi introduzida no ciclo congelado.

## Pré-normalização autorizada e em preparação em 28/10/2026

O pesquisador autorizou implementar a recomendação e treinar/testar somente Mamba, após reconferir a penalização no CryptoMamba. A consulta ao repositório confirmou o mesmo commit da pesquisa anterior. O código dos autores usa Adam uniforme, sem a isenção explícita de A_log/D; nosso ciclo mantém AdamW e as isenções corrigidas, para mudar somente a posição da LayerNorm. A mensagem e a consulta estão em `registros/normalizacao/autorizacao.json` e `conferencia_criptomamba.json`.

Foram criados fontes separadas em `experimento_normalizacao/`, entrada `run_normalizacao.py`, configuração própria e [protocolo](protocolo_normalizacao_mamba.md). A [ADR 0005](adr/0005-proposta-prenormalizacao-mamba.md) passou de proposta para autorizada, preservando a proposta anterior no snapshot da pesquisa. O novo treinador só altera a fábrica de rede em relação ao treinador corrigido; a rede herda os módulos e muda exclusivamente o forward. O código rejeita outras famílias neste ciclo.

Preparação iniciada em `registros/normalizacao/preparacao_2026-10-28T045741.033627_0000/`: inventário de preservação com 11.243 arquivos dos ciclos anteriores e fontes. A conferência de artefatos, contratos e qualificação precede o congelamento. Neste registro inicial, ainda não havia novos treinos de mercado. Plano: 384 novos Mamba, dois controles Mamba, referências de outras famílias herdadas. O [relatório do ciclo](../arquivo/estudos_preliminares_2026-10-28/documentacao/resultados_normalizacao_mamba.md) permanece sem conclusão antecipada; o estado atualizado será acrescentado abaixo após evidência.

Atualização da mesma preparação: passaram 31 testes (17 contratos anteriores, sete da penalização e sete específicos) e oito casos CUDA, duas repetições por caso com recarga exata. GPU RTX4050 Laptop; maior diferença de repetição sintética 1,1921e-7, abaixo do limite predefinido de 1e-6. A identidade congelada é `9e03af2150cbb7b1068d`, em `dados/experimentos/normalizacao_9e03af2150cbb7b1068d/`. O executor iniciou em 28/10 às05:02:09UTC (02:02:09 em São Paulo), PID425 no WSL, host MuriloRFM. O primeiro ajuste é o controle pós-normalizado BTC/DB1/W24/seed42. A existência de processo vivo e qualificação aprovada ainda não comprova aprovação dos controles ou conclusão dos 384 novos ajustes. Ponteiro, lançamento, logs e preparação estão em `registros/normalizacao/`; o catálogo identifica o ciclo em andamento e publicações/fechamento futuros ainda ausentes.

Liberação da grade às05:05:24UTC: os dois controles pós-normalizados passaram, com mesma época do histórico; diferenças máximas de previsão de 8,5683e-9 (W24) e 9,1593e-9 (W336), abaixo de 1e-5. As variações relativas de MSE foram 9,7978e-9 e 2,0973e-9, abaixo de 1e-4. A reprodução não foi bit a bit idêntica e essa limitação ficou nos recibos. Os dois pilotos pré-normalizados também foram auditados, incluindo recarga exata; contam como dois dos 384 novos ajustes. `piloto_aprovado.json` registra o gate e o executor prossegue automaticamente com a grade fixa. A conclusão e o efeito da intervenção continuam pendentes.

## Pesquisa sobre Mamba e CryptoMamba em 27/10/2026

A pedido do pesquisador, foi conferida a identidade do Mamba instalado e pesquisado o CryptoMamba antes de decidir a próxima alteração. A [revisão técnica](../arquivo/estudos_preliminares_2026-10-28/documentacao/revisao_mamba_criptomamba.md) confirmou a classe Mamba-1 oficial: fonte instalada idêntica byte a byte à tag `v2.2.6.post3` e ao hash da qualificação anterior. A instanciação de inspeção confirmou 20.129 parâmetros Mamba, 12.961 LSTM e os 2.176 escalares marcados para isenção de penalização. Não houve novo forward, treinamento ou reprodução de checkpoints nesta revisão.

Foram preservados artigo v2, 17 arquivos do repositório CryptoMamba no commit `fef42727861a9c3a32241283ab981ef21a49e291`, fontes oficiais versionadas e fontes locais, com URLs/hashes. O estudo externo usa outro alvo, entradas, arquitetura e treinamento; a leitura do código identifica scan entre variáveis, enquanto o nosso percorre horas. A tabela preditiva do artigo não inclui Naive. A pesquisa distingue configuração publicada de execução efetivamente reproduzida e documenta discrepância de early stopping e risco da normalização opcional, desligada nos YAMLs CryptoMamba consultados.

A [ADR 0005](adr/0005-proposta-prenormalizacao-mamba.md) propõe priorizar pré-LayerNorm versus pós-LayerNorm, mantendo o restante igual à extensão de penalização corrigida. É uma hipótese de adaptação apoiada pelo bloco oficial e pelo CryptoMamba, sem prova de que a pós-normalização causou a desvantagem. Essa prioridade refina a recomendação anterior de frequência; os resultados anteriores permanecem válidos. **Nenhuma nova variante foi implementada ou treinada e nenhuma grade foi iniciada.** Proposta não equivale à adoção pelo pesquisador. Evidências e limites estão no [fechamento da pesquisa](../registros/revisoes/mamba_criptomamba_2026-10-28T000408.161229Z/fechamento.json), registrado no dia seguinte em UTC. Os períodos de avaliação continuam retrospectivos para novas hipóteses.

## Revisão de frequência e configurações em 27/10/2026

O pesquisador solicitou procurar erros e melhorias, em particular a possibilidade de emitir previsões a cada 24h. Foi realizada uma revisão de código, literatura primária e artefatos, sem novos treinamentos. O [relatório de diagnóstico](../arquivo/estudos_preliminares_2026-10-28/documentacao/diagnostico_frequencia_e_configuracoes.md) separa candle horário, contexto, horizonte de 24h, frequência das origens e atualização dos pesos. A simulação Spot existente já opera com uma decisão diária.

O [diagnóstico posterior](../registros/revisoes/frequencia_2026-10-27T230053.607585Z/resumo.json) conferiu 1.216 resultados e as épocas dos 1.152 ajustes neurais, recalculou o MSE em todas as origens e em cada horário diário, e estimou intervalos pareados por blocos. O recorte principal foi 00 UTC, previamente usado pela simulação; nenhum horário foi escolhido pelo teste. Em 2024–2025, Naive=100: LSTM passou de 100,005 na avaliação horária para 100,423 na diária; Mamba corrigido, de 101,272 para 101,905. No recorte diário, os intervalos favorecem LSTM/Naive frente ao corrigido; LSTM versus Naive continua inconclusivo. Avaliar diariamente não resolveu a diferença; o efeito de **treinar** com origens diárias continua não testado.

Não foi encontrado novo erro nas verificações de alvo, alinhamento, fronteiras, seleção de época e MSE. Os 17 testes da referência e sete da extensão passaram novamente; três testes do diagnóstico também passaram. A auditoria identificou limitações: forte sobreposição dos alvos horários, queda de aproximadamente 24 vezes na quantidade de exemplos ao usar origens diárias, efeito sobre orçamento por época, sinais compatíveis com sobreajuste e adaptação Mamba com pós-normalização diferente do empilhamento de referência da biblioteca. Essa adaptação está conforme o protocolo executado; seu efeito não foi isolado e não foi classificada como bug comprovado.

Foram preservados código, plano anterior ao cálculo, hashes das fontes lidas, tabelas, intervalos, logs de testes, cópias dos módulos Mamba inspecionados e figura PNG/PDF com inspeção visual. Fechamento em [recibo da revisão](../registros/revisoes/frequencia_2026-10-27T230053.607585Z/fechamento_revisao.json). O catálogo conecta essa revisão aos dois estudos existentes; não a conta como novo treinamento. As propostas de frequência, normalização e entradas no relatório não alteram o protocolo vigente e não constituem nova grade autorizada. B1–B4 permanecem períodos conhecidos e retrospectivos para novas hipóteses.

## Organização e rastreabilidade conferidas em 27/10/2026

A pedido do pesquisador, foi revisada no notebook a reorganização recebida do outro dispositivo, no commit `9af48a933e39b962f0cc789966d096d3387d6e84`. A separação entre guia AGENTS, decisões ADR, cronologia, evidências e artefatos foi mantida. A [ADR 0004](adr/0004-rastreabilidade-de-ciclos.md) documenta o complemento: [catálogo de estudos](../registros/catalogo_estudos.json), [procedimento para mudanças](registro_de_experimentos.md) e [modelo de proposta](modelos/proposta_experimento.md). São registros de organização, não autorização ou execução de uma nova grade.

O catálogo liga o ciclo histórico de barreiras, a referência de retorno24 e a extensão controlada, preservando seus layouts. O ciclo 002 de barreiras permanece classificado como proposta não executada. Para consultar o início da evolução, usar o [relatório arquivado do ciclo 001](../arquivo/estudo_barreiras_2026-10-20/projeto/historico/analises/ciclo_001_resultados.md), sua [proposta posterior](../arquivo/estudo_barreiras_2026-10-20/projeto/historico/ciclos/ciclo_002_proposto.md) e as [decisões de reformulação](../arquivo/estudos_preliminares_2026-10-28/documentacao/decisoes.md); o catálogo não cria retroativamente pré-registro ou aprovação.

Foi executada `python manutencao/auditar_catalogo.py --integridade --exigir-completo`, com [recibo próprio](../registros/revisoes/catalogo_2026-10-27T224713.066988Z/resumo.json): **8.743 hashes conferidos, sem divergências ou ausências no escopo**. A cobertura foi exata: 832 resultados auditados da referência, 384 corrigidos e dois controles da extensão, sem células inesperadas ou duplicadas. As duas tentativas interrompidas permanecem contabilizadas. Foram verificadas fontes atuais/congeladas, identidade/configuração, dataset e arquivos das quatro publicações (216 por fase da referência; 101 por fase da extensão). Esta revisão não repetiu inferência ou cálculo de métricas, nem reauditou integralmente brutos e legado; a auditoria científica anterior continua sendo a fonte dessas verificações. Sete testes do novo verificador passaram, incluindo duplicidade, herança incorreta, ausência parcial e divergência CRLF/LF.

As 30 fontes científicas atuais conferem com seus hashes congelados. Destas, 28 coincidem em bytes com HEAD; `previsao24/coleta.py` e `experimento_penalizacao/treino.py` diferem do blob do commit apenas por finais de linha. O achado é local e não certifica o checkout do desktop. `.gitattributes` passou a preservar bytes de fontes, registros e arquivo histórico, sem renormalização, alteração de fontes ou atualização de hashes antigos. As regras anteriores de converter os registros para LF foram substituídas, pois os snapshots podem conter CRLF original.

Antes da revisão textual, foram preservados e conferidos os oito documentos vinculados por hash ao fechamento da extensão em [snapshot anterior](../registros/revisoes/organizacao_2026-10-27T223818/inicio.json). O fechamento antigo não foi sobrescrito. O [recibo desta organização](../registros/revisoes/organizacao_2026-10-27T223818/resumo.json) relaciona as verificações e as versões documentais posteriores.

O [inventário local](../registros/revisoes/organizacao_2026-10-27T223818/volumes_locais.json) mediu 518.553.824 bytes no dataset processado, 438.401.967 na referência, 230.780.121 na extensão e 169.714.342 no portal: cerca de 1,36 GB, sem incluir os brutos ou o arquivo histórico. No instante da auditoria havia 6.449 arquivos elegíveis ainda não rastreados, somando 27.767.463 bytes; esse número aumenta com os próprios recibos novos. Elegibilidade não significa commit, envio ou backup. Nenhum commit/push/Release foi feito nesta revisão. A preservação externa e a restauração no outro dispositivo continuam pendentes, conforme a [política](armazenamento_e_reproducao.md).

O acompanhamento agendado da penalização foi encerrado após a entrega final, conforme [recibo](../registros/penalizacao/acompanhamento_encerrado.json). O próximo ciclo científico deve partir de pergunta e configuração próprias, com registro dos resultados já conhecidos e autorização correspondente. A organização permite evoluir dados, entradas e parâmetros sem substituir o passado; não transforma a exploração de B1–B4 em confirmação independente.

## Extensão concluída e conferida em 27/10/2026

A execução `7868a4d847c1410fc681` terminou os treinamentos às 20:33:49 UTC e a consolidação/preservação às 20:39:05 UTC (17:39:05 em São Paulo). Foram 384 ajustes corrigidos completos e dois controles aprovados. As duas tentativas interrompidas continuam no histórico; houve 388 tentativas de mercado e 386 conclusões auditadas, sem escolha pelo resultado. As duas publicações contêm, cada uma, 192 ajustes novos, 416 resultados herdados, 192 pares e 96 cenários financeiros. O recibo `preservacao_depois.json` confirma os 7.082 arquivos da referência.

A conferência posterior independente foi aprovada em `registros/revisoes/penalizacao_2026-10-27T210853.776756_0000/resumo.json`: cobertura exata, fontes, dataset, artefatos, populações, métricas, escalas/configurações de todos os checkpoints corrigidos, grupos do otimizador, 60 intervalos temporais e 9.022 registros de operações nos dois cenários de custos. Esses registros financeiros repetem os sinais nos cenários base/agravado; não representam 9.022 operações independentes. O verificador não repetiu inferência neural; a recarga exata de cada ajuste consta da auditoria original por tentativa. A primeira tentativa dessa revisão falhou apenas ao salvar o recibo, por conflito de variável; código e diagnóstico preservados em `registros/revisoes/penalizacao_2026-10-27T210425.386923_0000/`. Somente o verificador foi corrigido e repetido.

Resultado: a correção diminuiu o MSE em 0,0068% no desenvolvimento de 2023; na avaliação retrospectiva de 2024–2025 aumentou 0,0505%, com intervalo incluindo zero. O corrigido permaneceu com MSE 1,2665% maior que LSTM e 1,2719% maior que Naive. Não houve solução para a desvantagem do Mamba nem evidência de rentabilidade consistente. A mediana da política Spot ficou em −10,48% na avaliação, embora alguns sinais e resultados individuais tenham mudado. Os períodos já eram conhecidos; não são novo holdout intocado.

O [relatório final da extensão](../arquivo/estudos_preliminares_2026-10-28/documentacao/resultados_penalizacao_mamba.md) contém interpretação, seeds, contextos, simulação, sete entregas da extensão e limitações. Foram geradas e inspecionadas cinco figuras PNG/PDF em `docs/figuras/penalizacao_7868a4d847c1410fc681/`, com manifesto. README, guia AGENTS, plano, auditoria e roteiro de redação foram atualizados. O portal continua apresentando o ciclo original; a extensão está documentada separadamente. Não reexecutar o executor concluído para regenerar relatórios. Redação acadêmica, aceite do orientador, preservação externa e eventual integração da extensão na interface são trabalhos distintos deste fechamento; nenhum novo treinamento foi autorizado por seus resultados.

## Segunda retomada operacional em 27/10/2026

Após novo reinício informado pelo pesquisador, a verificação encontrou o executor encerrado e 299 ajustes corrigidos concluídos, além dos dois controles. O último progresso era de 11:23:40 UTC; a tentativa BTC/B3/W336/seed2026 tinha log até 11:26:14 UTC, sem conclusão auditada. O Windows informou início da sessão atual às 15:15:51 UTC. Foram preservados os eventos de desligamento inesperado e reinício por atualização; seus horários não permitem atribuir com certeza a causa exata da parada do treinamento.

A auditoria de retomada terminou aprovada às 15:28:47 UTC: 299 resultados corrigidos e dois controles íntegros, dataset verificado, fontes atuais e congeladas conferidas, 7.082 arquivos da referência preservados, nenhum executor ativo e trava livre. Evidências em `registros/incidentes/penalizacao_retomada_2026-10-27T152403.256870_0000/verificacao.json`, com os eventos em `eventos_windows.json` e cópia dos registros e da tentativa incompleta. O verificador operacional passou a receber a evidência de cada incidente como argumento, evitando reutilizar a descrição do primeiro reinício; nenhuma fonte científica foi alterada.

A execução foi retomada pela mesma entrada congelada. Os resultados auditados são revalidados e reaproveitados; somente a tentativa incompleta é repetida com a mesma seed/configuração, mantendo a tentativa anterior no histórico. Restavam 85 ajustes corrigidos na conferência. A conclusão da grade e a comparação científica final ainda estavam pendentes.

## Retomada operacional em 27/10/2026

Às 04:05 UTC, a verificação encontrou o executor anterior encerrado, com 56 ajustes corrigidos e dois controles concluídos. O último log da tentativa incompleta era de 27/10 às 00:43:34 UTC; o Windows informou início da sessão atual em 27/10 às 00:50:47 UTC. Isso evidencia um reinício posterior ao último log, sem estabelecer a causa exata do encerramento do treino. Não houve exceção final registrada pelo executor.

Antes da retomada, foram preservados os registros de processo, progresso, aprovação dos pilotos e todos os arquivos da tentativa incompleta. A conferência de 27/10 às 04:07:54 UTC aprovou as fontes atuais e congeladas, o dataset, os 7.082 arquivos da referência, os 56 resultados corrigidos e os dois controles. Não havia executor ativo e a trava estava livre. Evidências em `registros/incidentes/penalizacao_retomada_2026-10-27T040636.095845_0000/verificacao.json`.

A retomada usa a mesma entrada e identidade congelada, reutiliza os resultados auditados e repete somente o ajuste incompleto com a mesma seed e configuração. A tentativa anterior permanece preservada; não houve alteração científica ou seleção pelo desempenho. O acompanhamento agendado verifica o estado a cada meia hora, mas depende do computador e do aplicativo disponíveis; não substitui o programa de treinamento.

## Extensão iniciada em 26/10/2026

O pesquisador autorizou corrigir a penalização do Mamba e executar a grade original de Mamba novamente, mantendo os demais fatores. O protocolo separado está em [penalização do Mamba](protocolo_penalizacao_mamba.md); a revisão das estruturas está em [auditoria de configuração](../arquivo/estudos_preliminares_2026-10-28/documentacao/auditoria_configuracao_penalizacao.md).

O código da correção e sete testes específicos foram implementados e aprovados. A execução foi iniciada com preservação, verificação das referências, repetição dos 17 contratos, qualificação CUDA e congelamento antes do treinamento de mercado. O estado exato deve ser consultado em `registros/penalizacao/execucao.json` e no `progresso.json` da execução apontada; antes de existir esse ponteiro, a preparação é registrada em `registros/penalizacao/preparacao_*/estado.json`.

São planejados 384 treinamentos corrigidos e dois controles de reprodução. Não se afirma conclusão da nova grade nesta entrada. Os resultados e a cronologia abaixo pertencem ao ciclo original, concluído em 21/10. As referências antigas não serão apagadas nem substituídas. A extensão usa períodos já consultados e é retrospectiva.

Congelamento da extensão: `7868a4d847c1410fc681`, com treinamento de mercado iniciado em 26/10 às 23:43:29 UTC. A preparação verificou as referências, passou nos 17 testes existentes e sete específicos, qualificou 12 combinações de modelo/contexto/política e comprovou equivalência exata da atualização em um teste de agrupamento com penalização uniforme. O manifesto inicial contém 7.082 arquivos preservados. Evidências em `registros/penalizacao/preparacao_2026-10-26T233400.168859_0000/`; o recibo final de preservação será emitido somente após execução e conferência.

Os dois controles reais BTC/DB1/seed42, W24 e W336, e os dois pilotos corrigidos foram aprovados. A reprodução dos controles manteve a época escolhida, com diferenças máximas de previsões abaixo de 1,25e-8 de log-retorno e variação relativa de MSE abaixo de 1,19e-8. Esses controles não são uma nova avaliação científica independente. A grade corrigida segue em execução; `piloto_aprovado.json` e os recibos `controles/celulas/*/tentativa_001/reproducao.json` preservam a evidência.

Foi configurado acompanhamento local para verificar a conclusão, executar as figuras científicas, revisar a documentação e entregar a interpretação final no chat. Registro: `registros/penalizacao/acompanhamento.json`. Não reiniciar um executor vivo; o acompanhamento não autoriza novo experimento além deste protocolo.

Atualização: 21/10/2026. Os horários desta página são UTC.

## Situação do ciclo de referência em 21/10/2026

As oito entregas computacionais estão concluídas e verificadas. Execução `1e7c5ed662fba55ddd25`; dataset `d25f6a93a9900725f51e`. A exportação final terminou às 18:36:54 UTC: **832 resultados auditados em 384 séries**, com os quatro modelos disponíveis. A conferência global e a inspeção da interface foram aprovadas; recibos `registros/auditorias/1e7c5ed662fba55ddd25/fechamento.json` e `registros/interface/aceite_final.json`.

São **768 ajustes neurais** (384 em cada fase), **32 referências Naive** e **32 seleções ARIMA**. Todos os **288 candidatos internos ARIMA** foram válidos. Referências compartilhadas entre contextos e seeds não contam como novos treinamentos. Duas publicações auditadas contêm **424 cenários financeiros e 16.284 registros de operações**; cenários correlacionados não são observações independentes nem uma carteira.

A conclusão da avaliação é: LSTM teve menor MSE que Mamba; a diferença LSTM–Naive foi inconclusiva. Mamba teve erro maior que LSTM, Naive e ARIMA no procedimento predefinido. Mais contexto não trouxe melhoria geral, e a simulação não demonstrou rentabilidade consistente. Ler [avaliação de 2024–2025](../arquivo/estudos_preliminares_2026-10-28/documentacao/resultados_avaliacao.md) e, separadamente, [desenvolvimento de 2023](../arquivo/estudos_preliminares_2026-10-28/documentacao/resultados_desenvolvimento.md).

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

## Comparação de entradas autorizada em03/11/2026

Após a proposta A/relativa,B/crua,C/níveis padronizados,o pesquisador autorizou início com oito seeds. Quatro blocos,32referências A/MSE da rodada Huber,64principais novos+2controles reais. Plano `4cb8d09f29e60463eac9`,19testes CPU aprovados e oito artefatos novos conferidos. Fila em segundo plano aguarda fechamento conferido da predecessora; qualificação CUDA e identidade da execução serão vinculadas antes de mercado. [Protocolo](protocolo_entradas_niveis.md), [estado](../registros/entradas_niveis/estado.json). Preparação/fila não comprovam treinamento real; não duplica a rodada ativa.

## Entradas em nível encerradas

Execução `76f6c437e70eaaa605ad`:64ajustes novos+2controles,32referências herdadas. [Resultados](resultados_entradas_niveis.md). Sem promoção ou nova busca automática.

## Revisão posterior das entradas em03/11/2026

Execução `76f6c437e70eaaa605ad` encerrada às08h59 de Brasília. Revisão de leitura conferiu95fontes,2.305arquivos publicados,9.632preservados,métricas96modelos,2controles,3contrastes e600carteiras. Nenhum novo treino,inferência ou simulação. Crua versus atual inconclusivo; crua versus níveis padronizados favorável no critério predefinido,sem promoção automática. [Interpretação](resultados_entradas_niveis.md), [recibo](../registros/entradas_niveis/entrega/20261103/conferencia.json).

## Combinação OHLCV cru/Huber autorizada em03/11/2026

Após consultar as duas rodadas encerradas,o pesquisador pediu oito seeds para a combinação e início imediato. As outras três combinações já possuem32ajustes cada,nos mesmos quatro blocos. [ADR0021](adr/0021-crua-huber-complemento-fatorial.md) e [protocolo](protocolo_crua_huber.md) delimitam32principais novos+1controle real,96herdados,192simulações novas+600herdadas. Qualificação CUDA em curso;preparação não comprova treinamento real. Estado em `registros/crua_huber/estado.json`. Os dois efeitos anteriores não foram confirmados contra a referência e não são presumidos aditivos;interação será medida. Não há autorização para outras configurações ou repetição de referências.

A qualificação da combinação crua/Huber foi aprovada:35testes,sem skips,dois ajustes sintéticos reproduzidos com previsões idênticas e recarga exata. Recibo `registros/crua_huber/qualificacoes/8478e752dad34802b1c9ac6eea512559/qualificacao.json`.Congelamento em preparação;qualificação não conta como treino de mercado.

Execução `1781f557fdf2b45a3ae2` congelada e vinculada à autorização;processo lançado em03/11 às16:19BRT (19:19UTC),em segundo plano. A conferência inicial antecede32principais+1controle e192simulações novas,com96referências e600simulações herdadas.35testes de qualificação aprovados;13049arquivos no mapa de preservação. [Ponteiro](../registros/crua_huber/execucao.json),[processo de lançamento](../registros/crua_huber/lancador.json). O lançamento ainda não comprova primeira época ou conclusão;progresso de mercado fica na execução.

## Combinação crua/Huber concluída

Execução `1781f557fdf2b45a3ae2`:32principais novos+1controle,96referências herdadas,192simulações novas+600herdadas. [Resultados](resultados_crua_huber.md). Sem promoção automática;2024/2025 retrospectivos.
