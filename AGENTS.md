# AGENTS.md

TCC: previsão de retorno em 24 horas, Mamba versus LSTM, Naive e ARIMA. Leia `plano.md` e `docs/protocolo_experimental.md`.

## Extensão autorizada em 26/10/2026

O pesquisador autorizou corrigir a penalização do Mamba e executar uma comparação controlada completa, preservando o ciclo anterior. Ler `docs/protocolo_penalizacao_mamba.md`, `docs/auditoria_configuracao_penalizacao.md` e `docs/roteiro_redacao_tcc.md`. Código novo em `experimento_penalizacao/`, entrada `run_penalizacao.py`, ponteiro próprio `registros/penalizacao/execucao.json`. Grade: 384 Mamba corrigidos e dois controles originais reexecutados; as demais referências são herdadas. Não contar planejamento como execução.

Preservar `previsao24/`, `run_previsao.py`, protocolo/configuração originais e todos os artefatos da execução `1e7c5ed662fba55ddd25`. A correção vale somente no novo ciclo; os arquivos antigos continuam representando a implementação realmente executada. Não alterar fontes após o congelamento da extensão. Os períodos DB/B são conhecidos: comparação retrospectiva, sem nova alegação de holdout intocado. Verificar PID, lock e logs antes de retomar; nunca duplicar processo por timeout. Qualquer falha/revisão deve ser registrada.

A extensão foi congelada como `7868a4d847c1410fc681` após 24 testes e 12 casos de qualificação CUDA. O manifesto inicial preserva 7.082 arquivos. A execução foi iniciada; conferir seu `progresso.json` para contagens atuais. Não presumir grade concluída por este registro. Os resultados previstos serão consolidados em `dados/experimentos/penalizacao_7868a4d847c1410fc681/analises/` e documentados em `docs/resultados_penalizacao_mamba.md` após as duas fases.

## Autorização vigente — 20/10/2026

O pesquisador autorizou arquivar o estudo anterior, substituir integralmente o projeto ativo, implementar, auditar e executar o protocolo novo de treinamento e testes, e apresentar os resultados reais na interface. Não é necessário pedir novamente autorização para coleta, preparação, qualificação e execução. Não reescrever Git.

O arquivo `arquivo/estudo_barreiras_2026-10-20/` é histórico imutável: manter fontes, configurações, dados, checkpoints e resultados; não importar código dele na aplicação atual. A preservação possui manifesto SHA-256 antes/depois. Arquivamento local não é backup externo.

## Contrato atual

- Quatro moedas Binance Spot: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT.
- Alvo terminal `ln(P[t+24h]/P[t])`; entradas exclusivamente retornos horários; contextos 24/72/168/336h; origem horária.
- Mamba oficial CUDA e LSTM, seeds 17/42/2026; Naive = retorno zero; ARIMA(p,1,q) sem deriva, p/q 0..2, seleção na validação.
- Scalers só no treino; purga temporal de 24h; mesmas origens entre modelos/contextos; nenhum filtro pela magnitude do retorno futuro; não interpolar lacunas.
- DB1–DB4 = desenvolvimento. B1–B4 exigem congelamento e registro de exposição prévia. Exposição desconhecida não permite alegar holdout intocado. Não alterar modelos após consultar esses resultados.
- Toda tentativa, falha e revisão fica registrada. Recarga de checkpoint e métricas recalculadas são obrigatórias. Não escolher seed favorável.
- Indicadores, granularidades 15/30min e outras configurações são extensões futuras, não parte da grade atual nem busca automática.
- Previsão e utilidade econômica são eixos distintos; nenhum resultado garante lucro ou superioridade de Mamba.
- Identificadores novos em português. Não alterar argumentos oficiais da API Mamba.

## Execução e interface

Inspecionar hardware e ambiente; qualificar dimensões, forward/backward, recarga e determinismo antes de treinar. Não substituir backend silenciosamente. Não duplicar processos após timeout: verificar PID e logs. Não comprar computação paga.

Next.js em `dataview/`, npm nesse diretório. A interface ativa mostra somente o novo estudo, com status/contagens derivados de registros reais. O arquivo histórico não compõe resultados atuais.

## Estado verificado em 21/10/2026

Oito entregas computacionais concluídas. Dataset `d25f6a93a9900725f51e`; execução `1e7c5ed662fba55ddd25`. Desenvolvimento e avaliação completos: 768 ajustes neurais, 32 Naive e 32 seleções ARIMA; 288 candidatos ARIMA válidos. Ler `docs/resultados_avaliacao.md` e `docs/resultados_desenvolvimento.md`. LSTM teve menor MSE que Mamba; LSTM–Naive inconclusivo na avaliação; sem melhoria geral de contexto ou rentabilidade consistente.

Fechamento em `registros/auditorias/1e7c5ed662fba55ddd25/fechamento.json`; aceite visual em `registros/interface/aceite_final.json`. Portal: 832 resultados/384 séries. A interrupção operacional e os 636 registros anteriores íntegros estão preservados em `registros/incidentes/`. Não regenerar recibos congelados nem alterar fontes científicas sob esta identidade. Novas hipóteses exigem novo ciclo; não iniciar busca automaticamente. Os períodos B1–B4 agora foram consultados e não voltam a ser confirmação intocada.
