# ADR0027 — Busca Astra002 com treino, parada e comparação separados

Data:04/11/2026. Situação: autorizada pelo pesquisador; qualificação e execução verificáveis em `registros/busca_astra_002/estado.json`.

## Contexto e autorização

Após discutir uma segunda sessão de um dia, o pesquisador confirmou: “arrume tudo e já pode começar o processo. Vou deixar o notebook ligado”. A proposta anterior e seu checksum estão preservados em `registros/busca_astra_002/proposta_preservada/`; [protocolo autorizado](../protocolo_busca_astra_002.md) e `configuracoes/busca_astra_002.json` são a especificação executiva. Essa confirmação autoriza preparar, qualificar, congelar e iniciar o orçamento descrito, sem exigir nova confirmação redundante.

## Decisão

Mamba1 oficial, BTC/1h/log-retorno24h, Huber/AdamW e estado16 fixos. Novo pacote `experimentos/busca_astra_002/` importa rede e ajuste encerrados sem editá-los. Três recortes progressivos de2023 separam treino T, parada V e comparação S; purga24h e população comum336. Busca de até12receitas com um fator por proposta, quatro ablações iniciais e diagnósticos complementares. Astra recebe só desenvolvimento, sem ferramentas ou testes, por Codex autenticado, sem API paga.

Duas âncoras: C05 anterior e OHLCV cru+Huber. **Zero ajustes herdados**: reestimar ambas na final pelo mesmo executor, evitando pressupor equivalência operacional completa. Matrizes/receitas antigas podem ser conferidas como teste de engenharia. Máximo197ajustes reais, incluindo dois controles,12consultas ao Astra (uma de qualificação técnica) e24h desde preparo operacional. Até800carteiras finais pelo F03 preservado, Smart e direcional filtrada, Spot/bilateral, custos base/estresse. Lucro nunca seleciona candidata.

Triagem seis ajustes por receita; até três promovidas recebem terceira seed em cada S. Elegibilidade exige superar referências/Naive/média constante no MSE relativo, estabilidade temporal e limite de MAE previamente fixados. Sem elegível, resultado negativo e encerramento sem finalista. Uma finalista congelada e duas âncoras recebem oito seeds por B1–B4. Inferência pareada por seeds/dias e correção dos três contrastes, explicitamente retrospectiva e condicional à seleção.

## Verificação e consequências

Testes incluem causalidade, escalas, purga, origens iguais, direções/constantes/métricas, gates de seleção, cobertura197 em fila simulada e bootstrap. Qualificação CUDA usa dados sintéticos, atualização, reprodução, recarga e alteração dos alvos de S sem mudar seleção/predição. Controle real A0/S1/42 precede outras seeds; controle candidata/B1/42 precede demais ajustes finais. Falha interrompe conservadoramente; não reiniciar por timeout/reboot sem conferir PIDLinux, locks, fontes e incidentes.

Identidade, autorização, fontes copiadas, pedidos, logs, propostas, curvas, checkpoints, previsões, avaliações e preservação antes/depois pertencem ao ciclo novo. Preparação não equivale a treino concluído. Não promover configuração automaticamente, exigir lucro ou considerar2024–2025 holdout intocado. Objetivo continua investigação de decisões de projeto para o TCC.
