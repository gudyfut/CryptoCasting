# Backtest de carteira Spot com previsões OHLCV24 preservadas

Versão1, 30/10/2026, definida antes dos novos resultados; autorização e escopo na [ADR0015](adr/0015-backtest-carteira.md). Entrada `run_backtest.py`, módulo `backtest_carteira/`, configuração `configuracoes/backtest_carteira_001.json`, registros `registros/backtest_carteira/`. Nenhum treinamento, inferência neural nova, alavancagem ou execução na exchange.

## Hipótese e fontes

Manter posição e ajustar apenas parte da carteira poderá reduzir giro/custos em comparação com liquidar todo dia. Isso não cria sinal preditivo e não garante lucro. O objetivo é medir desempenho e investigar se eventual retorno depende de informação temporal, viés positivo, exposição ou custos.

Fonte: [artigo CryptoMamba v2](https://arxiv.org/html/2501.01010v2), algoritmos1/2, e código público MIT em `registros/cryptomamba/fontes_externas/fef42727861a9c3a32241283ab981ef21a49e291/utils/trade.py`. O código público usa o fechamento anterior como execução, sem comissão/slippage explicitamente debitados. Sua curva é marcada no preço anterior durante o loop e não recebe o saldo final liquidado; aqui o risco inclui o percurso de preços e o evento terminal. Isso descreve o código consultado, não certifica a execução exata publicada. Não copiar short sem financiamento/margem.

## Grade fechada e modelos

17 séries existentes:6Mamba16/taxa0,0002,3LSTM,6CryptoMamba adaptado,Naive eARIMA, da publicação59séries `cryptomamba_adaptado_35dd98141ee20d9b8885`. Modelos e escalas permanecem congelados; todas as seeds entram.306simulações:17séries×3políticas×3cenários×2períodos.51controles:17constantes×3cenários apenas no teste.12benchmarks:caixa/comprar-manter×3cenários×2períodos. Total369; não expandir depois de observar lucro/prejuízo.

Comparação principal usa as6seeds Mamba16 no Smart. LSTM recebe recorte pareado17/42/2026, distinto das médias de6. CryptoMamba tem6seeds, mas outra arquitetura/receita; não atribuir diferença econômica apenas ao otimizador.

## Sinal e políticas

A política recebe somente o retorno log previsto r e o estado conhecido da carteira. Preço previsto=C_origem×exp(r). Dados/alvo observado futuro não entram na decisão.

1. **Smart2% (principal):** delta=(1−exp(−r))/0,02. Se delta>0, comprar min(delta,1) do caixa disponível; se delta<0, vender min(−delta,1) do BTC mantido. Não é peso-alvo: previsões positivas pequenas repetidas acumulam BTC progressivamente. Neutralidade mantém posição.2%não é stop ou limite de perda.
2. **Vanilla1% (secundária):** se abs(exp(r)−1)<0,01, manter carteira. Fora dessa faixa, alta compra com todo caixa, queda vende todo BTC. Não encerrar automaticamente no dia seguinte.
3. **Diária24 equivalente ao R0 (controle):** vender a posição a cada decisão seguinte e comprar tudo se r superar o limiar base ln((1+s)(1+f)/((1−s)(1−f))). O sinal permanece baseado no custo base nos três cenários. Usa a nova contabilidade/filtros; não substitui o número congelado SpotR0.

Benchmarks: caixa, comprar/manter e **controle de viés Smart**: r constante igual à média das previsões diárias de validação de cada modelo. Esse controle é calibrado em2024 e executado somente em2025; nunca usar média do teste. Não identifica perfeitamente efeito causal de timing ou exposição: reportar também exposição média.

## Calendário causal e execução

Origem diária00UTC, somente previsões com alvo24h inteiramente dentro da partição publicada. São365decisões em2024 e364em2025, conferidas entre modelos. Executar na abertura do minuto00:01. Prever por24h não obriga a vender24h depois nas políticas retidas: a decisão diária renova a perspectiva.

Janela começa na primeira execução; termina24h após a última execução, com liquidação programada no open desse minuto. Assim o teste cobre2025-01-01T00:01 até2025-12-31T00:01UTC, sem a última sessão inteira do ano. Todos os modelos/benchmarks usam os mesmos preços/instantes. Validar C_origem contra o close do minuto imediatamente anterior à origem. Não interpolar faltas ou executar sem negócios; indisponibilidade invalida a publicação, sem trocar datas por resultados.

Capital inicial10.000USDT, BTC inicial0, compra/caixa Spot, sem rendimentos no caixa, impostos ou financiamento. Sinal/fração calculados antes de ler o preço de execução. Execução simulada no open1min depois, piorado por slippage: compra×(1+s),venda×(1−s). Sem livro de ofertas ou certificação de fill.

**Cenários fixos por lado:** ideal0/0,base comissão0,10%/slippage0,05%,agravado0,20%/0,10%. O ideal mantém política e filtros, mas a evolução distinta do saldo pode mudar tamanhos/ordens; não chamar de mesmas operações monetárias. Não usar exemplo de taxa da documentação Binance como taxa histórica comprovada.

Compra: orçamento é fração do caixa; quantidade bruta=floor(orçamento/preço_execução/passo)×passo. Debitar notional do caixa; creditar BTC bruto×(1−taxa), comissão emBTC. Venda: arredondar a quantidade vendida para baixo; creditar notional×(1−taxa), comissão emUSDT. Guardar comissão convertida emUSDT, slippage e estados antes/depois. Essa dedução no ativo recebido segue a [documentação de comissões](https://developers.binance.com/en/docs/products/spot/faqs/commission_faq); taxa exata depende de conta,par,descontos e época.

Filtros assumidos: mínimo5USDT por ordem e passo0,00001BTC, inclusive na liquidação terminal. São aproximações declaradas, não certificação de filtros históricos/avgPrice/book. Ordens menores são registradas como não executadas. Não fabricar venda de poeira; saldo final inclui caixa e resíduoBTC marcado ao open terminal, com resíduo apresentado separadamente.

## Métricas, risco e auditoria

Retorno líquido,capital final,drawdown,exposição média temporal,giro sobre capital inicial,ordens/compras/vendas,comissões,slippage,resíduo e dispersão entre seeds. Nada de taxa de acerto de trades ficticiamente pareados numa carteira fracionada. Curvas médias são médias de carteiras individuais, não ensemble ou carteira negociável.

Drawdown por marcação cash+BTC×close em todos os minutos, incluindo saldos antes/depois das execuções e liquidação final. Não subtrair comissão de venda hipotética a cada marcação. Movimentos dentro do minuto não são observados. Salvar curva horária e eventos, ordens e recusas; reconstituir caixa,BTC,custos e risco dos lançamentos com um verificador separado, usando os preços congelados. Não confundir menos exposição com previsão superior.

Para o Smart/Mamba16, diferenças de retorno log diário frente ao controle de viés são o contraste primário; caixa e comprar/manter são secundários. Bootstrap circular14dias,2000réplicas,seed20261030; perdas/retornos médios entre as seis seeds. IC95%condicional aos checkpoints, sem propagar toda seleção histórica ou conferir independência. Não usar horas sobrepostas como replicações independentes. Lucro descritivo exige capital>inicial; robustez será examinada em todas as seeds/custos, sem promoção automática.

2024participou da seleção de checkpoints.2025já conhecido e esta nova política foi decidida depois: estudo retrospectivo de operação, não holdout novo ou walk-forward. Não escolher parâmetros,seed ou política pelo teste nem repetir até lucrar. Resultado negativo será publicado.

Antes: testes sintéticos de contabilidade,filtros,causalidade,risco terminal,retenção,independência de alvo e equivalência das frações ao código público. Congelar fontes/configuração/protocolo,previsões,manifestos e preços após qualificação. Preservar resultados/modelos anteriores e autorização vinculada à identidade. Depois: cobertura369,verificador independente,preservação antes/depois,relatório e figuras; nenhum executor de treinamento será chamado.
