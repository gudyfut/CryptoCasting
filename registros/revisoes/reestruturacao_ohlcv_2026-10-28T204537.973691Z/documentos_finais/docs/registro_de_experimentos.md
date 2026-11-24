# Como registrar a evolução dos experimentos

Cada mudança deve permitir responder depois: qual era a pergunta, o que já sabíamos, o que mudou, quem autorizou, quais dados e configurações foram usados, o que foi realmente executado e qual resultado sustentou a conclusão. O projeto aceita evolução de desenho; o requisito é abrir versões identificáveis, em vez de modificar o passado.

**Granularidade do registro:** essas regras se aplicam a decisões e experimentos materiais, não a cada mensagem explicativa. Atualizar a proposta existente, a cronologia e o relatório do ciclo antes de criar documentos novos. Só um novo ciclo com função própria precisa de protocolo/configuração próprios; dúvidas conceituais normalmente ficam na conversa. A navegação atual está em [índice documental](README.md) e a proposta única em [desenho OHLCV](desenho_ohlcv24.md).

O [catálogo de estudos](../registros/catalogo_estudos.json) conecta o estudo arquivado de barreiras, a referência de retorno em 24h e a extensão de penalização. É um índice retrospectivo criado em 27/10/2026, não um pré-registro. A cronologia narrativa permanece somente em [andamento](andamento.md). O catálogo aponta evidências, sem copiar métricas ou transformar ausência de arquivos em resultado zero.

| Etapa registrada | O que consultar | Como relacionar |
|---|---|---|
| Barreiras, ciclo 001 executado e arquivado | [Relatório histórico](../arquivo/estudo_barreiras_2026-10-20/projeto/historico/analises/ciclo_001_resultados.md) | Explica o desenho anterior; não comparar log-loss com MSE |
| Retorno em 24h, ciclo de referência | [Decisão 0001](adr/0001-estudo-retorno-24h.md), [desenvolvimento](resultados_desenvolvimento.md) e [avaliação](resultados_avaliacao.md) | Nova pergunta científica; dados/configuração próprios |
| Penalização do Mamba, extensão controlada | [Decisão 0002](adr/0002-penalizacao-mamba.md) e [relatório](resultados_penalizacao_mamba.md) | Uma intervenção; comparação pareada com a referência preservada |
| Pré-normalização do Mamba, autorizada em 28/10 | [Decisão 0005](adr/0005-proposta-prenormalizacao-mamba.md) e [protocolo](protocolo_normalizacao_mamba.md) | Só muda a posição da LayerNorm; preservar penalização corrigida; estado real no andamento |
| Barreiras, ciclo 002 apenas proposto | [Proposta histórica](../arquivo/estudo_barreiras_2026-10-20/projeto/historico/ciclos/ciclo_002_proposto.md) | Não contar como treinamento ou entrega executada |

## Onde guardar cada coisa

| Informação | Local | Quando registrar |
|---|---|---|
| Regras permanentes e caminhos | `AGENTS.md` | Quando mudar a orientação geral |
| Pergunta, motivo, alternativas, autorização e exposição prévia | `docs/adr/NNNN-*.md` | Ao propor/decidir; indicar se reconstruído depois |
| Método, métricas, grade, seleção e limites | Protocolo específico em `docs/` e configuração própria em `configuracoes/` | Antes dos treinos do novo ciclo |
| Ligação com ciclos anteriores | `registros/catalogo_estudos.json` | Ao registrar um ciclo identificado; propostas não recebem ID de execução fictício |
| Fontes, ambiente, dados e identidade | `execucao.json`, `fontes/`, manifesto do dataset e qualificação | No congelamento, antes do treino de mercado |
| Cada tentativa, inclusive interrompida | `dados/experimentos/<execucao>/celulas/<celula>/tentativa_NNN/` | No início e encerramento de cada tentativa |
| Falha e retomada operacional | `registros/incidentes/` | Na ocorrência; preservar logs e estado anterior |
| Resultados agregados, incerteza e simulação | Publicações próprias da execução, com auditoria e hashes | Após a cobertura exigida para a publicação |
| Interpretação e evolução factual | Relatório por ciclo e `docs/andamento.md` | Após evidência; distinguir hipótese e resultado |
| Revisão posterior ou correção de cálculo | `registros/revisoes/` com vínculo ao original | Sem substituir o recibo anterior |
| Transporte e restauração em outra máquina | `registros/distribuicao/`, conforme política de preservação | Depois de inventariar, enviar e conferir o download |

Os layouts já executados são mantidos. A referência publica em `registros/analises/<id>/<fase>/`; a extensão em sua própria pasta `analises/`. O catálogo resolve essa diferença sem mover arquivos. Uma revisão de documentação não é novo treinamento; revalidar resultados após reinício também não é.

## Antes de mudar dados, entradas ou parâmetros

1. Preencher o [modelo de proposta](modelos/proposta_experimento.md) e a ADR. Registrar a pergunta, o motivo, os resultados conhecidos e quais fatores mudam. Uma ideia ainda não aprovada permanece proposta.
2. Definir o que será comparado. Se a intenção é medir um fator, manter os demais constantes. Se vários fatores mudarem juntos, declarar comparação entre abordagens; não atribuir todo o ganho a um único fator. Grades fatoriais devem explicitar interações e orçamento.
3. Fixar população, alvo, granularidade, entradas, contextos, separação temporal, tratamento de ausências e scalers. Mudança de dados ou preparação exige identidade do dataset/preparação que permita reconstruir os bytes e as janelas usadas. Registrar também fonte, data de obtenção, versões e dependências de cada indicador.
4. Fixar métricas, baselines, seeds, orçamento de busca e regra de seleção. Se houver busca, registrar **todos** os candidatos, falhas e o critério de escolha na validação. Teste não escolhe o vencedor. Ajustes diferentes por arquitetura podem ser legítimos, mas exigem orçamento comparável e justificativa explícita.
5. Registrar exposição aos períodos. B1–B4 já conhecidos não voltam a ser teste intocado. Se houver novas decisões usando seus resultados, tratá-las como exploração retrospectiva. Definir dados realmente novos ou avaliação prospectiva para confirmação, quando disponível.
6. Criar configuração e protocolo novos, relacionando-os ao ciclo de referência. Qualificar o ambiente, testar os contratos, congelar fontes/configuração/dados e só então executar, dentro da autorização dada. Não editar `previsao24/` ou `experimento_penalizacao/` sob as identidades já congeladas.

