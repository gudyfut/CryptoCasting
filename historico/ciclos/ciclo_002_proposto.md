# Ciclo 002 — proposta de ablação do estado interno do Mamba

**Estado: proposto, não executado.** Definido em 18/10/2026 após a análise completa do ciclo 001. Não é busca automática ilimitada nem abertura de B1–B4. Configuração candidata: [ciclo_002_proposto.json](../../configuracoes/ciclo_002_proposto.json).

## Motivação e hipótese

No desenvolvimento do ciclo `4e232a796fcda0ea34c3`, Mamba/W168 piorou a log-loss semanal em média 0,026343 frente a W24. As duas redes perderam para as frequências de treino em H168. Esses achados não demonstram sobreajuste nem atribuem a causa ao estado interno.

A hipótese testável é: **reduzir o tamanho do estado Mamba de 16 para 8, mantendo o restante fixo, melhora a previsão semanal e/ou reduz a penalidade do contexto longo.** O sentido da mudança testa uma representação menor; não se presume que 8 seja ótimo. O valor é uma ablação simples do catálogo metodológico, e não resultado de busca escondida. Uma piora é igualmente informativa.

H168 foi escolhido para investigar a deficiência observada, e não por ter maior lucro. A seleção usa o teste de desenvolvimento já consultado; o novo ciclo também será desenvolvimento retrospectivo. Os quatro pares e os dois contextos permanecem, evitando escolher somente a moeda ou janela favorável.

## Desenho fechado

| Item | Definição |
|---|---|
| Referência | Células H168 do ciclo 001, `4e232a796fcda0ea34c3` |
| Único parâmetro alterado | Mamba `estado`: 16 → 8 |
| Moedas | BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT |
| Contextos | 24 e 168 horas |
| Prazo máximo | 168 horas |
| Folds/seeds | DB1–DB4, seed 42 |
| Dados | Dataset `9341610dbb329a858784`; mesmas origens, features, scalers e rótulos |
| Demais parâmetros | Iguais ao ciclo 001; inclusive largura 32, duas camadas, dropout 0,1, convolução 4, expansão 2, AdamW e early stopping |
| Política econômica | Mesmos custos, risco, limiar e convenções; nenhuma procura de limiar |
| Orçamento | 32 células novas × duas redes = 64 ajustes neurais; máximo de 100 épocas cada, patience 10 |

O executor atual sempre treina a dupla: serão 32 Mamba novos e 32 LSTM repetidos como controle de execução. A LSTM inalterada não será contada como nova arquitetura nem evidência independente. A referência primária da ablação são os 32 Mamba H168 já executados. O fluxo atual pode recalcular até 16 ajustes AR(1) e suas previsões por moeda/fold dentro da nova identidade; não prometer reaproveitamento entre identidades que a implementação não oferece. O cache atual calcula os três prefixos H1/H24/H168 mesmo quando a grade usa somente H168; seu custo não está incluído na contagem de 64 ajustes neurais. Essa recomputação também não é evidência independente adicional.

Não é necessário recolher o mercado ou reconstruir a pipeline para alterar somente o estado interno. Verificar hashes e conservar o dataset. Se surgir um defeito real de dados ou implementação, registrar a interrupção, explicar o impacto e revisar a proposta antes de continuar; não misturar uma correção silenciosa com a ablação.

## Comparação, seleção e parada

1. Antes do primeiro treino, qualificar forward/backward, causalidade e recarga da dimensão 8 no mesmo ambiente, registrar número efetivo de parâmetros e gerar outra identidade. O qualificador deve efetivamente receber estado 8; a aprovação anterior de estado 16 não basta. Preservar os snapshots do ciclo 001.
2. Preparar a comparação entre ciclos por timestamps e por moeda/W/H/fold/seed, verificando rótulos e população idênticos. Não usar índice de linha. O consolidado normal de cada ciclo não substitui esse contraste entre variantes.
3. Critério primário: diferença média de log-loss **estado8 menos estado16**, peso igual nas 32 células. Calcular também contraste pareado por blocos sincronizados de 14 dias, 2.000 réplicas, sensibilidades de 7/28 dias, sem usar os testes para escolher época.
4. Critério administrativo para considerar a variante promissora: redução média de pelo menos **0,005** na log-loss, com redução também em pelo menos três dos quatro folds e três das quatro moedas, após agregar os contextos. Esse limiar é definido para limitar a busca, não tem significado de teste de hipótese ou garantia econômica. Reportar os intervalos mesmo se o critério for atingido; não chamar isso de confirmação independente.
5. Secundários: Brier, calibração das três classes, diferença de contexto W24−W168, tamanho/tempo/memória, operações, retorno, drawdown e exposição. Publicar a interação de contexto: se estado8 melhora somente W24, não afirmar que resolveu o contexto longo. Lucro isolado não substitui o critério primário.
6. Parar após as 32 células novas auditadas e sua análise, independentemente do resultado. Sem procurar outros estados, larguras, seeds ou limiares dentro deste ciclo. Falhas e repetições justificadas por defeito devem ficar registradas e contabilizadas.
7. Se promissora, propor separadamente confirmação da referência e da variante nas seeds 17 e 2026, preservando também a 42. Se não promissora, manter a referência como referência; não apagar a tentativa. Uma configuração final só será escolhida depois de avaliar a estabilidade e o segundo eixo econômico.

Essa proposta atende à investigação dos parâmetros internos do Mamba sem modificar simultaneamente candle, prazo, política e arquitetura. Mesmo um ganho preditivo não prova utilidade econômica. Os dados finais continuam bloqueados durante a seleção, e sua abertura exige congelamento e declaração de exposição prévia pelo pesquisador.
