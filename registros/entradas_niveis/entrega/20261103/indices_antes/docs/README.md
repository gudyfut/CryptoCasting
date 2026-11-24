# Documentação do CryptoCasting

## Comece aqui

1. [TCC1](TCC_1_MuriloRFM.pdf): objetivo e fundamentação originais; PDF preservado.
2. [Desenho OHLCV](desenho_ohlcv24.md): método de dados, alvo e referência; as preparações históricas não substituem os estados das rodadas executadas.
3. [Plano](../plano.md), [cronologia única](andamento.md) e [catálogo](../registros/catalogo_estudos.json).
4. [Roteiro de redação](roteiro_redacao_tcc.md): como transformar decisões e evidências no artigo.

## Rodada atual

**Comparação de entradas autorizada, em fila após Huber:** A/relativa atual, B/OHLCV cru e C/níveis padronizados, quatro blocos e oito seeds.32referências A herdadas e64ajustes novos+2controles reais. [Protocolo](protocolo_entradas_niveis.md), [ADR0020](adr/0020-comparacao-entradas-niveis.md), [estado da fila/execução](../registros/entradas_niveis/estado.json). Entrada `python -m experimentos.entradas_niveis`; a fila exige fechamento conferido da predecessora e qualificação CUDA antes de mercado. Sem nova hipótese de volume relativo ou indicadores.

**Mamba16 MSE versus Huber em quatro blocos e oito seeds**,64ajustes principais+2controles reais autorizados: [protocolo](protocolo_huber_blocos.md), [ADR0019](adr/0019-huber-blocos-oito-seeds.md), [estado verificável](../registros/huber_blocos/estado.json). Entrada `python -m experimentos.huber_blocos`; sem editar fontes anteriores. A avaliação é retrospectiva e começa com novos scalers/pesos em cada bloco. Preparação não comprova treinamento real. O [estudo anterior de seis seeds](resultados_perda_huber.md) continua encerrado e preservado.

O [diagnóstico das previsões existentes](diagnostico_previsoes.md) acrescenta distribuição dos erros, associação com retornos e faixas fixadas na validação, sem novos ajustes. Correlação e lucro são avaliações distintas de MSE.

## Arquitetura e manutenção

| Etapa | Documento | Evidências |
|---|---|---|
| Mercado e entradas | [Arquitetura dos dados](arquitetura_dados.md) | [Estado](../registros/dados/estado.json) |
| Consumo pelos modelos | [Arquitetura dos modelos](arquitetura_modelos.md) | [Estado](../registros/modelos/estado.json) |
| Treino, seleção e checkpoints | [Arquitetura de treinamento](arquitetura_treinamento.md) | [Referência executada](../registros/treinamento/estado.json) |
| Novas hipóteses | [Registro de experimentos](registro_de_experimentos.md) | [Mapa de registros](../registros/README.md) |
| Decisões e transporte | [ADRs](adr/README.md), [preservação](armazenamento_e_reproducao.md) | Catálogo e recibos por ciclo |

Novas hipóteses ficam em `experimentos/`; diagnósticos reutilizáveis em `analises/`. As camadas científicas antigas e pacotes `experimento_*/` permanecem congelados nos caminhos originais. Refinamentos do desenho não exigem recoleta automática de mercado.

## Estudos encerrados

| Estudo | Protocolo | Resultado |
|---|---|---|
| Referência modular OHLCV | [Desenho](desenho_ohlcv24.md) | [Estado/publicação](../registros/treinamento/estado.json) |
| Estado16→8 | [Método](protocolo_estado_mamba.md) | [Relatório](resultados_estado_mamba.md) |
| Estados32/64 e complemento16 | [32/64](protocolo_estados32_64.md), [complemento](protocolo_complemento_estado16.md) | [Quatro estados/seis seeds](resultados_estados32_64.md) |
| Taxa constante menor | [Método](protocolo_taxa_aprendizado.md) | [Relatório](resultados_taxa_aprendizado.md) |
| Taxa dinâmica Mamba16 | [Método](protocolo_taxa_dinamica.md) | [Relatório e conferência posterior](resultados_taxa_dinamica.md) |
| Perda Huber Mamba16 | [Método](protocolo_perda_huber.md) | [Relatório e conferência posterior](resultados_perda_huber.md) |
| Carteira retida | [Método](protocolo_backtest_carteira.md) | [Relatório](resultados_backtest_carteira.md) |
| CryptoMamba adaptado | [Método](protocolo_cryptomamba_adaptado.md) | [Relatório](resultados_cryptomamba_adaptado.md) |
| Adam→AdamW nessa adaptação | [Método](protocolo_otimizador_cryptomamba.md) | [Relatório](resultados_otimizador_cryptomamba.md) |

A linha CryptoMamba foi encerrada após a solicitação de voltar ao Mamba temporal; seus resultados não são apagados ou confundidos com o Mamba16. A preparação `92e3eb82e3f6adf99994` em `estudo_ohlcv/` permanece sem treino; a referência modular e as extensões possuem identidades próprias, já executadas.

## Histórico e disciplina documental

[Estudos preliminares até28/10](../arquivo/estudos_preliminares_2026-10-28/README.md) ligam a fase de retornos escalares, penalização, pré-normalização e barreiras. Os protocolos congelados `protocolo_experimental.md`, `protocolo_penalizacao_mamba.md` e `protocolo_normalizacao_mamba.md` permanecem aqui por integridade; não definem automaticamente o próximo ciclo. O [cronograma acadêmico](../arquivo/estudo_barreiras_2026-10-20/projeto/docs/Cronograma_Atividades_TCC2_Murilo_Monferrari.pdf) não comprova aceite do orientador.

Não produzir explicações avulsas a cada conversa. Método no desenho/protocolo; decisões nas ADRs; fatos em `andamento.md`; evidências técnicas em `registros/`; resultados por tentativa. Preservar versões editoriais vinculadas aos fechamentos antes de consolidá-las. Não mover artefatos congelados para reduzir contagem de pastas. O portal existente ainda pertence ao estudo preliminar.
