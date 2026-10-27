# Mapa dos registros científicos

Esta pasta já concentra evidências do trabalho. Não criar outra timeline concorrente nem mover recibos congelados. O histórico factual legível está em [docs/andamento.md](../docs/andamento.md); motivos e decisões estão em [docs/adr/](../docs/adr/README.md).

| Local | Conteúdo |
|---|---|
| `dataset_atual.json` | Identidade e caminho do dataset; não contém os dados |
| `execucao_atual.json` | Ponteiro do estudo de referência |
| `penalizacao/execucao.json` | Ponteiro separado da extensão corrigida |
| `qualificacao/` | Ambiente e evidências dos testes prévios |
| `penalizacao/preparacao_*/` | Preparação, qualificação e preservação da extensão |
| `analises/<execucao>/<fase>/` | Publicações, tabelas, operações e respectivas auditorias |
| `auditorias/` | Recibos de integridade e fechamento |
| `revisoes/` | Verificações posteriores, pareceres e diagnósticos |
| `incidentes/` | Falhas, interrupções, snapshots e decisões de retomada |
| `interface/` | Verificações e aceite da interface |
| `exposicao_previa.json` | Declaração histórica sobre exposição aos períodos de avaliação |

## Onde estão os modelos e cada tentativa?

Na pasta indicada pelo ponteiro, em `dados/experimentos/<ciclo>/celulas/<id>/tentativa_*/`. Conforme o modelo, os arquivos incluem `tentativa.json`, `resultado.json`, `auditoria.json`, `checkpoint.pt`, `epocas.json`, previsões Parquet e log. Na extensão há também `otimizador.json`; controles reexecutados ficam em `controles/` com organização equivalente.

Esses arquivos devem permitir identificar moeda, contexto, bloco, seed, configuração, escalas, origens avaliadas, seleção de época e resultado da auditoria. Não inferir informações ausentes pelo nome da pasta. Preservar tentativas interrompidas e falhas, inclusive quando outra tentativa termina corretamente.

## Como ler o progresso

1. Resolver o ponteiro do ciclo correto e verificar se a pasta existe localmente.
2. Consultar progresso e tentativas, conferindo data, host e recibos. Para atividade em tempo real, conferir PID/lock/logs no executor.
3. Se houver apenas registros copiados, relatar a data do snapshot. Ausência de pasta não demonstra que o treinamento nunca aconteceu.
4. Diferenciar resultados novos, controles e referências herdadas; não somar revalidação ou recarga como novo treinamento.

Novos recibos devem identificar ciclo, data UTC, ambiente/host quando relevante, escopo, status e caminhos/hashes das evidências. Um manifesto descreve arquivos e permite conferi-los; não substitui seu armazenamento. Seguir a [política de preservação](../docs/armazenamento_e_reproducao.md).
