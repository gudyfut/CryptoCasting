# Orientações para trabalhar no CryptoCasting

## Contexto e objetivo

Este repositório contém um TCC sobre investigação controlada de decisões de projeto do Mamba com dados históricos de mercado. A referência acadêmica é [TCC1](docs/TCC_1_MuriloRFM.pdf), especialmente resumo, introdução e seção 2.7: entradas OHLCV/indicadores, desenvolvimento iterativo e avaliação walk-forward. Não transformar o objetivo em vencer LSTM ou obter lucro. Referências auxiliares ajudam a interpretar o desempenho; uma conclusão negativa é válida.

A direção atual é estabelecer uma referência OHLCV, conforme [desenho em discussão](docs/desenho_ohlcv24.md) e ADR 0006. Reorganização e uso inicial de OHLCV foram solicitados pelo pesquisador; detalhes do protocolo estão propostos, sem nova execução autorizada por implicação. Recomenda-se exploração BTC/168h/24h/três seeds e posterior avaliação temporal ampliada. Não apresentar esse desenho como implementado ou aprovado pelo orientador.

Os ciclos de retorno24 em quatro moedas, entrada escalar de retornos, contextos 24/72/168/336 e extensões concluídas são [estudos preliminares preservados](arquivo/estudos_preliminares_2026-10-28/README.md). Não são resultados de uma rede com entrada OHLCV. Previsão terminal e utilidade econômica continuam eixos distintos.

## Leitura inicial e fontes de informação

1. Começar por [índice documental](docs/README.md), [plano.md](plano.md) e [desenho OHLCV](docs/desenho_ohlcv24.md). Consultar o PDF acadêmico quando a tarefa envolver objetivos/metodologia. O [protocolo experimental anterior](docs/protocolo_experimental.md) descreve uma execução congelada, não a próxima etapa por padrão.
2. Ler o [índice de decisões (ADRs)](docs/adr/README.md) e as decisões pertinentes à tarefa. Para a extensão de penalização, ler também [seu protocolo](docs/protocolo_penalizacao_mamba.md) e a [auditoria de configuração](docs/auditoria_configuracao_penalizacao.md).
3. Consultar [andamento](docs/andamento.md), o [relatório da extensão de penalização](docs/resultados_penalizacao_mamba.md) e o [mapa de registros](registros/README.md). Confirmar o estado pelos artefatos da máquina responsável; um snapshot no Git não informa se o processo remoto continua ativo.
4. Antes de transferir ou publicar resultados, seguir a [política de preservação](docs/armazenamento_e_reproducao.md). Para escrever o TCC, usar o [roteiro de redação](docs/roteiro_redacao_tcc.md).
5. Para localizar ciclos ou propor mudanças, consultar o [catálogo](registros/catalogo_estudos.json) e o [procedimento de registro](docs/registro_de_experimentos.md). Usar o [modelo de proposta](docs/modelos/proposta_experimento.md); manter proposta, autorização e execução separadas. A auditoria posterior `manutencao/auditar_catalogo.py` verifica disponibilidade e integridade sem iniciar treinamento.

## Regras científicas permanentes

- Aplicar scalers somente no treino, purga temporal de 24h e mesmas origens entre modelos/contextos. Não interpolar lacunas nem selecionar exemplos pela magnitude do retorno futuro.
- Distinguir dados coletados de entradas efetivas. A referência OHLCV precisa usar e documentar O/H/L/C/V, fórmulas causais, unidades e dimensão de entrada. Retorno somente de C é controle de informação, não OHLCV completo.
- Usar Mamba oficial CUDA, sem fallback silencioso. Preservar seeds 17/42/2026, Naive de retorno zero e ARIMA(p,1,q) sem deriva, p/q em 0..2 selecionados na validação, conforme o protocolo.
- DB1–DB4 são desenvolvimento. B1–B4 já foram consultados: novas hipóteses nesses períodos são retrospectivas, sem alegação de holdout intocado. Não selecionar seed favorável nem alterar modelos durante uma avaliação congelada.
- Uma divisão fixa de exploração não é validação walk-forward; avaliação em blocos exige reestimação com passado permitido. Não aplicar um checkpoint treinado no futuro a períodos anteriores. Dados/preços de 2026 aparecem no PDF: não presumir independência desse ano sem conferir exposição específica.
- Preservar toda tentativa, falha, interrupção e revisão. Recarga de checkpoint e métricas recalculadas são requisitos de auditoria. Planejamento e aprovação de testes sintéticos não comprovam conclusão de treinamento.
- Fontes, configurações, protocolos e recibos congelados são imutáveis sob a identidade da execução. Não regenerar hashes para aceitar divergências. Uma nova mudança científica exige ciclo identificado, registro da decisão e autorização compatível.
- Novos indicadores, candles, horizontes, políticas operacionais e busca de parâmetros exigem hipótese e orçamento identificados; não iniciá-los automaticamente. LayerNorm do bloco não é normalização adaptativa dos dados. Não inferir utilidade operacional a partir de MSE isolado.

