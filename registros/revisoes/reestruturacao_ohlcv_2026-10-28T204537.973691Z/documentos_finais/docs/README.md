# Documentação: por onde começar

## Trabalho atual

1. [TCC1 original](TCC_1_MuriloRFM.pdf): objetivo acadêmico e fundamentação; original preservado.
2. [Desenho OHLCV em 24h](desenho_ohlcv24.md): documento único para fechar entradas, alvo, treinamento, variações e avaliação. Proposta; ainda sem treinamento novo.
3. [Plano de trabalho](../plano.md): etapas atuais e distinção do plano histórico.
4. [Andamento](andamento.md): única cronologia factual.
5. [Roteiro de redação](roteiro_redacao_tcc.md): como usar as evidências no artigo.

## Histórico e evidências

- [Estudos preliminares até 28/10](../arquivo/estudos_preliminares_2026-10-28/README.md): referência de retornos, penalização, normalização e ligação ao estudo anterior de barreiras.
- [Catálogo](../registros/catalogo_estudos.json) e [mapa dos registros](../registros/README.md): execuções, tentativas, checkpoints e recibos.
- [ADRs](adr/README.md): somente decisões duráveis, não cada pergunta ou época.
- [Registro de experimentos](registro_de_experimentos.md) e [preservação](armazenamento_e_reproducao.md): como manter rastreabilidade e transportar artefatos.
- [Cronograma acadêmico preservado](../arquivo/estudo_barreiras_2026-10-20/projeto/docs/Cronograma_Atividades_TCC2_Murilo_Monferrari.pdf): documento administrativo; não comprova aceite de entregas.

Os protocolos `protocolo_experimental.md`, `protocolo_penalizacao_mamba.md` e `protocolo_normalizacao_mamba.md` descrevem **execuções históricas congeladas**. Permanecem nos caminhos originais porque seus bytes/endereços participam de recibos e referências. Os relatórios `resultados_*.md` e diagnósticos anteriores são acessados pelo arquivo preliminar; sua presença nesta pasta não os torna o desenho atual.

## Regra para evitar fragmentação

- Resposta explicativa normalmente fica na conversa; não criar Markdown, ADR ou pasta de revisão só por haver uma nova mensagem.
- Refinamentos do desenho atual ficam em `desenho_ohlcv24.md`; fatos de execução ficam em `andamento.md`.
- Novo documento só para um artefato com função própria: protocolo de ciclo que será implementado, relatório de ciclo concluído, decisão material ou entrega solicitada.
- Recibos técnicos, logs, extrações e medições ficam em `registros/` ou na execução. Snapshot documental apenas antes de alteração material que precise preservar uma versão vinculada, não por cada pequena edição.
- Não mover/apagar evidências antigas apenas para reduzir o número de arquivos. Não produzir versões concorrentes de cronologia ou placar.

Essas regras também estão no [AGENTS.md](../AGENTS.md), para valerem nas próximas interações.
