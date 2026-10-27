# AGENTS.md

TCC científico: primeiro toque em barreiras de preço com Mamba, LSTM e AR(1). Leia `plano.md` e `docs/protocolo_experimental.md` antes de implementar.

## Autorização e objetivo atual

Em 18/10/2026, o pesquisador solicitou retirar os registros da metodologia e do piloto anteriores, reorganizar o projeto para barreiras, implementar, auditar e executar coleta, pipeline, treinamento e testes. Esta autorização substitui a restrição anterior de execução exclusiva pelo pesquisador. Não é necessário pedir nova confirmação para essas etapas. Não reescrever o histórico Git.

O trabalho é iterativo: avaliar uma grade inicial e depois formular ciclos novos, inclusive de parâmetros internos do Mamba, documentando cada hipótese e todos os resultados. Desenvolvimento iterativo não transforma o mesmo teste consultado repetidamente em avaliação final independente.

## Estado verificado em 18/10/2026

Primeiro ciclo concluído: dataset `9341610dbb329a858784`, execução `4e232a796fcda0ea34c3`, DB1–DB4/seed 42, 96 células auditadas, 192 ajustes neurais e 16 ajustes únicos AR(1). Recargas exatas; auditoria suplementar 96/96 aprovada; 25 testes Python finais aprovados. Ler `historico/analises/ciclo_001_resultados.md` antes de interpretar os placares. Não há superioridade demonstrada de Mamba sobre LSTM nem rentabilidade consistente. O relatório preserva perdas, caixa e controles financeiramente não auditáveis.

`historico/ciclos/ciclo_002_proposto.md` e `configuracoes/ciclo_002_proposto.json` são proposta não executada de ablação do estado 16→8 em H168. Não iniciar outra busca automaticamente. A qualificação atual foi feita para a configuração inicial; antes de uma variante, qualificar suas dimensões e preparar comparação entre ciclos. Preservar protocolo/fontes/checkpoints do ciclo concluído. B1–B4 seguem bloqueados.

## Invariantes científicos

- Quatro moedas: BTCUSDT, ETHUSDT, BNBUSDT e XRPUSDT; Binance Spot.
- Ciclo inicial: entrada 1h, base 1m, contextos 24/168h, prazos máximos 1/24/168h; três classes de primeiro toque.
- Walk-forward expansivo por datas. Scalers só no treino; purga pela expiração máxima planejada. Sem split aleatório.
- Mamba e LSTM recebem as mesmas origens, entradas e regras de treino. Validação escolhe época por log-loss; testes de desenvolvimento só orientam ciclos posteriores, nunca a seleção retroativa de checkpoint.
- DB1–DB4 são desenvolvimento. B1–B4 permanecem bloqueados até congelamento e declaração de exposição anterior. Não afirmar holdout intocado sem evidência.
- Toda tentativa nova, inclusive falha, precisa de configuração, versões, hashes, timestamps, métricas recalculáveis e estado de auditoria. Não apagar tentativas deste novo ciclo por resultado ruim.
- Probabilidades e operações são avaliações distintas. Custos, caixa, risco e ordem desconhecida de toques devem ser explícitos. Não usar completude futura para decidir entrada financeira.
- Não filtrar por magnitude futura. Não inventar ordem intraminuto ou preencher lacunas de preço. Não alinhar arquivos por número de linha.
- Identificadores novos em português; argumentos da API Mamba mantêm compatibilidade.

## Ambiente e execução

Inspecionar a máquina atual, sem presumir hardware a partir de registros. Em 18/10/2026 foi encontrada RTX 4050 6 GB e WSL Ubuntu com Python 3.12 e PyTorch CUDA em `~/.venvs/cc`. Qualificar importação, forward/backward, recarga e determinismo antes do treino. O protocolo especifica backend oficial; não substituir silenciosamente.

Não lançar processos duplicados após timeout de observação. Verificar o handle/PID vivo e seus logs. Registros científicos não podem confundir teste sintético com treino de mercado. Não fazer compras ou contratar computação paga sem autorização.

## Interface

Next.js em `dataview/`. Npm deve rodar nesse diretório. Interface e documentação devem mostrar somente o estudo de barreiras e resultados reais auditados. A configuração executada e os registros são a fonte das contagens, nunca números inventados na interface.
