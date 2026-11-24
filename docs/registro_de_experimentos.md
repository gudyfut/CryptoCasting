# Procedimento de pesquisa e registro

Aplicar as [diretrizes de pesquisa](diretrizes_pesquisa.md) para transformar uma pergunta em evidência e conclusão utilizável no TCC. A escala do registro acompanha o trabalho: uma conversa conceitual, revisão textual ou correção simples não exige um novo ciclo, ADR ou conjunto de documentos. Atualizar o material que já cumpre a função.

## Fluxo de trabalho

| Etapa | Conteúdo necessário | Onde fica |
|---|---|---|
| Pergunta | O que queremos aprender, por quê, conhecimento prévio, referência e contribuição esperada para o TCC | Proposta existente ou [modelo de proposta](modelos/proposta_experimento.md); decisão material pode justificar ADR |
| Planejamento | Fatores, dados, comparação, seleção, métricas, orçamento, dependências e encerramento | Protocolo/configuração próprios quando houver experimento distinto; próximas ações em `plano.md` |
| Autorização | Escopo efetivamente solicitado e limites de recursos | Registro pertinente ao ciclo; não inventar autorização nem pedir novamente a já recebida |
| Preparação e qualificação | Identidades, ambiente, contratos e verificações proporcionais ao método | Fontes, manifestos e recibos da execução; [guia técnico](ambiente_e_execucao.md) |
| Execução | O que realmente ocorreu, tentativas, interrupções e cobertura | Pasta própria da execução, logs e estado |
| Conferência | Integridade, métricas, comparação prevista, incerteza e limites | Auditoria e publicação identificadas |
| Interpretação e escrita | Achados, evidências, limites, perguntas respondidas e implicações | Análise pertinente e [roteiro de redação](roteiro_redacao_tcc.md); cronologia recebe apenas o fato material |

As etapas distinguem proposta, autorização e resultado; não são um ritual obrigatório para toda edição. Uma análise sem treino identifica fontes, método e saída, sem inventar checkpoints. Revisão de literatura identifica pergunta, referências verificadas e limitações. Redação referencia evidências existentes, sem gerar um novo experimento.

## Antes de um experimento

1. Delimitar a pergunta e o que constituirá evidência favorável, desfavorável ou inconclusiva. Registrar resultados e períodos já conhecidos; distinguir proposta anterior à execução de reconstrução retrospectiva.
2. Definir os fatores alterados e os preservados. Uma ablação isola um fator; uma receita composta ou grade fatorial deve declarar suas interações e limites de atribuição. Explicitar o tratamento dos pesos, da inicialização e de referências herdadas quando aplicável.
3. Fixar dados, disponibilidade causal, alvo, frequência, contexto, população comum, lacunas, scalers, divisões temporais e purga. Uma alteração de entrada pode reutilizar o mercado já coletado; uma preparação diferente precisa de identidade própria.
4. Definir métricas, referências, pareamentos/seeds, critério de seleção e orçamento. Se houver busca, identificar espaço, feedback permitido, todos os candidatos e falhas, condições de promoção/parada e confirmação reservada. Selecionar no conjunto previsto para isso, sem aproveitar o teste para escolher o vencedor.
5. Declarar exposição dos períodos e limites de generalização. Dados conhecidos continuam retrospectivos; não chamar um novo recorte desses mesmos dados de confirmação intocada. Política operacional e custos são definidos apenas quando fizerem parte da pergunta.
6. Conferir autorização e qualificar o necessário antes de congelar e executar. Registrar configuração efetiva, versões, fontes, ambiente, dados e dependências. Não modificar uma identidade científica existente para incorporar a nova hipótese.

Exemplo: acrescentar média móvel exige janela, colunas de origem, instante de disponibilidade, aquecimento, lacunas, escala e população comparável. Trocar candles de 1h por 15min altera o número de passos; declarar separadamente contexto em tempo e horizonte previsto. Uma métrica melhor após mudar alvo e população não isola o efeito da nova entrada.

## Durante e depois

Guardar identidade da tentativa, fatores, data/horário, máquina, configuração efetiva, fontes e estado. Preservar logs, checkpoints, escalas e previsões conforme o método; Naive não exige checkpoint neural e uma interrupção pode não gerar previsões finais. Falhas conservam a causa conhecida ou a hipótese de diagnóstico. Não apagar tentativa por resultado ruim nem repetir automaticamente após falha.

