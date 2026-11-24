# 0005 — Pré-normalização como próxima alteração isolada

- Data da proposta e registro: 27/10/2026, São Paulo (28/10 UTC).
- Situação: **adotada, executada e conferida em 28/10/2026**; resultado e limites no relatório vinculado abaixo.
- Autorização e evidência: após a pesquisa, o pesquisador autorizou implementar a recomendação e treinar/testar apenas Mamba. Mensagem preservada em `registros/normalizacao/autorizacao.json`. A proposta de 27/10 está preservada no snapshot da pesquisa anterior.
- Ciclo afetado: `9e03af2150cbb7b1068d`; referência de comparação `7868a4d847c1410fc681`, mantendo `1e7c5ed662fba55ddd25` preservado.

## Contexto

Os resultados das duas execuções, DB1–DB4 e B1–B4, já eram conhecidos. A correção da penalização não resolveu a desvantagem do Mamba. A revisão de frequência mostrou que reavaliar as previsões existentes diariamente também não a resolveu; não houve treinamento diário. A configuração atual usa Mamba-1 oficial com pós-LayerNorm no wrapper local.

A [pesquisa técnica](../revisao_mamba_criptomamba.md) verificou identidade da fonte instalada e examinou artigo v2 e código dos autores do CryptoMamba. O bloco oficial e o CMBlock usam normalização antes do mixer. O CryptoMamba muda simultaneamente entradas, alvo, eixos, profundidade e treinamento; sua adoção integral não permitiria atribuir um efeito a um único fator.

## Proposta e alternativas

Priorizar o contraste `LN(x + Mamba(x))` → `x + Mamba(LN(x))`, mantendo todos os outros componentes e a penalização corrigida. O caminho residual e a posição da normalização formam um único fator arquitetural; não alterar RMSNorm, inicialização, dropout, learning rate, dados ou frequência junto.

Alternativas adiadas: treino com origens diárias, maior estado/largura, scheduler, novas entradas e reprodução integral do CryptoMamba. A prioridade decorre da especificidade e proximidade ao empilhamento das referências, não de evidência de ganho de mercado. Pós-normalização não foi classificada como bug.

## Consequências e limites

A proposta original previa novo protocolo/configuração/identidade, com qualificação e controles da variante corrigida. A grade autorizada e executada manteve 384 novos ajustes Mamba, 192 por fase, três seeds e duas reproduções de controle curto/longo especificadas antes da execução. Referências inalteradas são herdadas, não novos treinamentos. Não ajustar parâmetros entre fases em função do placar. Preservar fracassos, hipóteses rejeitadas e todas as tentativas.

Contraste primário pré versus pós-normalização com penalização corrigida; LSTM/Naive são comparações secundárias relevantes. MSE pareado com intervalos temporais, variação entre seeds e operação Spot separada. Um ganho retroativo não representa confirmação em holdout desconhecido. A escolha desta hipótese depois dos resultados deve aparecer no TCC.

## Evidências e verificação

Consultar o [protocolo autorizado](../protocolo_normalizacao_mamba.md), configuração e `registros/normalizacao/`. O ID foi atribuído após qualificação/congelamento; a conclusão é sustentada pelos artefatos, não apenas pela autorização. A cronologia factual permanece em [andamento](../andamento.md). A verificação de 28/10 confirmou que a penalização corrigida não reproduz o Adam uniforme do CryptoMamba; manter AdamW e isenções evita mudar dois fatores neste ciclo.

O [relatório final](../resultados_normalizacao_mamba.md) e o [fechamento](../../registros/auditorias/9e03af2150cbb7b1068d/fechamento_normalizacao.json) registram o efeito: redução numérica de 0,8051% no MSE retrospectivo, com intervalo incluindo zero; sem superioridade demonstrada sobre LSTM/Naive e sem melhoria na mediana Spot. A ablação está concluída, sem autorização implícita para novas buscas. Versões anteriores desta decisão estão preservadas nos snapshots das revisões.
