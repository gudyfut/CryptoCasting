# F02 — Smart retida comum no Spot e nos futuros

Autorização: pedido explícito do pesquisador em04/11/2026 para comparação justa Smart Spot/futuros, manutenção de posições, filtro de operação e **nenhum novo treinamento**. [ADR0025](adr/0025-smart-spot-futuros.md). Esta rodada não altera F01, previsões, checkpoints ou resultados Spot anteriores.

## Desenho fixado antes da execução

64séries herdadas da comparação `ce284eb4a489f604fb9c`: Astra e crua/Huber, quatro blocos B1–B4 e oito seeds. Origem diária00UTC, ordem00:01, carteira mantida até a próxima decisão, encerramento programado24h após a última decisão do bloco. Mesmas727datas (181/183/180/183), sem antecipar execução ou pular exemplos. O horizonte da previsão permanece24h; a posição pode durar vários dias se a decisão continuar favorável/neutra.

| Braço | Posição permitida | Preços/marcação | Funding |
|---|---|---|---|
| `spot` | comprada/caixa | Spot | nenhum |
| `futuro_sem_funding` | comprada/caixa | perpétuo/mark | desligado, controle hipotético |
| `futuro` | comprada/caixa | perpétuo/mark | histórico real |
| `futuro_bilateral` | comprada/vendida/caixa | perpétuo/mark | histórico real |

Contraste principal: Smart sem filtro, cenário de custos iguais, `futuro − spot`. `futuro_sem_funding − spot` mostra diferenças de preços/marcação e sua repercussão no dimensionamento; `futuro − futuro_sem_funding` mede a inclusão do funding, inclusive os efeitos posteriores sobre o saldo/tamanho. Não são carteiras com quantidades necessariamente idênticas, mas **o mesmo algoritmo** aplicado a cada mercado. `futuro_bilateral − futuro` mede permitir shorts na extensão Smart. A comparação filtrada versus não filtrada é pareada dentro de cada mercado/receita.

Grade:64séries ×2políticas ×4braços ×3cenários =1.536carteiras de modelos. Referências caixa e comprar/manter:4blocos ×2referências ×4braços ×3cenários =96. **Total1.632carteiras,zero treinos**. Referências sem seeds artificiais; nenhum controle extra de modelo ou busca de limiar. Controles sintéticos precedem dados históricos.

## Smart comum e manutenção da posição

Preservar a transformação Smart histórica da previsão r em intensidade:

`d = clip((1 − exp(−r))/0,02, −1, +1)`.

O2% é escala de ajuste, não stop-loss nem confiança calibrada. A implementação limita r a[−1,+1] antes da exponencial para estabilidade; fora desses extremos o resultado já estaria saturado no mesmo±1. Sinais não acessam alvo, preço futuro ou funding futuro.

Usar10.000USDT iniciais por bloco, **capacidade nocional95% do patrimônio conhecido** e reserva5%, passo comum0,001BTC e mínimo comum100USDT. Sem teto monetário adicional. Estes são parâmetros compartilhados de pesquisa, não reconstrução dos filtros históricos de cada conta. Comissões são debitadas em equivalenteUSDT nos dois braços para padronizar a comparação.

No instante do sinal, E é o patrimônio marcado já conhecido, P o último preço negociado anterior à origem e q a posição existente:

- Comprada/caixa: d>0 compra `d × max(0;0,95E−qP)/P` BTC; d<0 vende `−d` da posição existente. Não vende BTC inexistente.
- Bilateral: ajuste assinado `d × max(0;0,95E−sign(d)qP)/P`. Sinal positivo aproxima a carteira da capacidade comprada; negativo aproxima da capacidade vendida. Uma reversão negocia apenas a diferença líquida. O saldo recebido nocionalmente em uma venda futura não é considerado caixa disponível.
- Zero: manter q, sem ordem. Quantidade do ajuste arredondada para baixo em módulo; abaixo do mínimo, não enviar. Preço/quantidade planejados não usam a cotação futura da execução.
- Não zerar diariamente, não recomprar toda a posição e não rebalancear neutralidade. Posição idêntica não gera compra/venda artificial. No fim do bloco, encerrar q se superar o mínimo; resíduo menor permanece marcado e é reportado.

Esta **Smart95 compartilhada** preserva a lógica de ajuste parcial/retido, mas não reproduz byte a byte a Smart histórica: reserva, filtros comuns, comissão equivalenteUSDT e quantidade planejada com preço conhecido diferem. Comparar diretamente com o antigo+12,15% não isola mudança de mercado. A evidência justa é a rodada nova entre seus próprios braços, sob o mesmo executor.

## Filtro fixo

