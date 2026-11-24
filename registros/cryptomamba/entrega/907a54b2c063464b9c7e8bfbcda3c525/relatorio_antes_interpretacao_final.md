# CryptoMamba adaptado ao nosso contrato: comparação e análise

Execução `35dd98141ee20d9b8885`:6novos ajustes nas seis seeds usuais e53referências herdadas. [Protocolo/diferenças](protocolo_cryptomamba_adaptado.md), [decisão](adr/0014-cryptomamba-adaptado.md). Código público fixado emfef42727861a9c3a32241283ab981ef21a49e291. Esta é adaptação de uma abordagem composta, não réplica das métricas do artigo.

## Fidelidade e diferenças

Preservados núcleo de3C-Blocks×4CMBlocks, d_state64, larguras14→16→32→1, residual/pré-LN,merge de canais,Adam0,01,batch32 eRMSE. O Mamba percorre canais; não é o mesmo eixo temporal do nosso Mamba. Adaptados: projeção168→14,cinco canais OHLCV publicados sem timestamp extra, saída log-retorno24h,scalers de treino,max100/paciência10,StepLR10/0,5,clipping1,isenções oficiais de decay eepsilonRMSE1e−8.139.317parâmetros versus20.257na referência. As mudanças não isolam causa por hiperparâmetro.

O original prevê fechamento diário em dólares em2018–2024; nossa candidata prevê retorno24h com168candles horários em2021–2025. O14da projeção é dimensão latente, não contexto14dias. O paper descreve early stopping, mas o script público consultado não o configura. NormalizeFalse é a configuração pública: a rotina opcional de escala global não foi usada como evidência de vazamento nos resultados do artigo. Políticas públicas não debitam custos explicitamente; a comparação usa SpotR0 com custos para todos.

## Métricas de retorno: médias por seed

Comparação principal usa seis seeds iguais, média aritmética das métricas, não ensemble. LSTM só tem três seeds e recebe pareamento próprio.

| Parte | Modelo | Seeds | MSE ↓ | MAE×100 ↓ | RMSE×100 ↓ | Habilidade Naive |
|---|---|---:|---:|---:|---:|---:|
| validacao | cryptomamba_seis | 6 | 0,000717831 | 1,9465 | 2,6792 | +0,559% |
| validacao | estado16_taxa0002 | 6 | 0,000719838 | 1,9493 | 2,6830 | +0,280% |
| validacao | estado8_taxa0002 | 6 | 0,000720546 | 1,9516 | 2,6843 | +0,182% |
| validacao | estado32_taxa0002 | 6 | 0,000721137 | 1,9530 | 2,6854 | +0,101% |
| validacao | estado64_taxa0002 | 6 | 0,000719912 | 1,9502 | 2,6831 | +0,270% |
| validacao | estado8_taxa0001 | 6 | 0,000721604 | 1,9525 | 2,6863 | +0,036% |
| validacao | estado16_taxa0001 | 6 | 0,000721145 | 1,9522 | 2,6854 | +0,099% |
| validacao | estado32_taxa0001 | 6 | 0,000721733 | 1,9533 | 2,6865 | +0,018% |
| validacao | estado64_taxa0001 | 6 | 0,000722161 | 1,9548 | 2,6873 | -0,041% |
| validacao | naive | 1 | 0,000721862 | 1,9523 | 2,6867 | +0,000% |
| validacao | arima | 1 | 0,000721588 | 1,9515 | 2,6862 | +0,038% |
| validacao | lstm_tres | 3 | 0,000719446 | 1,9477 | 2,6822 | +0,335% |
| teste | cryptomamba_seis | 6 | 0,000497959 | 1,5886 | 2,2315 | -0,553% |
| teste | estado16_taxa0002 | 6 | 0,000496570 | 1,5894 | 2,2284 | -0,272% |
| teste | estado8_taxa0002 | 6 | 0,000498745 | 1,5922 | 2,2333 | -0,712% |
| teste | estado32_taxa0002 | 6 | 0,000499044 | 1,5927 | 2,2339 | -0,772% |
| teste | estado64_taxa0002 | 6 | 0,000503767 | 1,5994 | 2,2444 | -1,726% |
| teste | estado8_taxa0001 | 6 | 0,000497800 | 1,5908 | 2,2311 | -0,521% |
| teste | estado16_taxa0001 | 6 | 0,000498570 | 1,5918 | 2,2329 | -0,676% |
| teste | estado32_taxa0001 | 6 | 0,000498599 | 1,5912 | 2,2329 | -0,682% |
| teste | estado64_taxa0001 | 6 | 0,000499372 | 1,5934 | 2,2347 | -0,838% |
| teste | naive | 1 | 0,000495221 | 1,5864 | 2,2254 | +0,000% |
| teste | arima | 1 | 0,000494622 | 1,5854 | 2,2240 | +0,121% |
| teste | lstm_tres | 3 | 0,000498010 | 1,5931 | 2,2316 | -0,563% |

