# ADR0025 — Comparação Smart comum entre Spot e futuros

Data:04/11/2026. Autorização explícita do pesquisador neste chat para executar sem novos treinamentos e avaliar filtro. Não presume aprovação do orientador.

F01 comparou compra versus compra/venda com encerramento diário. Não isolava Spot contra futuros da Smart histórica. Decidimos uma nova rodada identificada, mantendo F01 e todas as previsões anteriores.

Smart retida compartilhada com reserva95%, dimensão/filtros comuns e comissões equivalentes emUSDT; mercado Spot, futuro comprado sem funding (controle hipotético), futuro comprado com funding e futuro bilateral. Custos iguais como comparação principal; ideal e custos por mercado como sensibilidades. Filtro simétrico fixo≈0,30% baseado no custo Spot anteriormente adotado, mantendo posição quando inativo. Sem busca ou treinamento.

Orçamento:1.536carteiras de modelos+96referências,total1.632.64séries herdadas,quatro blocos,oito seeds. [Protocolo](../protocolo_smart_mercados.md), módulos `simulacao_operacoes/smart/` e `experimentos/smart_mercados/`, testes `tests_smart_mercados/`, registros `registros/smart_mercados/`.

Exigir equivalência sintética Spot/futuro em preços idênticos e funding zero, ledger independente, fontes congeladas, lock e preservação antes/depois. Não reescrever Smart histórica nem chamar Smart95 de reprodução exata dela. Períodos retrospectivos, liquidação oficial não integralmente modelada, sem promoção por lucro. Filtro altera comportamento de entrada/saída, não capacidade preditiva dos checkpoints.