`smart_filtrada` conserva exatamente a Smart, mas só permite novo ajuste quando `abs(r) > log((1+s)(1+f)/((1−s)(1−f)))`, com f=0,001 e s=0,0005. Limiar aproximadamente**0,30% de log-retorno**, baseado no custo completo Spot previamente adotado e comum aos mercados/cenários. Não estimar limiar em2024–2025, testar uma grade ou escolher pelo lucro. Não usa funding futuro.

Quando o sinal fica abaixo do limiar, **manter a posição existente**, não liquidar. Assim, o filtro pode reduzir custos, mas também atrasar saída de uma posição ruim. O mesmo filtro simétrico se aplica a compras, reduções/vendas e shorts; risco prudencial não é desativado. Filtro de magnitude não equivale a probabilidade de acerto ou retorno líquido garantido.

## Custos e contabilidade

| Cenário | Comissão Spot por lado | Comissão futuros por lado | Slippage por lado |
|---|---:|---:|---:|
| ideal |0|0|0|
| iguais (principal) |0,05%|0,05%|0,05%|
| por_mercado (sensibilidade) |0,10%|0,05%|0,05%|

Taxas/filtros são hipóteses de pesquisa herdadas, não certificação histórica deVIP/BNB/livro. Ideal mantém funding nos braços com funding. Filtro permanece fixo0,30% em todos os cenários, sem alteração conjunta de regra.

Spot: saldo de caixa mais BTC marcado; proibir caixa/BTC negativos. Futuros: colateral mais PnL não realizado, preço médio atualizado apenas ao aumentar posição; reduzir realiza PnL somente da quantidade encerrada, reverter realiza a parte antiga e abre o saldo na direção nova. Comissões sobre cada ajuste, não sobre posição inteira. Funding `−q × markPrice_evento × taxa`, para posição em aberto no evento; intervalos **execução anterior < evento ≤ execução seguinte**, atribuindo o evento de fronteira à posição anterior.

Quantidade planejada na origem. Gap que tornaria uma compra Spot sem saldo ou aumentaria posição futura além de1× do patrimônio marcado após custos causa recusa registrada, sem redimensionamento oportunista. Perdas podem elevar exposição efetiva de posição existente; redução continua permitida. Drawdown marcado em cada minuto e antes/depois das ordens. Em futuros, buffer prudencial2% do nocional nos extremos mark, antes/depois do funding intraminuto; violação bloqueia a rodada com incidente. Não é liquidação oficial Binance, nem ADL/seguro/margem cruzada. Sem stop-loss/take-profit nesta hipótese.

## Dados, qualificação e preservação

Spot: mercado minuto `449aab6c79dbf88aa625`,25arquivos BTC de dezembro/2023 a dezembro/2025, recorte a partir de31/12/2023às23:59 para preço anterior. Futuros: coleta F01 `979c54995465216ea020` e complemento `a3f7d049d06d31955d9b`. Reutilização por checksum, sem nova coleta ou interpolação. Comparar fechamento Spot anterior à origem com o fechamento registrado na previsão. Exigir cobertura comum completa e mesmas origens entre receitas/seeds.

Teste fundamental: com preços iguais, custos iguais e funding zero, Smart comprada Spot/futuro deve produzir mesma curva, patrimônio, ordens e custos. Testes de retenção, filtro, funding positivo/negativo, fronteiras, redução/reversão, causalidade, gap e risco complementam a qualificação. Auditor independente usa identidade de caixa equivalente e ledger, sem classe de conta ou simulador, para reconciliar saldo verdadeiro, quantidade, preço médio, plano e eventos.

Congelar fontes, protocolo, configuração,grade, testes, previsões e mercado antes do primeiro backtest histórico. Preservação antes/depois inclui F01 e estudos anteriores; nenhuma fonte encerrada é alterada. Lock exclusivo; falha interrompe,sem retomada automática. Cada carteira guarda ordens, funding, diários, curva, resumo e auditoria. Publicação é única; análise posterior não chama executor encerrado. Entradas: `python -B -m experimentos.smart_mercados preparar` e `executar`.

## Interpretação

Primeiro média das8seeds de cada bloco, depois média de4blocos com peso igual. Relatar blocos,seeds,contrastes pareados,risco,giro,custos,funding,exposição,ordens,recusas e carteiras sem ordens. Não somar retornos de carteiras independentes nem chamar média de retorno anual. Caixa representa ação do Naivezero; comprar/manter usa mesma capacidade95%, sem previsão. As séries preditivas/MSE não mudam.

Resultados descritivos retrospectivos, sem novo holdout ou intervalo confirmatório de significância. Cenários e filtro conhecidos previamente são sensibilidades, não busca até lucrar. Nem ganho filtrado nem ganho vendido promove receita automaticamente. Sinais foram treinados emSpot; diferença entre mercados e hipóteses de execução permanecem limitações. Para um futuro teste confirmatório seria necessário protocolo e período não usados na seleção.
