# Decisões do trabalho (ADRs)

ADRs guardam decisão,motivo,alternativas e consequências. Estado científico real depende dos artefatos: proposta,autorização,qualificação,execução e conferência são etapas distintas. A [cronologia](../andamento.md) e o [catálogo](../../registros/catalogo_estudos.json) ligam essas evidências.

| Registro | Decisão | Situação |
|---|---|---|
| [0001](0001-estudo-retorno-24h.md) | Concentrar o estudo no retorno terminal de 24h | Adotada em 20/10/2026; execução documentada separadamente |
| [0002](0002-penalizacao-mamba.md) | Investigar a correção de weight decay em ciclo separado | Autorizada em 26/10/2026; consultar execução para progresso |
| [0003](0003-preservacao-e-organizacao.md) | Separar orientação, decisões, evidências e distribuição de artefatos | Organização adotada em 27/10/2026; publicação dos pacotes pendente |
| [0004](0004-rastreabilidade-de-ciclos.md) | Relacionar ciclos, conferir registros e padronizar futuras mudanças | Organização adotada em 27/10/2026; não autoriza nova grade |
| [0005](0005-proposta-prenormalizacao-mamba.md) | Testar pré-normalização no Mamba corrigido | Proposta em 27/10; autorizada, executada e conferida em 28/10/2026 |
| [0006](0006-reorganizacao-e-desenho-ohlcv.md) | Realinhar ao TCC1, separar estudos preliminares e concentrar documentação | Reorganização e direção OHLCV adotadas em 28/10; método novo proposto, sem execução |
| [0007](0007-modulos-de-dados.md) | Separar mercado Binance, entradas e execução; revisar módulos antes de treinar | Adotada em 28/10; camada de dados implementada e conferida, sem treino |
| [0008](0008-consumo-de-dados-pelos-modelos.md) | Contratos separados para consumo por Mamba, LSTM, Naive e ARIMA | Adotada em29/10; inferência e contratos conferidos, sem ajuste de parâmetros |
| [0009](0009-treinamento-modular.md) | Integrar treinamento, seleção, checkpoints e avaliação por nova identidade | Preparação/qualificação concluídas; rodada modular autorizada por “ok” em29/10 |
| [0010](0010-estado-interno-mamba.md) | Testar d_state16→8 em seis seeds Mamba, com três pareadas | Rodada delimitada pelo pesquisador em29/10; consultar estado próprio |
| [0011](0011-estados32-64.md) | Rodadas32→64, seis seeds cada, com congelamento prévio e fila sequencial | Autorizadas em29/10; consultar fila e registros próprios |
| [0012](0012-referencia16-e-proxima-hipotese.md) | Encerrar estados8/16/32/64 e adotar16 como referência para próximas ablações | Adotada em29/10; taxa0,0002→0,0001 apenas proposta, sem novo treino |
| [0013](0013-taxa-aprendizado-quatro-estados.md) | Ampliar a redução de taxa aos quatro estados, seis seeds cada | Autorizada em29/10;24ajustes novos, progresso e qualificação em registros próprios |
| [0014](0014-cryptomamba-adaptado.md) | Comparar abordagem CryptoMamba adaptada, seis seeds | Concluída; resultados e limitações no estado próprio |
| [0015](0015-backtest-carteira.md) | Avaliar carteira retida com previsões preservadas | Concluída;369simulações, zero novos treinos |
| [0016](0016-otimizador-cryptomamba.md) | Isolar Adam→AdamW no CryptoMamba adaptado | Concluída; seis ajustes e54carteiras, histórico preservado |
| [0017](0017-taxa-dinamica-mamba16.md) | Mamba16 com taxa dinâmica e namespace comum de experimentos | Concluída/conferida; referência constante mantida |
| [0018](0018-perda-huber-mamba16.md) | Isolar MSE→2×Huber no Mamba16, mantendo seleção por MSE | Concluída/conferida; referência MSE mantida, sem promoção |
| [0019](0019-huber-blocos-oito-seeds.md) | Avaliação temporal MSE/Huber, quatro blocos e oito seeds | Autorizada;64principais+2controles, consultar estado próprio |
| [0020](0020-comparacao-entradas-niveis.md) | Comparar entrada relativa, OHLCV cru e níveis padronizados | Autorizada;32referências herdadas e64novos+2controles, fila após Huber |

## Como registrar

- Usar numeração crescente e o [modelo](modelo.md). Registrar a data da decisão e a data em que o documento foi escrito.
- As ADRs 0001 e 0002 foram reconstruídas em 27/10 a partir de documentos existentes. Não foram escritas antes dos experimentos e não constituem novos pré-registros.
- Uma proposta não altera o protocolo vigente. Identificar quem autorizou e apontar a evidência disponível, sem inventar aprovação do orientador.
- Para substituir uma decisão, criar nova ADR e relacionar as duas; conservar motivos e escopo históricos. Resultados conhecidos não podem ser apresentados como desconhecidos no passado.
- Guardar contagens/progresso em registros de execução e `docs/andamento.md`. Não abrir ADR para cada época, ajuste ou retomada operacional; incidentes ficam em `registros/incidentes/`.
- Não mover ou editar evidências congeladas para reorganizar a documentação. Criar índices e links.

O [registro narrativo anterior](../../arquivo/estudos_preliminares_2026-10-28/documentacao/decisoes.md) permanece preservado como fonte histórica.