## Métricas no preço: mesma população para todos

Preço previsto=C_atual×exp(log-retorno). MAPE usa preço positivo no denominador; não MAPE de retornos. RMSE/MAE emUSDT não são comparáveis diretamente a1598,1/1120,7USD do artigo, por diferenças de datas,tarefa,fonte e formulação.

| Parte | Modelo | RMSE preço ↓ | MAE preço ↓ | MAPE preço (%) ↓ |
|---|---|---:|---:|---:|
| validacao | cryptomamba_seis | 1778,08 | 1279,04 | 1,945 |
| validacao | estado16_taxa0002 | 1780,36 | 1280,82 | 1,947 |
| validacao | naive | 1781,76 | 1281,65 | 1,948 |
| validacao | arima | 1781,28 | 1281,14 | 1,948 |
| validacao | lstm_tres | 1782,45 | 1280,24 | 1,944 |
| teste | cryptomamba_seis | 2179,47 | 1581,73 | 1,593 |
| teste | estado16_taxa0002 | 2177,99 | 1583,07 | 1,595 |
| teste | naive | 2171,50 | 1578,64 | 1,589 |
| teste | arima | 2170,35 | 1577,73 | 1,588 |
| teste | lstm_tres | 2179,43 | 1586,09 | 1,598 |

## Incerteza e critério anterior ao treinamento

| Parte | Contraste | Diferença de MSE | IC95%14dias |
|---|---|---:|---|
| validacao | cryptomamba_seis_menos_estado16_taxa0002 | -2.00719583e-06 | [-9.80472557e-06;4.39921801e-06] |
| validacao | cryptomamba_seis_menos_naive | -4.03191491e-06 | [-1.23287858e-05;3.92935933e-06] |
| validacao | cryptomamba_tres_menos_lstm_tres | -2.0566195e-06 | [-1.6720087e-05;1.20210629e-05] |
| teste | cryptomamba_seis_menos_estado16_taxa0002 | 1.38902635e-06 | [-2.61435055e-06;5.87550004e-06] |
| teste | cryptomamba_seis_menos_naive | 2.73803575e-06 | [-2.8066065e-06;8.23364475e-06] |
| teste | cryptomamba_tres_menos_lstm_tres | 1.08741085e-06 | [-3.75625674e-06;5.8981652e-06] |

Critério primário não atendido: este procedimento não fornece evidência suficiente para substituir a referência16/0,0002.

A avaliação é retrospectiva, condicional aos modelos; não corrige toda seleção histórica. Resultado favorável não prova reprodução do artigo ou lucro; resultado negativo vale para esta adaptação. Nenhuma receita é promovida automaticamente.

## Spot com mesma política e custos

