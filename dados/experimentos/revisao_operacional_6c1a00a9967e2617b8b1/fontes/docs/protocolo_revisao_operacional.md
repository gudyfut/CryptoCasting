# F03 — Revisão de execução e políticas operacionais

## Escopo fixado antes da execução

Autorização: solicitação do pesquisador em 04/11/2026 para auditar, corrigir e simular Spot/futuros. ADR0026. Zero novos treinamentos. Herdar as 64 séries imutáveis da comparação Astra/crua+Huber: oito seeds em cada um dos quatro blocos B1–B4, 2024–2025. Identidades/fontes/mercados do pai F02 entram na assinatura; cada execução nova possui cópia das fontes, grade, autorização, incidentes e preservação antes/depois. Nunca chamar executor encerrado.

1.152 carteiras = 2 modelos × 4 blocos × 8 seeds × 3 políticas × 3 braços × 2 custos. Mais 48 controles = 4 blocos × caixa/comprar-manter × 3 braços × 2 custos. Não replicar controles por seed. Total **1.200**, sem buscas adicionais. Um único executor com lock, interrompendo em falha. Qualificação sintética e auditoria independente por carteira obrigatórias.

## Calendário, mercado e capital

Mesmas origens diárias 00:00 UTC; previsão de retorno terminal24h. Quantidade calculada com patrimônio e preço do fechamento23:59, antes de receber funding das00:00. Envio simulado às00:01; preço-base é abertura desse minuto do mercado correspondente. Não consultar alvo nem preço de destino. Terminal no mesmo calendário F02: 181/183/180/183 dias, total727, com carteiras independentes por bloco. Cada uma inicia com10.000USDT e reserva alvo5%; não compor as médias como retorno de dois anos.

Spot usa negócios Spot; futuros usam negócios perpétuos, mark OHLC e eventos históricos reais de funding. Funding no timestamp de liquidação, cobrado da quantidade mantida antes da ordem. Eventos entre execuções são únicos, inclusive a fronteira final. Contabilidade futura separa colateral, PnL realizado e não realizado; nocional do short não vira caixa disponível. Entrada limitada a1x após custos; marcação pode elevar essa razão durante uma posição. Envelope conservador de2% do nocional é verificado nos extremos intraminuto e nas fronteiras; violação interrompe, não inventa uma liquidação favorável. Não se afirma simulação completa de margem de manutenção/liquidação Binance.

## Correções e premissas de execução

- Spot: na compra, comissão em BTC recebido; na venda, USDT. Sem BNB, promoções, impostos ou taxa específica de uma conta. Futuros: comissão em USDT. Configuração base:0,10%Spot,0,05%futuros,0,05%slippage adverso por lado. Estresse: mesmas comissões,slippage0,15% por lado. São premissas, não tarifas privadas certificadas.
- Reduções de futuros são ordens reduceOnly: não podem inverter/abrir posição e não exigem mínimo nocional de abertura. Reversão separa fechamento e abertura; se fechamento falha, abertura não ocorre. Toda abertura/aumento exige margem, inclusive reversões menores em módulo. Quantidades não são redimensionadas com preço futuro após gap; ordem sem saldo/margem é recusada e registrada.
- Arredondar para baixo em passos decimais: Spot0,00001BTC,futuros0,001BTC. Mínimos conservadores de pesquisa10USDTSpot/100USDTfuturos, teto1BTC por ordem. Os snapshots oficiais correntes são5/50USDT e ficam em `registros/revisao_operacional/fontes_publicas/`: **não comprovam regras de2024–2025**. Não reinterpretar o snapshot atual como filtro histórico. O mínimo é aproximado pelo último preço conhecido; a média oficial usada pela exchange não foi reconstruída. Pode-se deixar de simular pequenas ordens válidas.
- Venda Spot terminal respeita passo e mínimo; resíduo fica marcado, identificado separadamente do saldo. Futuros encerram quantidade negociável via reduceOnly. Slippage fixo representa spread/impacto agregado; preços não são ordens reais, não há livro de ofertas, execução parcial, fila, indisponibilidade ou latência aleatória. Teto1BTC é controle de pesquisa, não prova de liquidez suficiente.

## Políticas separadas

Definir `d=clip((1-exp(-r))/0,02,-1,+1)`, onde `r` é a previsão de log-retorno.2% é escala de intensidade, não stop. Sinal zero mantém posição. O teto desejado é95% do patrimônio conhecido. As três políticas usam as mesmas previsões:

1. **smart:** conserva a fórmula F02. Comprado/Spot reduz `|d|` da compra em sinal negativo. Bilateral usa capacidade direcional e pode reduzir compras mais depressa. Mantida como controle histórico; não é ablação pura de short.
2. **direcional:** sinal oposto encerra integralmente a posição anterior. Em seguida, pode abrir na nova direção a fração `|d|` do teto95%; o braço comprado nunca abre short. Sinal no mesmo sentido aumenta proporcionalmente a capacidade restante. Comprado e bilateral possuem a mesma regra de fechamento; seus históricos de patrimônio/exposição podem divergir depois.
3. **direcional_filtrada:** mesma regra de fechamento, mas abre/aumenta somente se `|r|>0,00300000075` (aproximadamente0,30%, limiar de custo fixado em F02). Sinal contrário fraco fecha, sem abrir posição nova; sinal zero mantém. Não selecionar limiar por lucro. Uma previsão de retorno não é probabilidade e o filtro não garante retorno líquido positivo.

Comparar Spot/futuros comprados como controle de instrumento e financiamento. Comparar futuros bilateral/comprado como extensão que permite short sob a mesma regra direcional, sem presumir trajetórias iguais. A mudança Smart→direcional é hipótese explícita de saída/posição, não ajuste silencioso para obter lucro.

## Avaliação e fechamento

Primário operacional descritivo: retorno líquido médio das oito seeds em cada bloco, depois média igual dos quatro blocos. Mostrar também drawdown, exposição, giro, número de ordens, comissão/slippage/funding, recusas e resíduos; caixa e comprar-manter95% como comparadores. Componentes comprado/vendido reconciliados com PnL total de futuros. Estresse de custos deve ser apresentado mesmo se piorar.

Comparações pareadas e dispersão entre seeds/blocos são descritivas; seeds não são oito mercados independentes, e estes períodos já orientaram hipóteses. Não prometer significância, certeza ou capacidade futura. Resultados ruins permanecem. A revisão não melhora as previsões, apenas muda/qualifica sua execução operacional. Não promover configuração com base em lucro retrospectivo.

Auditor usa caixa equivalente e fórmula de plano independentes, confere saldo, quantidade, ativo da comissão, preços, funding, motivos de recusa, causalidade e fechamento. Publicação exige cobertura exata e integridade das referências; conferência posterior gera novo recibo sem sobrescrever publicação. Fonte editorial de resultados distinta do protocolo congelado.

## Fontes oficiais consultadas

- [Comissões Spot e ativo recebido](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/commission_faq.md).
- [Filtros Spot: LOT_SIZE, MARKET_LOT_SIZE, NOTIONAL](https://github.com/binance/binance-spot-api-docs/blob/master/filters.md).
- [Erros futuros: mínimo nocional e exceção reduceOnly](https://developers.binance.com/en/docs/products/derivatives-trading-usds-futures/error-code).
- [Funding e sua cobrança](https://www.binance.com/en/support/faq/detail/360033525031).
- APIs públicas exchangeInfo, URLs e respostas BTCUSDT preservadas no registro. Regras correntes são informação auxiliar, não a reconstrução de toda a conta histórica.
