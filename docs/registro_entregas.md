# Registro de entregas e situação da pesquisa

Atualização documental: 19/10/2026. Esta revisão organiza a apresentação; não altera o protocolo 2.1, a configuração, os checkpoints ou os resultados do ciclo 001.

## Quantas entregas foram concluídas?

**Distinção acadêmica recuperada em 19/10/2026:** o cronograma original tem **12 entregas ao orientador**. Na conferência atual, os objetivos técnicos das entregas 1–5 estão cobertos pelo estudo de barreiras, a entrega 6 está parcial/alterada e a semana da entrega 7 começa hoje. Envio e aceite não estão comprovados. Consulte a [conferência do cronograma](acompanhamento_orientador.md). Os seis marcos abaixo não são as seis primeiras entregas do PDF.

**Seis marcos do primeiro ciclo**, conforme a seção de encerramento de `plano.md`. Essa contagem não corresponde a seis etapas de um total fixo do TCC e não permite calcular uma porcentagem de conclusão acadêmica. Há uma primeira grade completa; a pesquisa iterativa e sua confirmação final ainda não terminaram.

| Marco | Situação | Evidência e conteúdo |
|---|---|---|
| 1. Implementação e verificação | Concluído | Rótulos, causalidade, purgas, normalização e contabilidade; testes de casos-limite. |
| 2. Coleta e pipeline | Concluído | 144 arquivos mensais de 2021–2023; quatro pares; dataset `9341610dbb329a858784`; lacunas preservadas. |
| 3. Qualificação do ambiente e modelos | Concluído | Mamba oficial/CUDA, referência numérica e gradientes; qualificação das simulações do AR(1). Testes sintéticos não são resultados de mercado. |
| 4. Casos iniciais e recargas | Concluído | BTC/W24/H24 e BTC/W168/H168 em DB1; incorporados na grade sem duplicar contagens. |
| 5. Grade de desenvolvimento e auditoria integral | Concluído | 96 células, 192 ajustes neurais e 16 ajustes únicos AR(1); DB1–DB4, seed 42; auditoria suplementar 96/96 aprovada. |
| 6. Consolidação e hipótese seguinte | Concluído | Relatório completo, tabelas, gráficos, incerteza e limitações; proposta 002 documentada, não executada. |

Fontes: `plano.md`, `docs/andamento.md`, `historico/analises/ciclo_001_resultados.md`, `historico/qualificacoes/testes_finais_ciclo_001.json`, registros individuais em `historico/execucoes/` e proposta em `historico/ciclos/ciclo_002_proposto.md`.

## Cronologia e dois calendários diferentes

- **Mercado:** dados de 2021–2023; quatro testes trimestrais de desenvolvimento em 2023. Treinos expansivos por datas e validações anteriores de três meses, com purgas.
- **Execução:** primeiro ajuste registrado da grade às 06:50 UTC de 18/10/2026; último encerramento às 12:21 UTC da mesma data. A interface calcula esses extremos a partir dos registros, sem inferir duração exclusiva de GPU.
- **Fechamento:** consolidação científica e proposta seguinte em 18/10/2026.
- **Apresentação:** em 19/10/2026, organização formal das entregas, ampliação das explicações e publicação local do explorador de previsões. É pós-processamento de leitura, não outro ciclo de treinamento.

## O que permanece pendente

1. Discutir os resultados de desenvolvimento e decidir as próximas hipóteses. A proposta 002 reduz o estado Mamba de 16 para 8 em H168; exige qualificação específica antes de executar.
2. Executar somente ciclos aprovados e registrados, preservar tentativas e confirmar estabilidade entre sementes antes de congelar uma escolha.
3. Congelar protocolo, configuração e política; registrar exposição anterior aos períodos de avaliação.
4. Liberar B1–B4 apenas após os requisitos. Não há resultado final independente disponível e não se presume holdout intocado.
5. Concluir redação, revisão pelo orientador e defesa conforme exigências institucionais. Não há registro que comprove essas entregas acadêmicas como encerradas.

Futuros, posições vendidas, margem, funding e liquidações são uma possível extensão não implementada. O ciclo concluído avalia compra Spot ou caixa. Esta revisão não inicia novos treinos nem essa extensão.

## Conclusão que os resultados atuais permitem

LSTM teve a menor log-loss média (1,009434), próxima de Mamba (1,010357). O intervalo pareado inclui zero, sem superioridade demonstrada entre as redes. O ganho frente às frequências de treino concentra-se em H1; ambas perdem para a referência em H168. Contexto maior não ajudou uniformemente. A política econômica apresentou ganhos, perdas e caixa, com poucas operações; não demonstrou rentabilidade consistente.

## Registro visual e rastreabilidade

O portal local contém o estudo em `/` e o explorador em `/previsoes`. O explorador cobre todas as 96 células e três modelos, com 189.792 previsões por modelo somando os recortes. Essa soma repete datas entre configurações; não representa amostras independentes. São 7.908 origens distintas por combinação no ano.

O exportador `scripts/exportar_explorador.py` verifica hashes, alinha os modelos por timestamp, compara os rótulos e recalcula log-loss/Brier. Os preços vêm do dataset auditado, sem interpolação. Os JSONs comprimidos de leitura ficam em `dataview/.dados/explorador`, fora do Git; o recibo leve fica em `historico/qualificacoes/explorador_previsoes_2026-10-19.json`. O servidor verifica o hash do índice e de cada pacote solicitado. Ausência ou divergência não é substituída por dados fictícios.

Os dados do explorador pertencem à população **preditiva comum observável**, não à população operacional causal. Filtros de acerto/desfecho são retrospectivos e apenas visuais. Previsões não equivalem a ordens executadas. Casos ambíguos são identificados, preservando a convenção inferior-primeiro do ciclo.

A revisão do portal passou por 15 testes da interface, três testes de alinhamento da exportação, verificações das rotas de dados, lint e compilação de produção. Foram conferidas as 1.353 fontes do relatório fechado, sem divergência. O [registro de qualificação da apresentação](../historico/qualificacoes/portal_formal_2026-10-19.json) separa essas verificações dos testes científicos anteriores e inclui evidências visuais em desktop e celular.
