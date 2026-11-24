# ADR0018 — Perda robusta no Mamba16

Data: 02/11/2026. Situação: execução autorizada pelo pesquisador após proposta explícita; qualificação e identidade ainda devem preceder mercado.

## Contexto

Estados, taxa constante menor e taxa dinâmica foram investigados e preservados. O ciclo99884456ac71fedfd9b0 não justificou substituir a referência16/AdamW/0,0002 constante. A hipótese seguinte investiga a influência de resíduos extremos, sem afirmar que extremos sejam erros de dados ou que robustez garanta menor MSE.

## Decisão

Executar seis ajustes com **2 × Huber(delta1 no alvo padronizado)**, mantendo dados, arquitetura, otimizador, taxa constante, batch, clipping, seleção e parada. Comparar com as seis referências existentes. Escolha/critério primário continuam MSE global de validação; demais métricas/Spot são secundários. Nenhuma grade de delta, repetição real extra ou promoção automática.

Código em `experimentos/perda_huber/`, entrada `python -m experimentos.perda_huber`, testes `tests_huber/`, ponteiro `registros/perda_huber/execucao.json`. O módulo executável evita editar `run_experimento.py`, que também integra fontes congeladas da rodada anterior. [Protocolo](../protocolo_perda_huber.md). As fontes encerradas permanecem em seus caminhos.

## Consequências

O fator2 iguala valor/gradiente ao MSE perto de zero; a limitação de influência nos maiores resíduos ainda muda a dinâmica do AdamW/clipping como efeito da intervenção. Huber altera a estimativa favorecida pela perda; melhorar MAE/lucro e piorar MSE será reportado como compromisso, sem trocar retrospectivamente o primário.2024/2025 conhecidos, sem alegação de confirmação independente. A avaliação walk-forward ampliada permanece etapa futura. Orçamento secundário54carteiras Smart com política congelada, sem nova estratégia. O encerramento será registrado nas evidências, não inferido desta decisão.
