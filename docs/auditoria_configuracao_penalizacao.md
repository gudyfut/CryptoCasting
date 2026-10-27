# Revisão das configurações para a extensão de penalização

Revisão de 26/10/2026. A correção planejada é restrita ao tratamento dos parâmetros marcados pelo Mamba. O código e o protocolo originais permanecem como evidência do que foi executado. A revisão de 24/10 e seus recibos estão em `registros/revisoes/parecer_2026-10-24.json`.

## O que foi encontrado

O treinador original aplica AdamW com penalização uniforme de 0,001. Os parâmetros `A_log` e `D` dos dois blocos Mamba têm `_no_weight_decay=True`, mas esse marcador não é processado pelo otimizador genérico. A extensão cria grupos explícitos, com zero nesses quatro tensores e 0,001 nos demais. São 2.176 parâmetros escalares isentos e 17.953 penalizados. O marcador `_no_reinit` de `dt_proj.bias` já era respeitado indiretamente: não existe reinicialização genérica que sobrescreva a inicialização oficial. Nenhuma inicialização será alterada.

Há uma diferença adicional na qualificação antiga: seu teste sintético de atualização passava somente a taxa de aprendizado ao AdamW, usando o weight decay padrão do otimizador, enquanto o treinamento real passava explicitamente 0,001. O treinamento de mercado executou o coeficiente documentado; a qualificação antiga não conferia essa particularidade. A qualificação nova utiliza todos os argumentos do treinamento, inclui clipping e verifica os grupos e a atualização dos pesos. O recibo antigo não será regenerado.

## Matriz de revisão

| Componente | Regra verificada e evidência | Tratamento na extensão |
|---|---|---|
| Alvo e relógio | Retorno logarítmico entre closes separados por 24h; origem após fechamento completo. Revisão de 24/10 reconstruiu as quatro séries desde os minutos salvos. | Mesmo dataset, sem nova coleta. |
| Lacunas | Sem interpolação; elegibilidade comum usa 336 retornos passados e observabilidade das pontas; população operacional usa somente passado. | Mesmas máscaras e origens, conferidas por célula contra o controle. |
| Separação temporal | Treino expansivo, validação seguinte, teste posterior; destino estritamente anterior ao fim de cada partição. | Mesmas datas DB1–DB4/B1–B4. Sem split aleatório. |
| Escalas | Entradas padronizadas nos retornos únicos das janelas de treino; alvo no treino. A revisão conferiu os 768 checkpoints. | Escalas recalculadas e comparadas com o checkpoint histórico de cada par. |
| Arquitetura | Mamba oficial CUDA, 20.129 parâmetros; LSTM, 12.961. Redes unidirecionais e saída do último estado. | Módulo original reutilizado sem alterações. |
| Inicialização e ordem | Seeds 17/42/2026, pesos novos por ajuste, permutação de exemplos apenas no treino. | Mesma rotina; criação dos grupos não muda RNG nem pesos. |
| Gradientes | MSE somado por microbatch e dividido pelo batch efetivo; clipping após acumulação. | Código estruturalmente idêntico fora da construção do otimizador. |
| Seleção de época | Mínimo estrito da MSE de validação em unidades originais; primeira época em empate, máximo100/paciência10. | Mesma regra. A época resultante pode mudar devido à correção. |
| Inferência | `eval()` desativa dropout; desfazer escala do alvo; previsão finita e recarga exata. | Mesmo procedimento em validação, teste e operação. |
| Otimizador | lr0,0002; betas0,9/0,999; eps1e-8; penalização0,001. | Única exceção: zero onde `_no_weight_decay=True`. Grupos contíguos mantêm ordem. |
| Precisão e backend | FP32, TF32 desativado, backend oficial sem fallback. Repetições CUDA podem ter pequenas diferenças. | Conferir versões, dimensões, forward/backward, recarga e repetição; não alegar determinismo absoluto. |
| ARIMA | d=1 sem deriva, ordens p/q0..2 selecionadas por validação, estados filtrados causais, calendário com NaN. | Resultados herdados verificados, sem reestimar. |
| Agregação | Média dos escores entre seeds e pesos iguais entre moedas/contextos/blocos. | Contraste principal corrigido menos original; resultados novos e herdados identificados. |
| Incerteza | Blocos móveis de dias, mesma reamostragem por moeda/contexto, sem atravessar folds. | Mesmo bootstrap, sensibilidades7/14/28, com limitação de exposição prévia. |
| Operação | Spot comprado/caixa, uma decisão diária; preços de minuto, custos nos dois lados, sem filtro por alvo futuro. | Mesma política e conferência independente das contas e sinais. |

## Limitações preservadas

O estudo compara configurações compactas fixas, não arquiteturas otimizadas individualmente nem redes com orçamento de parâmetros igual. A entrada é univariada; aumentar o contexto não adiciona volume, notícias ou indicadores externos. Os alvos horários de 24h se sobrepõem. O bootstrap trata parte dessa dependência temporal, mas não quantifica toda a incerteza de treinamento e seleção entre ciclos.

O estudo de referência registrou recarga exata, enquanto a repetição sintética de treinamento Mamba teve pequenas diferenças em W168/W336. A nova comparação qualifica essa situação e reexecuta controles curtos/longos. Nenhuma diferença será atribuída exclusivamente à arquitetura sem distinguir configuração, aleatoriedade e seleção por validação.

Uma nova hipótese foi formulada depois de observar 2024–2025. A extensão deve ser descrita como análise retrospectiva controlada. Congelamento e pares iguais melhoram a rastreabilidade, mas não restauram um período de confirmação intocado.

## Evidências e atualização

Os testes específicos estão em `tests_penalizacao/`. A preparação preserva seus logs e os dos contratos existentes; a qualificação registra ambiente, casos, agrupamento uniforme, tolerâncias e descrição dos grupos. O novo `execucao.json` vincula fontes, protocolo e recibos. Cada ajuste tem `otimizador.json`, `epocas.json`, `checkpoint.pt`, previsões, métricas e auditoria. Antes de concluir a extensão, conferir grade completa, publicações das duas fases e `preservacao_depois.json`.

A preparação de `7868a4d847c1410fc681` aprovou 24 testes (17 existentes e sete específicos), 12 casos CUDA com repetição e recarga e quatro verificações sintéticas da equivalência de agrupar parâmetros mantendo a penalização uniforme. Registro: `registros/penalizacao/preparacao_2026-10-26T233400.168859_0000/qualificacao.json`. A qualificação não substitui os controles reais nem a execução completa da grade.
