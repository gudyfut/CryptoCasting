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
