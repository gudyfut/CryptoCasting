# ADR 0007 — Separar mercado, entradas e execução

Decisão e registro: 28/10/2026. Situação: adotada para organização/implementação dos dados, sem treinamento.

## Contexto e autorização

Após a preparação de R0, o pesquisador definiu outra prioridade: revisar os módulos antes de treinar, começando pela coleta Binance, sua pipeline, conferência e camada configurável de entradas. Esta decisão não altera retrospectivamente os estudos de retornos nem a preparação congelada de R0. Não autoriza novas hipóteses científicas ou buscas.

## Decisão

Criar `mercado_binance/` para aquisição pública, normalização do contrato de mercado, validação e agregação; `entradas_modelo/` para representação, alvo, contexto, divisões e escalas; `infraestrutura/` para publicação/rastreabilidade compartilhadas. Usar `run_dados.py`, configuração de mercado e configuração de entradas separadas. Documentar contratos e limites em [arquitetura dos dados](../arquitetura_dados.md).

Reutilizar os ZIPs íntegros das quatro moedas; gerar artefatos novos sem sobrescrever dados, fontes ou recibos antigos. Preservar a receita científica de R0 e testar equivalência com ela. Uma consulta pequena real à API e um download mensal verificam os caminhos de aquisição, sem recoleta integral.

## Alternativas e consequências

Editar diretamente `previsao24/coleta.py` e a preparação R0 quebraria a ligação entre fontes e execuções congeladas. Apenas redistribuir arquivos, mantendo alvo/scaler dentro da coleta, não resolveria o acoplamento. A separação nova conserva temporariamente dois caminhos: os históricos continuam reproduzíveis, o caminho modular será integrado por etapas.

O consumidor recebe um conjunto identificado e contrato explícito. Receitas novas exigem testes e nova identidade; não exigem recolher o mercado. Não publicar resultados parciais como completos. Não usar teste de dados como prova de treinamento, desempenho ou lucro.

## Verificação e próximos passos

Evidências em [estado dos dados](../../registros/dados/estado.json) e fatos na [cronologia](../andamento.md). Conferir causalidade, purga, escalas, casos inválidos, integridade, aquisição real e equivalência numérica antes da entrega. A etapa seguinte é revisar modelos/consumo e treinamento; a referência congelada não será modificada silenciosamente.
