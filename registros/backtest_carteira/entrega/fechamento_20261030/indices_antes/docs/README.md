# Documentação: por onde começar

## Trabalho atual

A avaliação operacional posterior usa [carteira retida](protocolo_backtest_carteira.md), conforme ADR0015, com [estado próprio](../registros/backtest_carteira/estado.json). São simulações sobre previsões já treinadas, sem modificar os modelos ou o SpotR0. Resultados continuam retrospectivos e incluem controles de exposição/viés/custos.

**Estado mais recente:** a investigação de estados e a grade de taxa estão concluídas/conferidas, conforme [resultados da taxa](resultados_taxa_aprendizado.md). A rodada posterior [CryptoMamba adaptado](protocolo_cryptomamba_adaptado.md) também foi concluída e conferida em seis seeds: [resultados e análise](resultados_cryptomamba_adaptado.md), com [estado verificável](../registros/cryptomamba/estado.json) e ADR0014. Os parágrafos abaixo sobre preparação descrevem etapas anteriores; não substituem os ponteiros de execução.

1. [TCC1 original](TCC_1_MuriloRFM.pdf): objetivo acadêmico e fundamentação; original preservado.
2. [Desenho OHLCV em 24h](desenho_ohlcv24.md): documento único para fechar entradas, alvo, treinamento, variações e avaliação. Contrato técnico e implementação preparados; ainda sem treinamento de mercado.
3. [Plano de trabalho](../plano.md): etapas atuais e distinção do plano histórico.
4. [Andamento](andamento.md): única cronologia factual.
5. [Roteiro de redação](roteiro_redacao_tcc.md): como usar as evidências no artigo.

A referência já tem [configuração](../configuracoes/ohlcv24_001.json), [qualificação](../registros/ohlcv/qualificacao.json) e [identidade preparada](../registros/ohlcv/execucao.json). Isso não significa treinamento de mercado iniciado. A prioridade posterior é revisar módulos antes de treinar: começar pela [arquitetura dos dados](arquitetura_dados.md) e [suas evidências](../registros/dados/estado.json). O executor preparado permanece separado dessa migração.

Em29/10, o consumo pelas quatro famílias passou a ter [arquitetura própria](arquitetura_modelos.md) e [evidências](../registros/modelos/estado.json): contratos, dimensões, janelas, alvo, inferência e recarga sem ajustes. A orquestração foi integrada em seguida, conforme a [arquitetura de treinamento](arquitetura_treinamento.md), [ADR0009](adr/0009-treinamento-modular.md) e [estado atual](../registros/treinamento/estado.json). A referência anterior continua preservada; a rodada modular foi autorizada por “ok” em29/10, conforme [recibo](../registros/treinamento/autorizacao.json); progresso e conclusão devem ser conferidos nos artefatos.

## Histórico e evidências

- [Estudos preliminares até 28/10](../arquivo/estudos_preliminares_2026-10-28/README.md): referência de retornos, penalização, normalização e ligação ao estudo anterior de barreiras.
- [Catálogo](../registros/catalogo_estudos.json) e [mapa dos registros](../registros/README.md): execuções, tentativas, checkpoints e recibos.
- [ADRs](adr/README.md): somente decisões duráveis, não cada pergunta ou época.
- [Registro de experimentos](registro_de_experimentos.md) e [preservação](armazenamento_e_reproducao.md): como manter rastreabilidade e transportar artefatos.
- [Cronograma acadêmico preservado](../arquivo/estudo_barreiras_2026-10-20/projeto/docs/Cronograma_Atividades_TCC2_Murilo_Monferrari.pdf): documento administrativo; não comprova aceite de entregas.

Os protocolos `protocolo_experimental.md`, `protocolo_penalizacao_mamba.md` e `protocolo_normalizacao_mamba.md` descrevem **execuções históricas congeladas**. Permanecem nos caminhos originais porque seus bytes/endereços participam de recibos e referências. Dez relatórios/diagnósticos anteriores saíram desta pasta para `arquivo/estudos_preliminares_2026-10-28/documentacao/`, com navegação atualizada e originais preservados. Somente os três protocolos congelados permanecem aqui por integridade.

## Regra para evitar fragmentação

