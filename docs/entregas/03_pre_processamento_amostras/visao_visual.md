# Entrega 3 — visão para apresentação

```mermaid
flowchart LR
    A[240 ZIPs Spot 15m<br/>BTC ETH BNB XRP] --> B[Manifesto da coleta<br/>aprovação e SHA-256]
    B --> C[Candles UTC<br/>15m → 1h, 4h, 1d]
    C --> D[Indicadores diários causais<br/>após fechamento]
    D --> E[Elegibilidade<br/>14 dias + alvo + lacunas]
    E --> F[Interseção das 16 células<br/>mesmas origens 00:00 UTC]
    F --> G[Matriz principal<br/>7d e 14d → próximas 24h]
    D --> H[Complementar<br/>7d → próximo candle]
    G --> I[D1–D4 e F1–F8<br/>purga por alvo]
    H --> I
    I --> J[Scaler ajustado somente<br/>nos candles únicos do treino]
    C --> K[Retornos diários<br/>dias comuns dos quatro pares]
    K --> L[Volatilidade anual<br/>e período completo]
```

**Exemplo de alinhamento:** às 00:00 UTC de um dia elegível, o fechamento recém-concluído é `C_t`. A entrada termina em `t`; o rótulo principal compara `C_t` com `C_(t+24h)`. Os quatro candles de entrada representam o mesmo período de calendário em resoluções diferentes, e a grade comum impede comparar populações de dias distintas.

**Números para a reunião:** 240 ZIPs auditados; 24 com somente lacunas e checksum válido; 1.661 origens diárias comuns; nenhum fold vazio; 1.811 retornos diários comuns. O desvio diário do período completo foi BTC 3,05%, ETH 4,13%, BNB 4,26% e XRP 5,13%. Essa ordem muda nos recortes anuais. Veja [resultados da execução oficial](resultados_execucao_oficial.md). Resultados preditivos só surgem nas entregas posteriores.
