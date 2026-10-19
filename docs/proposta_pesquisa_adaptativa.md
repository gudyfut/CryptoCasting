# Proposta em discussão — pesquisa experimental adaptativa

Data: 19/10/2026. **Avaliação de possibilidade; não altera o protocolo 2.1 nem aprova uma nova grade.** Preserva o ciclo 001, a proposta 002 como não executada, as quatro moedas e o bloqueio de B1–B4. O enquadramento e o cronograma acadêmico dependem de alinhamento com o orientador.

## Enquadramento sugerido

**Situação do alinhamento em 19/10/2026:** o pesquisador confirmou que a alteração do cronograma ainda precisa ser apresentada ao orientador. Esta proposta deve compor essa discussão; não representa uma mudança acadêmica já acordada.

**Título de trabalho:** Investigação experimental adaptativa de previsões úteis para o mercado de criptomoedas: comparação entre Mamba e LSTM.

**Pergunta:** em quais formulações de previsão e condições experimentais Mamba apresenta vantagens ou limitações em relação a LSTM, considerando qualidade preditiva, estabilidade, custo computacional e utilidade econômica sob regras explícitas?

**Objetivo:** desenvolver e comparar, por ciclos documentados, alternativas de representação, treinamento e previsão, procurando as melhores soluções dentro de um orçamento e domínio delimitados. A conclusão pode favorecer Mamba, favorecer LSTM, ser inconclusiva ou mostrar ausência de vantagem econômica. Não se promete melhor resultado possível em sentido global nem lucro como requisito de conclusão do TCC.

O protocolo atual já permite desenvolvimento iterativo de configurações, mas mantém a tarefa de barreiras como referência. Permitir novos tipos de alvo amplia o escopo e exige versões adicionais. Cada ciclo fechado continua sendo descrito pelo protocolo realmente executado, sem reescrever o passado sob a proposta nova.

## Liberdade entre ciclos e compromissos de avaliação

| Pode mudar mediante decisão registrada antes do novo ciclo | Permanece exigência da comparação |
|---|---|
| Features, indicadores causais e representação | Nenhuma informação futura no input, scaler ou ajuste |
| Contexto, frequência do candle e horizonte | Pareamento temporal; quatro moedas preservadas; efeito de contexto e prazo identificável |
| Arquitetura, estado, largura, dropout e otimização | Mamba e LSTM comparados na mesma tarefa/população, com orçamento explícito |
| Pesos de classe, calibração e regra de treinamento | Ajuste no treino/validação; probabilidades verificadas na distribuição-alvo |
| Tipo de previsão: barreiras, direção, quantis/retornos etc. | Nova definição do alvo, métricas apropriadas e comparadores correspondentes |
| Política de transformar previsões em decisões | Custos, execução, risco e seleção da política declarados; teste final protegido |
| Próxima hipótese, conforme os achados anteriores | Registro de todas as tentativas, falhas e escolhas; parada por orçamento/calendário |

Não é obrigatório alterar só um parâmetro por vez. Um desenho fatorial pequeno, interações ou uma busca limitada também podem ser legítimos. Entretanto, mudar cinco fatores simultaneamente mede o efeito do pacote; não identifica qual fator causou a diferença. Ablações ou referências pareadas são necessárias quando essa atribuição faz parte da conclusão.

## Dois tipos de comparação que não podem ser confundidos

1. **Efeito da arquitetura:** mesma tarefa, dados, informação e regras de treino comparáveis; trocar Mamba por LSTM. É o desenho mais direto para atribuir diferenças à arquitetura.
2. **Melhor solução de cada família dentro de um orçamento:** permitir configurações próprias de Mamba e LSTM e conceder oportunidades comparáveis de otimização. Registrar tentativas e custo. Isso compara pipelines selecionadas, não a arquitetura isolada. Não otimizar Mamba extensamente e tratar uma LSTM fixa como se fosse a melhor LSTM possível.

Número de tentativas e tempo de GPU são orçamentos distintos; escolher o critério e reportar ambos. Uma GPU mais rápida ou uma rede maior não torna a previsão mais correta. A repetição de seeds mede variabilidade e não deve ser usada para selecionar apenas a seed favorável.

## Como comparar tarefas diferentes

Log-loss binária, log-loss de três classes e erro de quantis medem alvos diferentes. Nem mesmo trocar a largura das barreiras preserva a dificuldade do problema. Não misturar esses números em um ranking absoluto.

