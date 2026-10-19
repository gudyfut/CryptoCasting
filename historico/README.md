# Registro da pesquisa de barreiras

Cada ciclo começa com hipótese e configuração fixadas antes de executar. Todas as novas tentativas, falhas e resultados ficam registradas. O estudo procura melhorar o desempenho no desenvolvimento, com avaliação final separada.

- `ciclos/`: hipótese, parâmetros, orçamento e decisões por ciclo.
- `execucoes/`: registros leves, resumo de métricas e estado da auditoria.
- `qualificacoes/`: testes funcionais, ambiente e verificações numéricas.
- `analises/`: [relatório integral do ciclo 001](analises/ciclo_001_resultados.md), tabelas, figuras, proveniência e retratos parciais preservados.
- `dados/experimentos/`: checkpoints, previsões, ordens, curvas, scalers e snapshots completos, fora do Git; precisam de backup.

Toda execução identifica fontes de dados, código, protocolo e ambiente. Alteração exige outra identidade; resultado desfavorável não autoriza apagar uma tentativa. A revisão de um resultado deve manter a evidência original e explicar a nova interpretação.

O catálogo de ciclos e a sequência de seleção estão no [protocolo](../docs/protocolo_experimental.md). O [andamento](../docs/andamento.md) distingue implementação, qualificação e execução efetivamente verificadas.