Exemplo: adicionar média móvel à entrada não é só mudar uma lista. É preciso registrar a janela, as colunas de origem, o instante em que o valor passa a ser conhecido, o tratamento do aquecimento/lacunas, a normalização e a população comum entre pares. Passar a candles de 15min muda a resolução e o número de passos: um contexto de 24h passa de 24 para 96 passos. Manter explicitamente o horizonte de 24h evita comparar tarefas diferentes sem perceber.

## Durante e depois da execução

Guardar identidade da célula (moeda/bloco/contexto/seed/modelo e fatores adicionais), data UTC, máquina, configuração efetiva, versão das fontes e política do otimizador quando aplicável. Cada tentativa precisa de seu próprio diretório e estado. Preservar logs, épocas, checkpoint e escalas conforme o modelo; tentativas concluídas devem guardar previsões por origem e auditoria. Naive não exige checkpoint neural, e uma interrupção pode não ter previsões finais. Registrar falhas com causa conhecida ou hipótese identificada como tal. Nunca apagar uma tentativa por resultado ruim.

Uma execução passa por proposta, autorização, preparação, qualificação, congelamento, execução, auditoria e publicação. Esses estados são distintos: testes sintéticos não contam como treino de mercado; uma previsão produzida não é automaticamente auditada. Um ensaio rejeitado pode ser útil para a cronologia mesmo sem entrar no placar principal.

Comparações devem indicar quais modelos foram reexecutados e quais foram herdados, diferenças de população e orçamento, pesos da agregação, incerteza temporal, seeds e custos da simulação. Se a população mudar, conservar o resultado original e, quando autorizado, calcular a comparação alinhada em uma nova análise identificada. Não comparar diretamente log-loss de barreiras com MSE de retorno. Não usar a contagem de janelas sobrepostas como número de observações independentes.

Se um bug for descoberto depois, registrar seu alcance: código de treino, dados, métrica, simulação ou apresentação. Uma correção científica precisa de novo ciclo ou nova publicação identificada, conforme o alcance; uma revisão textual não deve alterar o recibo de execução. Preservar o material anterior, inclusive conclusões que foram revistas.

## Preservar documentos e trabalhar em mais de um dispositivo

O Git registra alterações **depois de um commit**; arquivo elegível ou não rastreado não está automaticamente salvo no histórico nem no remoto. Antes de editar documentos vinculados por hash a um fechamento, conservar uma cópia dos bytes anteriores ou um commit recuperável. Neste projeto foi preservado o snapshot do fechamento da extensão em `registros/revisoes/organizacao_2026-10-27T223818/documentos_antes/`. O recibo antigo continua descrevendo aquela versão, não a página atual eternamente.

Fontes e artefatos científicos dependem de hashes de bytes. Converter LF/CRLF pode invalidá-los. As regras de `.gitattributes` devem preservar os bytes desses arquivos; não normalizar em massa nem atualizar hashes para aceitar uma conversão. Regras novas não corrigem automaticamente blobs já existentes no Git. Pacotes de reprodução devem levar as fontes congeladas junto dos modelos e ser conferidos após restauração.

Antes de continuar no outro dispositivo: conferir o commit e as alterações locais, ler AGENTS/ADRs/andamento, consultar o catálogo, verificar disponibilidade dos artefatos e executar a auditoria do catálogo. Não iniciar treino para compensar ausência de um pacote. O acompanhamento local e o arquivo de PID de outra máquina não demonstram atividade remota.

## Consulta e auditoria

Na raiz, executar `python manutencao/auditar_catalogo.py`. O verificador usa apenas a biblioteca padrão, não inicia treino e grava um recibo novo em `registros/revisoes/`. Confere links, identidades, relações entre ciclos, cobertura exata das tentativas dos dois layouts ativos, fontes congeladas e manifestos das publicações. Registra ausências separadamente de divergências; dados binários presentes não são considerados integralmente auditados apenas pela existência. `--integridade` também verifica hashes dos artefatos de cada tentativa auditada e do dataset, podendo demorar mais. Usar `--exigir-completo` no notebook responsável pelo fechamento para tratar ausências como erro; um clone parcial continua identificável como parcial.

O recibo também mostra a quantidade e o volume dos arquivos não rastreados elegíveis e diferenças entre fontes científicas do checkout e do commit. O inventário mais amplo desta revisão está em [volumes locais](../registros/revisoes/organizacao_2026-10-27T223818/volumes_locais.json). O verificador não faz commit, upload, download ou reparo automático. Seguir a [política de preservação](armazenamento_e_reproducao.md) para produzir e restaurar pacotes. A publicação externa permanece pendente até existir evidência correspondente.

Para escrever o TCC, seguir a sequência: ADR explica o motivo → protocolo/configuração define o método → execução identifica dados e implementação → tentativas mostram o que ocorreu → publicação sustenta o resultado → revisão/andamento explica sua interpretação e evolução. Ver o [roteiro de redação](roteiro_redacao_tcc.md).