| Modelo | Bruto | Líquido base | Agravado | Drawdown base | Operações médias |
|---|---:|---:|---:|---:|---:|
| cryptomamba_seis | +0,000% | +0,000% | +0,000% | +0,000% | 0,0 |
| estado16_taxa0002 | -3,344% | -18,464% | -30,134% | +28,325% | 58,0 |
| estado8_taxa0002 | -2,057% | -14,523% | -24,623% | +25,500% | 45,7 |
| estado32_taxa0002 | +1,149% | -14,456% | -23,800% | +21,088% | 55,7 |
| estado64_taxa0002 | -5,892% | -18,852% | -27,902% | +27,289% | 57,5 |
| estado8_taxa0001 | -6,104% | -14,292% | -21,147% | +18,472% | 32,2 |
| estado16_taxa0001 | -0,166% | -11,774% | -20,850% | +22,067% | 40,8 |
| estado32_taxa0001 | -3,762% | -11,879% | -18,901% | +17,089% | 29,8 |
| estado64_taxa0001 | -1,068% | -7,903% | -13,741% | +17,797% | 25,2 |
| naive | +0,000% | +0,000% | +0,000% | +0,000% | 0,0 |
| arima | +0,000% | +0,000% | +0,000% | +0,000% | 0,0 |
| lstm_tres | +4,595% | -15,514% | -28,487% | +20,963% | 74,3 |

Retornos/drawdowns são médias individuais, não carteira combinada. Receita mantém decisão00UTC,latência1min,saída24h,taxa0,10%/slippage0,05% por lado e cenários; sem política nova/short/futuros. Não escolher uma seed favorável.

## Seeds candidatas

| Seed | MSE validação | MSE teste | Retorno líquido |
|---|---:|---:|---:|
| 17 | 0,000717568 | 0,000498256 | +0,000% |
| 42 | 0,000717310 | 0,000499434 | +0,000% |
| 2026 | 0,000717291 | 0,000499601 | +0,000% |
| 7 | 0,000718356 | 0,000496794 | +0,000% |
| 123 | 0,000718741 | 0,000495816 | +0,000% |
| 31415 | 0,000717718 | 0,000497854 | +0,000% |

## Evidências e limites

[Auditoria](../registros/cryptomamba/conferencias/2fe2252bc16e4e02946cc374a819a14e/conclusao.json), [comparação posterior](../registros/cryptomamba/analises/4fe723b2a57b4690b6a26193c5cdc772/comparacao.json), [estado](../registros/cryptomamba/estado.json). Fontes próprias/externas/configurações,contratos,checkpoints,seleção e recarga foram preservados e conferidos. Sem nova inferência/treino no pós-processamento. Qualificação sintética inclui equivalência do núcleo em tensor/pesos iguais, não reprodução de treinamento/artigo. Sem repetição real extra; seis ajustes de uma candidata, sem busca.2024/2025já conhecidos; divisão fixa, não walk-forward ou holdout novo. Custos/fills reais da Binance e backup externo não foram certificados.

## Revisão independente e recorte de três seeds

As 59 séries tiveram MSE/MAE/RMSE de retorno e métricas de preço recalculados por outro procedimento. O relatório automático anterior foi preservado junto ao verificador. O recorte abaixo mantém17/42/2026 em todas as redes para comparação com LSTM; é posterior e não substitui o critério principal de seis seeds.

| Modelo (3 seeds nas redes) | MSE validação | MSE teste | RMSE preço teste (USDT) | MAPE preço teste (%) | Spot líquido |
|---|---:|---:|---:|---:|---:|
| cryptomamba | 0.000717389 | 0.000499097 | 2182.48 | 1.596 | +0.000% |
| estado8_taxa0002 | 0.000720855 | 0.000498582 | 2180.91 | 1.597 | -9.560% |
| estado8_taxa0001 | 0.000722213 | 0.000497999 | 2179.11 | 1.596 | -16.132% |
| estado16_taxa0002 | 0.000719164 | 0.000495890 | 2177.33 | 1.594 | -18.852% |
| estado16_taxa0001 | 0.000721217 | 0.000498343 | 2180.37 | 1.596 | -5.496% |
| estado32_taxa0002 | 0.000719675 | 0.000501114 | 2188.30 | 1.603 | -20.574% |
| estado32_taxa0001 | 0.000721479 | 0.000498551 | 2180.67 | 1.597 | -13.773% |
| estado64_taxa0002 | 0.000717444 | 0.000507149 | 2200.19 | 1.609 | -16.927% |
| estado64_taxa0001 | 0.000721030 | 0.000499384 | 2182.58 | 1.599 | -6.714% |
| naive | 0.000721862 | 0.000495221 | 2171.50 | 1.589 | +0.000% |
| arima | 0.000721588 | 0.000494622 | 2170.35 | 1.588 | +0.000% |
| lstm | 0.000719446 | 0.000498010 | 2179.43 | 1.598 | -15.514% |

