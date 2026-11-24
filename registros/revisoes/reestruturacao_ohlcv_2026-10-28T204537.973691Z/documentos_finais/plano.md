# Plano de trabalho — transição para OHLCV

Atualizado em 28/10/2026 após consulta do [TCC1](docs/TCC_1_MuriloRFM.pdf). A orientação acadêmica é investigar decisões do Mamba; referências auxiliares não transformam o objetivo em ranking de arquiteturas.

## Etapa atual

Reorganização autorizada pelo pesquisador; método detalhado ainda proposto em [desenho OHLCV](docs/desenho_ohlcv24.md). Nenhum treino novo iniciado. OHLCV completo como referência inicial; proposta de BTC, 1h, contexto 168h, horizonte 24h, três seeds, exploração curta seguida de walk-forward ampliado. Não apresentar desenho recomendado como execução realizada ou aceite acadêmico.

1. Conferir e preservar os estudos encerrados; organizar o [arquivo preliminar](arquivo/estudos_preliminares_2026-10-28/README.md).
2. Fechar entradas, alvo, divisões, orçamento, critérios preditivos e política operacional no documento único de desenho; explicitar correspondência e delimitações perante o TCC1.
3. Implementar ciclo novo com dados multivariados e identidade própria; qualificar causalidade, treinamento, reprodução e contabilidade antes do congelamento.
4. Executar somente a rodada definida e autorizada, com todas as tentativas e seeds; selecionar pela validação.
5. Congelar referência/candidata e executar avaliação temporal ampliada, reestimando somente com passado permitido. Classificar corretamente os períodos já consultados.
6. Escrever metodologia, resultados e limites a partir dos registros, sem buscar indefinidamente até Mamba vencer ou aparecer lucro.

As etapas 3–5 são planejamento, não autorização automática de treinamento. Perguntas e refinamentos atualizam os documentos existentes. A [ADR 0006](docs/adr/0006-reorganizacao-e-desenho-ohlcv.md) registra a mudança de orientação.

## Plano histórico do estudo de retorno em 24h

O conteúdo abaixo descreve o contrato anterior. Sua versão antes desta organização está preservada no arquivo preliminar. O protocolo científico vinculado às execuções permanece inalterado.

Versão adotada em 20/10/2026 após definição do pesquisador e discussão com o orientador.

Investigar o efeito de 1, 3, 7 e 14 dias de contexto na previsão do retorno de quatro criptomoedas em 24 horas. Comparação principal Mamba–LSTM; referências Naive e ARIMA. Não condicionar sucesso do TCC a vitória de uma arquitetura ou lucro.

O contrato executável é `configuracoes/retorno24_001.json`; as regras estão em `docs/protocolo_experimental.md`. Acompanhamento factual: `docs/andamento.md` e `registros/`. Código científico: `previsao24/`; entrada: `run_previsao.py`.

## Entregas obrigatórias desta execução

1. Preservar e verificar o estudo anterior no arquivo histórico; retirar seus componentes do projeto ativo.
2. Fixar protocolo, configuração, fontes e classificação da exposição prévia aos períodos de avaliação.
3. Coletar/auditar dados de 2021–2025; construir dataset causal, com origem e destino identificáveis.
4. Testar contratos, vazamento, fronteiras temporais, ARIMA, métricas e contabilidade; qualificar redes CUDA em todos os contextos.
5. Executar desenvolvimento: quatro moedas × quatro contextos × quatro blocos × três seeds × duas redes = 384 ajustes neurais. ARIMA ajustado/selecionado por moeda/bloco; Naive determinístico.
6. Congelar e executar avaliação 2024–2025 em quatro blocos semestrais, mesma grade e três seeds: outros 384 ajustes neurais. Não selecionar configurações ou seeds pelo teste. Classificar corretamente a independência conforme exposição anterior.
7. Auditar todos os checkpoints e previsões; consolidar resultados por moeda, contexto, período e seed, diferenças pareadas e incerteza temporal. Simulação diária Spot separada, com custos e ausências explícitos.
8. Reconstruir interface e explorador de previsões reais; verificar métricas, filtros, gráficos, explicações e versões responsivas.

Nenhum item é concluído apenas por existir código. A conclusão exige execução e evidência verificável. Futuras entradas/indicadores e candles menores exigem novos ciclos; não fazem parte desta entrega inicial.

## Extensão autorizada em 26/10/2026

O pesquisador solicitou corrigir a penalização dos parâmetros marcados pelo Mamba, executar um novo experimento controlado com o restante igual, preservar o estudo concluído e comparar os resultados. O contrato adicional está em `docs/protocolo_penalizacao_mamba.md`. São previstos 384 novos ajustes Mamba e dois controles originais reexecutados para conferir reprodução; LSTM, Naive e ARIMA são referências herdadas, sem novos ajustes.

A comparação é retrospectiva em períodos já expostos. Não altera a classificação histórica do primeiro ciclo nem autoriza busca indefinida de hiperparâmetros. As novas entregas são: correção isolada e testada; qualificação e congelamento; controles e piloto; grade completa; comparação pareada e simulação com política preservada; preservação antes/depois; documentação com rastreabilidade para a redação. As oito entregas anteriores continuam sendo do ciclo original.

Execução concluída em 27/10/2026: 384 ajustes corrigidos e dois controles, com duas tentativas interrompidas preservadas. As sete entregas da extensão e suas evidências são detalhadas em `docs/resultados_penalizacao_mamba.md`; não são sete novas etapas acadêmicas aprovadas pelo orientador. A correção não eliminou a desvantagem frente à LSTM/Naive. O próximo trabalho é consolidar a redação científica, mantendo explícita a natureza retrospectiva da extensão; nenhum novo experimento está iniciado por este fechamento.
