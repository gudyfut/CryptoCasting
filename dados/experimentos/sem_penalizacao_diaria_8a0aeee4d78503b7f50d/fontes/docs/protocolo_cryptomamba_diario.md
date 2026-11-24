# CryptoMamba diário adaptado a futuros24h — protocolo001

## Pergunta, autorização e orçamento

Estabelecer uma referência próxima da implementação pública de CryptoMamba usando Binance USD-M, com operações compradas/vendidas encerradas24h após entrada. Autorização explícita do pesquisador neste chat em05/11/2026, delimitada na ADR0031. São3ajustes principais (42/17/2026) e1controle real42,1000épocas cada, sem outras receitas. Qualificação artificial não conta como treino de mercado.70carteiras previstas. Sem LSTM/ARIMA nesta rodada;Naive e posições constantes são controles sem treino. Não consultar Astra, buscar limiares ou iniciar variações automaticamente.

Entrada: `python -B -m experimentos.cryptomamba_diario qualificar|preparar|executar|conferir-preservacao`. Coleta separada: `python -B -m mercado_futuros.diario_cryptomamba`. Fonte pública fixada em `MShahabSepehri/CryptoMamba@fef42727861a9c3a32241283ab981ef21a49e291`; licençaMIT e bytes originais preservados em `registros/cryptomamba/fontes_externas/`. Configuração: `configuracoes/cryptomamba_diario_001.json`.

## Dados e calendário

Candles1d completos UTC do contrato BTCUSDT perpétuo USD-M, arquivos mensais oficiais Binance Vision com CHECKSUM,2020-01-01 a2026-01-01 exclusivo. Não interpolar. Timestamp em milissegundos na coleta, convertido para segundos somente no canal de entrada. PreçoUSDT e volume-baseBTC.72arquivos mensais. Conferir contínuo diário,OHLC positivo/extremos,volume e consistência com agregação dos minutos existentes em2024/2025 (tolerância0,11USDT para preços e1e−6relativo para volume, apenas arredondamento).

Incidente de preparação, antes de qualquer treino: a soma dos volumes de minutos difere do arquivo diário em14/01/2025 e29/01/2025. Conferência adicional dos2192dias pela API oficial encontrou preçosOHLC idênticos aos arquivos diários, mas volumes diferentes em27/03/2024,28/03/2024 e14/01/2025. Não há evidência suficiente para afirmar qual versão de volume é definitiva. Manter uniformemente os arquivos mensais diários, com checksum e versão reproduzível, sem substituir seletivamente valores ou excluir dias. Os minutos servem somente à execução, onde volume não entra no cálculo de sinal/PnL. Respostas oficiais, valores e checksums em `registros/cryptomamba_diario/incidentes/volumes_2026-11-05T150354.183547_0000/`. Preparação exige coincidência exata com as divergências investigadas; qualquer outra interrompe. Esta limitação de fonte é explícita, não aumento silencioso da tolerância.

Divisão por anos civis, seguindo a proporção4:1:1, aproximadamente66,7%/16,7%/16,7% (anos bissextos não são redivididos artificialmente): treino2020–2023;validação2024;teste2025. Como no Dataset público, cada partição constrói suas próprias janelas14dias e exclui a última janela possível. Isso dá1446/351/350exemplos. A última janela excluída é uma particularidade documentada da implementação, não requisito estatístico. A primeira origem de cada fase ocorre após14candles. Nenhum alvo de treino alcança validação; nenhuma entrada inclui o dia previsto. Não há treino do modelo em2024 após seleção e não há walk-forward.2024–2025 são retrospectivos já consultados.

O mercado de execução2024–2025 (negócios1min,mark1min,funding com preço no evento) é herdado por hash de `registros/mercado_futuros/execucao.json`, sem sobrescrever os dados. Não é necessário recolher minutos de2020–2023: são dados de treino de preço diário, não simulação de operações de treino.

## Entradas, rede e alvo

Entradafloat32 `[B,6,14]`:TimestampUnixUTC,Open,High,Low,Close,Volume/1e9. Preços em nível; nenhuma padronização por dataset, nenhum indicador extra. Timestamp é canal efetivo do código público. Não é um Mamba percorrendo14tokens temporais: o eixo de sequência percorre6canais e a dimensão interna começa em14. Copiar esse contrato faz parte da referência; não atribuir causalidade temporal ao eixo errado.

TrêsC-Blocks com4CMBlocks cada;larguras14→16→32→1,estado64,d_conv4,expand2,LayerNorm prévia eps1e−5,residual,merge6→1;sem adapter de contexto,MLP extra ou dropout. NúcleoSSM Mamba-1 oficialCUDA, sem fallback. Comparar outputs e carregamento de pesos do núcleo com a classe pública na qualificação.

Alvo: fechamento do próximo candle diário, emUSDT. Conversão operacional causal: `previsao_preco / ultimo_close_conhecido - 1`. Não é probabilidade nem payoff líquido. O alvo se realiza imediatamente antes de00UTC; a entrada ocorre00:01UTC e a saída00:01UTC seguinte. A previsão e o retorno efetivamente executável diferem pela latência e pelos custos. Essa diferença fica explícita em métricas/ledger, não se usa o preço de entrada futuro para gerar o sinal.

## Treinamento e seleção

