# Simulação posterior de BTCUSDT perpétuo — F01

Decisão e autorização: [ADR0024](adr/0024-simulacao-futuros.md), pedido explícito do pesquisador de 04/11/2026. Camada operacional nova, **zero novos treinamentos**, sem alteração de previsões, checkpoints, resultados Spot ou critérios dos estudos anteriores. Fontes/configuração são congeladas antes de simular. Execução por `python -B -m experimentos.futuros preparar` e, separadamente, `executar`. Preparar valida evidências; executar recusa ciclo já iniciado/encerrado e usa lock exclusivo.

## Pergunta, população e orçamento

Qual o resultado descritivo de transformar as previsões existentes em posições compradas ou vendidas, comparado a permitir somente compras **no mesmo contrato futuro**? O contraste principal é `sinal24/bilateral/base` menos `sinal24/comprada/base`, separadamente para Astra/C05 e crua/Huber. A diferença contra Spot não isola somente abertura de shorts: mercado, funding, custos e política também diferem.

Reutilizar exatamente as 64 séries principais vinculadas à publicação da comparação `ce284eb4a489f604fb9c`: duas receitas, quatro blocos e oito seeds. Controles reais não entram nas médias. Os modelos foram treinados em **Spot**, não em futuros; transferir seus sinais não equivale a validar previsões do preço futuro. Não retreinar, converter checkpoints ou recalcular a seleção.

| Dimensão | Regra congelada |
|---|---|
| Mercado | Binance USDT-M perpétuo linear BTCUSDT; colateral USDT |
| Blocos | B1–B4, semestres de 2024 e 2025; mesmos dias disponíveis nas previsões, sem deslocamento para preencher falhas |
| Seeds | 42,17,2026,7,123,31415,271828,161803 |
| Políticas | `sinal24`, `filtrada24` |
| Modalidades | `comprada`, `bilateral` |
| Custos | ideal, base, agravado |
| Carteiras de modelos | 2 × 4 × 8 × 2 × 2 × 3 = 768 |
| Referências operacionais | sempre comprado diariamente, sempre vendido diariamente e caixa: 4 × 3 × 3 = 36 |
| Total | **804 carteiras**, sem busca de política, limiar, alavancagem ou seed |

Cada carteira começa com 10.000 USDT; blocos independentes. Referências diárias usam o mesmo dimensionamento e custos; não são buy-and-hold sem rebalanceamento. Caixa corresponde à ação do Naive de retorno zero. Não gerar oito cópias idênticas dessa referência.

## Fontes e cronologia causal

Dados públicos oficiais: negócios e mark price de 1 minuto de 2024–2025, arquivos mensais com SHA256 remoto, e taxas históricas de funding. API de funding fornece também o mark price de cada liquidação periódica; taxas/cobertura são cruzadas com arquivos mensais. Dois minutos ausentes no arquivo mensal de mark price de agosto/2024 foram obtidos na API oficial com proveniência própria, sem interpolação. Milissegundos reais dos eventos são preservados; conferência da periodicidade usa o minuto nominal. Um complemento identificado acrescenta 23:59 UTC de 31/12/2023 para o preço conhecido antes do primeiro sinal; não modifica a coleta publicada.

Sinal somente na origem **00:00 UTC**, depois do fechamento dos candles de entrada. Filtrar a publicação horária para essas origens; não gerar nova previsão. O simulador recebe apenas origem, destino, índice, fechamento já conhecido e previsão: alvo e preço futuro são proibidos no contrato. Abertura a 00:01, encerramento exatamente 24h depois, a 00:01. O sinal do próximo dia é calculado antes do encerramento anterior. Sempre encerrar e reabrir, mesmo sem mudança de direção; os dois lados pagam custos. Sem stop-loss ou take-profit nesta rodada.

`sinal24`: previsão positiva compra, negativa vende (ou fica em caixa na modalidade comprada), zero fica em caixa. `filtrada24`: exige magnitude superior a `log((1+s)(1+f)/((1-s)(1-f)))`, com f=s=0,0005 fixos do cenário base, aproximadamente 0,20%. Limiar simétrico e fixo nas três sensibilidades, sem funding futuro na decisão. É filtro heurístico de custos, não promessa de cobrir todos os custos do contrato.

