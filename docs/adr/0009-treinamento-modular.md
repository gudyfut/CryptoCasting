# ADR 0009 — Orquestração modular de treinamento e avaliação

Data da decisão e registro:29/10/2026. Situação: implementação/qualificação concluídas; treinamento, validação e testes da rodada ab5baf3eab3a2e66d8b2 autorizados por “ok” explícito em29/10/2026. Evidência em [autorização](../../registros/treinamento/autorizacao.json); progresso e resultados são registrados separadamente.

## Contexto

Dados e consumo foram separados nas ADRs0007/0008. O executor OHLCV preparado ainda usava a implementação anterior. O pesquisador pediu organizar treinamento, seleção e checkpoints, integrar as camadas e conferir o caminho até os resultados antes de autorizar ajustes reais.

## Decisão

Criar `treinamento/`, `avaliacao/` e `run_treinamento.py`, com [arquitetura própria](../arquitetura_treinamento.md). Manter o desenho científico R0 e seus limites de orçamento; congelar uma nova identidade que incorpore os módulos revisados. Preservar integralmente `estudo_ohlcv/` e a identidade92e3eb82e3f6adf99994. Não aproveitar autorizações antigas como autorização do novo ciclo.

Separar treino/seleção da avaliação. Guardar checkpoints por época de melhora, vinculados ao contrato; recarregar antes de testar. Preservar candidatos ARIMA, seeds, controles e tentativas. Exigir qualificação sintética completa, integridade dos dados reais, lock, rastreabilidade e autorização vinculada antes do início.

## Alternativas e consequências

Alterar o executor preparado no lugar invalidaria suas fontes congeladas. Reutilizar executores históricos dentro da nova camada manteria o acoplamento que motivou a revisão. A migração escolhida mantém as implementações anteriores como evidência e usa a nova cadeia apenas por identidade própria. O pequeno conjunto de funções econômicas/estatísticas migradas precisa de testes de equivalência e limites explícitos.

Não muda o problema, os hiperparâmetros, as populações ou o significado retrospectivo do teste. Uma migração não prova resultados numéricos idênticos de futuros treinamentos. Os ensaios são artificiais e não contam como treinamento de mercado nem aceite acadêmico. Evidências e falhas ficam em `registros/treinamento/`; fatos de conclusão são registrados no [andamento](../andamento.md).