## A rede usa as entradas ou responde quase sempre igual?

| Seed | Valores previstos distintos no teste | Desvio previsão / desvio alvo | Saídas distintas em 8 janelas, antes → depois | Máximo gradiente da saída nas entradas |
|---|---:|---:|---:|---:|
| 17 | 1 | 0 | 8 → 1 | 0 |
| 42 | 1 | 0 | 8 → 1 | 0 |
| 2026 | 1 | 0 | 8 → 1 | 0 |
| 7 | 1 | 0 | 8 → 1 | 0 |
| 123 | 8732 | 0.0093076 | 8 → 8 | 0.00109328 |
| 31415 | 1 | 0 | 8 → 1 | 5.02929e-16 |

Em 5/6 checkpoints, o retorno previsto no teste foi exatamente constante. Uma constante positiva pode reduzir o erro em um ano de alta sem reconhecer movimentos específicos. Uma constante abaixo dos custos implica permanecer em caixa; retorno Spot zero não demonstra capacidade de selecionar boas operações. O diagnóstico inicial/checkpoint usa oito janelas reais só de passado, sem otimizador ou ajuste adicional. Pesos próximos de zero e gradiente zero evidenciam perda de sensibilidade sob esta receita; isolar a causa entre Adam/L2/taxa/escala/arquitetura exige outro contraste autorizado. As tentativas degeneradas foram preservadas, não substituídas.

RMSE de preço pesa mais erros em dias nos quais BTC é caro; MSE de retorno mede a variação relativa. MAPE de preço em torno de 2% não equivale a 98% de acerto direcional nem a 2% de lucro.

![Comparação das abordagens](figuras/cryptomamba_35dd98141ee20d9b8885/comparacao_abordagens.png)

Habilidade acima de zero significa MSE menor que Naive. As barras de dispersão financeira mostram desvio entre seeds, não confiança estatística ou incerteza do preço. Métricas e retornos são médias dos modelos individuais.

[Análise independente e diagnósticos](../registros/cryptomamba/revisoes/3dbd58da46d148dfb6371934ed7f6acf/analise.json). Nenhum dado, checkpoint, receita ou publicação foi sobrescrito.

## Persistência nos dados públicos do CryptoMamba: diagnóstico separado

O Naive também foi calculado nos CSVs públicos fixados no mesmo commit do código. São 350 alvos de teste conforme CMambaDataset(window_size=14), com a última janela excluída pelo próprio __len__ público. Uma segunda conferência usou as classes originais e float32. Nenhuma rede foi treinada neste diagnóstico; ele não integra os 59 resultados Binance.

| Origem | RMSE (USD) | MAE (USD) | MAPE (%) |
|---|---:|---:|---:|
| Naive calculado no split público | 1568.50 | 1091.90 | 1.973 |
| CryptoMamba-v reportado no artigo | 1598.10 | 1120.70 | 2.034 |

Os números publicados são maiores neste confronto numérico, mas não foram recalculados dos checkpoints/previsões do artigo. A identidade da população exata da tabela não foi certificada; não há contraste pareado ou conclusão de significância. A tabela principal do artigo não inclui Naive. Esse diagnóstico sustenta manter persistência como referência; não refuta o trabalho nem prova vantagem da nossa arquitetura.

[Artigo, tabela 3](https://arxiv.org/html/2501.01010v2), [fontes e recibos do cálculo independente](../registros/cryptomamba/analise_dados_publicos/d54bb78d424e4aa987920add99f418bf/analise_naive.json).