## Escopo autorizado e preservação

As autorizações históricas estão contextualizadas nas ADRs 0001/0002/0005. Os ciclos foram concluídos e permanecem preservados. Elas não autorizam busca indefinida nem repetição de executor encerrado. A solicitação de 28/10 autoriza reorganizar e estabelecer o desenho OHLCV; a nova implementação/grade deverá ter contrato e autorização compatíveis antes do treino.

- Referência: código `previsao24/`, entrada `run_previsao.py`, configuração `configuracoes/retorno24_001.json` e ponteiro `registros/execucao_atual.json`. Preservar integralmente a execução `1e7c5ed662fba55ddd25`.
- Extensão: código `experimento_penalizacao/`, entrada `run_penalizacao.py`, ponteiro `registros/penalizacao/execucao.json`; identidade congelada `7868a4d847c1410fc681`. Respeitar o escopo de 384 Mamba corrigidos e dois controles reexecutados; LSTM/Naive/ARIMA são referências herdadas. Não alterar suas fontes congeladas.
- Pré-normalização: autorizada e concluída em 28/10/2026 (ADR 0005), identidade `9e03af2150cbb7b1068d`, código `experimento_normalizacao/`, entrada `run_normalizacao.py`, configuração `configuracoes/normalizacao_mamba_001.json`, protocolo `docs/protocolo_normalizacao_mamba.md`, ponteiro `registros/normalizacao/execucao.json`. Somente posição da LayerNorm mudou, mantendo penalização corrigida. Preservar fontes e fechamento; não reexecutar para gerar relatórios.
- `arquivo/estudo_barreiras_2026-10-20/` é histórico imutável. Não importar seu código na aplicação ativa nem misturar seus resultados com os atuais. Não reescrever o histórico Git.

## Operação, interface e trabalho entre máquinas

- Antes de treinar, inspecionar hardware/ambiente e exigir qualificação de dimensões, forward/backward, atualização, repetição e recarga. Não comprar computação paga.
- Antes de retomar, conferir host, PID, lock e logs no computador executor. Nunca duplicar um treinamento por timeout, falta de arquivos em outra máquina ou snapshot antigo. Não iniciar cópia concorrente de um ciclo que segue no notebook.
- Para um ciclo concluído, usar ferramentas posteriores de leitura/conferência com recibos próprios. Não chamar novamente o executor apenas para regenerar relatórios, contagens ou recibos; preservar publicações e incidentes existentes.
- A interface Next.js está em `dataview/`; executar npm nesse diretório. Exibir contagens e resultados derivados de evidências reais, distinguir ciclos e informar artefatos indisponíveis. Ausência local não significa zero treinamentos no estudo.
- O portal existente mostra o estudo preliminar. Não apresentá-lo como evidência da nova proposta OHLCV. O agrupamento em `arquivo/estudos_preliminares_2026-10-28/` é por índice e snapshot documental; artefatos científicos não foram movidos.
- Identificadores novos em português; preservar nomes dos argumentos oficiais da API Mamba. Registrar verificações realizadas e limitações do ambiente.

## Manutenção da documentação

Manter este arquivo como guia estável. Atualizá-lo quando mudarem objetivo, regras permanentes ou caminhos de referência; não usá-lo como diário de treinamento ou placar. Registrar decisões e motivos em `docs/adr/`, evolução factual em `docs/andamento.md`, evidências em `registros/` e artefatos por tentativa em `dados/experimentos/`. Seguir os formatos existentes sem mover artefatos congelados. Distinguir claramente proposto, autorizado, executado e auditado.

- **Não gerar documentos a cada interação.** Perguntas explicativas normalmente são respondidas na conversa; não criam por si só ADR, relatório, snapshot ou pasta de revisão.
- Refinamentos do desenho ficam em `docs/desenho_ohlcv24.md`; cronologia somente em `docs/andamento.md`; navegação em `docs/README.md`.
- Antes de criar arquivo, procurar onde a informação já deve viver. Criar documento novo apenas para função distinta: protocolo de ciclo, relatório de execução, decisão material ou entrega explicitamente solicitada.
- Recibos técnicos, extrações, logs e benchmarks ficam em `registros/`/execuções. Não duplicar seus conteúdos integralmente em Markdown. Snapshot documental apenas quando necessário para preservar versão vinculada a fechamento ou reorganização material.
- Preservar documentos/artefatos científicos antigos em seus caminhos quando usados por hashes e links. Preferir índices a movimentações em massa. Não produzir versões concorrentes de cronologia ou placar. Não editar o PDF acadêmico compilado; mudanças de redação precisam de fontes editáveis ou nova versão identificada.
