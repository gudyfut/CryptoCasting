# Taxa de aprendizado0,0001 nos estados8/16/32/64

Delimitado em29/10/2026, após o pesquisador autorizar seguir a proposta de redução da taxa, ampliando explicitamente aos quatro estados. Os resultados anteriores já eram conhecidos. ADR0013 e `registros/taxa_aprendizado/autorizacao.json` distinguem esta autorização da proposta anterior restrita a16. A referência de trabalho16 permanece preservada; esta grade investiga também se o efeito da taxa depende do estado.

## Desenho e orçamento

Exatamente **24 ajustes reais novos**: estados **8,16,32,64**, cada um nas seeds **17,42,2026,7,123,31415**. Ordem sequencial de estados8→16→32→64; dentro de cada um42→17→2026→7→123→31415. Congelar as quatro configurações e todas as referências antes do primeiro treino. Nenhuma adaptação pelo resultado dos estados anteriores; falha interrompe a grade. Sem repetir LSTM,Naive,ARIMA ou os24 Mambas anteriores. Sem repetição completa real extra da mesma seed; reprodução sintética e recarga exata são controles, com essa limitação declarada.

Comparação pareada por estado: **lr0,0002 existente contra lr0,0001 nova**, mesmas seis seeds e mesmos dados. A variação de estado é fator cruzado previamente fixado, não uma segunda alteração dentro de cada par. Estado16 continua referência adotada; nenhum resultado promove automaticamente outra arquitetura. A nova publicação contém24ajustes novos e29herdados:24Mambas anteriores,LSTM/três seeds,Naive,ARIMA.

## Fatores fixos

BTCUSDT Spot, candles1h, contexto168h, alvo log-retorno terminal24h, cinco canais OHLCV transformados. Conjunto `dados/entradas/0420879c2afc454c7754`, mesmas origens, purga24h, lacunas e escalas de treino; sem recoleta ou recalcular scalers. Treino2021–2023, validação2024, teste retrospectivo2025. Uma divisão fixa não é walk-forward.

Mamba-1 oficial CUDA/FP32, pré-LayerNorm, largura32, duas camadas, d_conv4,expand2,dropout0,1. Parâmetros por estado8/16/32/64:17.185/20.257/26.401/38.689. AdamW betas0,9/0,999,eps1e−8,coeficiente de decay0,001 com isenções oficiais A_log/D,batch64/microbatch32,clipping1,100épocas/paciência10. **Somente lr passa de0,0002 para0,0001 em cada arquitetura.** A taxa é constante; sem scheduler ou warmup novo. Selecionar menor MSE de validação, empate pela primeira época; recarregar checkpoint selecionado antes do teste e conferir previsões em segunda instância.

Preservar simulação R0: decisões00UTC, comprado/caixa, latência1min, saída24h, capital10.000USDT,taxa0,10%/slippage0,05% por lado; agravado0,20%/0,10%, mesmos sinais e bruto de mesmos sinais. Não unir manutenção de posição, novos limiares/horários/stops ou contabilidade de custos a esta hipótese. Publicar bruto/líquido,drawdown,exposição,giro e custos; retorno médio não é carteira combinada.

## Motivação e limites

Taxa menor pode modificar trajetória/estabilidade e o compromisso entre aprender o treino e generalizar, mas não há garantia. Nas seis curvas16 conhecidas, a seleção ocorreu nas épocas9–13; depois treino online caiu e validação piorou. Isso não prova taxa alta: regularização e mudança de distribuição também podem explicar. Não comparar níveis de erro online padronizado com validação em retorno real. AdamW aplica decay dependente da taxa por passo, e o número de épocas pode mudar: o contraste mede o efeito total da taxa sob a receita fixa. Se100épocas não bastarem, preservar a limitação sem ampliar o orçamento automaticamente.

## Qualificação, congelamento e execução

Pacote novo `experimento_taxa_aprendizado/`, entrada `run_taxa_aprendizado.py`; quatro receitas/modelos em `configuracoes/`, grade `taxa_aprendizado_mamba_001.json`. Qualificar todas as arquiteturas com dois ajustes sintéticos seed42/duas épocas, dimensões/forward/backward/atualização, grupos AdamW, reprodução e recarga exata. Testar orçamento24,seeds,autorização,heranças,parada em falha e proibição de reexecutar encerrado.

Uma identidade da grade congela quatro receitas/fontes/protocolo/ambiente/dados/qualificação e29heranças antes do primeiro ajuste. Cada célula tem estado,seed,tentativa,checkpoint,previsões e conclusão próprios. Verificar host/PID/boot/lock e logs; nunca duplicar processo vivo. Retomada apenas após investigar processo encerrado, mantendo fontes/científico íntegros; preservar e reiniciar só a tentativa incompleta da mesma célula. Qualificação/preparação não treina mercado. Orçamento24 autorizado pela mensagem humana, ligado depois à identidade concreta.

## Métricas e critérios fixados antes da grade

Primários: quatro efeitos pareados de taxa, um por estado, no **MSE médio de validação das seis seeds**. Média das métricas/perdas individuais, não ensemble. Bootstrap circular em dias7/14/28,principal14,2.000réplicas,seed20261020. Publicar IC95% descritivo e IC98,75% simultâneo por Bonferroni para a família dos quatro efeitos (erro familiar nominal5%). Esse ajuste não corrige toda seleção histórica/adaptativa nem a seleção de checkpoints; inferência permanece exploratória/condicional.

Uma candidata tem evidência favorável no procedimento se reduz a média de validação e o limite superior do IC98,75% principal da diferença candidato−referência é menor quezero. Inconclusão mantém a referência, sem procurar outra taxa. A decisão humana de adotar posteriormente outra receita/estado é separada do encerramento; não escolher pela melhor seed ou pelo lucro de2025.

Secundárias: MSE,RMSE,MAE,habilidade Naive,viés,direção,dispersão,seeds individuais,trimestres,origens00UTC e Spot. RMSE é média dos RMSE por seed; não raiz do MSE médio. Recalcular a mesma avaliação em origens00UTC para ambos os lados; não substituir o critério primário por um ranking favorável. Comparações entre estados na nova taxa e diferenças dos efeitos por estado são exploratórias. Teste2025 nunca seleciona época/taxa; períodos já consultados não são novo holdout.

## Encerramento

Após24conclusões: conferir cobertura exata, fontes/manifestos, checkpoints/dimensões, mínimo de validação e métricas recalculadas. Publicar comparações e um relatório próprio da taxa, preservando o relatório fechado de estados. Pós-processamento de leitura não chama novamente executor de mercado. Registrar preservação antes/depois, exposição e controles. Uma falha de pós-processamento deixa treino concluído e etapa posterior pendente, com incidente preservado; não treinar de novo para gerar tabela. Esta autorização termina na grade delimitada e não abre busca de novas taxas/indicadores.
