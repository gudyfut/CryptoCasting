# Complemento descritivo — retorno de comprar/manter entre pontas observadas

Registrado em 18/10/2026, durante a execução do ciclo `4e232a796fcda0ea34c3`, após examinar a lacuna de DB1. Esta é uma análise descritiva posterior, não uma mudança retroativa do protocolo 2.1, dos checkpoints, dos sinais ou das métricas originais. Nenhum resultado de treinamento foi substituído.

O contrato executado marcou o controle comprar/manter de DB1 como não auditável porque faltam preços durante a posição. Isso impede reconstruir integralmente a curva e seu drawdown. No entanto, essa política tem quantidade constante e saída em data fixa: quando entrada e saída são observadas, o saldo final pode ser calculado sem conhecer os preços intermediários.

Com preço de compra A e preço de venda B, o complemento aplica exatamente os custos convencionais do controle original:

`retorno = (B/A) × (1−0,0005) × (1−0,001) / [(1+0,0005) × (1+0,001)] − 1`.

Exigir preço positivo e finito e negócios observados nos dois minutos. Usar o open de entrada e o open do último minuto antes do fim do bloco. Não utilizar o close posterior à saída. Uma ponta ausente ou sem negócios mantém o retorno indisponível.

Para DB1, as pontas das quatro moedas são 01/01/2023 00:01 UTC e 31/03/2023 23:59 UTC. [Dados e procedência](ciclo_001_DB1_pontas.json):

| Moeda | Retorno líquido entre pontas | Drawdown integral |
|---|---:|---|
| BTC | +71,5908% | Indisponível |
| ETH | +51,8166% | Indisponível |
| BNB | +28,3193% | Indisponível |
| XRP | +58,1679% | Indisponível |

O controle investe todo o capital. As políticas de barreiras dimensionam a posição pelo risco nominal e podem permanecer em caixa; seus níveis de exposição são diferentes. Esses retornos observados não demonstram superioridade ajustada ao risco, não recuperam o drawdown e não autorizam intervalos de incerteza baseados em uma curva diária incompleta.

Este raciocínio **não se aplica às saídas por barreiras**: uma lacuna pode ocultar o primeiro toque, alterar o preço de saída e modificar as entradas seguintes. Conhecer apenas a cotação no fim do prazo não recupera o resultado de uma estratégia dependente do percurso. O estado dessas simulações permanece conforme o contrato original.

Em `consolidacao/controles/auditoria.json`, os campos `resultado` e `concatenados` mantêm os controles integrais originais. `complemento_pontas` e `complemento_pontas_concatenadas` identificam o cálculo adicional. A concatenação só publica retorno quando todas as pontas de todos os folds planejados estiverem observadas; mantém o fechamento e a nova entrada em cada bloco, incluindo os respectivos custos. Não representa uma compra única mantida sem interrupção durante todo o ano. Não se preenchem lacunas nem se publica drawdown desse complemento.

Quando a trajetória completa está disponível, o retorno entre pontas é conferido contra o retorno integral. Quatro testes sintéticos verificaram saída no open, preservação de lacunas, pontas conhecidas com risco intermediário desconhecido e recusa de pontas sem preço/negócio. Registro: [testes do complemento](../qualificacoes/testes_complemento_pontas_2026-10-18.json).
