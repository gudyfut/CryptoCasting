# Dados, modelos e resultados

| Material | Localização |
|---|---|
| Brutos e proveniência de mercado | `brutos/`, `coletas_binance/`, `mercado/` |
| Matrizes de entrada, divisões e escalas | `processados/`, `entradas/` e as pastas identificadas no congelamento de cada ciclo |
| Ajustes, checkpoints, previsões e publicações | `experimentos/<ciclo_identidade>/` |
| Diagnósticos posteriores | `diagnosticos/` |
| Reavaliações identificadas e avaliação temporal do ensemble | `reavaliacoes/<identidade>/`: previsões, carteiras, resultados, manifestos e publicações posteriores |
| Exportações consumidas pela interface | `portal/`, `portal_panorama/` |

O [catálogo](../registros/catalogo_estudos.json) e o [mapa dos registros](../registros/README.md) apontam a execução correta. Os layouts históricos variam: não há um único nome de subpasta de checkpoints válido para todos os ciclos.

Cada identidade conserva dados preparados, modelos, seeds, controles, tentativas e publicações no seu próprio escopo. Na generalização, a execução separa `ETHUSDT/`, `BNBUSDT/` e `XRPUSDT/`. Modelos e carteiras de moedas diferentes não devem ser misturados. Na receita diária, distinguir médias das seeds e ensemble.

A avaliação de2026 está em `reavaliacoes/ensemble_2026_14b4a75f21eb63ab04e2/`; mercado correspondente em `mercado/ensemble_2026/14b4a75f21eb63ab04e2/<moeda>/`. O [índice de checkpoints](../registros/ensemble_2026/modelos_utilizados.json) mantém os vínculos aos modelos/scalers antigos, e o [fechamento](../registros/ensemble_2026/fechamento.json) aponta a conferência. A tentativa inicial interrompida conserva sua identidade; não é cache nem modelo alternativo.

As fontes copiadas em `fontes/` são evidências da implementação usada no experimento. Não são módulos ativos duplicados a serem editados ou apagados. Logs, incidentes e checkpoints de resultados desfavoráveis também fazem parte da pesquisa. A limpeza do desenvolvimento preserva esses materiais.
