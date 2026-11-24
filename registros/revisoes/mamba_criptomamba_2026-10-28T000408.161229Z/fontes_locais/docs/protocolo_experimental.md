# Protocolo experimental — retorno24-1.0

Definido em 20/10/2026, antes da execução de mercado. O pesquisador autorizou implementar e executar esta referência completa. Configuração: `configuracoes/retorno24_001.json`. Extensões futuras não são parte desta grade.

## 1. Pergunta e hipótese

Investigar como 1, 3, 7 e 14 dias de sequência de retornos influenciam a previsão terminal em 24 horas de Mamba e LSTM em BTCUSDT, ETHUSDT, BNBUSDT e XRPUSDT, Binance Spot. Comparadores Naive e ARIMA. A conclusão pode ser negativa; não exigir vantagem neural, vantagem Mamba ou lucro. Não extrapolar quatro moedas escolhidas para todo o mercado.

Alvo `y_t = ln(P_(t+24h)/P_t)`. `P_t` é o close do candle horário completo imediatamente anterior ao instante t, em UTC. Não é preço executável garantido. A saída neural é uma estimativa pontual do retorno logarítmico médio condicional, treinada por MSE. `expm1(previsão)` e `P_t*exp(previsão)` são transformações para apresentação; a última não é automaticamente a esperança do preço em nível.

Não prever trajetória, probabilidade de alta, intervalo ou ordem de eventos. Direção derivada do sinal é diagnóstico secundário, não um classificador otimizado. Indicadores, OHLCV como features adicionais, quantis e candles 15/30min são hipóteses para outros ciclos.

## 2. Grade predefinida

- Candle 60min, origem a cada hora, horizonte exatamente 24h.
- Entrada única: retorno logarítmico horário. Sem informação auxiliar de volatilidade nem indicadores com histórico escondido.
- Contextos W=24/72/168/336 retornos. Um retorno usa dois closes: W retornos correspondem a W horas de variação e W+1 preços de fronteira.
- Modelos por moeda, sem pré-treino conjunto; Mamba e LSTM em todas as células, seeds 17/42/2026.
- Mesmas origens elegíveis entre contextos/modelos e, para a análise principal, entre quatro moedas. Isso controla população, mas limita a inferência à população comum; reportar exclusões por moeda.
- 16 combinações moeda/contexto por bloco. Quatro blocos por fase × três seeds × duas redes = 384 ajustes neurais por fase; 768 no total, antes de falhas/revisões. Não contar checkpoint recarregado como novo ajuste.
- ARIMA: nove candidatos por moeda/bloco, p/q em {0,1,2}, d=1, sem deriva. 16 seleções por fase, 144 ajustes candidatos planejados por fase; o comparador selecionado é compartilhado entre contextos/seeds, não réplicas independentes.
- Naive: retorno zero/persistência de preço, sem treinamento e sem seeds. Não é persistência do último retorno.

## 3. Dados, tempo e população

Fonte: Binance Public Data Spot, ZIP mensal 1m em `[2021-01-01,2026-01-01)` UTC, 240 arquivos esperados. Reutilizar arquivos antigos somente após conferir SHA-256 oficial; copiar brutos para a área nova sem alterar o arquivo histórico. Preservar ZIPs, checksums, URLs, unidades e auditorias. Fonte: https://github.com/binance/binance-public-data . Desde janeiro de 2025, timestamps Spot em microssegundos, antes em milissegundos.

Auditar ordem, duplicatas, domínio temporal, finitude, preços positivos, relações OHLC, volume e negócios não negativos. Minuto interrompido (close_time antes do fim previsto) é preservado no ZIP e marcado incompleto. Construir grade completa de minuto com NaN em lacunas; não interpolar. Hora só é válida com todos os 60 minutos completos. OHLC por primeira abertura, máxima/mínima e último fechamento; volumes somados. Origens usam o fechamento exclusivo (fim da hora), não a abertura do candle.

Entrada causal elegível: todos os últimos 336 retornos finitos. Isso garante as mesmas origens de comparação de W. População preditiva: entrada causal comum às moedas e preços terminais t e t+24h observáveis. Não exigir percurso futuro completo para um alvo terminal; não excluir pelo sinal/magnitude do retorno. Lacunas entre pontas não são preenchidas. Exclusão por ausência de alvo pertence à avaliação preditiva, nunca à decisão operacional. Preservar separadamente máscaras causal e observada.

O dataset contém OHLC horário, retornos, preços de origem/destino, timestamps, máscaras por moeda e comuns. Manifesto com hashes de fontes e saídas. Arquivos de minuto são mantidos para simulação de execução e auditoria de risco.

## 4. Separação temporal

Treino expansivo desde 01/01/2021. Datas UTC; intervalos semiabertos. Cada ajuste neural parte de pesos novos.

