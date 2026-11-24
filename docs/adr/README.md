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
| [0020](0020-comparacao-entradas-niveis.md) | Comparar entrada relativa, OHLCV cru e níveis padronizados | Concluída/conferida;32referências herdadas e64novos+2controles, consultar resultados |

## Como registrar

- Usar numeração crescente e o [modelo](modelo.md). Registrar a data da decisão e a data em que o documento foi escrito.
- As ADRs 0001 e 0002 foram reconstruídas em 27/10 a partir de documentos existentes. Não foram escritas antes dos experimentos e não constituem novos pré-registros.
- Uma proposta não altera o protocolo vigente. Identificar quem autorizou e apontar a evidência disponível, sem inventar aprovação do orientador.
- Para substituir uma decisão, criar nova ADR e relacionar as duas; conservar motivos e escopo históricos. Resultados conhecidos não podem ser apresentados como desconhecidos no passado.
- Guardar contagens/progresso em registros de execução e `docs/andamento.md`. Não abrir ADR para cada época, ajuste ou retomada operacional; incidentes ficam em `registros/incidentes/`.
- Não mover ou editar evidências congeladas para reorganizar a documentação. Criar índices e links.

O [registro narrativo anterior](../../arquivo/estudos_preliminares_2026-10-28/documentacao/decisoes.md) permanece preservado como fonte histórica.

- [0021 — Combinação crua/Huber](0021-crua-huber-complemento-fatorial.md):complemento fatorial autorizado,32principais+1controle,96herdados;interação e contrastes predefinidos.

- [0022 — Busca adaptativa assistida por Astra](0022-busca-adaptativa-astra.md):exploracao autorizada com orcamento, avaliador fixo, desenvolvimento separado e referencia compativel.

- [0023 — Comparação Astra versus crua/Huber](0023-comparacao-astra-crua.md):mesmo executor e população;32Astra herdados,32crus novos e dois controles;sem busca adicional.

- [0024 — Simulação modular de futuros](0024-simulacao-futuros.md):804carteiras posteriores,zero treinamento,compra/venda com funding e preservação do Spot.

- [0025 — Smart comum Spot/futuros](0025-smart-spot-futuros.md):posições retidas,controle de funding,custos iguais e filtro fixo;1.632carteiras sem treino.

- [0026 — Revisão de execução operacional](0026-revisao-execucao-operacional.md): comissão recebida, reduceOnly, margem e políticas de saída explícitas; 1.200 carteiras, sem treino.

- [0027 — Busca Astra002 T/V/S](0027-busca-astra-treino-parada-comparacao.md): autorização delimitada, duas âncoras, critérios fixos e orçamento de um dia.

- [0028 — Pesquisa operacional em futuros](0028-pesquisa-operacional-futuros.md): linha separada de modelo + política; Calmar/crescimento/risco, proposta sem execução, preservação dos ciclos anteriores.

- [0029 — Diagnóstico operacional](0029-diagnostico-operacional.md): leitura separada das previsões, direção/intensidade/regimes e operações, sem treino ou novas carteiras.

- [0030 — Histórico acumulado versus12meses](0030-historico-acumulado-movel.md): primeiro contraste autorizado;18principais+2controles,456carteiras;preservação de C06/calendário e zero busca adicional.

- [0031 — CryptoMamba diário e futuros24h](0031-cryptomamba-diario-futuros.md): cópia da receita pública adaptada à Binance,4:1:1,3seeds+1controle,70carteiras;sem busca.

- [0032 — Reprodução numérica do CryptoMamba](0032-reproducao-numerica-cryptomamba.md): reinício técnico com scan oficial de referência em CUDA, receita/tolerâncias mantidas e tentativa reprovada preservada.

- [0033 — Alvo de retorno diário](0033-alvo-retorno-diario.md): comparação pareada com preço; entradas, receita e política fixas, três seeds e controle.

- [ADR0034 — Padronização dos seis canais diários](0034-padronizacao-diaria.md).

- [0035 — Adam sem penalização no desenho diário](0035-sem-penalizacao-diaria.md): coeficiente zero, mesma referência padronizada, controle e observação não interventiva.

- [0036 — Generalização para ETH, BNB e XRP](0036-generalizacao-tres-moedas.md): receita diária padronizada confirmada pelo pesquisador, modelos independentes e dados por instrumento.

- [0037 — Continuidade das posições diárias](0037-continuidade-posicoes-diarias.md): marco da redução de giro, correção de mínimo nocional por ordem e ampliação operacional para quatro moedas com referências justas.