- Dentro de cada tarefa: comparar modelos e melhoria frente a uma referência apropriada, nas mesmas origens e com incerteza. Mesmo um ganho relativo frente ao baseline não torna tarefas diferentes equivalentes.
- Entre tarefas: usar uma decisão operacional comum previamente definida, com mesmo período, capital, custos, risco e restrições, ou apresentar uma comparação por múltiplos critérios sem declarar um vencedor absoluto.
- Barreiras avaliam primeiro evento; quantis usuais do preço no horizonte avaliam a distribuição terminal. Quantis terminais não informam sozinhos qual stop ou alvo seria atingido antes. A política e a avaliação precisam respeitar essa diferença.
- “Útil” deve ser operacionalizado: melhoria probabilística/calibração e, para a alegação econômica, desempenho líquido e risco sob uma política explícita. Não trocar a medida de sucesso depois de observar qual favoreceu Mamba.

A simulação Spot existente não equivale a uma simulação de futuros. Se futuros forem adotados, fonte, margem, funding, liquidação e preços de referência precisam de outro contrato antes de qualquer alegação de utilidade nesse mercado.

## Validação de um processo que aprende com os próprios resultados

Os DB1–DB4 já consultados pertencem ao desenvolvimento. Podemos aprender com eles para escolher o próximo ciclo. Quanto mais escolhas forem feitas sobre esses resultados, menor a justificativa para tratá-los como evidência confirmatória. Separar treino e teste dentro de cada execução não elimina o viés da busca que consulta repetidamente o teste.

O processo terá uma etapa de desenvolvimento adaptativo e uma confirmação temporal externa à seleção. Antes da abertura de B1–B4, congelar tarefa final, modelos, calibração, regras de decisão, métricas e política de reestimação; documentar exposição anterior aos dados. Se o final orientar outra alteração, ele passa a desenvolvimento e outra confirmação é necessária. Uma validação temporal aninhada é alternativa, mas requer desenho próprio; não aplicar k-fold aleatório em séries com rótulos sobrepostos.

O risco de sobreajuste na seleção está documentado em [Cawley e Talbot, 2010](https://www.jmlr.org/papers/v11/cawley10a.html). A [documentação do scikit-learn](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html) distingue seleção e estimativa externa de desempenho; seu exemplo não é uma receita temporal pronta para este dataset.

## Recorte viável para o calendário atual — sugestão, não agenda aprovada

O PDF prevê fechamento em 23/11. Em 19/10, faltam 35 dias corridos. Há espaço para iteração delimitada, mas não para uma busca aberta em todas as tarefas, frequências, arquiteturas e políticas.

| Período original | Adaptação proposta para discussão |
|---|---|
| 19–25/10 | Alinhar escopo e entrega 6; investigar representação/calibração e um comparador simples. Decidir se uma única tarefa alternativa merece um piloto limitado. |
| 26/10–01/11 | Executar ciclos selecionados de configuração/ablação com orçamento simétrico entre redes. Encerrar busca de novas tarefas até 01/11, mesmo sem ganho. |
| 02–08/11 | Confirmar referências e candidatos com múltiplas seeds de desenvolvimento; congelar a seleção e preparar a avaliação final, com exposição prévia declarada. |
| 09–15/11 | Executar a avaliação final apenas se todos os gates estiverem atendidos, e consolidar conclusões. Se não houver tempo/integridade, reduzir escopo e declarar a limitação; não inventar confirmação. |
| 16–22/11 | Finalizar capítulos, figuras e reprodutibilidade; a escrita deve avançar em paralelo desde agora. |
| 23/11 | Fechamento documental conforme o cronograma disponível. Não presume data oficial de defesa. |

Uma sugestão de contenção é manter barreiras como referência e admitir **no máximo uma tarefa alternativa inicialmente**, expandindo somente mediante justificativa e saldo de orçamento. O conjunto completo de combinações não é obrigatório; o ciclo 001 já contém a exploração inicial de quatro moedas, contextos e prazos.

## Entrega de cada ciclo

Antes: hipótese, mudança, configuração, identidade dos dados, referências, orçamento e critério de seleção/parada. Depois: todas as execuções, verificação, resultados favoráveis/desfavoráveis, incerteza, custo, limitações e decisão sobre o próximo ciclo. Uma hipótese negativa pode encerrar um ramo. A monografia explica o processo e a evidência, não apenas a configuração vencedora.

**Recomendação:** adotar flexibilidade nas hipóteses e nas soluções, mantendo um compromisso estável com comparação justa e avaliação independente. A atividade científica pode procurar desempenho melhor sem exigir que Mamba vença ou que o produto final seja rentável.
