# Orientações para trabalhar no CryptoCasting

## Contexto e objetivo

Este repositório contém um TCC sobre previsão do retorno de criptomoedas em 24 horas. A pergunta principal é como o tamanho do contexto histórico afeta Mamba e LSTM, com Naive e ARIMA como referências. Uma conclusão negativa é válida: não condicionar o sucesso do trabalho à vitória do Mamba ou a lucro simulado.

O estudo ativo usa BTCUSDT, ETHUSDT, BNBUSDT e XRPUSDT da Binance Spot; retornos horários como única entrada; contextos de 24/72/168/336 horas; origem horária e alvo terminal `ln(P[t+24h]/P[t])`. É regressão, avaliada principalmente por MSE. Direção é um diagnóstico secundário; previsão e utilidade econômica são eixos distintos.

## Leitura inicial e fontes de informação

1. Ler [plano.md](plano.md) e [protocolo experimental](docs/protocolo_experimental.md) para entender o contrato científico.
2. Ler o [índice de decisões (ADRs)](docs/adr/README.md) e as decisões pertinentes à tarefa. Para a extensão de penalização, ler também [seu protocolo](docs/protocolo_penalizacao_mamba.md) e a [auditoria de configuração](docs/auditoria_configuracao_penalizacao.md).
3. Consultar [andamento](docs/andamento.md) e o [mapa de registros](registros/README.md). Confirmar o estado pelos artefatos da máquina responsável; um snapshot no Git não informa se o processo remoto continua ativo.
4. Antes de transferir ou publicar resultados, seguir a [política de preservação](docs/armazenamento_e_reproducao.md). Para escrever o TCC, usar o [roteiro de redação](docs/roteiro_redacao_tcc.md).

## Regras científicas permanentes

- Aplicar scalers somente no treino, purga temporal de 24h e mesmas origens entre modelos/contextos. Não interpolar lacunas nem selecionar exemplos pela magnitude do retorno futuro.
- Usar Mamba oficial CUDA, sem fallback silencioso. Preservar seeds 17/42/2026, Naive de retorno zero e ARIMA(p,1,q) sem deriva, p/q em 0..2 selecionados na validação, conforme o protocolo.
- DB1–DB4 são desenvolvimento. B1–B4 já foram consultados: novas hipóteses nesses períodos são retrospectivas, sem alegação de holdout intocado. Não selecionar seed favorável nem alterar modelos durante uma avaliação congelada.
- Preservar toda tentativa, falha, interrupção e revisão. Recarga de checkpoint e métricas recalculadas são requisitos de auditoria. Planejamento e aprovação de testes sintéticos não comprovam conclusão de treinamento.
- Fontes, configurações, protocolos e recibos congelados são imutáveis sob a identidade da execução. Não regenerar hashes para aceitar divergências. Uma nova mudança científica exige ciclo identificado, registro da decisão e autorização compatível.
- Indicadores, candles menores, horizontes diferentes e busca adicional de parâmetros são extensões futuras; não iniciá-las automaticamente.

## Escopo autorizado e preservação

As autorizações de 20/10 e 26/10/2026 estão contextualizadas nas ADRs 0001 e 0002. Elas permitem executar os ciclos definidos, sem pedir novamente autorização para suas etapas necessárias; não autorizam buscas indefinidas.

- Referência: código `previsao24/`, entrada `run_previsao.py`, configuração `configuracoes/retorno24_001.json` e ponteiro `registros/execucao_atual.json`. Preservar integralmente a execução `1e7c5ed662fba55ddd25`.
- Extensão: código `experimento_penalizacao/`, entrada `run_penalizacao.py`, ponteiro `registros/penalizacao/execucao.json`; identidade congelada `7868a4d847c1410fc681`. Respeitar o escopo de 384 Mamba corrigidos e dois controles reexecutados; LSTM/Naive/ARIMA são referências herdadas. Não alterar suas fontes congeladas.
- `arquivo/estudo_barreiras_2026-10-20/` é histórico imutável. Não importar seu código na aplicação ativa nem misturar seus resultados com os atuais. Não reescrever o histórico Git.

## Operação, interface e trabalho entre máquinas

- Antes de treinar, inspecionar hardware/ambiente e exigir qualificação de dimensões, forward/backward, atualização, repetição e recarga. Não comprar computação paga.
- Antes de retomar, conferir host, PID, lock e logs no computador executor. Nunca duplicar um treinamento por timeout, falta de arquivos em outra máquina ou snapshot antigo. Não iniciar cópia concorrente de um ciclo que segue no notebook.
- A interface Next.js está em `dataview/`; executar npm nesse diretório. Exibir contagens e resultados derivados de evidências reais, distinguir ciclos e informar artefatos indisponíveis. Ausência local não significa zero treinamentos no estudo.
- Identificadores novos em português; preservar nomes dos argumentos oficiais da API Mamba. Registrar verificações realizadas e limitações do ambiente.

## Manutenção da documentação

Manter este arquivo como guia estável. Atualizá-lo quando mudarem objetivo, regras permanentes ou caminhos de referência; não usá-lo como diário de treinamento ou placar. Registrar decisões e motivos em `docs/adr/`, evolução factual em `docs/andamento.md`, evidências em `registros/` e artefatos por tentativa em `dados/experimentos/`. Seguir os formatos existentes sem mover artefatos congelados. Distinguir claramente proposto, autorizado, executado e auditado.
