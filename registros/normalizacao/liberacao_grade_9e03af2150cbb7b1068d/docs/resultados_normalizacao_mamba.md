# Pré-normalização do Mamba — execução e resultados

Ciclo autorizado em 28/10/2026. **Ainda não há resultados finais deste experimento.** O estado operacional deve ser conferido no ponteiro `registros/normalizacao/execucao.json` e nos arquivos da execução; ausência de conclusão não significa resultado zero.

Execução congelada: `9e03af2150cbb7b1068d`. Preparação aprovada com 31 testes e oito casos CUDA em pré/pós-normalização, duas repetições por caso e recarga exata. Processo iniciado em 28/10/2026 às02:02:09 de São Paulo, inicialmente nos controles de reprodução. Caminho: `dados/experimentos/normalizacao_9e03af2150cbb7b1068d/`. Esta é uma atualização de início, não um placar ou conclusão.

Às02:05:24 de São Paulo, os dois controles e dois pilotos foram aprovados e a grade completa foi liberada. Os controles reproduziram a época histórica e ficaram dentro das tolerâncias predefinidas; houve diferenças numéricas pequenas, não reprodução bit a bit. Os pilotos são dois dos 384 ajustes, sem conclusão de superioridade a partir desse subconjunto. Conferir `progresso.json` para contagem posterior.

## O que muda

Somente a posição da LayerNorm em cada bloco: pós-normalização passa para pré-normalização. Mantêm-se a entrada de retornos horários, as quatro moedas, contextos 24/72/168/336h, horizonte24h, origens horárias, três seeds e todo o treinamento da extensão corrigida. A penalização continua AdamW com isenção de A_log/D; não é a política uniforme de Adam do CryptoMamba.

Comparador direto: Mamba corrigido de `7868a4d847c1410fc681`. São 384 novos ajustes pré-normalizados e dois controles Mamba corrigidos. Os resultados antigos de LSTM, ARIMA e Naive são herdados; não há novos treinamentos dessas famílias. Os dois estudos anteriores permanecem preservados.

## Método e evidências

- [Protocolo anterior aos novos treinos](protocolo_normalizacao_mamba.md).
- [Decisão e autorização](adr/0005-proposta-prenormalizacao-mamba.md).
- [Configuração](../configuracoes/normalizacao_mamba_001.json).
- [Autorização preservada](../registros/normalizacao/autorizacao.json).
- [Conferência da penalização no CryptoMamba](../registros/normalizacao/conferencia_criptomamba.json).
- [Cronologia factual e progresso verificado](andamento.md).

O congelamento cria o ID próprio após testes, conferência de artefatos e qualificação CUDA. A grade começa somente após aprovação de dois controles e dois pilotos. A publicação requer cobertura exata das fases e auditorias; os pilotos são parte dos 384 ajustes. O relatório automático ficará na pasta da execução, preservando este documento interpretativo.

## Como interpretar quando terminar

O contraste principal é MSE pré-normalização menos MSE pós-normalização corrigida: negativo favorece a variante nova. Intervalos que incluem zero não demonstram melhora nem equivalência. Comparar também magnitude, consistência entre seeds e contextos, e resultados da política Spot sem confundi-los com erro preditivo. Não escolher subconjuntos favoráveis.

Desenvolvimento de 2023 e avaliação retrospectiva de 2024–2025 devem permanecer separados. Todos esses períodos já foram consultados; o novo congelamento não cria holdout intocado. Resultados finais, análise independente, incidentes e preservação antes/depois serão vinculados após existirem evidências.
