# Documentação do CryptoCasting

**Ciclos recentes concluídos:** [LSTM diária nas quatro moedas](resultados_lstm_diaria.md) e [walk-forward diário BTC](resultados_walkforward_diario.md), ambos auditados. A contribuição dos ramos dependeu do checkpoint, com uma seed de efeito relevante; o desempenho operacional variou entre blocos. Os períodos são retrospectivos e não representam confirmação independente.

**A versus L em 2026:** [resultado e explicação dos modelos](resultados_ablacao_linear_diaria.md#extensão-retrospectiva-al-em-2026), [protocolo](protocolo_ablacao_linear_2026.md), [conferência](../registros/ablacao_linear_2026/conferencia_posterior.json) e [figuras](../registros/ablacao_linear_2026/publicacao/inspecao_visual.json). Extensão encerrada em 13/11; sem treino ou promoção por teste conhecido.

**Fechamento experimental concluído em 13/11:** [relatório canônico](resultados_ablacao_linear_diaria.md#fechamento-fatorial-e-replicação-entre-ativos), [protocolo](protocolo_fechamento_ramos_diarios.md), [auditoria independente](../registros/fechamento_ramos_diarios/conferencia_posterior.json) e [figuras conferidas](../registros/fechamento_ramos_diarios/publicacao_final/inspecao_visual.json). Fatorial BTC e A/L nas quatro moedas; 12 ajustes científicos novos, oito controles exatos e 288 carteiras. Escopo encerrado; incorporar resultados positivos, negativos e limites à redação, sem nova busca automática.

## Orientação vigente

O [guia base](../AGENTS.md) direciona a leitura por tarefa. O projeto tem como finalidade investigar e registrar conhecimento para o TCC, incluindo resultados negativos ou inconclusivos.

| Função | Documento |
|---|---|
| Objetivo e princípios científicos | [Diretrizes de pesquisa](diretrizes_pesquisa.md) |
| Pergunta, planejamento, execução e registro dos achados | [Procedimento de pesquisa](registro_de_experimentos.md) e [modelo de proposta](modelos/proposta_experimento.md) |
| Ambiente, comandos e verificações | [Ambiente e execução](ambiente_e_execucao.md) |
| Preservação, limpeza e transferência | [Armazenamento e reprodução](armazenamento_e_reproducao.md) |
| Argumentos, evidências e produção do artigo | [Roteiro de redação](roteiro_redacao_tcc.md) e [espaço de escrita](../escrita_tcc/README.md) |

## Contexto e estado

**Ablação linear diária concluída em12/11:** [resultado e limites](resultados_ablacao_linear_diaria.md), [protocolo](protocolo_ablacao_linear_diaria.md), [fechamento](../registros/ablacao_linear_diaria/fechamento.json) e [conferência posterior](../registros/ablacao_linear_diaria/conferencia_posterior.json). A versus projeções treinadas do zero, BTC, três seeds/200épocas; controles exatos e60carteiras completas. Menor complexidade sem benefício incremental demonstrado dos ramos nesta receita; não é prova de equivalência ou inutilidade universal do Mamba.

**[Exploração do processo de melhoria de modelos com IA](exploracao_ia.md)** reúne a fase Astra posterior ao panorama web de 03/11: propósito, evolução, resultados, limitações e o planejamento daquele momento. É a síntese histórica dessa fase; as prioridades atuais estão no plano.

[Plano atual](../plano.md) · [Cronologia única](andamento.md) · [Catálogo](../registros/catalogo_estudos.json) · [Mapa dos registros](../registros/README.md).

## Base acadêmica e arquitetura

| Assunto | Documento |
|---|---|
| Proposta original e redação | [TCC1](TCC_1_MuriloRFM.pdf), [roteiro para o artigo](roteiro_redacao_tcc.md) |
| Projeto LaTeX e futura narrativa | [Espaço de escrita reservado](../escrita_tcc/README.md) |
| Referência OHLCV anterior | [Desenho](desenho_ohlcv24.md), [panorama web até 03/11](../dataview/README.md) |
| Dados e entradas | [Arquitetura dos dados](arquitetura_dados.md) |
| Contratos dos modelos | [Arquitetura dos modelos](arquitetura_modelos.md) |
| Treino e seleção | [Arquitetura do treinamento](arquitetura_treinamento.md) |
| Simulação de operações | [Arquitetura operacional](arquitetura_operacoes.md) |
| Registro e decisões | [Procedimento](registro_de_experimentos.md), [ADRs](adr/README.md) |
| Transporte e reprodução | [Política de preservação](armazenamento_e_reproducao.md) |

## Etapa mais recente concluída

[Penalização seletiva diária](resultados_penalizacao_seletiva_diaria.md): concluída em12/11 às13h48BRT, três ajustes científicos e dois controles exatos de200épocas;60carteiras. [Protocolo](protocolo_penalizacao_seletiva_diaria.md), [fechamento](../registros/penalizacao_seletiva_diaria/fechamento.json), [conferência posterior](../registros/penalizacao_seletiva_diaria/conferencia_posterior.json). Sem superioridade demonstrada; ensemble S ficou em caixa em2025.

## Etapas anteriores

[Fatorial temporal × penalização](resultados_eixo_temporal_diario.md) concluído em12/11: seis novos ajustes e dois controles exatos de200épocas, seis referências herdadas;108carteiras completas. [Método](protocolo_eixo_temporal_diario.md), [fechamento](../registros/eixo_temporal_diario/fechamento.json), [conferência posterior](../registros/eixo_temporal_diario/conferencia_posterior.json). Sem superioridade demonstrada da adaptação temporal sobreA.

[Ensemble preservado em2026](protocolo_ensemble_2026.md): período posterior de01/01 a10/11, mesmos12modelos/escalas, sem treino.24carteiras, controles e auditorias concluídos. [Resultados e limites](andamento.md#11112026--ensemble-preservado-avaliação-temporal-em-2026), [exposição](../registros/ensemble_2026/exposicao.json), [fechamento](../registros/ensemble_2026/fechamento.json).

[Continuidade das posições diárias](protocolo_continuidade_moedas.md): reavaliação operacional concluída em11/11 para quatro moedas,408carteiras, mesmos modelos padronizados e referências diárias. [Marco e interpretação](andamento.md#11112026--marco-operacional-continuidade-das-posições-diárias), [ADR0037](adr/0037-continuidade-posicoes-diarias.md), [fechamento e tabelas](../registros/continuidade_moedas/fechamento.json). Menor giro melhorou os resultados; somente ETH tem lucro médio em2025, ainda com elevado drawdown. Fontes anteriores preservadas, sem novo treino neural.

[Generalização para ETH, BNB e XRP](protocolo_generalizacao_moedas.md): receita diária padronizada concluída nas três moedas, modelos e dados separados por instrumento. [Comparação com BTC](../registros/generalizacao_moedas/comparacao_quatro_moedas.json). [Estado real](../registros/generalizacao_moedas/estado.json). Rodada sem penalização encerrada e demais comparações na [cronologia](andamento.md).

Ablação da taxa inicial diária concluída em11/11: [resultado e limites](resultados_taxa_diaria.md), [protocolo](protocolo_taxa_diaria.md), [fechamento](../registros/taxa_diaria/fechamento.json) e [conferência](../registros/taxa_diaria/conferencia_posterior.json). O [diagnóstico consolidado](../registros/taxa_diaria/diagnostico.json) reutiliza os modelos anteriores, com médias e Ridge como referências auxiliares. Resultado negativo preservado; não há treino ativo nesta rodada.

## Estudos encerrados e anexos

| Conjunto | Método e evidência |
|---|---|
| Estudos preliminares | [Arquivo acadêmico](../arquivo/estudos_preliminares_2026-10-28/README.md), [catálogo](../registros/catalogo_estudos.json) |
| Entradas e treinamento modular OHLCV | [Dados](arquitetura_dados.md), [treinamento](arquitetura_treinamento.md), [desenho](desenho_ohlcv24.md) |
| Estados, taxa e otimizador | [Estados](resultados_estados32_64.md), [taxa](resultados_taxa_aprendizado.md), [otimizador](resultados_otimizador_cryptomamba.md) |
| Perda e representação | [Huber](resultados_huber_blocos.md), [entradas](resultados_entradas_niveis.md), [combinação](resultados_crua_huber.md) |
| Exploração assistida por IA | [Síntese e mapa de evidências](exploracao_ia.md) |
| Políticas de futuros | [Arquitetura](arquitetura_operacoes.md), [revisão operacional](resultados_revisao_operacional.md), [busca operacional](resultados_operacional_futuros.md) |
| Receita diária e ablações | [Reprodução](protocolo_cryptomamba_reproducivel.md), [alvo](protocolo_alvo_retorno_diario.md), [padronização](protocolo_padronizacao_diaria.md), [penalização](protocolo_sem_penalizacao_diaria.md) |
| Código de análises posteriores | [Leitores por etapa](../codigo/analises/README.md) |
| Executores e ferramentas encerrados | [Pacote e recuperação verificada](../arquivo/desenvolvimento_encerrado/README.md) |

Os anexos da fase Astra estão indexados ao final da [síntese](exploracao_ia.md#8-onde-as-evidências-ficaram). Para localizar hipóteses anteriores de estados, taxa, otimizador, Huber e entradas, usar o [catálogo de estudos](../registros/catalogo_estudos.json) e o [panorama](../dataview/README.md). Os [estudos preliminares](../arquivo/estudos_preliminares_2026-10-28/README.md) preservam os desenhos antigos de retorno escalar e barreiras.

Os arquivos `protocolo_*.md`, `resultados_*.md`, `desenho_operacional_futuros.md` e `diagnostico_operacional.md` documentam identidades específicas. Sua presença nesta pasta não os torna desenhos atuais. Permanecem nos caminhos originais porque fontes, fechamentos, testes e leitores podem depender deles. Não criar um novo índice ou relatório por conversa; acrescentar informação à função documental pertinente.

As referências de [retorno diário](../registros/retomada_alvo_diario/estado.json) e de preço reproduzível estão concluídas e preservadas. Os respectivos protocolos são históricos; não instruem uma nova execução.
