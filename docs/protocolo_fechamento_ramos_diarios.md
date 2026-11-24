# Fechamento da contribuição dos ramos — protocolo 001

Autorização: Goal do pesquisador em 13/11/2026. Escopo finito, até 12 novos ajustes científicos lineares, além dos controles. Nenhuma busca, promoção pelo teste ou avaliação de 2026. [Configuração](../configuracoes/fechamento_ramos_diarios_001.json). A estrutura completa deriva do CryptoMamba de Sepehri et al., commit `fef42727861a9c3a32241283ab981ef21a49e291`, com Mamba-1 oficial; a ablação linear não constitui um novo SSM.

## Perguntas e intervenções

Em BTC, completar o fatorial ramos presentes/ausentes × penalização uniforme Adam de 0,001/zero: A, B e L herdados somente após comprovação; três redes L0 novas, sem ramos e sem penalização. Contrastes de MSE definidos antes da execução: A−L, B−L0, (B−L0)−(A−L); L0−L secundário. Menor MSE é melhor; o sinal de um contraste deve ser interpretado pelos seus termos. As diferenças são entre receitas com orçamento idêntico, não efeitos causais universais de uma matriz individual.

Em ETH, BNB e XRP, replicar A versus L com penalização 0,001, independentemente do resultado BTC. São nove novos ajustes científicos L. Não transportar os pesos BTC, não juntar moedas no treino, não selecionar ativos favoráveis. A ablação conserva a inicialização das quatro projeções e o estado RNG: construir A e substituir os 12 CMBlock por identidades antes de qualquer atualização. A tem 136.952 parâmetros; L/L0 têm 824. Conservar o treinamento fatorado, sem substituir por regressão fechada ou acrescentar ativações.

## Dados e treinamento fixos

Herdar os mercados Binance USD-M, dados diários, lacunas e exceções já documentadas. Seis canais Timestamp/Open/High/Low/Close/Volume; timestamp Unix em segundos e volume/1e9 antes do z-score por canal, ajustado nos candles únicos das janelas de treino. Contexto 14 dias, entrada `[B,6,14]`, scan sobre canais. Alvo: retorno simples do fechamento seguinte, sem normalização. Não recoletar ou substituir revisões de mercado.

Treino termina antes de 2024; validação 2024; retrospectiva 2025. Manter início original: BTC/ETH em 01/01/2020, BNB em 11/02/2020 e XRP em 07/01/2020, devido à disponibilidade do instrumento. Populações de validação/teste: 351/350 por moeda; treino conferido individualmente. Dados de 2026 não entram nesta execução.

Seeds 42/17/2026, 200 épocas completas, Adam taxa 0,01, betas 0,9/0,999, epsilon 1e−8, StepLR passo100/gamma0,5, batch32, lote final parcial, perda `sqrt(mean((pred−y)^2)+1e−8)`. Sem clipping ou early stopping. Selecionar menor RMSE global de validação, primeira época em empate. Teto técnico de 4h por ajuste, sem publicar ajuste interrompido como concluído. Mesmo backend oficial scan_ref CUDA/float32; sem troca silenciosa de precisão, otimizador, minibatching ou executor para obter reprodução.

## Qualificação, herança e controles

Reconferir fechamentos, snapshots, checkpoints, índices e referências antes/depois. Provar equivalência de seleção nas primeiras 200 épocas pelas histórias completas; estar abaixo de 200 no índice não basta. Reconstruir dados e escalas, conferir origens/alvos/publicações e recarregar as previsões herdadas exatamente. Não treinar uma referência ausente para substituir evidência perdida.

Ensaios sintéticos verificam as quatro receitas, reprodução, recarga, inicialização/RNG, contratos causais e ausência de acesso ao teste. Contratos do novo ciclo limitam moedas, alterações, ordem e orçamento; herdam as suítes pertinentes de dados, modelo e simulador. Os controles CUDA não podem ser considerados aprovados por testes Windows que os omitam.

Ordem fixa por moeda: controle da referência seed42 → primeira rede linear seed42 → repetição linear seed42 → linear17 → linear2026. BTC reproduz B42; demais moedas reproduzem A42. Controles exigem trajetórias científicas de 200 épocas, seleção, todos os checkpoints de melhoria do prefixo e previsões de validação exatos. São 12 ajustes científicos novos + 8 controles, 4.000 épocas novas. Controles não integram médias ou ensembles. Uma falha interrompe a sequência e é preservada; não repetir até passar nem relaxar tolerâncias. Referências A/B/L BTC: nove redes herdadas; A nas outras moedas: nove redes herdadas; total de 30 redes científicas consideradas (18 herdadas + 12 novas).

