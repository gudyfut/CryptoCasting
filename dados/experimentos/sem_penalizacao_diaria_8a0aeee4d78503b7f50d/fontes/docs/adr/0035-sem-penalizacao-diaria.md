# ADR0035 — Retirar a penalização do Adam no desenho diário padronizado

Data: 08/11/2026. Estado: autorizado para qualificação e execução, ainda sem conclusão científica.

## Contexto

O diagnóstico da rodada `f3f8772670f244779ad7` mostrou perda de contribuição dos ramos Mamba, também observada na referência de retorno. O coeficiente L2 de0,001 aplicado globalmente é candidato causal. Reprodução e contabilidade corretas não garantem aproveitamento da capacidade da rede. Evidências na cronologia e em `registros/padronizacao_diaria/diagnosticos/2026-11-08T200124.658529Z/conclusao.json`.

## Decisão autorizada

Testar apenas `weight_decay=0` no Adam, contra a referência padronizada preservada. Mesmas seeds42/17/2026 e controle42,1000épocas, entradas/alvo/arquitetura/taxa/scheduler/seleção/política/custos. Nenhuma busca adicional. Qualificar observação não interventiva dos ramos e sua equivalência com o treinador herdado antes de iniciar. [Protocolo](../protocolo_sem_penalizacao_diaria.md).

## Consequências e limites

Quatro ajustes novos e70carteiras em namespace próprio. Não retreinar a referência nem editar protocolos/fontes históricos. Retirar penalização não garante generalização, lucro ou recuperação dos ramos; pode aumentar sobreajuste. Reportar todos os resultados, sementes e contrastes, com controles fora das médias. 2024/2025já consultados; não apresentar confirmação intocada. Alterar somente grupos A_log/D, trocar AdamW, taxa ou eixo temporal seriam hipóteses distintas e não estão autorizadas neste ciclo.