Controles não entram nas médias principais. Relatar cobertura, heranças, diferenças de população/executor, pesos de agregação e dependência temporal. Seeds e origens sobrepostas não são evidências independentes de mercados diferentes. Resultados de tarefas distintas não são diretamente ordenáveis por seus escores. Não somar retornos de carteiras independentes.

Publicar após a cobertura e as conferências previstas, ou identificar explicitamente a entrega como parcial. Um bug exige delimitar o alcance em dados, treinamento, métrica, simulação ou apresentação. Correções científicas produzem uma revisão/publicação ou ciclo identificado, conservando o original; revisão textual não altera recibos nem transforma evidência ausente em resultado zero.

## Como registrar um achado útil ao TCC

Acrescentar uma seção curta na análise ou síntese pertinente, com:

- **Pergunta e observação:** o que foi examinado e o que os resultados mostram, incluindo resultados negativos.
- **Evidência:** ciclo/artefato, comparação, população, métrica e localização verificável; fonte bibliográfica quando aplicável.
- **Interpretação e limites:** o que é sustentado, o que permanece hipótese, incerteza, exposição dos dados e possíveis confundidores.
- **Implicação:** pergunta respondida, cuidado metodológico, próxima hipótese justificável ou motivo para encerrar a investigação daquele recorte.
- **Destino na escrita:** seção ou argumento do artigo que poderá usar o achado, ligado ao [roteiro](roteiro_redacao_tcc.md) ou ao [planejamento editorial](../escrita_tcc/cronologia_narrativa/planejamento_artigo.md).

Não copiar grandes tabelas entre documentos. Usar links para a publicação e consolidar interpretações quando várias observações sustentarem o mesmo ponto. Achados exploratórios não viram conclusões confirmadas por serem interessantes. A síntese [exploracao_ia.md](exploracao_ia.md) cobre a fase Astra identificada; não deve absorver toda pesquisa futura ou substituir a narrativa geral do TCC.

## Função de cada material

| Material | Responsabilidade |
|---|---|
| `AGENTS.md` e [diretrizes](diretrizes_pesquisa.md) | Entrada geral e princípios de pesquisa |
| `plano.md` | Próximos passos e vínculos de estado, sem duplicar placares |
| `docs/README.md` | Navegação |
| `docs/andamento.md` | Cronologia factual única |
| `registros/catalogo_estudos.json` | Índice retrospectivo de estudos e evidências; não é pré-registro nem substitui artefatos |
| `docs/adr/` | Decisões materiais, motivos, alternativas e consequências; não um documento por mensagem |
| Protocolos e `configuracoes/` | Método e receita identificados; estudo encerrado conserva seu contrato |
| `dados/experimentos/`, `dados/diagnosticos/`, `dados/reavaliacoes/` | Tentativas/publicações, análises posteriores e releituras financeiras identificadas |
| `registros/` e pastas das execuções | Estados, controles, recibos, incidentes e auditorias |
| `escrita_tcc/` | Narrativa, planejamento editorial, LaTeX e materiais de apoio |
| `arquivo/` | Evidências e versões históricas preservadas |

Os layouts científicos já executados permanecem intactos; o catálogo resolve diferenças de localização. Só atribuir ID de execução depois de existir execução identificada. Uma proposta, teste sintético, alteração documental ou herança não conta como novo treino de mercado.

## Preservação e auditoria

Antes de editar documentos vinculados a fechamentos, preservar os bytes anteriores ou verificar que há versão recuperável. Um arquivo não rastreado ou ignorado não está salvo no Git/remoto; commits locais também não comprovam backup externo. Seguir a [política de armazenamento](armazenamento_e_reproducao.md), sem regenerar hashes ou normalizar finais de linha para aceitar divergências.

Na raiz, no ambiente configurado, usar `python -B -m manutencao.auditar_repositorio --integridade --exigir-completo`. A auditoria acrescenta localização explícita dos originais preservados aos critérios do auditor histórico e grava recibo próprio. Não inicia treino nem faz reparos; sua cobertura não representa todos os estudos, todos os dados brutos ou validade científica das conclusões. Ausência de artefatos e divergência de hashes são situações diferentes. Conferir também os manifestos específicos exigidos pelo material alterado.

Para continuar em outra máquina, conferir commit/alterações, orientações, plano, estado, disponibilidade dos artefatos e integridade pertinente. Não treinar para compensar pacote ausente. A cadeia para a escrita é: pergunta/decisão → método → execução → evidência conferida → interpretação com limites → argumento no artigo.