| Bloco | Início validação / fim treino | Início teste / fim validação | Fim teste |
|---|---|---|---|
| DB1 | 2022-10-01 | 2023-01-01 | 2023-04-01 |
| DB2 | 2023-01-01 | 2023-04-01 | 2023-07-01 |
| DB3 | 2023-04-01 | 2023-07-01 | 2023-10-01 |
| DB4 | 2023-07-01 | 2023-10-01 | 2024-01-01 |
| B1 | 2023-10-01 | 2024-01-01 | 2024-07-01 |
| B2 | 2024-04-01 | 2024-07-01 | 2025-01-01 |
| B3 | 2024-10-01 | 2025-01-01 | 2025-07-01 |
| B4 | 2025-04-01 | 2025-07-01 | 2026-01-01 |

Em cada partição, manter origens cujo destino t+24h seja estritamente anterior ao fim da partição. É uma purga conservadora comum. Não dividir aleatoriamente. Contextos de validação/teste podem incluir passado anterior à fronteira: isso é informação disponível, não vazamento. Nunca permitir que rótulos de treino atravessem a fronteira de validação.

DB1–DB4 são desenvolvimento já exposto em estudos anteriores e continuarão assim. B1–B4 são avaliação predefinida posterior. Antes da abertura: congelar protocolo, configuração, códigos, dataset, ambiente, regras de atualização e política; registrar exposição humana anterior. Exposição desconhecida/confirmada impede alegar holdout intocado. Não substituir por alegação de independência só porque o alvo mudou.

A escolha de época/ordem em cada validação posterior é algoritmo predefinido; testes antigos podem integrar treino/validação posteriores. Não há alteração discricionária da metodologia entre B1 e B4. Não escolher contexto/seed vencedores pelo teste; avaliar toda a grade. Novas experiências de features/candles ficam para ciclos separados; após consultar avaliação, esses dados não voltam a ser confirmação intocada.

## 5. Normalização e treinamento

StandardScaler de entrada por moeda/bloco, ajustado apenas aos retornos horários únicos pertencentes à união das janelas W336 das origens de treino. Reutilizar entre W/redes/seeds. Não contar repetição de janelas como observações adicionais. Alvo padronizado pela média/desvio populacional dos retornos-alvo de treino; ambos salvos. MSE de validação calculado após desfazer a escala, na unidade original do log-retorno.

Mamba oficial: projeção 1→32, dois blocos Mamba com estado16, convolução4, expansão2, residual e LayerNorm; dropout0,1 e saída linear escalar do último estado. LSTM: entrada1, largura32, duas camadas unidirecionais, dropout0,1 entre camadas e saída linear escalar do último estado. Contagens de parâmetros medidas, não presumidas iguais.

AdamW lr0,0002, weight_decay0,001, betas(0,9;0,999), epsilon1e-8; batch efetivo64, microbatch32; clipping de norma1; no máximo100 épocas, paciência10 sem melhora estrita. Escolher exclusivamente a menor MSE de validação; em empate, manter primeira época. Mesma regra/entradas nas redes. Sem scheduler, pesos de classe, calibração ou busca neural nesta referência. Treino pode embaralhar exemplos dentro do passado permitido; isso não é split aleatório.

FP32, TF32 desativado, cuDNN determinístico e benchmark desativado, seeds fixadas. `torch.use_deterministic_algorithms(..., warn_only=True)` não certifica todos os kernels; registrar avisos e comparação de repetições sintéticas. Qualificar importação, forward/backward, atualização, repetição e recarga para todos os W e ambas as redes. Não usar implementação alternativa silenciosamente. Recarga de pesos deve reproduzir exatamente previsões salvas sob o mesmo ambiente e lote. Preservar checkpoints, épocas, escalas, tempos e memória.

## 6. ARIMA e Naive

ARIMA(p,1,q) sem tendência/deriva no log-preço horário, nove candidatos. Ajuste por máxima verossimilhança em espaço de estados, preservando NaN em horas ausentes; não compactar o calendário. Estimar parâmetros apenas no histórico permitido de treino, encerrado no último preço de destino dos alvos de treino, ainda estritamente anterior à validação. Assim o baseline pode usar os preços já revelados pelos alvos de treinamento das redes. Informações passadas subsequentes atualizam o estado filtrado, sem reestimar parâmetros durante validação/teste.

Para cada origem, usar o estado **filtrado**, nunca o suavizado com futuro, e projetar 24 passos. Previsão de retorno = log-preço projetado − log-preço observado na origem. Selecionar menor MSE da validação nas mesmas origens das redes. Empates: menor p+q, depois p, depois q. Máximo200 iterações; falhas/não convergência registradas e excluídas da seleção, nunca omitidas do relatório. Se nenhum candidato válido, bloquear aquela avaliação. Preservar parâmetros, estado inicial, série temporal e diagnósticos; conferir previsões vetorizadas contra `get_forecast(24)` em prefixos truncados.

Naive produz zero em todas as origens. Métricas direcionais de uma previsão neutra são apenas diagnósticas: não interpretá-lo como classificador de alta/queda nem atribuir automaticamente probabilidade0,5. ARIMA(0,1,0) sem deriva coincide com persistência; a referência explícita permanece, sem contar duplicação como modelo independente adicional.

