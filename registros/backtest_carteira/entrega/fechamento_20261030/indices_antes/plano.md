# Plano de trabalho

Atualizado em 29/10/2026. O [TCC1](docs/TCC_1_MuriloRFM.pdf) orienta a investigação iterativa do Mamba com OHLCV e avaliação temporal. O método concreto está apenas no [desenho OHLCV](docs/desenho_ohlcv24.md), para evitar versões concorrentes.

## Etapas

Situação posterior às etapas abaixo: estados/taxa concluídos e preservados. A rodada CryptoMamba adaptada foi concluída e conferida em seis seeds, sem repetição de referências; [resultado e análise](docs/resultados_cryptomamba_adaptado.md). O critério de melhora não foi atendido e a referência16/0,0002 permanece. [Protocolo](docs/protocolo_cryptomamba_adaptado.md) e [estado real](registros/cryptomamba/estado.json) distinguem qualificação, preparação, execução e auditoria. Referência16/0,0002 mantida até análise; nenhuma busca posterior automática.

1. **Preservar e separar a fase preliminar:** ciclos de retornos e extensões concluídos, indexados no [arquivo](arquivo/estudos_preliminares_2026-10-28/README.md); fontes, artefatos e recibos intactos. Relatórios/diagnósticos editoriais arquivados, com navegação atualizada.
2. **Definir R0 e preparar o fluxo:** BTC/1h/168h→24h, cinco canais, uma divisão temporal, seis ajustes principais e dois controles; implementação separada, testes sintéticos e conferência independente dos dados. Situação factual e recibos na [cronologia](docs/andamento.md).
3. **Revisar módulos antes de treinar:** prioridade posterior solicitada pelo pesquisador. Dados e entradas separados conforme a [arquitetura](docs/arquitetura_dados.md)/ADR0007; consumo por modelos conferido conforme a [arquitetura dos modelos](docs/arquitetura_modelos.md)/ADR0008. Treinamento/seleção/checkpoints e avaliação agora têm [arquitetura integrada](docs/arquitetura_treinamento.md)/ADR0009, com identidade e qualificação próprias em `registros/treinamento/`. Preservar R0 anterior; a rodada foi autorizada por “ok” explícito em29/10/2026; consultar o estado atual em `registros/treinamento/estado.json`.
4. **Executar a referência após a revisão:** Mamba/LSTM nas três seeds, Naive e ARIMA. Sem ablações simultâneas. Conferir controles, checkpoints, origens, métricas e custos antes de interpretar. Ainda sem treino de mercado desta referência.
5. **Evoluir uma variável por ciclo:** hipótese, antecedente, única diferença, orçamento e critérios antes dos ajustes; examinar desempenho e estabilidade na validação. Publicar fracassos; não escolher a seed vencedora. Nenhuma busca automática autorizada.
6. **Avaliação temporal ampliada:** R0 e no máximo uma candidata; walk-forward com reestimação em cada bloco. Os períodos conhecidos permanecem retrospectivos, mesmo após nova divisão; confirmação independente requer dados/condições apropriados.
7. **Redação e análise acadêmica:** escrever método, evolução, resultados e limites a partir das evidências. Alinhar delimitação BTC/24h com o orientador; não presumir aceite. Não exigir vitória do Mamba ou lucro para concluir o TCC.

A implementação/qualificação não é resultado de mercado. Os estados atuais são verificáveis em `registros/treinamento/`; `registros/ohlcv/` conserva a preparação anterior; a preparação não inicia o executor de treinamento. O portal existente ainda mostra o estudo preliminar.

## Relação com o histórico

O plano anterior de 20/10 estudou quatro moedas/contextos com entrada de retornos do fechamento. A referência foi concluída em21/10; a extensão da penalização em27/10; a pré-normalização em28/10. Cada uma tem protocolo e identidade preservados. A cronologia detalhada, contagens, resultados e incidentes ficam em [andamento](docs/andamento.md) e no arquivo preliminar, sem repeti-los neste plano.

A passagem a R0 altera mais de um fator e não mede isoladamente o efeito de OHLCV. As comparações controladas começam a partir da nova referência. A [ADR0006](docs/adr/0006-reorganizacao-e-desenho-ohlcv.md) explica a transição; o [procedimento de registro](docs/registro_de_experimentos.md) rege os próximos ciclos.

Rodada controlada delimitada em29/10: estado interno Mamba16→8, seis seeds, comparação primária pareada em17/42/2026. Mantém R0 e suas entradas/política. Consultar [protocolo](docs/protocolo_estado_mamba.md) e [estado](registros/estado_mamba/estado.json); não iniciar variações adicionais automaticamente.

Fechamento em29/10: a extensão estado8 foi concluída/conferida, sem melhora preditiva demonstrada. Preservar R0 e a variante como tentativas distintas. [Relatório](docs/resultados_estado_mamba.md) e `registros/catalogo_estudos.json` identificam desenhos/modelos/resultados. As próximas etapas continuam dependendo de hipótese e orçamento próprios.

Sequência autorizada em29/10: Mamba32 e depois64, seis seeds cada, mantendo os outros fatores. [Protocolo](docs/protocolo_estados32_64.md) e [índice operacional](registros/estados_ampliados/estado.json). Configurações definidas antes do primeiro treino; não adaptar64 ao resultado32. Comparar8/32/64 em seis seeds e os quatro estados em três comuns.

Fechamento32/64 em29/10: sequência concluída/conferida, médias comparadas em grupos separados de três/seis seeds. [Relatório consolidado](docs/resultados_estados32_64.md). Não houve melhora consistente com aumento do estado; futuras hipóteses permanecem sem execução automática.

Complemento estado16 autorizado em29/10: executar somente7/123/31415 e herdar17/42/2026 de R0, completando a comparação dos quatro estados em seis seeds. [Protocolo](docs/protocolo_complemento_estado16.md) e [estado](registros/complemento_estado16/estado.json). Nenhuma configuração ou baseline adicional autorizado.

Complemento16 concluído/conferido: os quatro tamanhos agora são comparáveis nas mesmas seis seeds. [Tabela e interpretação](docs/resultados_estados32_64.md). Mantém-se a exploração retrospectiva e a exigência de novo ciclo delimitado para qualquer próxima alteração.

A investigação de capacidade está encerrada: seguir com16estados como referência de trabalho, conforme [ADR0012](docs/adr/0012-referencia16-e-proxima-hipotese.md), sem alegação de ótimo universal. O próximo contraste proposto muda apenas taxa AdamW0,0002→0,0001, seis seeds, resto fixo. Método/critério na [seção11 do desenho](docs/desenho_ohlcv24.md#11-referência-adotada-e-próxima-hipótese-proposta); ainda sem implementação, qualificação ou execução de mercado. Não combinar revisão Spot/normalização nessa rodada.

A proposta da taxa foi ampliada pelo pesquisador aos quatro estados e autorizada como grade24ajustes (ADR0013). Congelar tudo antes do primeiro treino; única mudança em cada par é0,0002→0,0001. Comparar seis seeds por estado, com receita/dados/Spot preservados. [Protocolo](docs/protocolo_taxa_aprendizado.md), [estado verificável](registros/taxa_aprendizado/estado.json). A autorização termina nessa grade.

Fechamento da hipótese de taxa: grade24concluída/conferida, sem benefício demonstrado da redução0,0002→0,0001 na validação. Manter referência16/0,0002; teste/Spot secundários não alteram a regra. [Resultados e limites](docs/resultados_taxa_aprendizado.md). Não há novo treinamento autorizado após esse encerramento.
