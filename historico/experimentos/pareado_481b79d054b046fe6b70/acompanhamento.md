# Acompanhamento

## 2026-10-13T16:40:12.293216+00:00 — registro inicial

Situação: **em_revisao**. Executado pelo agente com autorizacao do pesquisador. Integridade e recarga de checkpoints conferidas. Diferenca de inicializacao do fallback requer qualificacao; causa da baixa BA nao isolada. Consulte [diagnostico posterior](../../analises/2026-10-13_diagnostico_mamba.md).

## Próximas revisões

Acrescentar data, responsável, motivo, evidência, classificação e vínculo com nova execução. Preservar entradas anteriores. Resultado desfavorável não implica invalidade técnica; auditoria aprovada não implica conclusão científica.

## 2026-10-13 — revisão do piloto

Responsável: agente, a pedido do pesquisador. Situação: **em revisão**. Foram preservadas as [evidências adicionais da auditoria](evidencias_adicionais/inventario.json), sem alteração dos originais. O [diagnóstico posterior](../../analises/2026-10-13_diagnostico_mamba.md) recarregou os pesos existentes e encontrou baixa discriminação no treino, mudança de distribuição e diferença de inicialização do fallback. A causa do resultado não está isolada. Qualificar a implementação antes da ampliação da grade; nenhuma correção ou novo treinamento foi executado nesta revisão.

## 2026-10-13 — conferência da exportação antes do primeiro commit

CSVs derivados foram formatados com 17 dígitos significativos, preservando os valores numéricos das probabilidades float32 também na leitura como float64. Tipos originais registrados no inventário e hashes dos CSVs recalculados. Os parquets e demais artefatos originais não foram alterados; não houve novo experimento.
