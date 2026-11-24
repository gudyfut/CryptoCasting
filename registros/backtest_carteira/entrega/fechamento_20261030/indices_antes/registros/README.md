# Mapa dos registros científicos

Em28/10, os ciclos anteriores foram agrupados no [arquivo preliminar](../arquivo/estudos_preliminares_2026-10-28/README.md), com relatórios em `documentacao/` e artefatos científicos nos caminhos originais. A referência atual está no [desenho OHLCV](../docs/desenho_ohlcv24.md). Preparação/qualificação/congelamento são separados de treino de mercado. Perguntas explicativas não criam novas pastas de revisão automaticamente; esta reorganização material tem recibos em `revisoes/limpeza_preparacao_ohlcv_2026-10-28T211713.614472Z/`.

Esta pasta já concentra evidências do trabalho. Não criar outra timeline concorrente nem mover recibos congelados. O histórico factual legível está em [docs/andamento.md](../docs/andamento.md); motivos e decisões estão em [docs/adr/](../docs/adr/README.md).

[treinamento/estado.json](treinamento/estado.json) e [treinamento/execucao.json](treinamento/execucao.json) identificam a cadeia modular preparada. `treinamento/qualificacoes/` conserva ensaios artificiais e suas falhas; não são resultados de mercado. O congelamento novo liga dados/modelos/otimização/avaliação, sem substituir ponteiros históricos. Checkpoints por melhora ficam em `celulas/<chave>/tentativa_NNN/checkpoints/`, com seleção, grupos, épocas, previsões e conclusão. Não criar autorização antes do “Ok” do pesquisador.

[modelos/estado.json](modelos/estado.json) aponta a revisão dos consumidores das quatro famílias, testes sintéticos de forward/recarga e conferência de todas as janelas reais. `modelos/conferencias/` guarda tentativas do comando `run_modelos.py conferir`. Não são tentativas de treinamento nem resultados preditivos. Seus ponteiros não substituem `ohlcv/` ou `dados/estado.json`.

A revisão atual começa pelos dados, antes do treinamento. [dados/estado.json](dados/estado.json) aponta os artefatos de mercado, candles e entradas, testes, conferência independente e consultas reais. `dados/falhas/` registra erros do comando de dados. As respostas brutas, tentativas e manifestos ficam sob `../dados/coletas_binance/`, `../dados/mercado/` e `../dados/entradas/`. Não substituir com esses ponteiros os de `ohlcv/`, que pertencem à preparação preservada.

| Local | Conteúdo |
|---|---|
| `catalogo_estudos.json` | Índice retrospectivo: barreiras arquivadas, retorno24 de referência, extensão e propostas não executadas; liga decisões, dados, configurações e publicações |
| `dataset_atual.json` | Identidade e caminho do dataset; não contém os dados |
| `execucao_atual.json` | Ponteiro do estudo de referência |
| `penalizacao/execucao.json` | Ponteiro separado da extensão corrigida |
| `normalizacao/` | Autorização, preparação/qualificação e ponteiro próprio do ciclo de pré-normalização; somente Mamba novo |
| `../dados/experimentos/normalizacao_<execucao>/analises/<fase>/` | Publicações da pré-normalização, com referências herdadas identificadas |
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

A pré-normalização `9e03af2150cbb7b1068d` está concluída e conferida: 384 novos ajustes e dois controles. As publicações estão na pasta própria do ciclo e o fechamento em `auditorias/9e03af2150cbb7b1068d/fechamento_normalizacao.json`. A conferência independente posterior está em `revisoes/normalizacao_2026-10-28T200441.557811_0000/`, com métricas, intervalos, operação e preservação. A auditoria do catálogo com `--integridade --exigir-completo` pode verificar a disponibilidade dos três ciclos concluídos; uma ausência em outra máquina continua sendo indisponibilidade local, não zero treinamentos. Os snapshots preservam o estado anterior em andamento.

Antes desta reorganização, os oito documentos vinculados por hash ao fechamento da extensão foram copiados para `revisoes/organizacao_2026-10-27T223818/documentos_antes/`, com conferência em `inicio.json`. Os hashes do fechamento descrevem essas versões históricas; páginas posteriores têm revisão própria. Arquivos locais não rastreados e binários ignorados continuam exigindo preservação externa verificada.

## OHLCV: preparação e próxima execução

- `ohlcv/dataset.json`: preparação multivariada atual; não reutiliza as máscaras de336h/quatro moedas.
- `ohlcv/qualificacao.json`: recibo de testes sintéticos/ambiente e treinamento curto de verificação; não resultados de mercado.
- `ohlcv/conferencias/`: reconstrução independente dos dados e escalas.
- `ohlcv/execucao.json`: ponteiro para congelamento; consultar `progresso.json` na pasta indicada para distinguir preparado de executando/concluído.
- `ohlcv/qualificacoes/`: conservar também ensaios falhos e superados; apenas o ponteiro identifica a qualificação compatível com as fontes atuais.

