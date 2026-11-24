# Diretrizes de pesquisa do TCC

## Finalidade e critério de sucesso

Orientação geral definida pelo pesquisador em **11/11/2026**: desenvolver o TCC por investigação iterativa de entradas, pesos, configurações, hiperparâmetros, estruturas e tipos de previsão, acumulando conclusões úteis para a redação. O repositório sustenta treinamento, validação, teste, análise, registro, preservação e produção de materiais acadêmicos.

Uma conclusão satisfatória responde às perguntas estudadas com evidências, limites e explicações claras. Não depende de superar todas as referências, confirmar uma hipótese ou produzir um modelo muito bom para operar no mercado. Resultados positivos, negativos e inconclusivos devem receber tratamento proporcional à sua evidência. Buscar melhorias continua válido; prolongar a busca até aparecer um ganho não é critério de encerramento.

Mamba e previsão de criptomoedas são o núcleo da trajetória existente. O recorte de cada estudo pode investigar entradas, candles, contexto, histórico de treino, alvos, horizontes, representação, arquitetura, aprendizado dos pesos, inicialização, regularização, perdas, seleção ou política operacional. A escolha deve responder a uma pergunta delimitada, com comparação e orçamento próprios. LSTM, ARIMA, Naive e outras referências participam conforme a pergunta; nenhuma grade, moeda, taxa ou política antiga é obrigatória para todo trabalho futuro.

A [proposta acadêmica original](TCC_1_MuriloRFM.pdf) permanece como referência histórica. Mudanças de escopo devem ser declaradas no texto e alinhadas com a orientação acadêmica; autorização do pesquisador neste repositório não comprova aceite do orientador ou da instituição. O PDF original não deve ser editado.

## Princípios científicos

1. **Pergunta antes do resultado.** Definir o que se quer aprender, a referência, a métrica e os limites da comparação antes de executar. “Melhor” pode significar menor erro, melhor calibração, estabilidade, eficiência ou utilidade operacional, conforme o critério declarado. Explorações posteriores são legítimas quando identificadas como exploratórias.
2. **Temporalidade e causalidade.** Usar apenas informações disponíveis na origem da decisão; ajustar scalers no treino; respeitar candles completos, aquecimento, lacunas, unidades, purga e realização do alvo. Não inventar candles, interpolar lacunas ou excluir observações por retorno futuro. Mudanças no tratamento dos dados exigem preparação identificada e justificativa.
3. **Comparação interpretável.** Preservar população comum, pareamentos, seeds, orçamento e executor quando a comparação exigir equivalência. Distinguir ablação de um fator, interação e comparação de receitas completas. Declarar diferenças e referências herdadas; herança não é novo treino. Controles de reprodução ficam fora das médias científicas.
4. **Seleção e avaliação distintas.** Selecionar checkpoints e receitas nas partições previstas pelo protocolo; não selecionar no teste. Separar desenvolvimento adaptativo e confirmação reservada. Uma divisão fixa não é walk-forward; reestimações por bloco usam somente o passado permitido. Nunca aplicar checkpoint treinado no futuro a períodos anteriores.
5. **Incerteza e limites.** Mostrar dispersão, suporte, dependência temporal e condições de validade. Seeds e previsões sobrepostas não são mercados independentes. Uma busca finita não demonstra impossibilidade geral; ausência de evidência não prova equivalência. Não transformar um corte encontrado em diagnóstico em filtro confirmado pelo mesmo resultado.
6. **Preservação e rastreabilidade.** Conservar todas as tentativas pertinentes, inclusive falhas e resultados desfavoráveis. Vincular conclusões às configurações, fontes, previsões e conferências que as sustentam. Corrigir com nova versão identificada, conservando o original e explicando o alcance da revisão.

### Exposição dos períodos

Na trajetória já realizada, 2023 teve desenvolvimento adaptativo e 2024–2025 foram consultados. Reutilizá-los não cria holdout intocado. Conferir a exposição de cada população e a de 2026 antes de reservar dados desse ano. Os protocolos e recibos delimitam o que cada estudo efetivamente observou; a nova prioridade acadêmica não muda essa história.

