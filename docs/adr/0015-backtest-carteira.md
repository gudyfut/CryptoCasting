# ADR0015 — Avaliar carteira retida com previsões já preservadas

- Decisão e registro: 30/10/2026.
- Situação: autorizada pelo pesquisador, antes das novas simulações.
- Evidência: pedido de estudar o backtest do CryptoMamba, fazer um bom backtest para o projeto e apresentar resultados. Não é autorização para operar dinheiro, retreinar ou procurar parâmetros até obter lucro.

## Decisão

Preservar SpotR0 e todas as execuções anteriores. Em novo ciclo de simulação, usar as previsões existentes do Mamba16/AdamW0,0002 (6 seeds), LSTM (3), CryptoMamba adaptado (6), Naive e ARIMA. Comparação principal: Smart2% no Mamba16; Vanilla1% é secundária. Os percentuais vêm do artigo, não serão ajustados ao resultado de2025. Uma regra diária24 equivalente a R0 no novo motor separa mudanças de contabilidade da mudança de política.

Smart movimenta uma fração do caixa ou do BTC e mantém posição entre decisões. O horizonte da previsão continua24h; uma posição poderá durar mais. O parâmetro2% regula a fração movimentada, não é stop-loss ou intervalo probabilístico. Sem short/futuros: os dados Spot não incluem funding, margem ou liquidação.

Executar369simulações previamente delimitadas, zero treinamentos e zero buscas:306 de modelos/políticas/custos/períodos,51 controles de viés no teste e12 benchmarks. Custos/filtros/latência, carteira, calendário e verificações no [protocolo](../protocolo_backtest_carteira.md). Fontes, configuração, previsões e preços serão identificados antes da execução.2024 é desenvolvimento com checkpoint selecionado nesse período;2025 também já foi consultado, portanto retrospectivo.

Um resultado positivo é descritivo desse backtest. Comparar média e dispersão, custos agravados, risco, comprar/manter e previsão constante calibrada na validação. Não escolher seed/estratégia pelo teste nem substituir a referência do modelo automaticamente. Registro próprio em `registros/backtest_carteira/`; resultados em execução própria, sem sobrescrever as publicações anteriores.
