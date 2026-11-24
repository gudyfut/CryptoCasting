# 0005 — Propor pré-normalização como próxima alteração isolada

- Data da proposta e registro: 27/10/2026, São Paulo (28/10 UTC).
- Situação: **proposta, não implementada e não executada**.
- Autorização e evidência: o pesquisador pediu pesquisar o Mamba usado, suas configurações e o CryptoMamba para decidir a próxima alteração. A pesquisa foi realizada; o pedido não fixa a adoção desta variante nem autoriza automaticamente uma nova grade.
- Ciclo afetado: futuro ciclo próprio; referência de comparação `7868a4d847c1410fc681`, mantendo `1e7c5ed662fba55ddd25` preservado.

## Contexto

Os resultados das duas execuções, DB1–DB4 e B1–B4, já eram conhecidos. A correção da penalização não resolveu a desvantagem do Mamba. A revisão de frequência mostrou que reavaliar as previsões existentes diariamente também não a resolveu; não houve treinamento diário. A configuração atual usa Mamba-1 oficial com pós-LayerNorm no wrapper local.

A [pesquisa técnica](../revisao_mamba_criptomamba.md) verificou identidade da fonte instalada e examinou artigo v2 e código dos autores do CryptoMamba. O bloco oficial e o CMBlock usam normalização antes do mixer. O CryptoMamba muda simultaneamente entradas, alvo, eixos, profundidade e treinamento; sua adoção integral não permitiria atribuir um efeito a um único fator.

## Proposta e alternativas

Priorizar o contraste `LN(x + Mamba(x))` → `x + Mamba(LN(x))`, mantendo todos os outros componentes e a penalização corrigida. O caminho residual e a posição da normalização formam um único fator arquitetural; não alterar RMSNorm, inicialização, dropout, learning rate, dados ou frequência junto.

Alternativas adiadas: treino com origens diárias, maior estado/largura, scheduler, novas entradas e reprodução integral do CryptoMamba. A prioridade decorre da especificidade e proximidade ao empilhamento das referências, não de evidência de ganho de mercado. Pós-normalização não foi classificada como bug.

## Consequências e limites

Se adotado, elaborar novo protocolo/configuração/identidade, com qualificação e controles da variante corrigida. Proposta de grade comparável: 384 novos ajustes Mamba, 192 por fase, três seeds; duas reproduções de controle curto/longo especificadas antes da execução. Referências inalteradas são herdadas, não novos treinamentos. Não ajustar parâmetros entre fases em função do placar. Preservar fracassos, hipóteses rejeitadas e todas as tentativas.

Contraste primário pré versus pós-normalização com penalização corrigida; LSTM/Naive são comparações secundárias relevantes. MSE pareado com intervalos temporais, variação entre seeds e operação Spot separada. Um ganho retroativo não representa confirmação em holdout desconhecido. A escolha desta hipótese depois dos resultados deve aparecer no TCC.

## Evidências e verificação

Consultar o relatório vinculado e seus recibos. Não existe ainda ID de execução da variante proposta, fonte executável nova, qualificação dessa variante, treino ou resultado. O detalhamento executável e a adoção pelo pesquisador devem anteceder a grade. A cronologia factual permanece em [andamento](../andamento.md).
