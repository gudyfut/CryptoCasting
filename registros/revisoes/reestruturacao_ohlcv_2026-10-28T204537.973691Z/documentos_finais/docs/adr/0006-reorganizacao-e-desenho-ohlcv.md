# 0006 — Realinhar o projeto ao TCC1 e organizar a fase OHLCV

- Data da decisão e registro:28/10/2026.
- Situação: reorganização e direção OHLCV adotadas por solicitação do pesquisador; detalhes do novo desenho propostos; sem novo treinamento ou aceite acadêmico presumido.
- Evidência: mensagens neste chat solicitando reestruturação, preservação dos estudos, consulta do PDF e redução da proliferação documental. Caminho do TCC1 fornecido pelo pesquisador; [identificação da fonte](../../registros/revisoes/reestruturacao_ohlcv_2026-10-28T204537.973691Z/fonte_tcc1.json).
- Ciclos afetados: os três ciclos de retorno24 passam a integrar a fase preliminar de navegação; identidades e fatos históricos permanecem iguais. Não substitui seus protocolos retroativamente.

## Contexto

O plano operacional priorizava efeito de contexto em quatro moedas e comparação Mamba–LSTM. O TCC1, especialmente resumo/introdução e seção 2.7, propõe investigação iterativa de decisões do próprio Mamba, entradas OHLCV/indicadores e avaliação walk-forward, sem ranking arquitetural como finalidade. Os ciclos de retorno24 alimentaram as redes somente com retornos do fechamento. O recebimento posterior do PDF permitiu verificar essa diferença; a pesquisa anterior havia consultado o plano do repositório, não o PDF agora fornecido.

Não há fundamento para invalidar toda a fase anterior: ela mediu o que seus contratos declararam e possui auditorias. Seu alcance é mais restrito que o desenho OHLCV requerido agora. Adicionar volume não garante melhorar resultados. Pré-LayerNorm e normalização adaptativa das entradas são eixos diferentes.

## Decisão

1. Manter artefatos/fontes/recibos intactos; criar [bloco preliminar](../../arquivo/estudos_preliminares_2026-10-28/README.md) com índice e snapshot documental anterior.
2. Tornar [desenho OHLCV](../desenho_ohlcv24.md) a única proposta de trabalho: Mamba central, OHLCV inicial explícito, referências auxiliares, critérios preditivos e operacionais separados.
3. Recomendar BTC/contexto168h/horizonte 24h/três seeds, exploração curta e posterior avaliação walk-forward de poucas configurações. Datas e orçamento estão propostos no documento; não iniciar automaticamente.
4. Corrigir AGENTS/plano/README para distinguir histórico de próxima etapa e consultar o PDF acadêmico.
5. Concentrar navegação em `docs/README.md`. Perguntas conceituais não geram documentos automaticamente; atualizar arquivos existentes, criar ADR apenas para decisão material.

## Consequências e limites

O PDF permanece inalterado. Delimitar BTC/horizonte e a amplitude das variações precisa aparecer na seção 3 e ser alinhado academicamente. “Teto de previsibilidade” não será interpretado como limite fundamental demonstrável por uma busca finita. LSTM permanece auxiliar, sem obrigação de superá-la. Qualificação e configuração executável do novo estudo ainda não existem.

A divisão única é exploração, não walk-forward. Reestimações em blocos ocorrerão apenas na avaliação ampliada definida antes de executar. Períodos2023–2025 conhecidos não voltam a ser holdout; o PDF mostra preços até junho/2026, então independência de 2026 também não deve ser presumida.

Não foi feito upload, commit, exclusão de histórico ou novo treinamento. A integridade local não equivale a backup externo. A revisão desta mudança concentra recibos em `registros/revisoes/reestruturacao_ohlcv_2026-10-28T204537.973691Z/`.
