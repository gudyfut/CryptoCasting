# ADR0028 — Linha separada de pesquisa operacional em futuros

Data:04/11/2026 (Brasília). Situação: organização e elaboração autorizadas; execução não autorizada por esta decisão. [Desenho canônico](../desenho_operacional_futuros.md), [estado](../../registros/operacional_futuros/estado.json).

## Contexto

O pesquisador solicitou separar uma nova busca de Mamba + esquema de operação com foco em lucro e drawdown no mercado futuro, permitindo compras e vendas. Em resposta à pergunta sobre teto de drawdown, solicitou uma métrica de compromisso entre risco e crescimento; não escolheu25%. Astra002 encerrou sem finalista pelo critério preditivo. F03 e demais estudos mantêm suas conclusões e artefatos.

## Decisão

Criar a linha `operacional_futuros`, com proposta/configuração/estado próprios e navegação pelo catálogo. Preservar o objetivo acadêmico dos ciclos anteriores e identificar a ampliação, sem editar o PDF nem alegar aceite do orientador. Não mover fontes, modelos ou recibos congelados para organizar pastas.

Propor Calmar por período como compromisso operacional principal, com crescimento composto, fronteira retorno–drawdown e incerteza obrigatórios. Picos de patrimônio não selecionam estratégia; nenhum limite25% foi aceito. Calmar é escolha de pesquisa, não medida universal de utilidade ou garantia contra ruína. Custos e motor fixos, escolhas de política em C e comparação em S separados de T/V. MSE permanece diagnóstico por tarefa, sem ser gate econômico.

Duas abordagens iniciais no próprio futuro: retorno terminal24h e resultado líquido de uma operação hipotética comprada/vendida com saída explícita. A segunda precisa de novo alvo/treino sempre que suas barreiras ou horizonte mudarem. Comparação composta, não ablação de um fator. Permitir shorts não demonstra previsão de quedas; auditar contribuições por lado e controles no mesmo instrumento.

Teto proposto de oito receitas e185ajustes condicionais,3.620avaliações lógicas; ainda depende de executor, dados2021–2023, fórmulas completas, qualificação, congelamento e autorização vinculada. Não tratar proposta como processo iniciado.2023–2025 já foram consultados; confirmação independente não é recriada por novas seeds.

## Consequências

O desenho operacional passa a ter endereço único distinto do desenho OHLCV anterior. O catálogo separa linhas, com ciclos originais intactos. Códigos novos só serão implementados em extensões identificadas, respeitando módulos de mercado, entradas, modelos, treinamento, simulação e coordenação. A preparação não altera critérios ou resultados de Astra002/F03, não autoriza conta real ou API paga e não obriga a busca a encontrar lucro.

## Preparação posterior do goal

O pesquisador solicitou preparar o necessário e um prompt para deixar executando à noite. Foram preparados dados2021–2023, métricas, adaptador Mamba com duas saídas e verificador da proposta, com24testes aprovados emWSL/CUDA. O desenho/seção10 e a configuração v2 enumeram as escolhas técnicas e uma janela noturna de12h, mais restrita que o teto geral. A redação do prompt não é autorização de treino recebida nem goal ativo. Sua mensagem de envio poderá autorizar implementação restante, qualificação e execução dentro do escopo, com vínculo à identidade, sem novo “Ok” redundante. Limitações do funding histórico, margem prudencial e componentes ainda não integrados permanecem explícitas. Versões anteriores e recibos em `registros/operacional_futuros/preparacao_goal/`.
