# Backtest de carteiras Spot com previsões já treinadas

Execução `8ec8a66648313caa48e3`.369 simulações, zero novos treinamentos,17 séries de previsão preservadas. [Protocolo](protocolo_backtest_carteira.md), [decisão](adr/0015-backtest-carteira.md), [estado/recibos](../registros/backtest_carteira/estado.json).

## Resultado principal e interpretação

**Não encontramos uma estratégia Mamba lucrativa e estável neste teste.** As previsões e os modelos são os mesmos; somente a camada operacional mudou. Com capital inicial de 10.000 USDT, a Smart aplicada ao Mamba16 terminou com **9.120,54 USDT em média: −8,79% líquidos**, desvio entre seeds de 1,57 ponto percentual. Nenhuma das seis seeds teve lucro: resultados entre −9,94% e −5,77%. A média é de seis carteiras individuais, não de um modelo ensemble.

No mesmo motor e nos mesmos instantes, a regra de saída diária perdeu 18,47%; a Smart perdeu 8,79%. Isso é melhora descritiva de **9,67 pontos percentuais**, mas não é ganho isolado de custos: a Smart também mudou os momentos e o tamanho da exposição. Ficou, em média, 89,40% investida, contra 15,94% na regra diária. Seu drawdown médio foi 34,43%, contra 28,33% na diária. Perder menos no encerramento não significou suportar menos risco durante o caminho.

O giro médio caiu de 111,87 para 4,91 vezes o capital inicial. As comissões e o slippage contabilizados somaram aproximadamente 1.678,02 USDT na saída diária e 73,63 USDT na Smart. Esses lançamentos já estão embutidos na carteira; não devem ser subtraídos de novo. A diferença entre cenários de custo não equivale exatamente à soma dos custos, pois o saldo disponível e as ordens posteriores também mudam.

Mesmo sem comissão e slippage, a Smart/Mamba16 perdeu 8,10%; com custos agravados perdeu 9,49%. Portanto, neste caso, o custo excessivo da regra antiga era parte do problema, mas removê-lo não revelou uma estratégia lucrativa.

O controle substituiu cada previsão diária por um único número: a média das previsões desse modelo em 2024, sem usar a média futura de 2025. Essa Smart de previsão constante perdeu **8,66%**, muito perto dos −8,79% do modelo variável. O contraste temporal principal teve IC95% incluindo zero. Não foi demonstrado que variar as previsões acrescenta valor econômico a esse viés constante. Esse controle não iguala perfeitamente a exposição; por isso também publicamos caixa, comprar/manter e exposição.

Comprar e manter perdeu 5,80% e permanecer em caixa retornou 0%. Assim, a Smart/Mamba16 teve desempenho descritivo pior que ambos. Isso não estabelece uma diferença estatística definitiva entre todas as políticas ou superioridade universal do caixa.

## Lucros isolados, período e comparação entre modelos

A Vanilla/Mamba16 perdeu 0,80% em média: a seed17 ganhou 9,06%, a seed42 perdeu 13,84% e as outras quatro não fizeram operações. Promover apenas a seed17 seria selecionar um resultado favorável depois de observá-lo. O retorno próximo de zero da média também não demonstra qualidade: a maioria das carteiras ficou inteiramente em caixa.

A Vanilla/LSTM retornou 1,58% em média nas três seeds: duas ganharam 2,37% cada e uma ficou parada. Cada carteira ativa teve somente uma compra e a venda terminal. As duas sementes lucrativas fizeram essencialmente a mesma aposta longa, não centenas de operações independentes. É um resultado descritivo positivo, insuficiente para declarar uma estratégia operacional robusta. Na comparação Smart pareada nas três seeds comuns, Mamba16 perdeu 8,29%, LSTM 5,20% e CryptoMamba adaptado 9,49%; as três médias foram negativas.

No desenvolvimento de 2024, a Smart/Mamba16 lucrou 81,45%, mas comprar/manter lucrou 118,69%. O CryptoMamba adaptado lucrou 109,41% nesse ano e perdeu 9,47% em 2025. Como suas previsões quase não variam, essa mudança entre anos ilustra como uma estratégia pode ganhar num período de alta por ficar comprada, sem demonstrar capacidade de antecipar movimentos. O ano de 2024 participou da seleção dos checkpoints; não é confirmação independente.

## O que foi encontrado no CryptoMamba publicado

