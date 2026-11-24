# ADR0012 — Encerrar a investigação de estados e adotar16 como referência

- Data da decisão e do registro:29/10/2026.
- Situação: referência16 adotada pelo pesquisador; próxima hipótese apenas proposta.
- Autorização: “separar esse resultado das4variações, escolher o16estados [...] me fale o que recomenda”. A solicitação define a referência, mas ainda pede recomendação do próximo fator; não inicia uma configuração nova de mercado.
- Investigação encerrada: estados8/16/32/64, seis seeds comuns, [fechamento verificável](../../registros/investigacoes/estados_internos_001/fechamento.json).

## Contexto

As quatro variantes e todos os resultados de2024/2025 já foram consultados. Estado16 teve o menor MSE médio nas seis seeds na validação e no teste horário; diferenças16/8 e16/32 são inconclusivas nos ICs exploratórios, enquanto16/64 favorece16. Nenhuma variante demonstrou superar Naive ou utilidade operacional consistente. MSE no horário00UTC e retorno Spot não têm o mesmo ranking do MSE em todas as origens. Escolher16 não prova ótimo universal, superioridade operacional ou confirmação independente.

## Decisão e alternativas

Encerrar o ciclo de capacidade e fixar16 para as próximas comparações controladas. A [referência de trabalho](../../registros/referencias/mamba16_ohlcv24_001.json) identifica as seis tentativas:17/42/2026 de R0 e7/123/31415 do complemento, sem escolher seed favorável ou fundir pesos. O bloco de resultados fica separado por índice/catálogo, preservando artefatos em seus caminhos. Não reabrir8/32/64 ou repetir a referência para produzir relatórios.

Estado8 seria alternativa de menor complexidade e menor dispersão;16 foi escolhido como continuidade de R0 e referência de menor erro médio observado. Não há necessidade de demonstrar que16 é ótimo para conduzir uma ablação posterior. Comparações futuras usam os mesmos dados, sementes e receita base explicitamente identificada.

## Próxima hipótese proposta, sem execução

Testar somente a taxa de aprendizado AdamW: **0,0002→0,0001**, com16estados e mesmas seis seeds. Hipótese: uma taxa base menor pode modificar a trajetória de otimização e melhorar o erro de validação/estabilidade sob o mesmo orçamento. Todas as seis curvas16 tiveram seleção nas épocas9–13; depois o erro online de treino caiu e a validação piorou. Isso é compatível com sobreajuste/mudança de distribuição, mas não diagnostica taxa alta nem garante benefício da redução. Treino e validação têm escalas/modos diferentes e não devem ser comparados pelo nível dos números.

Detalhamento e critérios ficam no [desenho único](../desenho_ohlcv24.md#11-referência-adotada-e-próxima-hipótese-proposta), sem protocolo/configuração/identidade de execução fictícia. Orçamento proposto: seis novos ajustes Mamba; referência de seis herdada, sem novo LSTM/Naive/ARIMA ou busca adicional. Qualificação, congelamento e autorização vinculada precedem uma futura execução.

Alternativas adiadas: AdamW→Adam, dropout/penalização, representação/normalização, contexto e indicadores. Não se afirma que taxa menor tenha maior probabilidade de ganho que todas as alternativas; ela é escolhida como contraste simples, interpretável e limitado. Não copiar automaticamente hiperparâmetros do CryptoMamba, que usa outra arquitetura/escala/tarefa. Não alterar a política Spot simultaneamente.

## Consequências e verificação

Preservar fontes, configurações, checkpoints, protocolos e publicações8/16/32/64. A referência escolhida é um índice de resultados existentes, não um novo treinamento ou ensemble. Cronologia em [andamento](../andamento.md), evidências no [catálogo](../../registros/catalogo_estudos.json), versões editoriais anteriores em `registros/revisoes/selecao_estado16_*/documentos_antes/`. Reduzir taxa muda também a trajetória e, em AdamW, a aplicação por passo da penalização; a hipótese mede o efeito total da taxa sob a receita fixa, não um mecanismo isolado da regularização. Não iniciar busca indefinida ou estender épocas depois de consultar resultados.

Referência de implementação do otimizador: [PyTorch2.6.0, AdamW](https://github.com/pytorch/pytorch/blob/v2.6.0/torch/optim/adamw.py), correspondente à família de versão usada. O código local de treino é a fonte da receita efetiva. Essa referência explica o hiperparâmetro; não fornece um valor ótimo para cripto.
