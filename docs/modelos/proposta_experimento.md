# Proposta de experimento

Modelo para um estudo distinto, conforme o [procedimento de registro](../registro_de_experimentos.md). Reutilizar uma proposta existente quando bastar. Preencher as partes aplicáveis, justificar itens não aplicáveis e salvar com nome próprio; não executar este modelo nem apresentá-lo como ciclo realizado. Uma análise sem treino não precisa inventar uma grade neural.

- Nome do estudo proposto e ADR, se houver decisão material:
- Natureza: experimento / análise posterior / comparação metodológica:
- Data da proposta e responsável:
- Ciclo anterior e motivo da mudança:
- Situação: proposta / autorizada (com evidência) / cancelada:
- Resultados e períodos já consultados antes desta proposta:

## Pergunta e comparação

- Pergunta principal e hipótese, incluindo possibilidade de resultado negativo:
- Contribuição esperada para o TCC e o que será aprendido mesmo sem melhoria:
- Comparação principal e métricas secundárias:
- Fatores alterados (valor anterior → novo valor ou grade):
- Fatores mantidos constantes:
- Interações que serão analisadas e limites de atribuição causal:

## Dados e previsões

- Origem, período, moedas, frequência, timestamps e disponibilidade causal:
- Dataset anterior reutilizado ou nova preparação, com identidade a gerar:
- Entradas, fórmulas, aquecimento, lacunas, normalização e treinamento dos scalers:
- Alvo, horizonte, contextos em tempo e número de passos:
- População comum e possíveis exclusões:
- Datas de treino, validação, teste e purga:
- Classificação da avaliação e exposição prévia:

## Treinamento e seleção

- Modelos e baselines, arquitetura/capacidade e versões:
- Pesos: aprendidos, inicialização, transferência ou intervenção proposta; origem e preservação dos checkpoints, quando aplicável:
- Hiperparâmetros, otimizador, seeds, orçamento máximo, parada e época selecionada:
- Se houver busca: espaço completo, regra de seleção por validação e registro de candidatos/falhas:
- Referências herdadas versus novos ajustes:
- Número planejado de células, controles, pilotos e custo estimado:
- Ambiente, qualificação e testes necessários:

## Avaliação e operação

- Agregação, comparações pareadas, bootstrap/dependência e multiplicidade:
- Critérios de aceite e o que seria inconclusivo:
- Critérios de suficiência da investigação, separados de promover um modelo para uso operacional:
- Simulação econômica, se aplicável: sinais, execução, custos, capital e limites:
- Critério de encerramento; não continuar procurando até obter resultado favorável:

## Evidência e preservação

- Caminhos futuros para configuração, protocolo, fontes congeladas, tentativas e publicações:
- Autorizações necessárias e evidências recebidas (não presumir aprovação do orientador):
- Registro dos incidentes, dados/modelos preservados e plano de distribuição:
- Depois da execução: preencher ID real, links de auditoria/relatório e atualizar o catálogo e andamento sem substituir a proposta original congelada:
- Achados a consolidar: observação, evidência, interpretação, limitações e ligação com uma seção do artigo:
