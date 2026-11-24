# CryptoCasting — TCC sobre previsão com Mamba e OHLCV

Investigação controlada de decisões de entrada e configuração do Mamba, com LSTM, Naive e ARIMA como referências. O objetivo é compreender o desempenho preditivo e sua relação com uma política operacional fixa. Uma conclusão negativa é válida.

**Estado atual: referências OHLCV, estados8/16/32/64 e taxa concluídos/conferidos; CryptoMamba adaptado concluído e conferido.** Consultar o [estado desta rodada](registros/cryptomamba/estado.json). A rodada inicial OHLCV foi concluída em29/10/2026, após qualificação e autorização explícita. Coleta, preparação das entradas e consumo por Mamba/LSTM/Naive/ARIMA estão separados; [dados](docs/arquitetura_dados.md), [modelos](docs/arquitetura_modelos.md), [evidências](registros/modelos/estado.json) e [cronologia](docs/andamento.md). A autorização está em `registros/treinamento/autorizacao.json`. Treinamento, seleção, checkpoints e publicação estão separados na [arquitetura de treinamento](docs/arquitetura_treinamento.md); consultar o [estado verificável](registros/treinamento/estado.json). A referência OHLCV preparada em `registros/ohlcv/` continua preservada, sem treino de mercado e sem migração silenciosa do executor. A definição acadêmica original está no [TCC1](docs/TCC_1_MuriloRFM.pdf); a delimitação atual não implica aceite do orientador.

A extensão `d_state16→8` foi concluída e conferida: seis seeds Mamba, três pareadas com R0. Não demonstrou melhora preditiva. [Relatório comparativo](docs/resultados_estado_mamba.md). [Protocolo](docs/protocolo_estado_mamba.md), [estado próprio](registros/estado_mamba/estado.json) e [auditoria OHLCV/Binance](registros/treinamento/auditoria_representacao_atual.json).

A sequência **estado32 → estado64** foi concluída e conferida, seis seeds em cada rodada, com o restante do desenho fixo. [Médias e fechamento dos quatro estados](docs/resultados_estados32_64.md). [Protocolo](docs/protocolo_estados32_64.md) e [registros/progresso](registros/estados_ampliados/estado.json). Resultados anteriores permanecem preservados e identificados.

O **estado16 também tem seis seeds concluídas e conferidas**, com três novas e três herdadas de R0. A [tabela comparativa](docs/resultados_estados32_64.md) e figura agora incluem os quatro estados nas mesmas seis seeds. [Protocolo do complemento](docs/protocolo_complemento_estado16.md) e [evidências](registros/complemento_estado16/estado.json). O16 teve o menor MSE médio observado, sem vantagem demonstrada sobre8/32 ou Naive; todas as médias líquidas Spot foram negativas.

## Comece aqui

O estudo de taxa0,0001 nos quatro estados foi encerrado/conferido: [médias e análise](docs/resultados_taxa_aprendizado.md). A referência permanece16/lr0,0002. A rodada posterior, autorizada em seis seeds, compara [CryptoMamba adaptado](docs/protocolo_cryptomamba_adaptado.md) no mesmo contrato de dados/alvo; [estado e evidências](registros/cryptomamba/estado.json). Mudam arquitetura e receita em conjunto; não é reprodução literal do artigo nem ablação de um fator.

- [Índice documental](docs/README.md): documentos atuais e histórico.
- [Desenho OHLCV](docs/desenho_ohlcv24.md): decisões, fórmulas, modelos, datas, avaliação e próximos ciclos.
- [Arquitetura de dados](docs/arquitetura_dados.md): etapas, contratos, testes, manutenção e fronteiras ainda a revisar.
- [Arquitetura dos modelos](docs/arquitetura_modelos.md): como cada família recebe dados e devolve previsões; sem treinamento.
- [Plano de trabalho](plano.md) e [andamento](docs/andamento.md).
- [Estudos preliminares preservados](arquivo/estudos_preliminares_2026-10-28/README.md): resultados anteriores, que usaram somente retornos do fechamento.
- [Catálogo de estudos](registros/catalogo_estudos.json), [mapa de registros](registros/README.md) e [roteiro de redação](docs/roteiro_redacao_tcc.md).

## Referência inicial

| Item | Definição |
|---|---|
| Mercado e dados | BTCUSDT, Binance Spot, OHLCV de candles completos de 1h |
| Contexto e horizonte | Últimas 168h → retorno terminal das próximas 24h |
| Entradas | ln(O/C anterior), ln(H/C anterior), ln(L/C anterior), ln(C/C anterior), ln(1+volume BTC); padronização só no treino |
| Divisão exploratória | Treino 2021–2023, validação 2024, teste retrospectivo 2025; purga24h |
| Redes | Mamba-1 oficial CUDA e LSTM; seeds17/42/2026 |
| Referências | Naive zero; ARIMA(p,1,q), p/q0..2, sem deriva, selecionado na validação |
| Orçamento inicial | 6 ajustes neurais principais + 2 controles de reprodução; nenhuma ablação nesta rodada |
| Avaliação | MSE primário, RMSE/MAE/direção secundários; simulação diária Spot com custos, separada |

