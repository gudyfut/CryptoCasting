# Marcos e decisões do projeto

Esta cronologia distingue datas documentadas, datas de execução desconhecidas e datas de importação. As evidências experimentais individuais estão na [linha do tempo](LINHA_DO_TEMPO.md).

| Data documentada | Marco / decisão | Evidência e consequência |
|---|---|---|
| 14/09/2026 | Reinício científico e remoção dos experimentos exploratórios por solicitação do pesquisador | `AGENTS.md`; dados removidos não são reconstituídos. Exposição prévia a scores continua sendo uma limitação a declarar. |
| 28/09/2026 | Protocolo 1.6 inclui LSTM como segunda baseline | [Protocolo](../docs/protocolo_experimental.md); AR(1) permanece como comparador estatístico. |
| Data de execução não preservada nos JSONs antigos | AR(1) BTCUSDT nos folds D1–D4 | Quatro registros originais importados; a ordem dos folds não demonstra a ordem das execuções. BA média histórica 49,11%. |
| 13/10/2026, antes do piloto neural | Infraestrutura e Mamba/LSTM implementados, testes sem treinamento | Entregas 4–5; isso ainda não constituía validação de treinamento real. |
| 13/10/2026, 16:00 UTC | Piloto pareado CPU autorizado pelo pesquisador e executado pelo agente | [Relatório](../docs/entregas/05_mamba_base/resultados_piloto_BTC_D1_cpu.md); Mamba 41,46%, LSTM 50%, AR(1) 46,34% em D1. |
| 13/10/2026, após execução | Auditoria, recarga de checkpoints e investigação do resultado | Integridade aprovada; generalização não demonstrada. Backend oficial/CUDA indisponível na máquina. |
| 13/10/2026, revisão posterior | Histórico versionado e diagnóstico do fallback | [Análise](analises/2026-10-13_diagnostico_mamba.md); diferença de inicialização em relação ao Mamba oficial documentada. Resultado original preservado e classificado em revisão. |

## Regra de continuidade

### 13/10/2026 — revisão aberta das tarefas de previsão

O pesquisador solicitou comparar formas de previsão e seus momentos de emissão, com explicação visual na interface. Foi criado o [estudo de tarefas A–H](../docs/estudo_tarefas_previsao.md), com pesquisa, prioridades propostas, requisitos e limites. Próximo candle já integrava o contrato 1.6; a interface dava destaque insuficiente a ele. C–H são candidatas, não decisões de implementação. Não houve treinamento ou alteração do dataset/alvos nesta revisão. A ampliação da grade depende da definição das tarefas, e F1–F8 continuam bloqueados. O piloto NVIDIA permanece qualificação técnica de A. A versão executável continua 1.6 até nova decisão registrada.

Registrar toda tentativa relevante, inclusive falhas, resultados ruins e conclusões provisórias. Qualquer revisão de implementação/inicialização deverá produzir nova execução identificada, mantendo este piloto. Mudanças metodológicas devem ser justificadas antes de novas avaliações; F1–F8 continuam bloqueados.

### 13/10/2026 — separação dos eixos e simplificação integral da interface

Após nova avaliação do pesquisador, o catálogo A–H foi reorganizado: ele misturava alvos, horizontes, origens e políticas de seleção. A interface agora tem cinco seções, cinco formulações ilustradas e um explorador de combinações com moeda/candle/prazo/alvo/contexto/agenda. Prazos de 3, 7 e 14 dias são candidatos para discutir usos entre dias e semanais; nomes de estilos de trading não substituem horizontes exatos. Fontes primárias e limites estão no [estudo atualizado](../docs/estudo_tarefas_previsao.md). A seleção de referências não constitui ranking bibliométrico. Nenhuma nova tarefa foi adotada ou treinada; o protocolo executável 1.6, os pilotos e o bloqueio final foram preservados. Rascunhos da interface são temporários e não alteram arquivos de treino.
