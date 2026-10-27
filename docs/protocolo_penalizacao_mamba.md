# Experimento controlado da penalização do Mamba

Protocolo definido em 26/10/2026, antes dos novos treinamentos, após solicitação explícita do pesquisador. O objetivo é medir o efeito de respeitar a marcação `_no_weight_decay` na implementação oficial do Mamba, mantendo os demais fatores do estudo de retorno de 24 horas. Uma melhora não é requisito para concluir o experimento.

## Origem e hipótese

A revisão de 24/10 reproduziu os escores do estudo de referência e identificou que `AdamW(rede.parameters(), weight_decay=0.001)` aplica a penalização também a `A_log` e `D`. A biblioteca instalada marca esses parâmetros com `_no_weight_decay=True`; o AdamW não interpreta esse atributo automaticamente. A referência possui quatro tensores marcados, dois por bloco, totalizando 2.176 dos 20.129 parâmetros escalares do Mamba. A origem e os hashes estão em `registros/revisoes/parecer_2026-10-24.json` e no recibo de checkpoints ali vinculado.

A hipótese é que excluir esses parâmetros da penalização pode alterar a generalização. Sua direção e magnitude serão medidas, sem presumir melhora. A intervenção não remove a regularização de todos os pesos: os demais 17.953 parâmetros mantêm o coeficiente 0,001. Não excluir outros vieses ou normalizações nesta experiência, pois seria uma segunda mudança.

## Preservação e identidade

Referência: execução `1e7c5ed662fba55ddd25`, dataset `d25f6a93a9900725f51e`. Código, dados, checkpoints, resultados, publicações e recibos existentes permanecem em seus caminhos originais. As fontes científicas `previsao24/`, `run_previsao.py`, `configuracoes/retorno24_001.json` e `docs/protocolo_experimental.md` não serão editadas. A preservação terá manifesto SHA-256 antes e conferência depois. Não se trata de backup externo.

O novo código fica em `experimento_penalizacao/`; a entrada é `run_penalizacao.py`; a configuração complementar é `configuracoes/penalizacao_mamba_001.json`. O novo diretório de execução terá identidade calculada a partir do protocolo, configuração, fontes, dataset, qualificação e referência. Todos os arquivos usados serão vinculados por hashes e as fontes terão cópia congelada. O ponteiro `registros/execucao_atual.json` da referência não será alterado; o novo ciclo terá ponteiro próprio.

## Intervenção e fatores constantes

O treinamento novo reproduz o treinamento original, substituindo somente a construção do otimizador por grupos explícitos. Os grupos são contíguos na ordem original de parâmetros; somente parâmetros marcados recebem `weight_decay=0`. A criação do otimizador não consome números aleatórios nem altera pesos. Um teste estrutural compara as rotinas para impedir mudanças acidentais no restante do treinamento.

Permanecem: quatro moedas BTC/ETH/BNB/XRP; candles de uma hora; entradas exclusivamente retornos horários; alvo `ln(P[t+24h]/P[t])`; contextos 24/72/168/336h; seeds 17/42/2026; todas as origens e partições DB1–DB4/B1–B4; escalas de treino; arquitetura, inicialização e backend oficial; FP32; AdamW com lr0,0002, betas(0,9;0,999), eps1e-8; batch64, microbatch32; clipping1; limite100 épocas e paciência10; escolha da menor MSE de validação com primeiro empate; inferência e recarga exata. Não há novo ajuste de hiperparâmetros.

A correção pode mudar gradientes posteriores, épocas selecionadas e duração do treinamento. Essas mudanças são consequências do tratamento, não fatores a forçar iguais. Fixar a época escolhida pelo modelo antigo mudaria a pergunta; ambos seguem a mesma regra de seleção por validação.

## Grade e controles

Serão 384 novos ajustes Mamba: quatro moedas × quatro contextos × oito blocos × três seeds. Desenvolvimento de 2023 e avaliação histórica de 2024–2025 serão reportados separadamente, com 192 ajustes por fase. Os 384 Mamba anteriores serão os controles pareados. As referências LSTM, ARIMA e Naive serão reutilizadas, explicitamente identificadas como herdadas, sem contá-las como novos treinamentos.

Antes da grade, serão reexecutados dois controles originais BTC/DB1/seed42, W24 e W336. Seus resultados serão comparados aos controles históricos para medir a reprodutibilidade no ambiente atual, sem seleção por desempenho. O piloto corrigido usa as mesmas duas células e será integrado à grade, sem duplicação. A qualificação sintética também compara grupos contíguos com penalização uniforme contra o otimizador original, isolando um eventual efeito apenas do agrupamento. Divergência relevante de ambiente ou implementação bloqueia a execução até registro de uma revisão; pequenas diferenças não determinísticas serão quantificadas e não ocultadas.

O orçamento é de 386 treinamentos de mercado, sem contar falhas documentadas. Os dois controles adicionais são verificações de reprodução, não novas seeds nem réplicas independentes. Reutilizar o dataset verificado evita nova coleta e mantém exatamente a população original.