- Resposta explicativa normalmente fica na conversa; não criar Markdown, ADR ou pasta de revisão só por haver uma nova mensagem.
- Refinamentos do desenho atual ficam em `desenho_ohlcv24.md`; fatos de execução ficam em `andamento.md`.
- Novo documento só para um artefato com função própria: protocolo de ciclo que será implementado, relatório de ciclo concluído, decisão material ou entrega solicitada.
- Recibos técnicos, logs, extrações e medições ficam em `registros/` ou na execução. Snapshot documental apenas antes de alteração material que precise preservar uma versão vinculada, não por cada pequena edição.
- Não mover/apagar evidências antigas apenas para reduzir o número de arquivos. Não produzir versões concorrentes de cronologia ou placar.

Essas regras também estão no [AGENTS.md](../AGENTS.md), para valerem nas próximas interações.

A rodada seguinte de Mamba está delimitada no [protocolo de estado16→8](protocolo_estado_mamba.md); seis ajustes novos, comparação pareada em três seeds, com [auditoria prévia de OHLCV/custos](../registros/treinamento/auditoria_representacao_atual.json). Estados próprios ficam em `registros/estado_mamba/`; R0 permanece concluída e preservada.

A extensão de estado8 foi concluída e conferida. O [relatório comparativo](resultados_estado_mamba.md) separa desenhos congelados, configurações/pesos, seis ajustes novos, oito heranças, resultados e limitações. O catálogo identifica as duas execuções em `rodadas_ohlcv`; os estados atuais não devem ser inferidos dos parágrafos históricos da cronologia.

A sequência seguinte32→64 tem [protocolo único previamente delimitado](protocolo_estados32_64.md), [ADR0011](adr/0011-estados32-64.md) e [índice dos registros](../registros/estados_ampliados/estado.json). São duas execuções separadas, seis ajustes cada; progresso operacional fica na fila e nas execuções, não nos parágrafos históricos.

A sequência32/64 foi concluída e conferida. O [relatório de fechamento32/64 e médias consolidadas](resultados_estados32_64.md) compara os quatro estados nas três seeds comuns e8/32/64 nas seis. [Dados verificáveis](../registros/estados_ampliados/comparacao_atual.json). O relatório anterior estado8 permanece específico daquela extensão; o novo não reescreve suas publicações.

O complemento posterior de estado16 para seis seeds tem [protocolo próprio](protocolo_complemento_estado16.md) e [estado verificável](../registros/complemento_estado16/estado.json). São três ajustes novos e três herdados R0; a comparação anterior permanece preservada. O complemento está concluído/conferido. O [relatório consolidado](resultados_estados32_64.md) agora compara8/16/32/64 nas mesmas seis seeds; [consolidação posterior](../registros/complemento_estado16/comparacao_atual.json).

A investigação dos quatro estados foi encerrada como bloco separado, sem mover artefatos. A [ADR0012](adr/0012-referencia16-e-proxima-hipotese.md), o [fechamento](../registros/investigacoes/estados_internos_001/fechamento.json) e a [referência16/seis seeds](../registros/referencias/mamba16_ohlcv24_001.json) orientam os próximos contrastes. A [seção11 do desenho](desenho_ohlcv24.md#11-referência-adotada-e-próxima-hipótese-proposta) propõe somente taxa0,0002→0,0001; proposta não inicia treino.

A proposta de taxa foi ampliada e autorizada para8/16/32/64, seis seeds cada: [ADR0013](adr/0013-taxa-aprendizado-quatro-estados.md), [protocolo delimitado](protocolo_taxa_aprendizado.md) e [estado/progresso próprios](../registros/taxa_aprendizado/estado.json).24ajustes novos,29heranças; preparação/qualificação não significam conclusão.

A grade de taxa está encerrada/conferida: [relatório de resultados e análise](resultados_taxa_aprendizado.md), [conferência posterior interpretativa](../registros/taxa_aprendizado/analise_interpretativa_atual.json) e [fechamento](../registros/taxa_aprendizado/fechamento.json). Médias em seis seeds são principais; recorte de três é diagnóstico. Nenhuma candidata satisfez o critério primário; referência16/0,0002 mantida.
