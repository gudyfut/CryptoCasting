# Mapa dos registros científicos

Esta pasta já concentra evidências do trabalho. Não criar outra timeline concorrente nem mover recibos congelados. O histórico factual legível está em [docs/andamento.md](../docs/andamento.md); motivos e decisões estão em [docs/adr/](../docs/adr/README.md).

| Local | Conteúdo |
|---|---|
| `catalogo_estudos.json` | Índice retrospectivo: barreiras arquivadas, retorno24 de referência, extensão e propostas não executadas; liga decisões, dados, configurações e publicações |
| `dataset_atual.json` | Identidade e caminho do dataset; não contém os dados |
| `execucao_atual.json` | Ponteiro do estudo de referência |
| `penalizacao/execucao.json` | Ponteiro separado da extensão corrigida |
| `qualificacao/` | Ambiente e evidências dos testes prévios |
| `penalizacao/preparacao_*/` | Preparação, qualificação e preservação da extensão |
| `analises/<execucao>/<fase>/` | Publicações, tabelas, operações e respectivas auditorias |
| `../dados/experimentos/penalizacao_<execucao>/analises/<fase>/` | Publicações próprias da extensão de penalização, separadas das análises da referência |
| `auditorias/` | Recibos de integridade e fechamento |
| `revisoes/` | Verificações posteriores, pareceres e diagnósticos |
| `incidentes/` | Falhas, interrupções, snapshots e decisões de retomada |
| `interface/` | Verificações e aceite da interface |
| `exposicao_previa.json` | Declaração histórica sobre exposição aos períodos de avaliação |

## Onde estão os modelos e cada tentativa?

O [procedimento de registro](../docs/registro_de_experimentos.md) define como manter essa cadeia ao mudar entradas, dados ou parâmetros. O [modelo de proposta](../docs/modelos/proposta_experimento.md) deve ser preenchido antes de um novo ciclo; resultados conhecidos e autorização precisam ficar explícitos.

Na pasta indicada pelo ponteiro, em `dados/experimentos/<ciclo>/celulas/<id>/tentativa_*/`. Conforme o modelo, os arquivos incluem `tentativa.json`, `resultado.json`, `auditoria.json`, `checkpoint.pt`, `epocas.json`, previsões Parquet e log. Na extensão há também `otimizador.json`; controles reexecutados ficam em `controles/` com organização equivalente.

Esses arquivos devem permitir identificar moeda, contexto, bloco, seed, configuração, escalas, origens avaliadas, seleção de época e resultado da auditoria. Não inferir informações ausentes pelo nome da pasta. Preservar tentativas interrompidas e falhas, inclusive quando outra tentativa termina corretamente.

## Como ler o progresso

1. Resolver o ponteiro do ciclo correto e verificar se a pasta existe localmente.
2. Consultar progresso e tentativas, conferindo data, host e recibos. Para atividade em tempo real, conferir PID/lock/logs no executor.
3. Se houver apenas registros copiados, relatar a data do snapshot. Ausência de pasta não demonstra que o treinamento nunca aconteceu.
4. Diferenciar resultados novos, controles e referências herdadas; não somar revalidação ou recarga como novo treinamento.

Novos recibos devem identificar ciclo, data UTC, ambiente/host quando relevante, escopo, status e caminhos/hashes das evidências. Um manifesto descreve arquivos e permite conferi-los; não substitui seu armazenamento. Seguir a [política de preservação](../docs/armazenamento_e_reproducao.md).

## Conferir o acervo disponível

Na raiz, `python manutencao/auditar_catalogo.py` confere navegação, identidades, fontes, cobertura das duas execuções atuais e publicações. `--integridade` acrescenta hashes dos arquivos manifestados por tentativa e do dataset; `--exigir-completo` falha também por ausência, adequado ao notebook executor. O modo sem essa exigência registra um clone parcial como parcial, nunca como zero treinamentos ou integridade completa. O legado de barreiras tem seus links conferidos; não é reauditado integralmente por essa ferramenta.

Cada uso gera recibo próprio em `revisoes/catalogo_*/`, acompanhado do verificador e catálogo usados. Não modifica os recibos congelados e não repete métricas ou inferência. A conferência científica da extensão continua vinculada ao seu fechamento e à revisão independente de resultados.

Antes desta reorganização, os oito documentos vinculados por hash ao fechamento da extensão foram copiados para `revisoes/organizacao_2026-10-27T223818/documentos_antes/`, com conferência em `inicio.json`. Os hashes do fechamento descrevem essas versões históricas; páginas posteriores têm revisão própria. Arquivos locais não rastreados e binários ignorados continuam exigindo preservação externa verificada.