Gate dos controles reais, definido antes de executá-los: mesma época selecionada; diferença máxima de previsão em cada população até 1e-5 de log-retorno e variação relativa de MSE de teste até 1e-4 (0,01%). Registrar também igualdade exata. A tolerância não autoriza desconsiderar divergências: um controle fora dela interrompe a grade para investigação.

## Treino, validação e teste

Valem integralmente as datas e regras do protocolo original. As escalas são ajustadas exclusivamente ao treino e conferidas contra os checkpoints anteriores. As entradas e alvos devem coincidir entre pares. A purga exige destino de cada alvo estritamente anterior ao fim da partição. Contextos podem incluir passado anterior à fronteira; dados futuros não entram nas entradas. Lacunas permanecem sem interpolação, sem seleção pela magnitude do retorno futuro.

O estudo original terminou e seus resultados foram consultados antes desta hipótese. Portanto, B1–B4 nesta extensão são **avaliação retrospectiva em períodos já expostos**, não confirmação independente. A referência mantém sua classificação histórica. Congelar a extensão antes dos novos treinos reduz decisões adaptativas dentro deste ciclo, mas não desfaz exposição anterior. Uma alegação futura de ganho generalizável exigirá outro período não usado para decisões ou avaliação prospectiva.

## Qualificação e execução

Registrar hardware, versões, GPU, memória e fontes da biblioteca. Rodar os 17 contratos existentes sem regenerar os recibos congelados, mais testes específicos de cobertura dos grupos, atributos preservados, RNG, atualização dos pesos, equivalência estrutural do treinador e integridade dos controles. Qualificar forward/backward, repetição e recarga nas quatro dimensões de contexto, em ambas as políticas de penalização; verificar LSTM inalterada.

Cada tentativa registra início, célula, política, identidade, PID, fontes e status. Salvar pesos, épocas, escalas, descrição do otimizador e previsões de validação, teste e população operacional. Exigir recarga exata, métricas recalculadas e alinhamento antes de marcar como auditada. Em falha, preservar a tentativa e diagnosticar; retomada só após conferir PID, fonte e artefatos. Não selecionar tentativas pela qualidade do teste. Só publicar placar de uma fase após cobertura exata.

## Análise predefinida

Contraste principal: MSE do Mamba corrigido menos MSE do Mamba original na fase de avaliação histórica. Negativo favorece a correção. Desenvolvimento terá análise separada de replicação temporal. Reportar diferença absoluta, variação relativa, MSE/RMSE/MAE, habilidade contra Naive, viés, direção, épocas e dispersão entre seeds. Os escores recebem média entre seeds e pesos iguais entre moedas/contextos/blocos; não se trata de ensemble.

Bootstrap pareado por blocos móveis de dias UTC: 2.000 réplicas, seed20261020, 14 dias principal, sete/28 de sensibilidade, sem cruzar blocos temporais. Mesmas reamostragens entre moedas e contextos, preservando alvos sobrepostos. Intervalos condicionais aos períodos e modelos; não cobrem toda a incerteza de treinamento nem a escolha retrospectiva desta hipótese.

Contrastes com LSTM, Naive e ARIMA, contextos, moedas e seeds são secundários/exploratórios. Não escolher vencedor por subconjunto nem interpretar a proporção de células melhores como teste estatístico. Reportar as três seeds, inclusive uma que piore. Diferença indistinguível de zero não prova equivalência; um intervalo que exclui zero não garante importância econômica.

## Simulação complementar

Aplicar às novas previsões operacionais a mesma política Spot diária do estudo original: 00:00 UTC, execução 00:01, saída24h depois, comprado/caixa, capital10.000USDT, custos base e agravados, sem mudanças no limiar ou seleção de estratégia. As decisões do cenário agravado seguem os sinais do cenário base. Conferir operações contra os minutos e preservar desconhecidos causados por lacunas. Comparar as 48 estratégias por fase com seus pares antigos; nenhuma constitui carteira combinada. A simulação não avalia futuros ou liquidação.

## Documentação para o TCC

O relatório final distinguirá: estudo de referência; revisão que identificou a penalização; protocolo desta extensão; resultados novos; controles de reprodução; limitações e implicações. Preservar dados por ajuste, fontes, logs, todos os incidentes, manifestos, comandos, ambientes, intervalos e operações. O estado real será atualizado em `docs/andamento.md`, e um roteiro de redação indicará quais fontes sustentam metodologia, resultados e discussão. Não antecipar conclusões enquanto houver resultados pendentes.

Fontes primárias: [implementação oficial do Mamba](https://github.com/state-spaces/mamba/blob/main/mamba_ssm/modules/mamba_simple.py), [grupos de parâmetros no PyTorch](https://docs.pytorch.org/docs/stable/optim.html#per-parameter-options) e [artigo original do Mamba](https://arxiv.org/abs/2312.00752). A versão local efetivamente utilizada e seu hash prevalecem para reprodução.
