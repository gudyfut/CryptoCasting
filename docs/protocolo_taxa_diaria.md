# Fechamento diário: diagnóstico e ablação da taxa inicial

Autorizado pelo pesquisador em 11/11/2026, com orçamento de dois a três dias de investigação. Pergunta: manter os ramos Mamba ativos e reduzir o passo inicial de otimização melhora a generalização? Nenhum resultado favorável é condição para encerrar.

## Contraste congelável

Referência: `8a0aeee4d78503b7f50d`, Adam sem penalização. Candidata: somente taxa inicial 0,01 → 0,001. Seeds 42, 17 e 2026; controle 42 antes das demais seeds. Mesmo BTC, dados, z-score dos seis canais ajustado no treino, 14 dias, retorno simples futuro, arquitetura, RMSE por lote, Adam, decay zero, lote32,1000épocas, StepLR100/gamma0,5, sem clipping ou parada antecipada. Seleção pelo mínimo global de RMSE de validação, primeiro em empate. Recarga e controle exigem previsões, época e histórico científico exatos; controles excluídos das médias.

Treino2020–2023, validação2024 e teste2025 permanecem retrospectivos. Sem seleção por lucro. Nenhuma troca de eixo do scan, alvo, entrada ou política está incluída. Não se promove a candidata por um resultado isolado. Orçamento: três ajustes principais novos e um controle; referência herdada, sem retreino.

## Eficiência antes de mercado

Medir separadamente custo de treino, validação e escrita em ensaio sintético. Examinar cache de entradas/índices/validação, transferências e armazenamento; preservar lotes, ordem, precisão float32, cálculos, verificações e seleção. Aceleração somente após equivalência de trajetória, pesos e previsões, além de ganho medido. Informar o pesquisador antes de aplicá-la. Não usar fused, AMP, TF32, maior lote, redução de épocas/seeds ou validação menos frequente para acelerar esta ablação. Uma alternativa sem ganho ou sem equivalência fica registrada como rejeitada; o executor herdado permanece opção.

## Qualificação, identidade e execução

Conferir host/boot/PID/locks/GPU; qualificar CUDA oficial com scan de referência, contratos, forward/backward, reprodução, dados/escalas reais idênticos e teste inacessível durante o treino. O novo namespace registra as fontes reais em `codigo/`; fontes encerradas são conferidas nos snapshots e pacotes, sem restaurar executores antigos. Congelar receita, protocolo, dependências, ambiente, qualificação, dados e referências antes de iniciar.

O novo treinador pode reutilizar a função de ajuste herdada; isso não reabre seu executor. Ausência de dependência ou divergência interrompe a preparação. Não retomar automaticamente uma execução interrompida; conservar incidente e tentativa. O teste só é acessado após o controle aprovado e o término dos três ajustes.

## Avaliação comum

Principal: diferença pareada de MSE de retorno candidata menos referência nas mesmas origens/seeds; reportar magnitude e IC exploratório com blocos móveis7/14/28dias,2000réplicas, principal14, seed3105. Complementares: MAE/RMSE, viés, correlação, acerto balanceado, dispersão, contribuição funcional dos ramos e trajetória de validação. Incerteza não corrige a seleção adaptativa anterior.

Finanças usam, para ambos os braços, a publicação conferida de custos `9f7598f109962adc3d76`: slippage provisório0,01% por lado, comissão0,05%, funding observado, filtro histórico±0,20%,95%nocional, latência1min e saída24h. A receita histórica conserva seus5bp; a camada de avaliação aplica a mesma releitura identificada à candidata e herda os resultados atuais da referência. Não misturar finanças antigas com atuais. Cenários de slippage1/2/3bp e restrições por lado permanecem; Naive, sempre comprado, sempre vendido e ensemble identificados.70carteiras novas. Médias individuais não são ensemble. Comparação exige baselines e origens equivalentes; sem seleção de filtros.

## Diagnóstico consolidado autorizado

Reutilizar as quatro receitas BTC e as três extensões de moeda, previsões e finanças vigentes. Conferir fontes e recalcular erro, viés, variância, covariância, direção, associação, faixas de magnitude e recortes trimestrais. Faixas absolutas fixas de retorno0/0,2/0,5/1% e acima; descritivas, sem promover filtros. Comparar retorno zero, média do treino e Ridge sobre as mesmas84coordenadas padronizadas; intercepto não penalizado, regularização selecionada emV na grade fixa0,01/0,1/1/10/100 para MSE médio + lambda*norma². Quatro referências lineares selecionadas e quatro médias estimadas, registradas como ajustes auxiliares CPU, não seeds Mamba. Nenhuma calibração usa teste. Comparações temporais são retrospectivas.

Diagnósticos ficam em `dados/diagnosticos/fechamento_diario_<id>`, com leitor reutilizável, plano, hashes, métricas e figuras. Estado, autorização e incidente em `registros/taxa_diaria/`; treinamento em `dados/experimentos/taxa_diaria_<id>`. Atualizar cronologia, catálogo e roteiro; não criar relato por interação.

## Avaliação temporal e encerramento

Auditar exposição de2026 antes de definir eventual janela adicional; não consultar seu desempenho para escolher datas ou receitas. A auditoria não certifica ausência de uso fora do repositório. Qualquer dúvida material precisa ser esclarecida antes de chamar a janela de reservada. Uma avaliação adicional dos checkpoints congelados mede envelhecimento, não walk-forward com retreino. Não iniciar outra hipótese nem ampliar grade automaticamente após a comparação. Resultado negativo ou inconclusivo encerra esta ablação e integra o artigo.
