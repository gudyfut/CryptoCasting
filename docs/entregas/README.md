# Entregas do desenvolvimento

Esta pasta organiza os documentos produzidos ao longo do cronograma do TCC 2. A numeração segue a ordem do cronograma acadêmico em [Cronograma_Atividades_TCC2_Murilo_Monferrari.pdf](../Cronograma_Atividades_TCC2_Murilo_Monferrari.pdf).

O [protocolo experimental](../protocolo_experimental.md) continua sendo a referência metodológica. Os documentos desta pasta registram planejamento, implementação, evidências e decisões de cada etapa, sem substituir ou alterar silenciosamente o protocolo.

| Entrega | Período | Atividade | Resultado previsto | Pasta |
|---:|---|---|---|---|
| 1 | 08/09–13/09 | Definição do protocolo experimental | Desenho experimental fechado | [`01_protocolo_experimental`](01_protocolo_experimental/) |
| 2 | 14/09–20/09 | Construção do pipeline de coleta | Dataset bruto reproduzível e script de coleta funcional | [`02_pipeline_coleta`](02_pipeline_coleta/) |
| 3 | 21/09–27/09 | Pré-processamento e construção das amostras | Pipeline de transformação dos dados em amostras | [`03_pre_processamento_amostras`](03_pre_processamento_amostras/) |
| 4 | 28/09–04/10 | Infraestrutura experimental e baselines | Primeiros resultados de B0–B3 nas combinações principais | [`04_infraestrutura_baselines`](04_infraestrutura_baselines/) |
| 5 | 05/10–11/10 | Implementação do Mamba base | Treinamento e previsão de ponta a ponta | [`05_mamba_base`](05_mamba_base/) |
| 6 | 12/10–18/10 | Experimento 1: resolução e contexto | Tabelas e gráficos de granularidade e janela histórica | [`06_experimento_1_resolucao_contexto`](06_experimento_1_resolucao_contexto/) |
| 7 | 19/10–25/10 | Experimento 2: representação das entradas | Análise de OHLCV e indicadores causais | [`07_experimento_2_representacao_entradas`](07_experimento_2_representacao_entradas/) |
| 8 | 26/10–01/11 | Experimento 3: normalização e Mamba | Configuração principal selecionada e documentada | [`08_experimento_3_normalizacao_mamba`](08_experimento_3_normalizacao_mamba/) |
| 9 | 02/11–08/11 | Avaliação de robustez | Resultados consolidados com múltiplas seeds | [`09_avaliacao_robustez`](09_avaliacao_robustez/) |
| 10 | 09/11–15/11 | Análise científica | Resultados finais e interpretação das evidências | [`10_analise_cientifica`](10_analise_cientifica/) |
| 11 | 16/11–22/11 | Escrita e finalização | Versão praticamente final do TCC 2 | [`11_escrita_finalizacao`](11_escrita_finalizacao/) |
| 12 | 23/11 | Fechamento | Trabalho consolidado para apresentação e submissão | [`12_fechamento`](12_fechamento/) |

## Convenção de uso

- Guardar em cada pasta somente materiais da respectiva entrega.
- Registrar decisões, critérios de aceite, verificações realizadas e limitações conhecidas.
- Não apresentar resultados parciais, simulados ou exploratórios como evidência científica final.
- Quando uma decisão alterar o protocolo, documentar a justificativa e a data antes de consultar os resultados finais.
- Evitar versionar datasets, checkpoints ou outros binários grandes dentro de `docs/entregas/`.

