# ADR0024 — Módulo operacional separado para futuros

Data: 04/11/2026. Estado: autorizado pelo pesquisador neste chat; qualificação e execução verificáveis em `registros/futuros/`. Não implica aceite do orientador.

## Contexto

Os resultados operacionais anteriores são Spot, sem venda descoberta. O pesquisador solicitou organizar/preservar o repositório e iniciar uma camada de futuros que permita compras e vendas. As previsões da comparação Astra/crua já existem; alterar treino simultaneamente impediria separar os efeitos.

## Decisão

Criar `mercado_futuros/` para observações oficiais e `simulacao_operacoes/` para contratos de previsão, políticas e contabilidade. `experimentos/futuros/` congela/executa a grade de 804 carteiras do [protocolo](../protocolo_futuros.md), sem qualquer novo treinamento. Importar somente infraestrutura de artefatos; não depender de redes, CUDA ou executores de treino. As 64 séries preservadas são referências de leitura.

Comparar bilateral e somente comprada no mesmo futuro, dados, custos, calendário e dimensionamento. BTCUSDT perpétuo linear, alvo24h, sinal diário, execução com atraso de um minuto, no máximo1× na abertura. Funding real e mark price separados do sinal. Custos de pesquisa declarados; buffer de margem interrompe trajetória inválida em vez de inventar liquidação.

## Preservação e limites

Os módulos históricos Spot permanecem em seus caminhos congelados. Limpeza só de caches comprovadamente regeneráveis, com recibo; scripts de auditoria/retomada documentam o histórico e não são lixo. Consolidação editorial não altera protocolos/fontes congeladas. Não editar `.git`, repetir ciclos, alterar a definição de resultados antigos ou abrir ordens reais.

Uma rodada operacional positiva não torna previsões mais precisas. Transferência de sinais Spot para perpétuos, custos hipotéticos, ausência de livro de ofertas e liquidação oficial completa são limitações. Nenhuma promoção automática, busca até lucrar ou nova autorização de treino. Estados e incidentes concretos ficam nos registros; o protocolo é congelado com a identidade da execução.
