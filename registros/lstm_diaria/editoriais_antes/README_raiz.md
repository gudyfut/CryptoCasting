# CryptoCasting

**Artigo v2 para revisão — 13/11/2026:** [PDF](escrita_tcc/artigo.pdf), [LaTeX e compilação](escrita_tcc/README.md) e [matriz de evidências](escrita_tcc/cronologia_narrativa/planejamento_artigo.md). Título original restaurado: **Previsibilidade de Criptomoedas com a Arquitetura Mamba: um Sistema de Forecasting Temporal**. A narrativa reúne exploração de entradas/configurações/alvos, sistema diário consolidado, resultados nas quatro moedas e diagnóstico dos ramos. Fundamentação original recuperada e adaptada; cinco seções, quatro figuras e três tabelas. Revisão de leitura e figuras concluída: 12 páginas de artigo/referências, 17 no PDF completo. A versão anterior e seus fontes ficam no histórico editorial. Texto e dados administrativos aguardam revisão acadêmica. Nenhum novo experimento foi iniciado nesta etapa editorial.

**Extensão A/L em 2026 concluída em 13/11:** 24 redes reaproveitadas, 132 carteiras e controles conferidos, sem novos treinos. Erros próximos e resultados operacionais mistos; nenhuma superioridade uniforme demonstrada. [Explicação e resultados](docs/resultados_ablacao_linear_diaria.md#extensão-retrospectiva-al-em-2026) · [Auditoria](registros/ablacao_linear_2026/conferencia_posterior.json). Recorte já consultado, retrospectivo; referência preservada.

**Fechamento experimental concluído em 13/11 às 02h40 BRT:** fatorial BTC e ablação A/L nas quatro moedas, 12 ajustes científicos novos, oito controles exatos e 288 carteiras. Auditoria independente e cinco figuras conferidas. Contribuição dos ramos ausente ou extremamente pequena em A; a ablação não demonstrou vantagem preditiva ou operacional uniforme. Evidências incorporadas à versão editorial para revisão. [Resultados e limites](docs/resultados_ablacao_linear_diaria.md#fechamento-fatorial-e-replicação-entre-ativos) · [Conferência](registros/fechamento_ramos_diarios/conferencia_posterior.json) · [Estado](registros/fechamento_ramos_diarios/estado.json).

Repositório de pesquisa e produção do TCC sobre previsão com Mamba e dados de criptomoedas. O objetivo é investigar entradas, pesos, hiperparâmetros, estruturas e tipos de previsão, registrando conclusões fundamentadas para o artigo. Resultados negativos ou inconclusivos também contribuem; um modelo lucrativo não é condição para concluir o trabalho. As [diretrizes de pesquisa](docs/diretrizes_pesquisa.md) definem os princípios e o [guia base](AGENTS.md) indica as instruções por tarefa.

O acervo reúne dados, treinamento, validação, teste, análises, simulações e materiais de escrita. LSTM, Naive e ARIMA são referências da trajetória; a utilidade operacional é uma das dimensões investigadas.

## Situação atual

**Concluída em 12/11 às 19h50 BRT: ablação linear contra A.** Três ajustes científicos e dois controles exatos de200épocas,60carteiras completas. L usa824parâmetros contra136.952; MSE médio0,095%menor e ensemble+17,01% contra+12,83% em2025, sem superioridade estatística estabelecida. [Resultado e limites](docs/resultados_ablacao_linear_diaria.md), [fechamento](registros/ablacao_linear_diaria/fechamento.json) e [conferência posterior](registros/ablacao_linear_diaria/conferencia_posterior.json). Escopo cumprido, referências preservadas, sem2026 ou nova busca.

**Concluído em 12/11 às13h48BRT: penalização seletiva contra A.** Execução `26cea089ba0faa9d64dc`, três ajustes científicos novos e dois controles exatos de200épocas;60carteiras completas, sem falhas prudenciais. MSE médio deS piorou0,43%; ensemble melhorou0,21% sem superioridade demonstrada e não operou em2025 por sinais dentro do filtro. [Resultados e limites](docs/resultados_penalizacao_seletiva_diaria.md), [fechamento](registros/penalizacao_seletiva_diaria/fechamento.json), [conferência posterior](registros/penalizacao_seletiva_diaria/conferencia_posterior.json). ReferênciaA preservada;2026excluído; ciclo encerrado; a ablação linear tem autorização própria.

**Concluído em12/11: fatorial temporal do CryptoMamba.** BTC,200épocas,três seeds por receita; seis ajustes novos, dois controles exatos e seis referências herdadas.108carteiras auditadas. A adaptação temporal não demonstrou superar a referênciaA; atividade dos ramosSSM não garantiu melhor previsão/lucro. [Resultados e limites](docs/resultados_eixo_temporal_diario.md), [fechamento](registros/eixo_temporal_diario/fechamento.json), [conferência](registros/eixo_temporal_diario/conferencia_posterior.json).2026não participou deste contraste.

Avaliação posterior encerrada em11/11: **ensemble nas quatro moedas em2026**, de01/01 a10/11, sem novos treinos. Mesmos12checkpoints, escalas e regras;24carteiras e controles exatos conferidos. [Resultados e interpretação](docs/andamento.md#11112026--ensemble-preservado-avaliação-temporal-em-2026), [exposição e fechamento](registros/ensemble_2026/fechamento.json).2026 passa a ser conhecido para hipóteses posteriores.

Próximos passos e prioridades no [plano](plano.md). A [generalização diária para ETH, BNB e XRP](docs/protocolo_generalizacao_moedas.md) concluiu os modelos independentes, com BTC herdado; depois vieram continuidade operacional e avaliação do ensemble em2026. [Comparação original das quatro moedas](registros/generalizacao_moedas/comparacao_quatro_moedas.json), [cronologia](docs/andamento.md) e [índice dos modelos usados no ensemble](registros/ensemble_2026/modelos_utilizados.json). A [exploração com IA](docs/exploracao_ia.md) conserva seu contexto histórico.

A apresentação financeira usa slippage **provisório de 0,01% por lado**, mantendo taxas e funding, conforme a [configuração](configuracoes/custos_vigentes_001.json) e a [reavaliação sem treino](registros/custos_vigentes/execucao.json). As fontes científicas originais continuam preservadas; esse cenário não certifica custo real histórico.

Marco operacional de11/11: [continuidade das posições diárias](docs/adr/0037-continuidade-posicoes-diarias.md),408carteiras concluídas nas quatro moedas, sem retreino neural. Reduzir fechamento/reabertura desnecessários melhora o backtest; só ETH tem lucro médio em2025 e o risco permanece elevado. [Comparação e limites](docs/andamento.md#11112026--marco-operacional-continuidade-das-posições-diárias), [artefatos e conferências](registros/continuidade_moedas/fechamento.json). É uma extensão separada; a interface anterior mantém sua política identificada.

| Para quê | Onde começar |
|---|---|
| Entender a exploração posterior à interface | [Síntese única](docs/exploracao_ia.md) |
| Ver o próximo passo | [Plano](plano.md) |
| Consultar documentação e metodologia | [Índice documental](docs/README.md) |
| Localizar uma execução/evidência | [Catálogo](registros/catalogo_estudos.json), [mapa dos registros](registros/README.md) |
| Retomar o ensemble e seus checkpoints | [Características da receita](docs/arquitetura_modelos.md), [índice dos12modelos](registros/ensemble_2026/modelos_utilizados.json), [passagem de contexto](plano.md) |
| Acompanhar a trajetória até a generalização diária | [Panorama web](dataview/README.md) |
| Trabalhar no repositório | [Guia base](AGENTS.md), [ambiente e comandos](docs/ambiente_e_execucao.md) |
| Preparar a escrita e receber o projeto LaTeX | [Espaço de escrita do TCC](escrita_tcc/README.md) |

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `codigo/` | Coleta, entradas, modelos, treinamento, avaliação, simulação, experimentos, análises e manutenção |
| `testes/` | Suítes por camada e ciclo, com descoberta única |
| `dataview/` | Interface web da trajetória e dos custos vigentes |
| `configuracoes/` | Receitas identificadas |
| `dados/` | Mercado, modelos, previsões e publicações preservadas |
| `registros/` | Catálogo, ponteiros, controles, conferências e incidentes |
| `docs/` | Guias, arquitetura, protocolos e decisões |
| `escrita_tcc/` | Redação e projeto LaTeX |
| `arquivo/` | Fontes históricas e materiais preservados |

## Trabalhar no projeto

Usar o ambiente Python existente. Na raiz:

```sh
python -m pip install --no-deps --no-build-isolation -e .
python -B -m comandos.dados --help
python -B -m comandos.modelos --help
python -B -m unittest discover -s testes -t . -v
python -B -m manutencao.arquivo_fontes conferir
python -B -m manutencao.auditar_repositorio --integridade --exigir-completo
```

No Windows, o Python local está em `.venv/Scripts/python.exe`. Testes neurais e locks Linux exigem o ambiente WSL/CUDA; skips não significam aprovação. A instalação editável registra os pacotes de `codigo/`, mantendo os namespaces Python. Treinamentos continuam sujeitos ao protocolo e à autorização da rodada.

Executar `npm run dev` dentro de `dataview/`. A interface apresenta a trajetória até a generalização das quatro moedas e usa a releitura financeira conferida de custos vigentes.

Consultar o [mapa dos dados](dados/README.md), os [leitores posteriores](codigo/analises/README.md) e as [ferramentas de manutenção](codigo/manutencao/README.md). Fontes históricas estão nos pacotes verificados de `arquivo/`; os caminhos antigos nos protocolos representam o layout científico original. A recuperação é explícita e não inicia executores.

Dados volumosos e checkpoints locais não são baixados automaticamente pelo Git. Consultar a [política de preservação](docs/armazenamento_e_reproducao.md) antes de transferir de máquina. Organização local não equivale a backup externo.