Atualização de11/11/2026: o ensemble fixo foi avaliado de01/01 a10/11/2026, após [auditoria de exposição e declaração humana](../registros/ensemble_2026/exposicao.json). Esse recorte agora está conhecido; o [fechamento](../registros/ensemble_2026/fechamento.json) identifica a avaliação. Não estender essa classificação automaticamente ao restante do ano nem chamar o recorte já consultado de nova confirmação intocada.

### Previsão e uso operacional

Distinguir OHLCV coletado de canais efetivos; contexto de previsão de histórico de treino; saída normalizada de retorno real; retorno terminal de payoff por lado; score de probabilidade. Menor MSE, acerto direcional, atividade e resultado financeiro respondem a perguntas diferentes.

Quando houver simulação, apresentar lucro líquido, drawdown, exposição, custos, funding e estabilidade separadamente. Não somar retornos de carteiras independentes, excluir operações retrospectivamente ou certificar execução, liquidação e tarifas históricas da exchange por convenção de backtest. Permitir compras e vendas não exige operar nos dois lados em todo regime. Corrigir contabilidade e mudar uma política são intervenções diferentes. A utilidade operacional é uma dimensão possível da pesquisa, não uma exigência para todo experimento ou para a conclusão do artigo.

### Uso de IA e intervenção nos modelos

Separar os papéis de proponente, executor e avaliador, inclusive quando a mesma ferramenta os desempenhar em etapas distintas. Isso não exige múltiplos agentes. O processo de seleção não recebe confirmação reservada nem pode alterar o avaliador para favorecer candidatos. Feedback deve incluir sinal, suporte, regime, risco, custos e motivos de rejeição quando aplicáveis, além da métrica agregada.

Distinguir pesos aprendidos de hiperparâmetros. Se uma hipótese envolver inicialização, edição direta ou transferência de pesos, explicitar a intervenção, sua origem e o controle de comparação; preservar checkpoints originais. Não chamar uma sugestão de IA de resultado experimental ou atribuir melhora a um mecanismo que não foi isolado.

## Registro e escrita ao longo do trabalho

Usar o [procedimento de registro](registro_de_experimentos.md) para documentar pergunta, decisão, execução e conclusão na escala necessária. Um achado relevante deve conservar a evidência, a interpretação, as limitações e a implicação para a pergunta do TCC, mesmo quando não indicar uma melhoria. Incorporação ao artigo exige conferir a fonte e distinguir observação de explicação causal.

Reutilizar o [roteiro de redação](roteiro_redacao_tcc.md) e os materiais de [escrita](../escrita_tcc/README.md). Não produzir uma síntese paralela por interação. Revisão de literatura, redação, figuras, organização e correção técnica também são trabalho do TCC; não precisam virar ciclos de treinamento.

## Manutenção das instruções

O [AGENTS.md](../AGENTS.md) é a entrada curta; este documento contém princípios; o [plano](../plano.md) contém prioridades e vínculos de estado; procedimentos e arquiteturas detalham tarefas; protocolos, configurações, recibos e ADRs identificam estudos e decisões. Números e exceções específicos de uma execução ficam em sua evidência, sem virar regra universal. Ao alterar uma orientação, corrigir os guias de entrada que a repetem, preservando documentos vinculados a fechamentos conforme a [política de armazenamento](armazenamento_e_reproducao.md).

Essa organização adapta a separação entre princípios, especificação, planejamento e execução do [Spec Kit](https://github.github.io/spec-kit/quickstart.html) às perguntas e evidências de pesquisa. A adaptação usa os arquivos que o projeto já possui; não instala o framework nem exige um conjunto de documentos por tarefa.

A [documentação oficial do Codex](https://learn.chatgpt.com/docs/agent-configuration/agents-md) descreve a descoberta hierárquica de `AGENTS.md`. Aqui, documentos Markdown comuns são consultados pela instrução explícita do guia principal. Um link serve de indicação de leitura, sem pressupor inclusão automática. Criar instruções locais somente quando houver regras específicas estáveis; cópias de `AGENTS.md` em arquivos históricos são evidência da época, não orientação vigente para o projeto atual. Fontes consultadas em 11/11/2026.
