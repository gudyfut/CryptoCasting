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

Registrar toda tentativa relevante, inclusive falhas, resultados ruins e conclusões provisórias. Qualquer revisão de implementação/inicialização deverá produzir nova execução identificada, mantendo este piloto. Mudanças metodológicas devem ser justificadas antes de novas avaliações; F1–F8 continuam bloqueados.
