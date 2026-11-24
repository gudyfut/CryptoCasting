# Estudos preliminares até 28/10/2026

Este bloco organiza o material anterior à referência OHLCV. **Relatórios e diagnósticos editoriais estão em `documentacao/`; os artefatos científicos permanecem em seus caminhos originais.** Checkpoints, previsões, tentativas, fontes e protocolos congelados não foram movidos nem modificados. A limpeza de 28/10 preservou os bytes anteriores dos documentos movidos antes de ajustar seus links; recibos históricos continuam descritivos daquelas versões.

“Preliminar” descreve seu papel na nova etapa do TCC. Não significa que os cálculos foram invalidados. O retorno24 examinou informação de fechamento; seus resultados não demonstram a qualidade de um modelo com todas as entradas OHLCV.

| Estudo | Identidade | Estado e acesso |
|---|---|---|
| Barreiras | `4e232a796fcda0ea34c3` | [Arquivo anterior](../estudo_barreiras_2026-10-20/README.md); alvo e métricas diferentes |
| Retorno24 escalar | `1e7c5ed662fba55ddd25` | 768 ajustes neurais; [desenvolvimento](documentacao/resultados_desenvolvimento.md), [avaliação](documentacao/resultados_avaliacao.md), [fechamento](../../registros/auditorias/1e7c5ed662fba55ddd25/fechamento.json) |
| Penalização corrigida | `7868a4d847c1410fc681` | 384 novos Mamba + 2 controles; [relatório](documentacao/resultados_penalizacao_mamba.md), [fechamento](../../registros/auditorias/7868a4d847c1410fc681/fechamento_extensao.json); interrupções preservadas |
| Pré-normalização | `9e03af2150cbb7b1068d` | 384 novos Mamba + 2 controles; [relatório](documentacao/resultados_normalizacao_mamba.md), [fechamento](../../registros/auditorias/9e03af2150cbb7b1068d/fechamento_normalizacao.json) |

As referências herdadas de LSTM/Naive/ARIMA nas extensões não são novos treinamentos. Controles de reprodução são separados da grade. Não somar candidatos ARIMA, checkpoints, publicações e ajustes como experimentos independentes.

## Onde estão as evidências

- Código original: `previsao24/`, `experimento_penalizacao/`, `experimento_normalizacao/`, na raiz do repositório; fontes congeladas também acompanham cada execução.
- Modelos, previsões e tentativas: `dados/experimentos/retorno24_1e7c5ed662fba55ddd25/`, `dados/experimentos/penalizacao_7868a4d847c1410fc681/` e `dados/experimentos/normalizacao_9e03af2150cbb7b1068d/`.
- Dados: `dados/processados/retorno24_d25f6a93a9900725f51e/` e coleta auditada, nos caminhos existentes.
- Índice técnico completo: [catálogo](../../registros/catalogo_estudos.json). Cronologia única: [andamento](../../docs/andamento.md).
- Diagnósticos posteriores: [frequência](documentacao/diagnostico_frequencia_e_configuracoes.md), [Mamba/CryptoMamba](documentacao/revisao_mamba_criptomamba.md), [fundamentos](documentacao/fundamentos_mamba_e_leitura_critica_criptomamba.md), com recibos em `registros/revisoes/`.
- [Snapshot dos documentos anteriores à reorganização](manifesto_documentos_antes.json):22 arquivos copiados com verificação de bytes em `documentos_antes/`. São versões históricas; os links internos das cópias mantêm sua origem e não servem como nova navegação. Use este índice para navegar.

O ciclo de pré-normalização terminou em 28/10 às 16:38:35 de São Paulo; cobertura384 + 2 e auditoria independente registradas. O MSE retrospectivo caiu 0,8051% frente ao pós-normalizado corrigido, com IC95% incluindo zero; não demonstrou superar LSTM/Naive. Mediana Spot base de −10,48% para −11,03%. Não tratar redução de MSE como ganho operacional.

A nova conferência de catálogo está em [recibo anterior à reorganização](../../registros/revisoes/catalogo_2026-10-28T204312.995454Z/resumo.json). Ela confere arquivos e hashes; não repete treinamento/inferência nem prova backup externo. A revisão desta organização terá seu próprio fechamento em `registros/revisoes/reestruturacao_ohlcv_2026-10-28T204537.973691Z/`.

## Uso futuro

Não reexecutar ciclos concluídos para produzir relatórios. Não editar protocolos/fontes/configurações congelados. Hipóteses novas usam novos ciclos. Não retirar resultados desfavoráveis e não apresentar períodos conhecidos como testes inéditos.

Para continuar o trabalho: [desenho OHLCV](../../docs/desenho_ohlcv24.md). Para localizar todos os documentos: [índice](../../docs/README.md).

Mapa da limpeza e conferência posterior: `registros/revisoes/limpeza_preparacao_ohlcv_2026-10-28T211713.614472Z/`. As cópias `documentos_antes/` são versões históricas vinculadas à organização, não documentação ativa duplicada.