Verificar host, boot, PID/início, logs, locks e GPU; exclusão mútua por ciclo/GPU. Identidade única com unidades separadas por símbolo, configurações e fontes congeladas antes dos ajustes de mercado. Não iniciar duas execuções nem reiniciar por timeout de observação. Retomada somente após diagnóstico e preservação do incidente. Problema técnico que não altera a receita pode ser corrigido em continuação identificada; alteração científica ou ampliação do orçamento exige decisão do pesquisador.

## Avaliação e diagnósticos posteriores

Mesmo avaliador e simulador aprovados, generalizados explicitamente por símbolo/variantes. Média e dispersão de métricas individuais separadas da carteira única do ensemble. Ensemble: média dos preços equivalentes, conservando a aritmética já publicada. MSE principal; RMSE, MAE, viés, direção balanceada/recalls, correlação e dispersão secundários. Naive de retorno zero e Ridge de 84 coordenadas com grade 0,01/0,1/1/10/100, selecionada por MSE de validação. Referências não selecionadas pelo lucro.

Bootstrap pareado por seeds e blocos de observações consecutivas de 7/14/28 dias (14 principal), 2.000 réplicas e seed do avaliador anterior. Ensemble fixo reamostra dias, não novas redes. Reportar intervalos por ativo; não tratar moedas correlacionadas ou seeds como mercados independentes. Ausência de significância não prova equivalência. A busca histórica e a exposição prévia limitam inferência confirmatória.

Backtest de continuidade: filtro ±0,2%, exposição alvo95%, capital inicial10milUSDT, comissão0,05% por lado, slippage provisório0,01% e estresses0,02%/0,03%, latência1min, funding histórico e regras por instrumento. Manter posição do mesmo lado e negociar diferenças; encerrar em caixa/inversão/fim. Sem stop/take e sem ordens reais. Conferir por auditor independente e reproduzir A/Naive contra a publicação de continuidade vigente (30 carteiras por moeda). BTC:108 carteiras; cada outra moeda:60; total288. Preservar falhas prudenciais e não remover carteiras ruins das médias.

Depois dos ajustes, diagnosticar todas as populações de cada checkpoint, sem atualizar pesos: previsão completa versus ramos desativados, erro residual e magnitude da contribuição; decomposição afim em intercepto, canais e defasagens. Em L/L0 a ausência de ramos é estrutural. OHLC correlacionados devem ser apresentados também em conjunto; contribuições algébricas não são importância causal. Conservar trajetórias já observadas de A/B/S e não inventar checkpoints intermediários. Relacionar contribuição, sinal e filtro sem escolher filtros novos.

Análise operacional posterior fixa: exposição por lado, custos/funding, concentração por episódios e semestres civis de 2024/2025, com todos os dias disponíveis em cada recorte e sem redefinir a carteira no meio da curva. Referências passivas existentes podem ser citadas apenas com população e política identificadas. Relatar lucro, risco e precisão separadamente; não atribuir lucro ao SSM quando a intervenção não modifica a previsão.

## Entrega e encerramento

Recibos e incidentes em `registros/fechamento_ramos_diarios/`; implementação em `codigo/experimentos/fechamento_ramos_diarios/`; artefatos em `dados/experimentos/fechamento_ramos_diarios_<id>/<simbolo>/`. Comparações anteriores continuam intactas. Auditoria posterior independente das métricas/contrastes e contabilidade publicada; figuras PNG/PDF inspecionadas e vinculadas à tabela fatorial, comparação entre ativos e diagnóstico dos ramos. Atualizar os resultados de ablação e os guias existentes, conservando seus bytes anteriores; não criar um relatório por conversa.

Encerrar somente após cobertura, controles, integridade, métricas, operações, figuras e interpretação verificadas. Resultado negativo ou inconclusivo cumpre o propósito de pesquisa; não ampliar a busca até obter lucro. 2024 selecionou checkpoints, 2025 já foi consultado, e o recorte anterior de 2026 também é conhecido; nenhuma dessas classificações muda por este fechamento.
