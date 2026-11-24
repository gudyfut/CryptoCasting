# Estado interno do Mamba:16 →8

Proposta e implementação:29/10/2026, após consulta dos resultados R0. O pesquisador solicitou uma alteração de configuração e treinamento/validação/teste somente de Mamba com seis seeds. Na pergunta sobre orçamento, escolheu **seis ajustes novos, com comparação pareada limitada às três seeds antigas**. Isso delimita esta rodada; não autoriza busca de parâmetros ou mudanças simultâneas.

## Hipótese e única diferença científica

R0 é a execução `ab5baf3eab3a2e66d8b2`. Seus registros mostram queda de perda de treino sem melhora correspondente de validação depois das épocas escolhidas. Hipótese: reduzir a dimensão do estado interno pode limitar capacidade e melhorar generalização. Resultado negativo é permitido. Essa evidência não demonstra que o estado16 seja a causa do sobreajuste.

Alterar somente `d_state` de16 para8 em cada bloco oficial Mamba-1. Largura32, duas camadas, convolução4, expansão2, dropout0,1 e pré-LayerNorm continuam iguais. Não é redução do contexto: cada exemplo continua168×5. A contagem esperada passa de20.257 para17.185 parâmetros, a confirmar na qualificação. Não aumentar a capacidade para perseguir menor erro de treino.

## Dados e ajustes

Reutilizar exatamente o conjunto `dados/entradas/0420879c2afc454c7754`, suas populações, canais, alvos e scalers. BTCUSDT/1h, contexto168h, alvo24h; treino2021–2023, validação2024, teste2025 retrospectivo. Não coletar novamente. Origens continuam horárias; a política de operação decide diariamente.

Seeds predefinidas, sem seleção por resultado: **17,42,2026,7,123,31415**. Ajustar somente Mamba. A ordem de execução começa por42 e segue17,2026,7,123,31415. Máximo100 épocas/paciência10, batch64/microbatch32, AdamW0,0002, decay0,001 com isenções oficiais, clipping1. Seleção exclusivamente pelo mínimo MSE de validação e empate pela primeira época; recarga do checkpoint antes do teste.

O orçamento é de **seis ajustes reais**. Não acrescentar uma sétima repetição real silenciosamente. Antes da grade, repetir dois ajustes curtos sintéticos seed42 com a arquitetura nova e exigir os limites de reprodução; a recarga exata continua obrigatória em cada ajuste real. **Não há repetição completa de uma mesma seed nos dados de mercado nesta extensão.** Os controles reais de R0 permanecem referências do procedimento, não certificação automática da variante. Essa limitação decorre do orçamento explicitamente escolhido e deve aparecer nos resultados.

Configurações: `configuracoes/modelos_mamba_estado8_001.json` e `configuracoes/mamba_estado8_001.json`. Código e entrada novos, preservando os módulos congelados de R0. Qualificação/fonte/configuração/protocolo/dados/heranças têm hashes vinculados à nova identidade antes da execução.

## Comparação e publicação

Comparação primária: perdas da variante versus R0 **nas mesmas seeds17/42/2026 e mesmas origens**. Média das perdas, não ensemble. Intervalos pareados em blocos circulares7/14/28 dias,2.000 réplicas, principal14. Métricas secundárias: RMSE, MAE, viés, sinal, dispersão entre seeds e trimestres.

As seis seeds novas descrevem estabilidade da candidata. A média de seis da candidata contra média de três de R0 é apenas descritiva e não substitui a comparação pareada primária. As três seeds adicionais não existem na referência; não imputar resultados nem selecionar três favoráveis. Herdar LSTM, Naive e ARIMA sem novos ajustes, identificando suas populações/seeds. A escolha da hipótese ocorreu após observar2024/2025; não apresentar esses períodos como confirmação independente.

Política Spot e contabilidade **idênticas à publicação R0** na comparação controlada. A auditoria posterior encontrou uma aproximação da comissão de compra; sua correção e sensibilidades ficam em recibo separado aplicado aos sinais fixos de R0, sem substituir a publicação ou mudar a política junto com a arquitetura. Uma futura versão de execução fiel à exchange precisa de identidade própria, com as duas variantes avaliadas sob a mesma regra.

## Auditoria de entradas e execução que precedeu a rodada

A auditoria em `registros/treinamento/auditoria_representacao_atual.json` liga as evidências. Fórmulas OHLCV, matrizfloat32 e scalers de treino foram refeitos; alvos/purga e preservação da geometria relativa conferidos. Oito candles horários nativos da Binance, em quatro datas2021/2023/2024/2025, coincidiram com a agregação. Essa é uma reconciliação amostral.

Há extremos na abertura relativa de treino e mudança de distribuição do volume/abertura nos períodos posteriores. São hipóteses de dificuldade de representação, não prova de implementação incorreta ou autorização para clipping, remoção de canal ou scaler adaptativo nesta rodada. Manter as entradas permite atribuir a diferença ao estado interno.

Na [tabela pública Spot](https://www.binance.com/en/fee/trading), a consulta de29/10/2026 mostra usuário comum0,10% por lado e0,075% com desconto BNB aplicável. Isso não certifica condições particulares/históricas2025. A [documentação de comissões](https://developers.binance.com/en/docs/products/spot/faqs/commission_faq) descreve desconto no ativo recebido: compra em BTC e venda em USDT quando não se paga BNB. O simulador usa uma aproximação na compra; a auditoria quantifica seu impacto pequeno. Slippage0,05% por lado é hipótese, não tarifa oficial.

O preço open do minuto não certifica preenchimento de uma [ordem MARKET](https://developers.binance.com/en/docs/products/spot/faqs/market_orders_faq). Faltam livro/fills, arredondamento e [filtros históricos](https://developers.binance.com/en/docs/products/spot/filters). O snapshot público de filtros atuais é evidência da consulta, não dado histórico2025. O cenário de taxa0,075% é custo equivalente; não simula carteira/reserva de BNB. Não chamar a simulação simplificada de reprodução exata de uma conta Binance.

## Preservação e encerramento

Configuração congelada, qualificação sintética aprovada, integridade/ambiente e ausência de processo concorrente antes do início. Tentativas/erros preservados. Processo com lock, PID/boot/host e estados. Ajuste incompleto só pode recomeçar com a mesma seed após investigar interrupção. Execução concluída não é chamada para refazer relatórios.

Encerrar após seis resultados, recarga e conferência de previsões, comparação/publicação e integridade. Não continuar até obter lucro ou superioridade. Recibos em `registros/estado_mamba/`; artefatos em `dados/experimentos/estado_mamba_<id>/`; cronologia em `docs/andamento.md`.