OHLCV não garante melhora. Esta divisão fixa é exploração, não walk-forward. Períodos já consultados continuam retrospectivos. A avaliação ampliada por reestimações temporais será outra etapa, após delimitar a candidata.

## Código e execução

Para trabalhar com dados: `python run_dados.py --help`. `mercado_binance/` coleta e confere OHLCV; `entradas_modelo/` configura representação/alvo/contextos/escalas sem acessar a Binance; `infraestrutura/` preserva identidades e dependências. Testes: `python -m unittest discover -s tests_dados -v`. Não exigem GPU. As configurações são `configuracoes/mercado_binance_001.json` e `configuracoes/entradas_ohlcv24_001.json`. Os consumidores estão em `modelos/`; a orquestração está em `treinamento/`, com avaliação em `avaliacao/`.

Para conferir os consumidores sem treinar: `python run_modelos.py conferir --entradas <pasta-do-conjunto>`. A cadeia atual usa `run_treinamento.py`, executado na raiz do projeto em Linux/WSL com CUDA oficial:

```text
python run_treinamento.py qualificar
python run_treinamento.py preparar --qualificacao <recibo-aprovado>
python run_treinamento.py conferir
```

Esses comandos não treinam dados de mercado. A execução real exige `executar --autorizacao <recibo>` depois do “Ok” explícito do pesquisador. A autorização identifica a execução e o orçamento. Retomada exige investigação e `--retomar`; não duplicar processos ou reexecutar ciclo concluído. A [arquitetura](docs/arquitetura_treinamento.md) documenta tentativas, seleção, checkpoints, controles e resultados.

`estudo_ohlcv/`, `run_ohlcv.py`, a configuração original e `registros/ohlcv/` preservam a preparação anterior; não são o executor da nova cadeia modular.

Conferência independente da preparação, sem treino: `python manutencao/conferir_preparacao_ohlcv.py`. Verificação dos estudos preliminares: `python manutencao/auditar_catalogo.py --integridade --exigir-completo` no computador que contém todos os artefatos. O auditor histórico não substitui a conferência OHLCV.

Dependências gerais em `requirements.txt`. Qualificação registra versões, hardware, implementação instalada, testes, recarga e reprodução. Não há fallback silencioso do Mamba. A integração do novo ciclo no portal será feita quando houver resultados reais.

## Organização e preservação

| Local | Função |
|---|---|
| `docs/` | Desenho atual, cronologia, redação e regras de registro; três protocolos históricos mantidos por integridade |
| `docs/adr/` | Decisões materiais e suas razões |
| `registros/` | Catálogo, ponteiros, auditorias, incidentes e recibos |
| `dados/experimentos/` | Execuções separadas; fontes congeladas, tentativas, checkpoints, previsões e publicações |
| `arquivo/estudos_preliminares_2026-10-28/` | Índice, documentação e snapshots da fase anterior |
| `previsao24/`, `experimento_penalizacao/`, `experimento_normalizacao/` | Fontes preservadas dos três ciclos encerrados; não editar sob suas identidades |
| `dataview/` | Portal Next.js do estudo preliminar; executar npm dentro desta pasta |

Não criar documentos para cada pergunta. Refinar o desenho existente, registrar fatos na cronologia e guardar evidências técnicas no ciclo correspondente. Não eliminar falhas ou resultados desfavoráveis. Os binários grandes são preservados localmente/pacotes, conforme a [política de armazenamento](docs/armazenamento_e_reproducao.md); arquivos locais não equivalem a backup remoto verificado.

Licença: [MIT](LICENSE).

**Referência adotada para as próximas hipóteses: Mamba16, seis seeds.** A investigação de8/16/32/64 está [encerrada e indexada](registros/investigacoes/estados_internos_001/fechamento.json), conforme a [ADR0012](docs/adr/0012-referencia16-e-proxima-hipotese.md). A próxima hipótese é apenas proposta: taxa AdamW0,0002→0,0001, mantendo os outros fatores. Ver [desenho, seção11](docs/desenho_ohlcv24.md#11-referência-adotada-e-próxima-hipótese-proposta). Nenhum novo treino iniciado.

**Grade de taxa autorizada:0,0001 nos estados8/16/32/64, seis seeds por estado (24novos ajustes).** Isso amplia a proposta anterior de16/seis seeds. [Protocolo](docs/protocolo_taxa_aprendizado.md), [ADR0013](docs/adr/0013-taxa-aprendizado-quatro-estados.md) e [progresso verificável](registros/taxa_aprendizado/estado.json). Referências0,0002 e estudo anterior permanecem preservados; identidade/início/conclusão dependem dos registros, não deste anúncio.

**Grade de taxa concluída e conferida:**24novos ajustes, seis seeds em cada estado. A redução para0,0001 não demonstrou ganho no critério primário de validação; a referência16/0,0002 permanece. [Comparação, interpretação e gráficos](docs/resultados_taxa_aprendizado.md). Resultados originais e os dois lados de cada contraste foram preservados.
