# CryptoMamba adaptado ao contrato OHLCV24

Autorizado pelo pesquisador em29/10/2026: preservar resultados, estudar diferenças com CryptoMamba, replicar configurações adaptadas ao nosso caso, executar e comparar. Escopo delimitado: **uma candidata, seis ajustes novos**, seeds17/42/2026/7/123/31415, ordem42/17/2026/7/123/31415. Não é busca de hiperparâmetros nem repetição de referências. A [ADR0014](adr/0014-cryptomamba-adaptado.md) registra que esta é comparação de abordagens, não ablação de um fator. Não substituir a referência16/0,0002 automaticamente.

## Fontes e diferenças verificadas

Artigo: [CryptoMamba, versão2](https://arxiv.org/html/2501.01010v2). Código público fixado em [fef42727861a9c3a32241283ab981ef21a49e291](https://github.com/MShahabSepehri/CryptoMamba/tree/fef42727861a9c3a32241283ab981ef21a49e291), o HEAD encontrado nesta consulta. Bytes,URLs,SHA-256 e licençaMIT preservados em `registros/cryptomamba/fontes_externas/<commit>/`. Nenhum checkpoint pré-treinado externo será usado.

| Elemento | Artigo/código CryptoMamba | Nosso estudo e adaptação |
|---|---|---|
| Dados/tempo | YahooFinance BTC-USD diário,2018–2024 | Binance BTCUSDT/1h,2021–2025, dataset vigente |
| Contexto/horizonte | 14dias→fechamento seguinte | 168horas→retorno terminal24h |
| Entrada efetiva no código | Timestamp+O/H/L/C e, na versão-v,Volume:6canais | Cinco canais OHLCV causais publicados, sem timestamp adicional |
| Escala | Preços em nível, volume/1e9; normalizeFalse | Representação/scalers de treino vigentes, alvo padronizado |
| Eixos | DataTransform produz[B,6,14]; Mamba d_model14 percorre6canais | Adapter[B,168,5]→[B,5,14]; núcleo percorre5canais |
| Arquitetura | 3C-Blocks,4CMBlocks cada,larguras14→16→32→1,d_state64 | Mesmo núcleo estrutural, adaptação linear168→14 antes dele |
| Nosso Mamba de referência | Não corresponde à arquitetura publicada | 2blocos temporais,largura32,estado16,último token,dropout0,1 |
| Perda/otimizador | RMSE por lote,Adam,lr0,01,batch32,decay0,001 | Copiados com adaptações abaixo; não AdamW/MSE da referência |
| Scheduler/orçamento | StepLR100,gamma0,5,max1000épocas com volume | StepLR10,gamma0,5,max100épocas,paciência10 |
| Seleção | Artigo descreve early stopping; script público só configura ModelCheckpoint opcional | Seleção obrigatória por MSE global de validação, primeira época em empate, recarga exata |
| Métricas | RMSE/MAE em dólares,MAPE de preço; trading com políticas próprias | Métricas originais de retorno + métricas de preço derivadas para todos, SpotR0 comum |

O eixo da varredura é constatado pelo código e será comprovado por hook e comparação sintética do núcleo com a classe pública carregada da fonte revisada. Não é acusação de uso de dados futuros: uma mistura de coordenadas históricas permanece causal se a janela só contém passado. O timestamp é de fato um canal no código, embora o texto descreva cinco atributos OHLCV. Nosso adapter não muda o contexto para14dias:14é a dimensão latente aprendida que resume as168horas.

Diferenças adicionais do código: a rotina opcional de normalização reúne mínimos/máximos de todos os splits; **essa opção está desativada nas configurações públicas consultadas**, portanto não se atribui esse vazamento às execuções do artigo. Mantemos apenas scalers de treino. `scripts/training.py` não contém callbackEarlyStopping, apesar da descrição no artigo. A avaliação pública registra por lote durante Lightning e também recalcula métricas globais no script separado; nós usamos métricas globais por origem. As funções de trading públicas não debitam comissão/slippage explicitamente: o limiar de1% é filtro de ação, não cobrança de custo. A faixa de risco2% descrita no artigo não é intervalo probabilístico calibrado. Não importar essas políticas para nossa comparação.

## Receita concreta e adaptações

Código novo em `experimento_cryptomamba/`, entrada `run_cryptomamba.py`, configuração `configuracoes/cryptomamba_adaptado_001.json`. Núcleo:12Mamba-1 oficiais CUDA, d_state64,d_conv4,expand2,pré-LayerNorm e residual de CMBlock,mlp_ratio0,dropout0. Três projeções14→16→32→1 e merge de canais5→1. O núcleo não possui a normalização final/último token da referência. Adapter de contexto é Linear168→14. Contagem esperada **139.317parâmetros**, versus20.257da referência16; o núcleo sem adapter tem136.951. Não igualamos tempo/FLOPS ou capacidade.

Treinar do zero com Adam,betas0,9/0,999,eps1e−8,lr0,01,batch32,microbatch32,RMSE por lote do alvo padronizado. Adicionar epsilon1e−8 dentro da raiz para gradiente finito quando MSEzero. Manter isenções oficiais de penalização emA_log/D,coeficiente0,001 nos demais,clipping1 e FP32. O código público usa Adam em todos os parâmetros, ignorando tais marcadores: essa diferença é uma adaptação explícita à regra permanente do projeto. StepLR a cada10épocas/gamma0,5: redução proporcional do passo100 publicado ao limite100, mantendo fração10%do orçamento nominal. Não é scheduler publicado literalmente nem valor ótimo demonstrado. Manter100épocas/paciência10 e checkpoint por mínimo global de MSE de validação; RMSEglobal é monotônico ao MSEglobal, mas média de RMSE por lote não é equivalente.

Dataset,cinco canais,scalers,origens,purga e divisão2021–23/2024/2025 iguais às referências. Sem nova coleta,novo indicador ou nova máscara de população. Horizonte24h e contexto168h fixos; alvo continua log-retorno, não preço em nível. Isso permite comparação direta com resultados existentes e impede alegar reprodução das métricas/retornos do artigo. As várias mudanças formam **uma abordagem composta**; eventual efeito não pode ser atribuído só aAdam,RMSE,estado64 ou arquitetura.

## Comparações e métricas

Primária: MSE médio de validação das seis seeds versus referência16/lr0,0002, perdas alinhadas e bootstrap circular7/14/28dias,principal14,2000réplicas,seed20261020. Um único contraste primário,IC95%; favorável somente se média menor e limite superior principal<0. Sem promoção automática. Comparações com Naive,ARIMA,LSTM/três seeds e as outras sete receitas Mamba são secundárias/exploratórias;2024/2025já conhecidos, sem novo holdout.

Secundárias: MAE,RMSE,habilidadeNaive,viés,direção,dispersão,origens00UTC e Spot. Acrescentar para **todas as59séries de previsão** (6novas+53herdadas): preço previsto=C_atual×exp(retorno_previsto),RMSE/MAE/MSE emUSDT e MAPE de preço. MAPE de preço tem denominador positivo; **não calcular MAPE de retornos**, que podem serzero. Prever a média do log-retorno e exponenciar não garante média do preço. Os preços/gráficos do artigo e seus números não são comparáveis numericamente sem igualar fonte,período,tarefa e população.

Manter integralmente SpotR0,com decisões00UTC,latência1min,saída24h,capital10.000USDT,custos base/agravados e bruto de mesmos sinais. Nenhuma política nova é testada aqui. Comparar médias individuais, não ensemble/carteira; não selecionar seed favorável. Referências53herdadas não são53novos treinos.

## Qualificação, execução e fechamento

Antes de mercado: dimensões/eixos, equivalência numérica do núcleo versus código público em entradas sintéticas e pesos idênticos, forward/backward/atualização,gruposAdam/scheduler,gradienteRMSE,causalidade/ausência de alvo na entrada,seleção e recarga; dois ajustes sintéticos seed42 reproduzidos. Sem repetição real extra no orçamento6. Registrar falhas e limitações; não repetir até obter resultado favorável. Uma falha de implementação pode ser corrigida antes do congelamento com nova qualificação e incidente preservado.

Congelar fonte própria+externa,configuração,protocolo,qualificação,ambiente,contrato e53heranças em nova identidade. Lock/host/PID/boot/logs; único executor; nunca duplicar vivo. Cada tentativa de seed guarda seleção,checkpoint,épocas,previsões e conclusão. Em interrupção, investigar processo/fonte e retomar somente mesma célula incompleta, preservando tentativa anterior. Não alterar orçamento,lr ou arquitetura silenciosamente após resultados.

Após seis conclusões: conferir artefatos/checkpoints/seleção/métricas e preservação. Publicar59resultados,contrastes,preços e relatório próprio que distingue fidelidade,adaptações e achados. Pós-processamento não chama novamente executor encerrado. Uma falha posterior deixa recibo e resultados disponíveis para revisão de leitura, sem retrain. Não iniciar novas variantes ou substituir referência sem decisão posterior.
