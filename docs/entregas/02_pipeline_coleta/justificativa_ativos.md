# Entrega 2 — escolha dos quatro ativos e hipótese de volatilidade

**Recorte aprovado antes da coleta científica:** BTCUSDT, ETHUSDT, BNBUSDT e XRPUSDT, Binance Spot, 2021–2025, candles-base de 15 minutos. A coleta preserva OHLCV bruto; a caracterização de retornos e volatilidade será calculada na Entrega 3, após auditoria e agregação diária. Nenhum número de volatilidade ou resultado de previsão foi produzido aqui.

## Por que estes quatro ativos

| Ativo | Propriedade documentada | Contraste que acrescenta ao estudo |
|---|---|---|
| **BTC** | Ativo nativo do Bitcoin, rede de pagamentos com validação por **prova de trabalho** e regra de oferta máxima de 21 milhões de BTC. [White paper](https://bitcoin.org/en/bitcoin-paper); [Bitcoin Core](https://bitcoin.org/en/bitcoin-core/features/validation). | Referência de uma rede monetária com regras de emissão próprias. A descrição do protocolo não determina antecipadamente sua volatilidade. |
| **ETH** | Ether é o ativo nativo do Ethereum: paga transações e execução de **contratos inteligentes**, além de participar da validação. Ethereum migrou de prova de trabalho para **prova de participação em 15/09/2022**, dentro do período estudado. [Ethereum.org](https://ethereum.org/developers/docs/intro-to-ether); [The Merge](https://ethereum.org/developers/docs/consensus-mechanisms/pos/faqs). | Uso ligado a computação e aplicações na rede; a mudança de consenso é um evento histórico a considerar na descrição temporal, sem atribuir a ela causalidade a partir de OHLCV. |
| **BNB** | É o ativo nativo da **BNB Chain**, usado para taxas e participação no ecossistema; também pode ser usado na **corretora Binance**, inclusive para benefícios nas taxas de negociação. A BNB Smart Chain usa validação por **Proof-of-Staked-Authority**. [Binance](https://www.binance.com/en/bnb); [BNB Chain](https://docs.bnbchain.org/bnb-smart-chain/staking/overview/). | Acrescenta um ativo de infraestrutura de aplicações com ligação comercial à própria corretora que fornece os candles. Essa ligação será mencionada como característica e possível fonte de especificidade da amostra, sem pressupor efeito sobre preço ou previsibilidade. |
| **XRP** | Ativo nativo do **XRP Ledger**, voltado a transferências e liquidação de pagamentos; a rede confirma transações por consenso entre validadores, em vez de mineração por prova de trabalho. [XRPL: visão geral](https://xrpl.org/docs/introduction/what-is-the-xrp-ledger); [protocolo de consenso](https://xrpl.org/docs/concepts/consensus-protocol). | Adiciona uma rede com finalidade principal e mecanismo de validação diferentes dos demais ativos. Não confundir **XRP**, o ativo, com o nome da rede **XRP Ledger** ou assumir que toda movimentação de preço tenha uma causa única. |

Essas características justificam uma amostra deliberadamente heterogênea em **função e infraestrutura**. Elas não bastam para deduzir ordenação de volatilidade, liquidez ou dificuldade preditiva. Mudanças de oferta, uso da rede, negociação, liquidez e eventos específicos podem ser mecanismos plausíveis; este estudo usa somente OHLCV e não medirá causalmente cada mecanismo. Os quatro pares têm a mesma moeda de cotação e a mesma fonte de mercado Spot, mas continuam sujeitos a diferenças de cobertura, liquidez e regime ao longo do tempo. A amostra de uma única corretora não representa automaticamente todo o mercado.

## Ordem de volatilidade: hipótese a medir

A ordem anotada pelo pesquisador, **BTC < ETH < BNB < XRP**, será tratada como **hipótese descritiva**, sem usar essa posição para escolher ou excluir dados/modelos. Volatilidade depende de período, frequência, medida e universo de dias. Não se atribuirá a ordem aos mecanismos das redes sem análise apropriada.

Na Entrega 3, depois de formar fechamentos diários UTC válidos:

1. Calcular `r_(a,t) = ln(C_(a,t) / C_(a,t-1))` para cada ativo `a`, apenas quando os dois dias consecutivos estiverem completos. Não interpolar lacunas.
2. Usar **os mesmos dias elegíveis para os quatro ativos** em cada comparação, identificados por timestamp, sem alinhar arquivos por posição de linha. Registrar também a cobertura individual antes da interseção, para tornar visível qualquer perda causada por BNB ou outro par.
3. Publicar por ativo e ano, e para 2021–2025 agregado: número de dias, desvio-padrão dos log-retornos diários, desvio-padrão anualizado `sd_diário × sqrt(365)` como escala descritiva para um mercado 24/7, mediana e percentil 95 de `|r|`. Mostrar a ordenação obtida **por medida e ano**, inclusive quando contrariar a hipótese.
4. Apresentar separadamente níveis de volume e cobertura observada, se úteis para contextualizar resultados. Volumes em unidades dos quatro ativos não são diretamente comparáveis; normalização por moeda de cotação exigiria cálculo específico. Não afirmar que volume prova causalmente a volatilidade.

Essa caracterização é **descritiva**. Não fará parte das features de treino por padrão, não alterará o alvo `alta` versus `não alta` e não será usada para reajustar a seleção de ativos após consultar os resultados de 2024–2025. A matriz científica e as baselines AR(1) e LSTM avaliarão os quatro pares definidos.

## Relação com as entregas

- **Entrega 2:** listar 240 ZIPs esperados (`4 pares × 60 meses`), preservar e auditar os arquivos brutos, registrar cobertura por par/mês. A existência de BNBUSDT desde o primeiro mês será **confirmada pela coleta e pelo manifesto**, não presumida a partir da configuração.
- **Entrega 3:** agregar candles completos de 15m em 1h, 4h e 1d; produzir a descrição de volatilidade acima; criar features causais, alvo e amostras com timestamps, lacunas e elegibilidade documentados.
- **Entrega 4:** ajustar ARIMA(1,0,0) apenas com o treino de cada fold; implementar a LSTM prevista na revisão 1.6 do protocolo e a infraestrutura compartilhada. Ainda não é parte da coleta.
