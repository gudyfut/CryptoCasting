# ADR0020 — Comparar entradas atuais, OHLCV cru e níveis padronizados

- Decisão e registro: 03/11/2026.
- Situação: execução autorizada explicitamente pelo pesquisador; fila separada da ADR0019.
- Evidência: após a proposta A/B/C, o pesquisador pediu oito seeds, comparação das médias e início para execução durante a noite. Mensagem literal preservada na autorização do plano.

## Decisão e escopo

Comparar A: receita OHLCV relativa/log e zscore vigente; B: O/H/L/C em USDT e V em BTC sem transformação/padronização; C: os mesmos níveis de B, com zscore por canal ajustado somente no treino. Manter alvo log-retorno24h padronizado pelo treino, Mamba16, AdamW/MSE e demais fatores. Não copiar timestamp, alvo em preço ou arquitetura CryptoMamba. Não incluir a hipótese de volume centralizado, médias ou indicadores discutidos anteriormente.

Mesmos quatro blocos e oito seeds da ADR0019:32referências A/MSE herdadas após fechamento conferido;32B+32C novos e dois controles reais B1/42, total66ajustes novos. Os controles precedem outras seeds e não entram nas médias. Não repetir A nem ampliar busca. A versão Huber não é candidata desta rodada.

O coordenador exclusivo aguarda encerramento/publicação/conferência da rodada Huber; verifica host, boot e PID, interrompe se ela falhar ou encerrar sem fechamento. Preparação CPU não compete com seu treino; qualificação CUDA e novo mercado só após essa barreira. Fontes antigas permanecem intactas.

Três contrastes pareados fixos (B−A,C−A,B−C), teste primário com peso igual entre blocos e oito seeds, bootstrap de seeds/dias14, sensibilidades7/28 e IC98,333% Bonferroni; IC95% descritivo. Oito seeds não garantem certeza.2024/2025 já consultados: retrospectivo. Seleção de checkpoint só por validação; nenhum parâmetro ajustado pelo lucro.

[Protocolo](../protocolo_entradas_niveis.md), `experimentos/entradas_niveis/`, `tests_entradas_niveis/`, `registros/entradas_niveis/`.384simulações novas,216herdadas,600comparáveis; sem novas políticas. Falha preserva tentativas e exige investigação; sem retomada automática ou repetição para obter resultado favorável.
