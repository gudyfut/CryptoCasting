# Leituras posteriores

O gerador editorial [redacao_tcc.py](etapas/redacao_tcc.py) lê resultados encerrados e prepara três tabelas e cinco figuras do artigo, com conferências contra as fontes e registro dos marcos exploratórios. As duas tabelas complementares vêm de `complemento_tcc`; o mapa experimental está no LaTeX. A tabela walk-forward distingue MSE médio individual e MSE do ensemble, conferindo ambos contra publicação e auditoria, além do hash da auditoria, população e Naive. Executar `python -B -m analises.etapas.redacao_tcc` na raiz. Não treina, não faz inferência e não executa backtests; as saídas ficam em `escrita_tcc/`, conforme o [planejamento](../../escrita_tcc/cronologia_narrativa/planejamento_artigo.md). A figura operacional usa previsões, posições e saldos preservados; a trajetória mostra o efeito dos ramos, com zeros numéricos representados sem piso positivo artificial.

`agregacao.py`, `metricas.py` e `previsoes.py` são utilitários compartilhados. `isolar_gradientes_cryptomamba.py` conserva o diagnóstico; os bytes do caminho científico original estão preservados no arquivo. As demais leituras estão agrupadas em `etapas/`:

| Etapa | Pasta |
|---|---|
| Extensão retrospectiva A/L a 2026, encerrada sem treino | [ablacao_linear_2026](etapas/ablacao_linear_2026/): reutiliza modelos/dados; `ciclo.py` guarda inferência e carteiras, `publicar.py` confere independentemente e apresenta. Identidade e estado em `registros/ablacao_linear_2026/`; não sobrescrever ou repetir execução encerrada |
| Ablação linear diária encerrada | [conferir.py](etapas/ablacao_linear_diaria/conferir.py): hashes, controles, métricas e contabilidade; sem treino ou simulação, recibo posterior sem sobrescrita |
| Reavaliação financeira dos custos vigentes | [custos vigentes](etapas/custos_vigentes/) |
| Continuidade diária, quatro moedas e referências | [continuidade_moedas](etapas/continuidade_moedas/): resultados encerrados; `publicar.py` é leitor posterior, sem treino/simulação |
| Ensemble preservado em período posterior de 2026 | [ensemble_2026](etapas/ensemble_2026/): mesma receita, novas previsões sem treino; estado em `registros/ensemble_2026/` |
| Simulações e comparações operacionais de futuros | [futuros](etapas/futuros/) |
| Diagnóstico operacional aprofundado | [diagnostico_operacional](etapas/diagnostico_operacional/) |
| Histórico acumulado versus móvel | [historico_treino](etapas/historico_treino/) |
| Reprodução e calibração da receita diária | [cryptomamba_diario](etapas/cryptomamba_diario/) |
| Comparação de receitas diárias em execução comum | [comparar_ensemble.py](etapas/cryptomamba_diario/comparar_ensemble.py): avaliação encerrada de preço sem padronização versus retorno padronizado; não é o checkpoint publicado |
| Conferência da reprodução | [cryptomamba_reproducivel](etapas/cryptomamba_reproducivel/) |
| Alvo de retorno diário | [alvo_retorno_diario](etapas/alvo_retorno_diario/) |
| Padronização e contribuição dos ramos | [padronizacao_diaria](etapas/padronizacao_diaria/) |
| Generalização e comparação das quatro moedas | [generalizacao_moedas](etapas/generalizacao_moedas/) |
| Retirada da penalização | [sem_penalizacao_diaria](etapas/sem_penalizacao_diaria/) |

Os originais estão preservados nos [pacotes históricos](../../docs/armazenamento_e_reproducao.md). Os scripts de etapas conservam verificações de identidade congelada; quando exigem as fontes originais nos caminhos antigos, sua reprodução depende de uma pasta isolada com o layout original. Não contornar essas verificações apontando para as fontes reorganizadas. O catálogo e os recibos identificam quais análises já foram executadas; a presença de um script não instrui sua repetição. Tabelas, figuras, carteiras e conferências existentes continuam nas pastas científicas originais.