O [artigo, seção6](https://arxiv.org/html/2501.01010v2) informa saldos finais partindo de100 USD:246,58 na Vanilla,213,20 na Smart e262,78 na Extended Smart. Isso corresponde a retornos de146,58%,113,20% e162,78%, respectivamente; não são percentuais fornecidos diretamente na tabela.

No [código público fixado por commit](https://github.com/MShahabSepehri/CryptoMamba/blob/fef42727861a9c3a32241283ab981ef21a49e291/utils/trade.py), as posições são mantidas entre decisões. A Vanilla usa limiar de1%; a Smart compra parte do caixa ou vende parte do BTC segundo a distância entre preço e previsão. Não há débito explícito de comissão ou slippage. O limiar de1% é um filtro, não um custo realmente pago. A Extended Smart permite posição vendida e não foi transferida para nosso estudo Spot sem dados de margem/financiamento.

Isso ajuda a entender a diferença para nossa saída diária, mas não reproduz os lucros publicados: são dados, modelos, calendários e hipóteses de execução diferentes. O desempenho precisa ser comparado a comprar/manter no próprio período, e o lucro por si só não mede a contribuição da previsão.

## Como a estratégia usa o modelo

A previsão continua sendo do retorno em 24 h. Smart transforma a alta prevista numa fração do caixa a comprar, e a queda numa fração do BTC a vender. Repete a decisão no próximo dia, mantendo o restante da posição. Uma previsão positiva pequena repetida pode acumular BTC até quase investir todo o caixa. Isso é diferente de manter uma pequena porcentagem fixa investida.

Vanilla (1%) compra/vende tudo apenas quando a variação prevista ultrapassa 1%; caso contrário mantém a carteira. O controle diária 24 vende a cada dia e decide se recompra. Nenhuma dessas regras foi ajustada para obter lucro em 2025. Os 2% da Smart são parâmetro de alocação, não stop-loss, garantia de risco ou intervalo calibrado.

O código público do CryptoMamba utiliza o fechamento anterior como execução e não debita custos explicitamente. Aqui há atraso de 1 min, preços de minutos Binance, comissão, slippage, filtros e risco até o saldo terminal. É adaptação da política, não reprodução dos lucros publicados. Short exige dados de financiamento/margem que não fazem parte deste estudo Spot.

## Calendário e custos

- validacao: 2024-01-01 T 00:01:00+00:00 → 2024-12-31 T 00:01:00+00:00; 365 decisões diárias, mesmas origens em todos os modelos.
- teste: 2025-01-01 T 00:01:00+00:00 → 2025-12-31 T 00:01:00+00:00; 364 decisões diárias, mesmas origens em todos os modelos.

Base: comissão 0,10% e slippage 0,05% por lado; agravado 0,20%/0,10%; ideal 0/0. Quantidades arredondadas para baixo em 0,00001 BTC e mínimo 5 USDT assumido. Filtros e taxas históricas reais da conta não foram certificados. Comissões de compra debitadas no BTC recebido e de venda noUSDT recebido. Resíduo sem tamanho de ordem permanece marcado e é mostrado nos arquivos de cada simulação.

## Médias por modelo, regra e período

Seis seeds no Mamba 16/CryptoMamba; três na LSTM. Para comparação pareada com LSTM usar os grupos de três da tabela seguinte. Médias individuais, não carteira formada por ensemble.

| Período | Regra | Modelo | N | Retorno base | Drawdown médio | Exposição média | Ordens médias |
|---|---|---|---:|---:|---:|---:|---:|
| validacao | diaria 24 | mamba 16_seis | 6 | +17,89% | +20,14% | 9,41% | 68,67 |
| validacao | diaria 24 | lstm_tres | 3 | +1,72% | +12,56% | 5,57% | 40,67 |
| validacao | diaria 24 | cryptomamba_seis | 6 | +0,00% | +0,00% | 0,00% | 0,00 |
| validacao | diaria 24 | naive | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| validacao | diaria 24 | arima | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| validacao | vanilla | mamba 16_seis | 6 | +52,62% | +16,79% | 39,31% | 1,67 |
| validacao | vanilla | lstm_tres | 3 | +30,14% | +20,96% | 44,66% | 2,00 |
| validacao | vanilla | cryptomamba_seis | 6 | +0,00% | +0,00% | 0,00% | 0,00 |
| validacao | vanilla | naive | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| validacao | vanilla | arima | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| validacao | smart | mamba 16_seis | 6 | +81,45% | +29,70% | 75,92% | 325,50 |
| validacao | smart | lstm_tres | 3 | +28,83% | +17,50% | 37,62% | 303,67 |
| validacao | smart | cryptomamba_seis | 6 | +109,41% | +32,96% | 95,93% | 73,83 |
| validacao | smart | naive | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| validacao | smart | arima | 1 | +32,67% | +12,11% | 34,78% | 295,00 |
| validacao | benchmark | caixa | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| validacao | benchmark | comprar_manter | 1 | +118,69% | +33,12% | 100,00% | 2,00 |
| teste | diaria 24 | mamba 16_seis | 6 | -18,47% | +28,33% | 15,94% | 116,00 |
| teste | diaria 24 | lstm_tres | 3 | -15,52% | +20,97% | 20,42% | 148,67 |
| teste | diaria 24 | cryptomamba_seis | 6 | +0,00% | +0,00% | 0,00% | 0,00 |
| teste | diaria 24 | naive | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| teste | diaria 24 | arima | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| teste | vanilla | mamba 16_seis | 6 | -0,80% | +12,00% | 29,30% | 0,67 |
| teste | vanilla | lstm_tres | 3 | +1,58% | +23,99% | 55,31% | 1,33 |
| teste | vanilla | cryptomamba_seis | 6 | +0,00% | +0,00% | 0,00% | 0,00 |
| teste | vanilla | naive | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| teste | vanilla | arima | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| teste | smart | mamba 16_seis | 6 | -8,79% | +34,43% | 89,40% | 254,17 |
| teste | smart | lstm_tres | 3 | -5,20% | +23,00% | 60,33% | 247,00 |
| teste | smart | cryptomamba_seis | 6 | -9,47% | +35,80% | 95,72% | 72,67 |
| teste | smart | naive | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| teste | smart | arima | 1 | -2,32% | +15,91% | 31,90% | 299,00 |
| teste | benchmark | caixa | 1 | +0,00% | +0,00% | 0,00% | 0,00 |
| teste | benchmark | comprar_manter | 1 | -5,80% | +35,99% | 100,00% | 2,00 |

## Smart no teste: comparação pareada nas três seeds comuns

| Modelo | Seeds | Retorno base | Desvio entre seeds |
|---|---:|---:|---:|
| mamba 16_tres | 3 | -8,29% | +2,21% |
| lstm_tres | 3 | -5,20% | +4,14% |
| cryptomamba_tres | 3 | -9,49% | +0,11% |

## Sensibilidade a custos no teste

| Regra | Modelo | Ideal | Base | Agravado |
|---|---|---:|---:|---:|
| diaria 24 | mamba 16_seis | -3,34% | -18,47% | -30,15% |
| diaria 24 | lstm_tres | +4,60% | -15,52% | -28,50% |
| diaria 24 | cryptomamba_seis | +0,00% | +0,00% | +0,00% |
| vanilla | mamba 16_seis | -0,70% | -0,80% | -0,90% |
| vanilla | lstm_tres | +1,79% | +1,58% | +1,38% |
| vanilla | cryptomamba_seis | +0,00% | +0,00% | +0,00% |
| smart | mamba 16_seis | -8,10% | -8,79% | -9,49% |
| smart | lstm_tres | -4,47% | -5,20% | -5,93% |
| smart | cryptomamba_seis | -9,20% | -9,47% | -9,74% |
| smart_constante | mamba 16_seis | -8,39% | -8,66% | -8,93% |
| smart_constante | lstm_tres | -2,46% | -2,55% | -2,64% |
| smart_constante | cryptomamba_seis | -9,19% | -9,46% | -9,72% |

## Cada seed do Mamba 16 no teste

| Seed | Diária 24 | Vanilla | Smart | Smart com viés fixo |
|---|---:|---:|---:|---:|
| 17 | -15,25% | +9,06% | -9,84% | -9,67% |
| 42 | -7,99% | -13,84% | -5,77% | -7,30% |
| 2026 | -33,33% | +0,00% | -9,27% | -9,68% |
| 7 | -24,49% | +0,00% | -9,43% | -9,64% |
| 123 | -22,30% | +0,00% | -8,53% | -7,70% |
| 31415 | -7,43% | +0,00% | -9,94% | -7,95% |

## Incerteza temporal do contraste principal

Média entre seeds de retornos log diários; bootstrap circular 14 dias,2000 réplicas. O intervalo é condicional aos checkpoints e ao histórico. Não corrige a escolha retrospectiva das políticas ou toda investigação anterior.

| Contraste Smart/Mamba 16 | Diferença log diária | IC 95% |
|---|---:|---|
| smart_mamba 16_menos_vies_validacao | -4.294261 e-06 | [-0.00013410088;0.00012129836] |
| smart_mamba 16_menos_comprar_manter | -8.9050685 e-05 | [-0.00039125451;0.00015170307] |
| smart_mamba 16_menos_caixa | -0.00025323331 | [-0.0019741496;0.0014906069] |

Intervalo que inclui zero é inconclusivo quanto ao efeito. Um saldo positivo isolado não demonstra vantagem futura. Os controles de viés usam apenas previsões de 2024 e nunca média futura de 2025.

![Resultado operacional e controle de previsão constante](figuras/backtest_carteira_8ec8a66648313caa48e3/leitura_resultados.png)

[Figura completa de desenvolvimento/teste, custos e seeds](figuras/backtest_carteira_8ec8a66648313caa48e3/carteiras.png). As figuras automáticas originais permanecem intactas; a ilustração acima reorganiza os mesmos dados.

## Auditoria e limites

Todas as 369 simulações têm ordens, recusas, saldos, curva horária, retornos diários e verificador independente. Caixa, BTC, comissão, slippage, quantidades e drawdown foram reconstituídos do livro de lançamentos. O drawdown considera closes de todos os minutos, saldos de execução e liquidação final; a curva ilustrada é amostrada. Não há stop-loss ou garantia de execução real. Dados/previsões/modelos anteriores não foram alterados.

2024 participou da seleção dos checkpoints.2025 já foi consultado antes desta decisão. Trata-se de backtest retrospectivo, sem novo holdout ou walk-forward. A receita do modelo, parâmetros das políticas e todas as seeds foram preservados; nenhum vencedor foi escolhido automaticamente e não houve busca até lucrar. Resultados devem ser confirmados por outros períodos e condições antes de qualquer alegação operacional.

[CryptoMamba](https://arxiv.org/html/2501.01010v2), [código público das políticas](https://github.com/MShahabSepehri/CryptoMamba/blob/fef42727861a9c3a32241283ab981ef21a49e291/utils/trade.py), [comissões Binance](https://developers.binance.com/en/docs/products/spot/faqs/commission_faq).

[Resultados estruturados](../dados/experimentos/backtest_carteira_8ec8a66648313caa48e3/resultados/comparacao.json) e [estado verificável](../registros/backtest_carteira/estado.json).

## Fechamento e continuidade

Conclusão da grade em 30/10/2026, às 02:44:15 de Brasília: 369 simulações, zero treinamentos/inferências novas, 19 fontes atuais e copiadas, 84 insumos e 1.163 arquivos anteriores conferidos. A conferência posterior recalculou médias, saldos, custos, retornos diários e os três contrastes bootstrap, além dos manifestos. [Recibo e verificador](../registros/backtest_carteira/entrega/fechamento_20261030/conferencia.json).

A tentativa inicial `b9fce5ae0300ce91ba69` falhou antes da primeira simulação por leitura de matriz somente leitura. Seus fontes, incidente e ponteiro permanecem preservados. A execução `8ec8a66648313caa48e3` acrescenta um leitor com cópia explícita, sem mudar política ou descartar resultados; 12 testes sintéticos foram aprovados. O protocolo congelado conserva o lançador original; o lançador corrigido é `run_backtest_revisado.py`, indicado nos registros e na ADR. A execução concluída não deve ser repetida para regenerar relatório.

Este fechamento não promove uma estratégia ou inicia outra busca. Recomenda-se usar a camada operacional para avaliar futuras hipóteses preditivas com modelos e regras identificados, sem escolher configurações pela seed lucrativa nem recalibrar políticas repetidamente sobre 2025. A referência Mamba16 e os testes de configuração anteriores continuam separados. Uma eventual hipótese Adam→AdamW pertence ao CryptoMamba adaptado; não é alteração já executada neste backtest. O Mamba16 de referência já utiliza AdamW.