Quantidade em BTC decidida com patrimônio conhecido antes da origem e último fechamento do contrato futuro anterior à origem. Alvo nocional = mínimo de 95% desse patrimônio e 50.000 USDT, arredondado para baixo em passos de 0,001 BTC. Mínimo de 100 USDT. Estes filtros/teto são parâmetros conservadores de pesquisa, não certificação da tabela histórica de uma conta. Reserva de 5%. Se gap/custos fariam o nocional superar o saldo disponível na abertura, recusar a ordem inteira e registrar; não redimensionar usando preço futuro. Quantidade fixa até o encerramento. Exposição máxima 1× **na abertura**; perdas podem elevar a exposição relativa ao patrimônio durante a operação. Não testar alavancagem adicional.

## Contabilidade e riscos

Para quantidade assinada q (positiva comprada, negativa vendida), PnL = q × (preço de saída − preço de entrada). Abrir vendido não requer BTC previamente comprado, mas exige colateral. O valor nocional vendido não é adicionado ao caixa como dinheiro livre. Entrada/saída sofrem slippage adverso e comissão proporcional ao nocional de cada execução.

| Cenário | Comissão por execução | Slippage por execução | Funding |
|---|---:|---:|---|
| ideal | 0 | 0 | histórico real |
| base | 0,05% | 0,05% | histórico real |
| agravado | 0,10% | 0,10% | histórico real |

O cenário ideal elimina somente custos de execução, **não funding**. Taxa base é hipótese ilustrativa de taker; não presume VIP, desconto BNB, promoção, spread ou profundidade historicamente reconstruídos. Slippage fixo não modela livro de ofertas. Preço do primeiro negócio do minuto é proxy de execução, não garantia de preenchimento real.

Funding líquido de cada evento: −q × markPrice do evento × fundingRate. Taxa positiva: comprados pagam, vendidos recebem; negativa inverte. Cobrar somente eventos com **entrada < fundingTime ≤ saída**. Em evento simultâneo ao fechamento/reabertura, atribuir à posição anterior, sem duplicação. Ordem temporal exata de eventos/execuções reais não está disponível; esta convenção é declarada. Funding integra saldo e patrimônio marcado, sem aparecer na política de entrada.

Marcação acompanha cada minuto; drawdown usa fechamentos de mark price e saldo no encerramento. Extremos high/low de mark price verificam um envelope prudencial: patrimônio acima de 2% do nocional marcado, considerando conservadoramente antes/depois do funding intraminuto. **Esse buffer não é a fórmula histórica de liquidação da Binance.** Se violado, interromper e preservar incidente; não inventar preço/taxa de liquidação, truncar prejuízo ou excluir carteira. Não simular ADL, seguro, empréstimos, juros de caixa, tiers históricos ou margem cruzada com outras posições. Sem violação do envelope não significa execução real certificada.

## Qualificação, publicação e interpretação

Testes sintéticos verificam long/short, sinais de funding e fronteiras, custos dos dois lados, Naive em caixa, entradas sem alvo, causalidade do tamanho da posição, rejeição por gap, reversão entre dias e bloqueio de margem. Auditoria separada reconstrói saldos, preço conhecido, dimensionamento, preenchimentos, comissões e cada evento de funding sem chamar o simulador. Trajetória de marcação/risco recebe testes próprios; essa auditoria não constitui reprodução de liquidação oficial.

Verificar hashes de séries, fontes e publicações; preservar mapa antes/depois das execuções antigas. Nova identidade vincula receita, fontes, qualificação, grade, mercado, proveniência e autorização. Cada carteira guarda operações, funding, curva, resumo, auditoria e manifesto. Falha interrompe sem retomada automática. Ciclo concluído nunca é executado de novo para relatar.

Relatar médias das oito seeds por bloco e média com peso igual dos quatro blocos; também dispersão entre seeds, blocos, custos, exposição, drawdown, operações, taxas, slippage e funding. Não somar retornos dos blocos como uma carteira contínua. Resultados desta rodada são **descritivos**, sem teste confirmatório de significância e sem seleção do melhor cenário. Os períodos já foram consultados e são retrospectivos; 804 carteiras não são 804 amostras independentes. Retorno positivo não demonstra melhora de previsão ou lucro futuro. Não promover modelo por lucro isolado.

## Referências oficiais consultadas

- [Binance Public Data](https://github.com/binance/binance-public-data): arquivos públicos e checksums; usar unidades de cada fonte, não supor a mudança de microssegundos Spot para futuros.
- [Funding Rate History](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History): taxa, tempo e mark price públicos.
- [Mark Price Klines](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Mark-Price-Kline-Candlestick-Data): observações de marcação.
- [Comissões Futures](https://www.binance.com/en/support/faq/detail/360033544231): cálculo por execução e exemplos de taker, não tabela histórica completa da conta.
- [Funding](https://www.binance.com/en/support/faq/detail/360033525031): pagamento entre lados e relação com posição aberta.