Adam lr0,01,betas0,9/0,999,eps1e−8,weight_decay0,001 em todos os parâmetros como a implementação pública. Isso difere da referência anterior que respeitava no_decay; não alterar fontes históricas. StepLR100/gamma0,5,step ao fim da época. Lote32,último lote parcial,FP32,sem clipping,1000épocas completas,sem early stopping. Permutar somente exemplos de treino; ordem interna das janelas permanece. Perda`sqrt(mean((p-y)^2)+1e−8)` por lote, sem escala do alvo. Preços não positivos são erros de previsão mantidos nas métricas e geram abstenção operacional; não descartar exemplos.

Checkpoint por menor RMSE **global** em validação, primeira época em empate. Divergência intencional do logging público por lotes: métrica global evita depender do particionamento dos lotes. Checkpoints de cada melhora são mantidos e seleção vinculada por hash; recarga precisa reproduzir exatamente a previsão salva. Máximo4h por ajuste; ultrapassar interrompe sem considerar completo. Não selecionar por lucro,MAPE ou teste.

Ordem42principal→42controle→17→2026. O controle real exige mesma época selecionada e previsões emV com rtol1e−5/atol0,01USDT, não entra nas médias. Controles artificiais antes do mercado incluem forward/backward, atualização,repetição,recarga e equivalência estrutural. Teste só é previsto após terminar os quatro ajustes e aprovar controle. Falha interrompe; não repetir até obter melhor resultado.

## Política de futuros e contabilização

Capital10.000USDT independente por carteira/fase. Sinal após candle fechado, entrada00:01UTC,saída24h depois; fecha primeiro a posição anterior e pode abrir outra, pagando custos de ambos os lados mesmo quando mantém a direção. Uma posição por vez. Sem stop/take na referência; a regra24h não mascara insolvência. Uma violação do buffer prudencial interrompe a avaliação e preserva o incidente, sem inventar uma liquidação fiel à Binance.

Se a variação prevista exceder+0,20%,compra;abaixo de−0,20%,vende;entre limites,caixa. Mesmo filtro em todas as seeds/cenários, fixado pelo custo base aproximado(2×(0,05%comissão+0,05%slippage)), não por lucro. Não é garantia de retorno líquido positivo: funding,arredondamento e erro podem superar a margem. Funding futuro nunca entra no sinal. Não calibrar o filtro emV ou teste.

Nocional máximo95%do patrimônio no início,quantidade arredondada para baixo em0,001BTC,tickadverso0,10USDT,nocional mínimo100USDT. São parâmetros prudenciais fixados, não reconstrução certificada dos filtros históricos/VIP. Comissão0,05%por preenchimento. Slippage adverso0,05%base,0,10%/0,15%nos estresses. Cobrar funding histórico nos eventos dentro de `[entrada,saida)`,com sinal do lado e mark price do settlement. PnL linear `lado×quantidade×(saida-entrada)`,menos comissões,mais funding assinado. Não usar receita de venda descoberta como patrimônio disponível extra.

Marcações pelo mark price1min;drawdown por envelope conservador máxima favorável seguida de mínima adversa em cada minuto. Não é caminho de ticks observado. Incluir saldo inicial,custos de abertura,financiamento,fechamento e saldo final. Exigir patrimônio conservador após provisão de comissão de saída maior que2,5%do nocional marcado; esse buffer não é regra oficial de liquidação. Sem ordens reais.

## Avaliação e publicação

Sete unidades:três seeds,ensemble pela média dos preços previstos,Naive=último fechamento,sempre comprado e sempre vendido. Cinco cenários:bilateralbase,slippage2×,slippage3×,somente compra, somente venda. Duas fasesV/S:70carteiras, mesmo calendário. As restrições por lado são diagnósticos; não escolher a lucrativa depois. Caixa tem retornozero;Naive gera caixa sob o filtro. Posições constantes fecham/reabrem24h e pagam custos, não são buy-and-hold sem giro.

Previsões:RMSE/MAE/MAPEdepreço,MSE e habilidade contraNaive,MAE/viésde retorno,acerto de sinal,preços inválidos. Operações:retornolíquido,crescimento log diário,drawdown,Calmar,Sharpe descritivo diário rfzero,profitfactor,taxa de acerto,exposição,contagem,custos/funding e contribuição de cada lado. Taxa de acerto não substitui lucro. Agregar métricas das três seeds;ensemble separado. Não fazer ranking pelo melhor seed. V participou da seleção de checkpoint e não é confirmação independente.

Incerteza exploratória por bootstrap pareado de seeds/dias em blocos7/14/28(principal14),2000réplicas:deltaMSEcontraNaive e crescimento log diário da política fixa. Um único ano e três seeds não garantem robustez;intervalos não corrigem a busca adaptativa histórica. Não comparar numericamente MSEdepreço com MSEdos antigos payoffs.

Guardar configuração,fontes,qualificação,autorização,ambiente e dados por identidade. Checkpoints,épocas,previsões individuais e carteiras em `dados/experimentos/cryptomamba_diario_<id>/`. Ponteiros em `registros/cryptomamba_diario/`. Conferir hashes antes/depois, controles,cobertura e contabilidade independente. Mudanças científicas posteriores exigem nova identidade; ciclo encerrado não é reexecutado para relatar. Nenhuma promoção automática por lucro.
