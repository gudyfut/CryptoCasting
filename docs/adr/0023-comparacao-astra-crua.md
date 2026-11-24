# ADR0023 — Comparação da C05 Astra com OHLCV cru + Huber

Data da decisão e registro:04/11/2026. Estado:autorizada pelo pesquisador, qualificação/preparação a conferir nos registros.

## Contexto

A busca Astra encerrou com C05,janela relativa72h/Huber. Seu MSE médio0,000612275 melhorou a referência reestimada, mas não o Naive. A receita antiga crua168h/Huber tinha MSE0,000611698; a comparação histórica não isolava executor/população. Ambos os resultados já são conhecidos e retrospectivos.

## Decisão e autorização

O pesquisador solicitou comparação justa, mesmo executor/dados/oito seeds, autorizando o início. Herdar32C05 e treinar32crus no executor científico da busca, sem modificar suas fontes. Adicionar controle de reprodução herdada C05B1/42 e repetição cruaB1/42:34ajustes novos delimitados, controles fora das médias. Reutilizar192carteiras C05+24benchmarks, produzir192cruas. Não recolher dados ou repetir as32C05.

Mantêm-se alvo24h,candles1h,quatro blocos,seeds,arquitetura/otimizador/perda,seleção e políticas operacionais. Duas diferenças entre receitas:representação e contexto. Três contrastes fixos com ajuste de multiplicidade; nenhum modelo promovido automaticamente. A autorização não é busca de novas receitas nem certificação de lucro.

[Protocolo](../protocolo_comparacao_astra_crua.md), [estado verificável](../../registros/comparacao_astra_crua/estado.json), [origem Astra](../../registros/busca_astra/fechamento.json). Preservar os ciclos anteriores e todas as tentativas.
