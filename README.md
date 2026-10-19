# CryptoCasting

Pesquisa de primeiro toque em barreiras de criptomoedas com Mamba, LSTM e AR(1). O trabalho combina avaliação probabilística e simulação financeira com custos, por ciclos documentados de melhoria.

## O estudo

- Quatro pares: BTCUSDT, ETHUSDT, BNBUSDT e XRPUSDT.
- Entradas de 1h, contextos de 24/168 horas e prazos máximos de 1/24/168 horas.
- Três classes: inferior primeiro, prazo esgotado e superior primeiro.
- Base 1m, sem interpolação de preços. Barreiras dependem apenas da volatilidade passada e do prazo.
- Walk-forward expansivo: desenvolvimento DB1–DB4 em 2023; avaliação final B1–B4 bloqueada.
- Primeira grade: 24 combinações, 96 células com fold/seed, 192 ajustes neurais.

Leia o [protocolo](docs/protocolo_experimental.md), o [plano](plano.md), a [hipótese do ciclo inicial](historico/ciclos/ciclo_001.md) e o [andamento verificado](docs/andamento.md).

O [roteiro de análise](docs/leitura_resultados.md) explica como comparar probabilidades, contexto, prazo, moedas e utilidade econômica antes de formular outro ciclo.

**Primeiro ciclo concluído em 18/10/2026:** 96/96 células auditadas, 192 ajustes neurais e 16 ajustes únicos de AR(1), identidade `4e232a796fcda0ea34c3`. O [relatório completo](historico/analises/ciclo_001_resultados.md) apresenta todas as combinações, inclusive perdas e ausência de operações. Mamba e LSTM ficaram próximos; não houve superioridade demonstrada de Mamba nem rentabilidade consistente. A [proposta do ciclo 002](historico/ciclos/ciclo_002_proposto.md) está documentada e não foi executada. A avaliação final continua bloqueada.

## Execução

O ambiente científico usa WSL Ubuntu, Python 3.12, PyTorch CUDA e Mamba oficial. O Python padrão do Windows não representa esse ambiente. Nesta máquina o interpretador qualificado está em `~/.venvs/cc/bin/python`. Executar os comandos abaixo no WSL, a partir da raiz do repositório:

Versões, proveniência dos wheels e limites de reprodução estão em [ambiente CUDA](docs/ambiente_cuda.md).

```bash
~/.venvs/cc/bin/python -m unittest discover -s tests -v
~/.venvs/cc/bin/python run_barreiras.py planejar
~/.venvs/cc/bin/python run_barreiras.py coletar
~/.venvs/cc/bin/python run_barreiras.py preparar
~/.venvs/cc/bin/python run_barreiras.py qualificar
~/.venvs/cc/bin/python run_barreiras.py auditar-dados
~/.venvs/cc/bin/python -u run_barreiras.py treinar --somente-pilotos
~/.venvs/cc/bin/python -u run_barreiras.py treinar
```

A primeira coleta usa 2021–2023 e verifica 144 arquivos mensais. A pipeline registra lacunas e minutos interrompidos e produz uma nova identidade de dataset. O comando de treino começa pelos dois casos de qualificação e depois percorre a grade. Células concluídas com a mesma identidade são verificadas e reutilizadas; falhas não são apagadas. Não iniciar dois executores para a mesma identidade.

A CLI rejeita folds finais. A abertura final exige congelamento do estudo e declaração de exposição aos dados; rodar mais ciclos de desenvolvimento não libera essa etapa automaticamente.

Durante a execução, `python scripts/estado_grade.py dados/experimentos/barreiras_<identidade>` mostra contagens e progresso sem lançar outro treino. No WSL, também confere o lock do executor; um estado escrito como “treinando” não prova sozinho que o processo continua vivo. Não reiniciar após um simples timeout de observação.

Para recalcular a consolidação, usar `run_barreiras.py consolidar dados/experimentos/barreiras_<identidade>`. O comando verifica hashes e produz tabelas por célula, contrastes pareados, efeito de contexto, incerteza por blocos e curvas concatenadas. Uma grade parcial é identificada como parcial; uma lacuna financeira impede publicar um retorno integral dessa estratégia.

Ao encerrar a grade, executar também `scripts/auditar_resultados.py <diretorio_do_ciclo>`, `scripts/auditar_controles.py <diretorio_do_ciclo>` e `scripts/diagnosticar_sinais.py <diretorio_do_ciclo>` com o Python científico. A auditoria suplementar exige a grade completa; `--parcial` permite uma inspeção intermediária sem certificá-la como concluída. Esses comandos conferem e analisam artefatos existentes, sem treinar ou escolher novos parâmetros.

`scripts/descrever_amostras.py <diretorio_do_ciclo>` verifica o dataset e descreve largura das barreiras, classes e duração por moeda/prazo/fold/partição, com conferência contra previsões já auditadas. Também preserva a contagem das origens operacionais cujo futuro não foi observado. A existência dessa descrição não significa que todos os modelos foram executados.

Figuras vetoriais podem ser geradas sem alterar o ambiente científico: em `dataview/`, executar `node scripts/gerar-figuras.mjs ../dados/experimentos/barreiras_<identidade>`. São gráficos dos resultados reais consolidados, com células ausentes sinalizadas e identidade no manifesto.

O resumo portátil da primeira grade foi gerado com `scripts/resumir_ciclo.py dados/experimentos/barreiras_4e232a796fcda0ea34c3 --destino historico/analises/ciclo_001_completo`. Esse comando somente lê artefatos auditados e exporta tabelas e proveniência; não treina. As quantidades e regras desse agregador correspondem ao ciclo inicial, não a grades futuras arbitrárias.

## Registro e melhoria

`configuracoes/ciclo_001.json` contém todos os parâmetros de redes e treinamento, sem configuração global oculta. Um ciclo posterior pode alterar a grade ou a configuração interna do Mamba, com hipótese, orçamento e critério de comparação definidos antes de executar. Resultados ruins, falhas e correções continuam no registro.

`historico/execucoes/` contém os resumos leves e o estado de cada tentativa. `dados/experimentos/` guarda checkpoints, fontes, scalers, previsões, curvas, ordens e auditorias; esses arquivos não entram no Git e precisam de backup.

## Interface

Em `dataview/`, usar `npm install` e `npm run dev`. A página lê os registros reais e distingue preparação, treino, falha e conclusão auditada. Não usa placares simulados. Verificações: `npm test`, `npm run lint` e `npm run build`.

## Limites

Acerto de previsão não garante lucro. O simulador opera comprado ou em caixa, sem alavancagem. Custos são hipóteses declaradas; não reconstrói livro de ofertas ou garante execução de stops. Lacunas que impeçam determinar uma saída tornam a trajetória financeira não auditável, sem remover a operação retrospectivamente.