O novo fluxo preserva tentativas em `dados/experimentos/ohlcv24_<id>/`; nunca agrega controles de reprodução às três seeds. O auditor do catálogo histórico não afirma ter auditado essa nova grade. Não chamar o executor de ciclo concluído para refazer relatório.

`estado_mamba/` guarda qualificação, autorização e ponteiro da extensão d_state16→8. Não substituir `treinamento/execucao.json` de R0. A auditoria de representação e sensibilidades econômicas fica em `treinamento/auditorias_representacao/`, com verificador e manifesto próprios; não sobrescreve a publicação econômica anterior.

As duas rodadas OHLCV concluídas estão indexadas em `catalogo_estudos.json → rodadas_ohlcv`, com protocolo/configurações congelados, pastas de pesos/previsões, publicação e auditoria. `estado_mamba/conferencias/` guarda a conferência posterior; `docs/resultados_estado_mamba.md` é o relatório desta extensão. A publicação nova agrega6novos+8herdados, não14treinos novos.

`estados_ampliados/` identifica a sequência autorizada32→64. Cada `estadoN/` tem qualificação, ponteiro e auditoria próprios. `fila/congelamento.json` fixa a ordem e as duas identidades antes do primeiro treino; `fila/progresso.json`/`processo.json` mostram o coordenador. O índice `estado.json` deve apontar esses estados operacionais sem funcionar como outra cronologia. Pesos, tentativas e publicações ficam em `dados/experimentos/estados_ampliados_N_<id>/`. Valores herdados não contam como novos ajustes.

`estados_ampliados/comparacao_atual.json` aponta consolidação posterior imutável em `comparacoes/<id>/`, com médias aritméticas por seed, todos os contrastes, fontes e verificador. São dois grupos: três seeds para8/16/32/64 e seis para8/32/64. Não é ensemble ou nova execução; resultados científicos anteriores permanecem intactos.

`complemento_estado16/` guarda protocolo vinculado, qualificação, autorização e identidade do complemento7/123/31415. As três seeds R0 não são repetidas. Resultados novos têm pasta própria; a consolidação nova terá `comparacao_atual.json` próprio, sem substituir a consolidação32/64. O estado verificável fica em `estado.json` e na execução apontada.

Complemento16 encerrado/conferido: três novos+26herdados. `complemento_estado16/comparacao_atual.json` aponta a consolidação posterior dos quatro estados em três/seis seeds; a comparação anterior32/64 permanece intacta. `conferencia_conclusao.json`, `preservacao_depois.json` e o catálogo ligam checkpoints, médias e relatório. Snapshot do relatório/figuras anteriores em `complemento_estado16/documentos_antes/`.

`investigacoes/estados_internos_001/fechamento.json` separa o bloco encerrado8/16/32/64 por índices de variantes/tentativas e hashes, sem mover binários ou contar heranças novamente. `referencias/mamba16_ohlcv24_001.json` identifica a referência de trabalho escolhida:16estados, seis seeds, receita lr0,0002 e checkpoints existentes. Não é execução nova ou ensemble. O catálogo registra a hipótese de taxa0,0001 como proposta, sem execução/qualificação fictícias; a ADR0012 vincula a decisão humana.

`taxa_aprendizado/` guarda a grade autorizada0,0001 nos quatro estados,24novos ajustes. `execucao.json` (após preparar) aponta congelamento único de quatro receitas e29heranças; cada estado/seed tem tentativa própria. `estado.json` é índice e o progresso real fica na execução. Após encerramento, `conferencia_conclusao.json`, `comparacao_atual.json` e `fechamento.json` são pós-processamento de leitura, sem repetir treino.

A grade de taxa foi encerrada/conferida. `taxa_aprendizado/fechamento.json` conserva o fechamento automático. `analise_interpretativa_atual.json` aponta revisão posterior com métricas conferidas, médias3/6seeds, dispersão, fontes e verificador; `revisoes/<id>/relatorio_automatico.md` preserva a versão anterior à interpretação. Nenhum executor concluído foi repetido para produzir o relatório/gráfico.

`cryptomamba/` guarda fontes públicas fixadas por commit/SHA, licença MIT, preservação anterior, qualificação, autorização e ponteiro da adaptação de seis seeds. Núcleo e eixos são conferidos contra o código público; fontes e protocolo congelam antes de mercado. `estado.json` aponta o progresso real; após conclusão, `comparacao_atual.json`, `conferencia_conclusao.json` e `fechamento.json` distinguem seis novos ajustes de53referências herdadas. Pesos e previsões permanecem em pasta própria da execução. Nenhuma referência antiga é reaberta.

`backtest_carteira/` separa simulação de carteira retida de treinamento e do SpotR0. `execucao.json` conserva a tentativa inicial de leitura interrompida com0simulações; `execucao_atual.json` aponta a revisão em `revisao_loader/`. O índice `estado.json` liga ambas. São369simulações delimitadas; pesos e previsões herdados não são refeitos. Fontes,ordens,recusas,curvas,auditoria,controles e resultados vivem na execução própria. Consultar o protocolo e ADR0015; não repetir executor encerrado.
