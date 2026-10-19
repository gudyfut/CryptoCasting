# Entregas ao orientador — conferência em 19/10/2026

Esta conferência usa o cronograma original de 12 entregas e as evidências atuais do estudo de barreiras. Distingue **trabalho tecnicamente disponível**, **correspondência com o compromisso original** e **envio/aceite pelo orientador**. Não há, nas fontes examinadas do repositório, comprovantes suficientes para declarar todas as entregas formalmente enviadas ou aceitas. Alterações combinadas fora do repositório precisam ser incorporadas ao registro.

## Recuperação do cronograma

**Atualização confirmada pelo pesquisador em 19/10/2026:** a alteração do cronograma, especialmente a substituição do experimento de granularidade por contexto e prazo, **ainda precisa ser apresentada ao orientador**. Portanto, essa reformulação está pendente de apresentação e alinhamento; não deve ser registrada como aprovada. Esta confirmação não informa o envio ou aceite individual das demais entregas.

O [PDF original](Cronograma_Atividades_TCC2_Murilo_Monferrari.pdf) foi adicionado em `30cf69c` (15/09/2026) e removido em `dbe2a96` (19/10/2026, mensagem “Estagio 5”). A cópia imediatamente anterior, obtida de `ea2a403`, foi restaurada em 19/10/2026, sem alterar seu conteúdo ou reescrever Git.

- Arquivo: `docs/Cronograma_Atividades_TCC2_Murilo_Monferrari.pdf`.
- Tamanho: 5.100 bytes; uma página.
- SHA-256: `5c94b86b55ce6d9cdf997edae1145c1304d5119f9a1934a5c65d2deba588e33e`.
- A página foi extraída e conferida visualmente. O PDF não imprime o ano; a associação a 2026 é sustentada pelos registros do projeto e pelo histórico de setembro/outubro de 2026.
- A mensagem do commit não explica especificamente por que o cronograma foi excluído. Não atribuir uma intenção sem evidência.

O PDF é uma referência administrativa. Restaurá-lo não restaura a metodologia direcional antiga nem substitui o protocolo científico de barreiras vigente.

## Correspondência entre cronograma e trabalho disponível

| Nº | Período original | Entrega prevista | Situação técnica em 19/10/2026 |
|---:|---|---|---|
| 1 | 08/09–13/09 | Desenho experimental fechado | Conteúdo disponível na versão de barreiras: protocolo 2.1 e configuração executada. O alvo foi revisto; o aceite acadêmico da mudança não está comprovado. |
| 2 | 14/09–20/09 | Dataset bruto reproduzível e coleta funcional | Conteúdo disponível: 144 arquivos mensais, quatro moedas, coleta e verificações. |
| 3 | 21/09–27/09 | Pipeline de amostras prontas para treino | Conteúdo disponível: base 1m, entradas 1h, rótulos de barreira, normalização causal e dataset auditado. |
| 4 | 28/09–04/10 | Infraestrutura walk-forward e primeiros resultados de baseline | Conteúdo disponível: folds temporais, métricas, frequências do treino, AR(1) e comparações com LSTM. Resultados negativos e limites do AR(1) documentados. |
| 5 | 05/10–11/10 | Mamba integrado, treinando em GPU e produzindo previsões | Conteúdo disponível: Mamba oficial/CUDA, checkpoints, seeds, 192 ajustes neurais pareados e auditorias do ciclo. Evidência do ciclo atual é de 18/10, posterior ao prazo original de 11/10. |
| 6 | 12/10–18/10 | Experimento de granularidade e contexto | **Parcial em relação ao PDF.** Contextos 24/168h comparados; granularidade permaneceu 1h. Prazos 1/24/168h foram comparados, mas isso não substitui automaticamente o experimento de granularidade. Há material para propor a reformulação desta entrega. |
| 7 | 19/10–25/10 | Experimento de representação das entradas | **Semana corrente; experimento ainda não executado.** As redes usaram a mesma representação fixa; não há comparação OHLCV versus indicadores/alternativas. A investigação de probabilidades é material de discussão, não essa ablação. |
| 8 | 26/10–01/11 | Normalização/configurações internas e seleção controlada | **Pendente.** Existe proposta 002 de estado 16→8; não foi executada. Não há comparação concluída entre normalizações ou configuração final escolhida. |
| 9 | 02/11–08/11 | Robustez com múltiplas seeds | **Pendente.** O ciclo de mercado usa apenas seed 42. Recargas exatas não são repetição entre sementes. |
| 10 | 09/11–15/11 | Análise científica final | **Pendente como entrega final.** Há análise completa do primeiro ciclo de desenvolvimento; confirmação final e conclusões do estudo inteiro não estão concluídas. |
| 11 | 16/11–22/11 | Texto quase final e código organizado | **Não comprovada.** Documentação e portal não substituem os capítulos finais da monografia. |
| 12 | 23/11 | Fechamento para apresentação/submissão | **Futura; não comprovada.** A data do PDF não comprova a data oficial da defesa ou da submissão institucional. |

Síntese: **objetivos técnicos das entregas 1–5 cobertos no escopo atual; entrega 6 parcial/alterada; entrega 7 na semana corrente; entregas 8–12 futuras.** Isso não é “cinco entregas aceitas” nem prova de pontualidade histórica. Uma implementação disponível hoje não prova que estava disponível em setembro.

Os **seis marcos técnicos do ciclo 001**, em [registro_entregas.md](registro_entregas.md), são outra decomposição do trabalho. Não correspondem às seis primeiras linhas do PDF. A referência acadêmica tem 12 entregas; o ciclo técnico tem seis marcos.

## O que precisa ser apresentado ao orientador agora

1. Relatório de progresso do ciclo inicial, com resultados, limitações e rastreabilidade.
2. Mudança do alvo para barreiras e justificativa operacional; evidências atuais não respondem mais exatamente à formulação direcional antiga.
3. Correspondência da entrega 6: contexto e prazo estudados, granularidade fixa. Solicitar alinhamento dessa reformulação, sem marcar o compromisso original como integralmente cumprido.
4. Escolha do trabalho a entregar em 25/10: manter o experimento de entradas ou revisar explicitamente a sequência para diagnóstico/comparadores/ablação de informação.
5. Eventual adoção da [proposta de pesquisa adaptativa](proposta_pesquisa_adaptativa.md), com orçamento, data de congelamento e espaço para confirmação e redação.

Até haver registro de alteração acordada, o PDF permanece a referência disponível para conferir os compromissos originais. Não se enviou mensagem ao orientador nesta conferência.
