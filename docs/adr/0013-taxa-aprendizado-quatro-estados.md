# ADR0013 — Reduzir a taxa nos quatro estados em grade delimitada

Data:29/10/2026. Situação: execução autorizada pelo pesquisador, sujeita a qualificação/congelamento. Mensagem: “prossiga dessa forma então [...] pode fazer essa variação para os4estados diferentes,8,16,32,64”. Esta autorização amplia a proposta da ADR0012 de seis para **24novos ajustes**; não autoriza mudar outros fatores ou repetir os24Mambas existentes.

Decisão: testar lr0,0001 contra0,0002 em cada estado, mesmas seis seeds e receita, numa grade cruzada congelada antes do primeiro ajuste.16permanece a referência de trabalho escolhida; as outras arquiteturas entram para examinar dependência do efeito da taxa. Não substituir a referência automaticamente por um ranking de teste/Spot.

O [protocolo](../protocolo_taxa_aprendizado.md) delimita ordem,controles,orçamento,preservação e comparação. São quatro efeitos primários de validação, com ICs95% descritivos e98,75% para Bonferroni dos quatro efeitos. A multiplicidade histórica/seleção de checkpoints e a exposição2024/2025 continuam limitações. Teste e operação são secundários retrospectivos.

Novos pacote/configurações/identidade; código de treinamento/modelos/dados congelados é reutilizado intacto. `registros/taxa_aprendizado/` contém preparo,autorização,estado e pós-conferência; `dados/experimentos/taxa_aprendizado_<id>/` guarda24tentativas novas e publicação53resultados com29heranças explícitas. Os estudos anteriores e a referência16 permanecem em seus caminhos. Consulta de progresso não deve duplicar execução viva. Não confundir autorização com conclusão nem preparação com treino.
