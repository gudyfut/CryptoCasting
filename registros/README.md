# Mapa dos registros científicos

O [catálogo](catalogo_estudos.json) é o índice estruturado das execuções; [andamento](../docs/andamento.md) é a cronologia única. Para entender a fase posterior à interface, ler a [síntese da exploração com IA](../docs/exploracao_ia.md).

## Como ler um ciclo

- `execucao.json`: identidade, pasta de artefatos e vínculo ao congelamento.
- `estado.json`: situação observada; conferir host/PID/logs se houver execução ativa.
- Autorizações, qualificação e preparação: distinguem o que foi proposto do que foi executado.
- Fechamento, publicação e conferências: resultados e integridade, com leitores posteriores identificados.
- Incidentes: falhas e suas resoluções; não apagar por parecerem arquivos temporários.

Os layouts históricos variam. O catálogo aponta as fontes corretas; ausência local não equivale a zero treinamentos. Heranças não são ajustes novos. Ciclos encerrados não devem ser reexecutados para gerar relatório.

Para retomar a etapa mais recente, usar [ensemble_2026/entrega.json](ensemble_2026/entrega.json) e o [índice dos12modelos utilizados](ensemble_2026/modelos_utilizados.json). Checkpoints e scalers continuam em seus estudos originais; o índice identifica caminhos/hashes/épocas sem copiá-los. Mercado novo, previsões, carteiras, métricas e figura pertencem à identidade2026, separada de2024/2025. A [verificação de organização](ensemble_2026/organizacao/verificacao.json) registra integridade e versões editoriais, sem substituir o fechamento científico.

O marco de continuidade diária está em [continuidade_moedas/fechamento.json](continuidade_moedas/fechamento.json): comparação ampliada de408carteiras, referências diárias, incidente técnico e continuação preservados. Não substitui a primeira comparação BTC em `continuidade_diaria/`, nem os custos vigentes ou modelos publicados. Os ledgers compactados, tabelas e figuras ficam em `dados/reavaliacoes/` sob a identidade do fechamento.

## Fase de exploração com IA consolidada

O contraste [historico_treino](historico_treino/estado.json), acumulado versus12meses, é uma etapa histórica posterior à exploração. A etapa vigente está indicada no [plano](../plano.md) e no [catálogo](catalogo_estudos.json); seu andamento deve ser consultado no estado próprio. Ponteiros, qualificações, autorizações e artefatos de cada ciclo permanecem independentes.

| Registro | Função |
|---|---|
| [busca_astra](busca_astra/estado.json) | Primeira busca e candidata final |
| [comparacao_astra_crua](comparacao_astra_crua/estado.json) | Comparação no mesmo executor |
| [futuros](futuros/estado.json) | F01: primeira simulação de futuros |
| [smart_mercados](smart_mercados/estado.json) | F02: política comum Spot/futuros |
| [revisao_operacional](revisao_operacional/estado.json) | F03: contabilidade e hipóteses de política |
| [busca_astra_002](busca_astra_002/estado.json) | Segunda busca, sem finalista |
| [operacional_futuros](operacional_futuros/estado.json) | Busca conjunta modelo/política |
| [diagnostico_operacional](diagnostico_operacional/estado.json) | Diagnóstico de leitura posterior |
| `organizacao_exploracao_ia_001/` | Consolidação, inventário, limpeza e duas verificações |

Modelos, previsões e carteiras estão em `dados/experimentos/`; tabelas diagnósticas em `dados/diagnosticos/`. Os registros acima não duplicam todos esses arquivos. As investigações anteriores, dados, módulos e referências continuam indexados no catálogo em seus próprios diretórios.

## Regras de manutenção

Não guardar explicações de chat como novos relatórios aqui. Recibos e snapshots só quando necessários para uma execução, incidente, transferência ou preservação de versão vinculada. Dados e artefatos congelados mantêm seus caminhos; fontes encerradas são localizadas pelo índice do pacote histórico. Não reescrever hashes nem selecionar seeds favoráveis.

Arquivos locais ignorados pelo Git não estão protegidos remotamente. A transferência entre máquinas deve incluir os pacotes e a [verificação de integridade](../docs/armazenamento_e_reproducao.md). Auditoria atual: `python -m manutencao.auditar_repositorio --integridade --exigir-completo` no computador executor.

## Fontes de desenvolvimento encerrado

Os recibos, resultados, logs e incidentes mantêm suas identidades. Scripts avulsos de revisões e versões editoriais antigas foram consolidados no [pacote de fontes](../arquivo/desenvolvimento_encerrado/README.md), com cada caminho e hash original no índice. Os caminhos citados nos registros históricos continuam identificando os originais; o auditor atual localiza esses bytes explicitamente no pacote. Essa localização não aceita uma fonte local divergente nem altera hashes científicos. As leituras posteriores úteis estão em [analises/etapas](../codigo/analises/README.md).

Fatorial temporal BTC de12/11: [autorização](eixo_temporal_diario/autorizacao.json), [qualificação](eixo_temporal_diario/qualificacao.json), [execução](eixo_temporal_diario/execucao.json) e [estado](eixo_temporal_diario/estado.json). A/B herdados após equivalência prefixo200; C/D novos, separados dos estudos anteriores.