## 7. Métricas e análise

Principal: MSE do log-retorno. RMSE, MAE e viés como complementares. Habilidade frente a Naive `1 − MSE_modelo/MSE_naive`; indefinida se denominador zero. Habilidade positiva indica redução de erro na mesma população, não lucro. Reportar MSE/RMSE/MAE por moeda/bloco/contexto/seed; não somar erros em dólares entre moedas.

Resumo de cada família: média de MSE entre seeds por célula; depois peso igual entre moedas/contextos/blocos. Reportar também habilidade média por célula, identificada como tal (não equivalente à razão de MSEs agregadas). Mostrar B e DB separados. Não escolher métrica, seed, contexto ou moeda após conhecer o placar.

Direção: sinais −1/0/+1 com zero exato; acurácia em todos os casos, recalls de queda/alta e sua média balanceada nas classes não nulas. Previsão zero em caso real não nulo conta como erro. Retornos exatamente zero mantidos, contados e excluídos apenas dos dois denominadores de recall; não criar limiar depois do resultado. Não interpretar balanced accuracy como percentual total de acertos.

Contrastes principais Mamba−LSTM e ganho frente a Naive/ARIMA; comparação de contextos dentro de mesma moeda/bloco/seed. Não usar contagem de vitórias como teste estatístico. Incerteza: bootstrap pareado por blocos móveis de dias UTC, 2.000 réplicas, 14 dias principal e sensibilidades7/28, mesma reamostragem para moedas/modelos/contextos, sem atravessar folds. Preservar contagens, recalcular escores; seed20261020. Dependência de alvos sobrepostos e correlação entre moedas impedem tratar cada linha como independente. Intervalos condicionais ao período/modelos, não captura completa da seleção entre ciclos; apresentar dispersão entre seeds separadamente.

## 8. Simulação econômica complementar

Binance Spot comprado/caixa, sem alavancagem, short ou stop. Decisão às00:00UTC, entrada no open do minuto00:01 e saída exatamente24h depois, independentemente do resultado. Uma operação diária por estratégia (moeda/modelo/contexto/seed), sem carteira combinada. Na fronteira de dias, saída agendada é contabilizada antes da nova entrada no mesmo minuto. Não entrar se o prazo de saída ultrapassar o fim do bloco. Trocar modelo nas fronteiras; manter capital ao concatenar blocos da mesma fase.

Capital ilustrativo10.000USDT. Taxa0,001 e slippage0,0005 por lado. Entrar com100% do patrimônio somente se a previsão logarítmica exceder `ln((1+s)*(1+f)/((1-s)*(1-f)))`. É uma regra heurística fixa, não estimativa garantida de lucro esperado. Quantidade = capital/[(open_entrada)*(1+s)*(1+f)]; saída = quantidade*open_saida*(1-s)*(1-f). Caixa não rende. Sensibilidade: taxa0,002/slippage0,001, preservando sinais base. Referências operacionais: caixa e compra diária sistemática com mesmas entradas/saídas/custos.

Elegibilidade de entrada usa apenas passado disponível e calendário. Não usar máscara de alvo futuro comum para decidir entradas. Precisa haver previsão operacional também para origens cujo alvo futuro não seja observável. Se um preço de execução estiver ausente/sem negócios, marcar operação/curva como não auditável, sem remover para melhorar resultado. Lacuna dentro de posição impede drawdown integral, mesmo se as pontas forem observáveis; separar disponibilidade de retorno das pontas e risco do percurso. Marcação a mercado por minuto; não inventar preços em lacunas. Publicar custos, operações, exposição, retorno e drawdown, com limites de auditabilidade. Não chamar esta simulação de futuros nem inferir liquidação ou stops.

## 9. Evidência e gates

Cada tentativa deve iniciar com identidade, timestamps, configuração, fontes/hashes, ambiente, dataset e status em andamento. Finalizar como auditada apenas após recarga, verificação das origens e recálculo independente. Falha/interrupção permanece documentada; não sobrescrever tentativa malsucedida com sucesso posterior. Retomar somente checkpoints/células íntegros; verificar PID/lock antes de executar. Código científico alterado exige nova identidade.

Antes de treinar mercado: testes sintéticos de alvo24h, ausência/duplicatas, purga, invariância ao futuro, scaler, Naive/ARIMA, métricas e finanças; qualificaçãoCUDA nas dimensões reais. Executar primeiro casos curto/longo reais na configuração completa e integrar à grade, sem duplicar. Auditar esses casos antes de liberar o restante. Abertura da avaliação só após desenvolvimento auditado, congelamento e exposição registrada.

Aceite final: inventário completo de ajustes/candidatos, previsões por origem, checkpoints e recargas, métricas recalculadas, todas as falhas preservadas, análise de incerteza, simulação com ausências explícitas, documentação factual, interface somente com resultados novos e verificações de gráfico/contagem/filtros. As próximas hipóteses ficam propostas; não iniciar busca indefinida automaticamente.
