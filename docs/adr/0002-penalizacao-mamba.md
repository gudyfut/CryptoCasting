# 0002 — Corrigir a penalização em experimento separado

- Decisão autorizada: 26/10/2026.
- Registro desta ADR: 27/10/2026, retrospectivo.
- Situação: adotada; conclusão deve ser consultada nos registros.
- Autorização: pesquisador, descrita no [protocolo da extensão](../protocolo_penalizacao_mamba.md).

## Contexto

A revisão de 24/10 identificou AdamW uniforme com weight decay 0,001, inclusive nos parâmetros A_log e D marcados pela biblioteca oficial como isentos. O otimizador não interpretava automaticamente esse marcador. Isso não invalida o cálculo das métricas dos modelos efetivamente treinados, mas justifica medir o efeito da correção.

## Decisão

Excluir da penalização somente os parâmetros marcados, mantendo os demais fatores. Preservar integralmente o código e os resultados da referência. Executar 384 ajustes Mamba corrigidos e dois controles originais para reprodução, herdando as referências LSTM/Naive/ARIMA. Não acrescentar busca de hiperparâmetros nem remover a penalização de outros pesos.

## Consequências

A extensão tem código, protocolo, configuração e identidade próprios. Os períodos DB/B já eram conhecidos; a comparação é retrospectiva. Melhora não é pressuposto nem condição de conclusão. A grade deve ser auditada antes da comparação final. Não modificar fontes congeladas ou duplicar a execução em outra máquina.

## Evidências

- [Parecer da revisão](../../registros/revisoes/parecer_2026-10-24.json).
- [Auditoria das configurações](../auditoria_configuracao_penalizacao.md).
- [Configuração da extensão](../../configuracoes/penalizacao_mamba_001.json).
- [Ponteiro da execução](../../registros/penalizacao/execucao.json), que indica onde consultar `progresso.json` na máquina executora.
- [Andamento e incidentes](../andamento.md).

Esta ADR não substitui os recibos de execução e não declara a grade concluída.
