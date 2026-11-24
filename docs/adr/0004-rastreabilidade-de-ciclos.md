# 0004 — Relacionar ciclos e registrar futuras mudanças

- Decisão e registro: 27/10/2026.
- Situação: adotada para organização; não autoriza novos treinamentos.
- Origem: solicitação do pesquisador neste chat para conferir a reorganização feita em outro dispositivo e guardar decisões, desenhos, treinamentos e resultados para a cronologia do TCC.

## Contexto

As ADRs e a separação de responsabilidades da ADR 0003 são mantidas. Faltava um índice que ligasse os desenhos históricos, as configurações, os recibos e as publicações em layouts diferentes. Vários resultados leves eram elegíveis para Git, mas ainda não versionados. Fontes locais do notebook e do commit também podem divergir em bytes por finais de linha, mesmo com texto equivalente.

## Decisão e alternativas

Criar um catálogo retrospectivo de referências em `registros/catalogo_estudos.json`, um procedimento de registro e um modelo de proposta. A cronologia narrativa continua em `docs/andamento.md`; não criar outro diário concorrente. Adicionar auditoria de navegação, identidade, cobertura e disponibilidade, com recibos novos e sem modificar os executores congelados.

Cada novo fator científico deve ser declarado em configuração/protocolo próprios e relacionado ao estudo anterior. Proposta, autorização, execução e auditoria são estados diferentes. Buscas futuras exigem orçamento e regra de seleção, conservando todos os candidatos. Ciclos com alvos diferentes não entram no mesmo ranking.

Preservar bytes científicos no Git e em pacotes, sem conversão automática de finais de linha. Manter snapshots de documentos associados a recibos antes de revisá-los. A alternativa de reorganizar fisicamente pastas antigas foi rejeitada porque quebraria referências e hashes; a de depender apenas do chat não oferece consulta suficiente para a redação.

## Consequências e limites

O catálogo não substitui artefatos, backup, pré-registro ou aprovação do orientador. Um clone incompleto deve mostrar quais evidências faltam. Um arquivo ignorado e um arquivo não rastreado exigem ações diferentes para preservação. Nenhum commit, push, Release, novo dataset ou treinamento é realizado por criar o índice. A distribuição externa segue a ADR 0003.

## Evidências

- [Procedimento de registro](../registro_de_experimentos.md) e [modelo de proposta](../modelos/proposta_experimento.md).
- [Catálogo](../../registros/catalogo_estudos.json) e [mapa de registros](../../registros/README.md).
- [Snapshot documental anterior](../../registros/revisoes/organizacao_2026-10-27T223818/inicio.json).
- [Andamento](../andamento.md), onde será registrado o resultado da auditoria desta organização.
