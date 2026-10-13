# Entrega 5 — Mamba base e treinamento pareado

**Estado em 13/10/2026:** implementação concluída para desenvolvimento D1–D4. O [piloto BTCUSDT/1d/D1 em CPU](resultados_piloto_BTC_D1_cpu.md) foi executado e auditado pelo agente após autorização do usuário. Aceite funcional CPU concluído, incluindo recarga dos checkpoints e reprodução exata das previsões. Mamba oficial/CUDA permanece pendente por indisponibilidade do ambiente compatível nesta máquina. Não há avaliação final.

## O que esta entrega acrescenta

**Revisão posterior em 13/10/2026:** o aceite funcional permanece registrado, mas a interpretação científica do piloto está **em revisão**. O [diagnóstico](../../../historico/analises/2026-10-13_diagnostico_mamba.md) identifica diferença na inicialização do fallback frente à referência oficial e baixa discriminação já no treino. Não foi demonstrada a causa do resultado nem executado novo treinamento. Qualificar a implementação antes de ampliar a grade. A [linha do tempo](../../../historico/LINHA_DO_TEMPO.md) preserva as evidências e incertezas.

O classificador Mamba preservado agora pode ser executado pelo mesmo treinador da baseline LSTM. Cada célula usa amostras e scaler compartilhados; os modelos e otimizadores são independentes. O fluxo acompanha o [protocolo 1.6](../../protocolo_experimental.md).

A **[matriz de configurações e períodos](matriz_experimental.md)** reúne as 16 combinações moeda/candle, janelas, exemplos de timestamps, etapas de desenvolvimento e os 12 folds. A interface apresenta o mesmo planejamento na seção **Configurações experimentais**. Janela de 7 dias é o passado de um exemplo, não o histórico total usado para treinar o modelo.

| Componente | Responsabilidade |
|---|---|
| `modelo/mamba_modelo.py` | Classificador com backend explícito `pytorch` ou `oficial`; a interface antiga ainda aceita seleção automática |
| `modelo/lstm_modelo.py` | LSTM unidirecional, duas camadas, largura 32/64, dropout entre camadas 0,1, último passo e saída de duas classes |
| `experimentos/dados.py` | Verificação de hashes, timestamps, rótulos e continuidade; scaler no treino; janelas sob demanda |
| `experimentos/treinamento.py` | Treino, early stopping, checkpoint e previsão em ordem cronológica |
| `experimentos/execucao.py` | Execução pareada, reaproveitamento do AR(1), registros e proteção contra sobrescrita |
| `experimentos/consolidacao.py` | Médias por fold, diferenças pareadas e PT concatenado de desenvolvimento |
| `experimentos/auditoria.py` | Verificação de datas, limiares, metadados e recálculo das métricas diretamente dos parquets |
| `experimentos/planejamento.py` | Tabelas de janelas e folds usadas pela documentação e interface |
| `run_treino.py` | CLI de planejamento e execução; piloto pelo agente expressamente autorizado pelo pesquisador |
| `run_avaliacao.py` | Consolidação de execuções explicitamente selecionadas |

## Como executar o primeiro piloto

Na raiz do repositório, com o ambiente Python ativo e as dependências de `requirements.txt` instaladas:

```powershell
python run_treino.py --configuracao configuracoes/treino_piloto_cpu.json --planejar
python run_treino.py --configuracao configuracoes/treino_piloto_cpu.json
```

O primeiro comando apenas lista a grade. O segundo executa AR(1), LSTM e Mamba para BTCUSDT, candles diários, contexto de 7 dias, próximas 24h, fold D1 e seed 42. A configuração inicial usa cinco features OHLCV, StandardScaler e Mamba PyTorch em CPU. A execução lê o dataset `daeec76f001afb50a8fe` existente; não é necessário coletar ou processar novamente por causa desta entrega.

No piloto executado, o treinador mediu 1,05 s para LSTM e 4,59 s para Mamba; a invocação pareada durou cerca de 13,51 s. Esses tempos não estimam a grade intradiária completa. Memória RAM não foi medida. O piloto usa o protocolo completo de até 100 épocas com parada antecipada; não é um resultado de teste final.

## Regras efetivamente implementadas

1. Validar a configuração e rejeitar chaves desconhecidas. Somente D1–D4/seed 42 estão liberados; não existe parâmetro para liberar F1–F8 nesta etapa.
2. Conferir o manifesto, hashes e contagens dos arquivos consumidos, identidade do par/candle, dimensão das janelas, datas e classe derivada do retorno. Rejeitar contexto ou alvo que atravesse uma lacuna.
3. Separar os blocos por datas e aplicar a purga estrita da Entrega 3. Treino ou validação sem ambas as classes interrompem a execução, porque não há seleção de checkpoint por BA válida.
4. Ajustar StandardScaler ou MinMaxScaler nos candles únicos das entradas de treino. Aplicar o mesmo estado às duas redes e aos três blocos, sem clipping do futuro.
5. Criar pesos e otimizador novos por rede, fold e seed. AdamW, taxa 0,0002, weight decay 0,001, batch efetivo 32, cross-entropy sem pesos, clipping da norma em 1, máximo de 100 épocas e paciência de 10 épocas.
6. Selecionar a época pela BA de validação; empate conserva o checkpoint mais antigo. O bloco de teste de desenvolvimento é consultado apenas após a seleção. A loss de treino e a BA/F1 de validação são registradas a cada época.
7. Prever alta somente quando `p(alta) > 0,5`. Guardar probabilidade, classe, rótulo e timestamps. Não transportar estado LSTM entre janelas ou batches.
8. Comparar os três métodos por `par`, `origem_utc` e `alvo_fim_utc`, exigindo cobertura e rótulos iguais. AR(1) principal usa seu próprio parquet diário, sem aproveitar índices de outro parquet.

O batch lógico de treino continua com 32 amostras. Em `microbatch=8`, por exemplo, os gradientes de quatro parcelas são acumulados e normalizados pelo tamanho real do batch antes do passo do otimizador. O batch parcial do fim da época usa seu próprio tamanho; não é descartado. Somente o DataLoader de treino embaralha. Validação/teste usam microbatches em ordem.

## Artefatos e reprodutibilidade

Cada execução gera `dados/experimentos/pareado_<identidade>/`:

```text
estado.json                         # em_execucao, concluido, falhou ou interrompido
configuracao.json                   # configuração da invocação, inclusive em falhas
ambiente.json                       # versões e hardware registrados no início
codigo_fonte.json                   # fontes efetivas, inclusive alterações sem commit
protocolo_executado.md              # cópia exata do protocolo usado na execução
normalizador.json                   # features, estatísticas e período de ajuste
indices_ajuste_normalizador.npy      # candles únicos que participaram do ajuste
lstm/melhor.pt                      # pesos, otimizador, época e configuração
lstm/historico.json
mamba/melhor.pt
mamba/historico.json
previsoes_<modelo>_<bloco>.parquet    # ar1/lstm/mamba × validacao/teste
resultado.json                      # métricas, diferenças, PT, ambiente e hashes
```

A identidade considera célula, configuração efetiva, dados, código, protocolo, versões e ambiente computacional registrado. Reexecutar uma célula concluída com a mesma identidade audita os arquivos e recalcula as métricas antes de reutilizar o resultado. Alterações de código/protocolo produzem outra identidade. O hash de código normaliza quebras CRLF/LF e cobre também as CLIs e `requirements.txt`; o snapshot preserva as fontes efetivamente lidas. Uma execução incompleta fica preservada; para reiniciar do começo em uma pasta nova:

```powershell
python run_treino.py --configuracao configuracoes/treino_piloto_cpu.json --nova-tentativa
```

Não há retomada de uma época interrompida. A opção inicia um treino novo com a mesma seed e mantém os artefatos anteriores. A consolidação rejeita duas tentativas da mesma célula/fold na mesma análise; a escolha de quais execuções compõem o relatório precisa ser explícita, sem selecionar a melhor BA retrospectivamente.

O AR(1) é armazenado em `dados/experimentos/ar1_compartilhado/` por moeda, frequência da tarefa e fold. Seus parâmetros não dependem da seed nem dos hiperparâmetros das redes; as cópias nas execuções pareadas não são novos ajustes independentes.

## Desenvolvimento em WSL/CUDA

**Pendência de ambiente:** na máquina verificada em 13/10/2026, a GPU é AMD RX 6600, CUDA está indisponível e `~/.venvs/cc` não existe no Ubuntu. Os comandos abaixo são instruções para um ambiente CUDA compatível; não foram executados nesta máquina. O piloto validado usa CPU/PyTorch. Depois de qualificar o backend oficial em uma célula piloto, conferir a grade:

```bash
python run_treino.py --configuracao configuracoes/treino_desenvolvimento_wsl.json --planejar
python run_treino.py --configuracao configuracoes/treino_desenvolvimento_wsl.json
```

Essa configuração contém 64 células (4 ativos × 4 resoluções × 4 folds) e **128 treinos neurais**. Usa Mamba oficial e CUDA explicitamente. O programa falha se o backend solicitado não estiver disponível; não muda de implementação silenciosamente. As versões de Python, PyTorch, CUDA, cuDNN, Mamba e bibliotecas de dados, GPU, sistema, commit e hash dos arquivos de código são registrados.

Seeds e opções de determinismo são configuradas, mas kernels podem emitir avisos de operação não determinística. A igualdade da interface dos dois backends Mamba não demonstra equivalência numérica; o piloto CPU não substitui a verificação do backend oficial. O orçamento final ainda depende de medir tempo e memória no desenvolvimento.

## Como consolidar e visualizar

Informe os diretórios reais impressos ao final de suas execuções. Exemplo de formato, substituindo os nomes entre marcadores:

```powershell
python run_avaliacao.py --execucoes dados/experimentos/pareado_<id_D1> dados/experimentos/pareado_<id_D2> --saida dados/experimentos/resumo_desenvolvimento_01
```

O comando exige os artefatos obrigatórios, valida seus hashes e recalcula métricas, diferenças e PT usando as previsões de validação/teste. Também confere datas UTC, purga, limiares, rótulos, backend e configuração. Resumo divergente das previsões interrompe a consolidação. Configurações, backends, versões e hardware diferentes ficam em grupos distintos. Médias dão pesos iguais aos folds; faltantes são explícitos e não viram zero. O comando salva `resumo.json` e `metricas_por_fold.csv`. O PT concatenado nessa etapa é exploratório sobre o desenvolvimento; não é o PT final das três seeds.

Resultados `entregas45-v1` anteriores à preservação das fontes continuam auditáveis pelos arquivos existentes, mas não recebem retroativamente um snapshot de código. Não há alegação de reconstrução exata desses resultados somente a partir de um commit com alterações locais.

Na pasta `dataview`, executar `npm run dev` e abrir `http://localhost:3000`. A seção Resultados lê os resumos `pareado_*` concluídos e mostra métricas por execução, configuração e fold. A matriz de 2024–2025 continua pendente. O painel usa rotas Next.js locais, sem servidor Python separado.

O painel confere BA, accuracy e F1 contra a matriz de confusão do resumo, além de suportes, diferenças e backend. Isso detecta inconsistências de apresentação; a auditoria completa continua sendo feita por `run_avaliacao.py`, que lê os parquets. A seção Configurações experimentais tem filtros de moeda, horizonte, contexto e entradas, exemplo de origem/alvo em UTC, sequência E0–E4 e tabelas D1–D4/F1–F8. Exibir os folds finais no planejamento não libera sua execução.

Para atualizar as tabelas após uma revisão autorizada do protocolo: `python scripts/atualizar_plano_experimental.py`. Esse utilitário só gera JSON/Markdown, sem ler dados de mercado ou treinar. A suíte verifica que os arquivos gerados correspondem aos contratos Python.

## Critérios de aceite e pendências

### Verificações anteriores ao piloto em 13/10/2026

- `python -m unittest discover -s tests`: 43 testes aprovados, incluindo 18 da infraestrutura experimental; nenhum treinamento. A suíte verifica contratos, causalidade do scaler/fallback, alinhamento temporal, PT, integridade, métricas adulteradas, snapshots e consolidação.
- `npm run test`: oito testes do leitor de resultados, incluindo métricas inconsistentes, suporte de classes, backend incorreto e bloqueio de folds finais.
- `npm run lint` e `npm run build`: aprovados, incluindo TypeScript e as novas rotas Next.js.
- Interface conferida no navegador em desktop e celular: seis seções, matriz filtrável, contexto de 14 dias/8 features, troca para próximo candle com retorno obrigatório a 7 dias, planejamento F1–F8 e estado sem execuções locais. Sem erros de console durante a conferência; sem transbordamento horizontal da página nos cenários móveis inspecionados.
- Leitura rápida do dataset real: D1/1d dos quatro ativos apresentou 495 janelas de treino, 91 de validação e 82 de avaliação. Conferidos hashes, entradas OHLCV/ampliadas e os dois scalers. Para BTC/D1, as quatro resoluções com 7/14 dias tiveram população, timestamps e rótulos pareados, com oito features finitas. Essas verificações não alteraram os dados e não ajustaram modelos preditivos.

Essas verificações confirmam os contratos e a implementação examinada. Não substituem o piloto de treinamento nem a validação do Mamba oficial/CUDA.

### Aceite das Entregas 4 e 5

- [x] LSTM e Mamba com entradas explícitas e treinador compartilhado.
- [x] Dados/normalização causais, alinhamento por datas e métricas separadas.
- [x] Checkpoints, histórico, versões, backend, hashes e proteção contra sobrescrita.
- [x] Verificações rápidas sem ajuste de modelos: dados sintéticos, forwards das redes, causalidade do fallback e testes de métricas.
- [x] Executar piloto CPU, conferir históricos, tempos, checkpoints e previsões. Auditoria e recarga independente aprovadas. RAM de CPU não medida; campo CUDA nulo explicitado.
- [ ] Validar Mamba oficial em ambiente CUDA compatível e medir custo da grade intradiária. Ambiente indisponível na máquina atual.

**Estado do aceite:** o piloto CPU está concluído e auditado. A autorização excepcional do usuário foi registrada em `AGENTS.md` e permitiu executar `run_treino.py`. O requisito específico do backend oficial continua pendente por ambiente; o piloto CPU não é rotulado como validação CUDA. Consulte o [relatório e as evidências](resultados_piloto_BTC_D1_cpu.md).

Procedimento utilizado para o aceite CPU e para futuras execuções intencionais:

1. Executar a configuração `configuracoes/treino_piloto_cpu.json` pelos comandos desta entrega. Ela treina LSTM e Mamba na mesma célula BTCUSDT/1d/D1 e inclui AR(1).
2. Guardar o diretório `pareado_<identidade>` informado ao final. Conferir `estado.json` concluído, os dois checkpoints, os dois históricos e os seis arquivos de previsões. A configuração CPU é um piloto do backend PyTorch, não uma validação do backend oficial.
3. Consolidar esse diretório com `run_avaliacao.py --execucoes <diretorio_real> --saida <diretorio_novo>`. A auditoria deve terminar sem divergências de hashes, datas, rótulos, metadados ou métricas.
4. Documentar BA, F1 macro, matriz de confusão, recalls, diferenças entre modelos e PT, incluindo casos em que PT seja indisponível. Registrar número de épocas, época escolhida e tempo de cada rede. O código registra pico de memória CUDA somente em GPU; em CPU esse campo é nulo, e não uma medição de RAM.
5. Antes da grade WSL, validar uma célula do backend oficial/CUDA, identificada separadamente. Conservar o piloto CPU e suas limitações no relatório.

Uma BA baixa não impede o aceite técnico. A aceitação depende da execução íntegra e da documentação; a qualidade preditiva será analisada nas etapas seguintes. Um piloto de uma célula também não constitui o resultado de toda a matriz experimental.

### Trabalho das entregas posteriores

As atividades abaixo pertencem às Entregas 6–9 e não são código faltante para iniciar o piloto das Entregas 4 e 5:

- [ ] Executar os experimentos das Entregas 6–8 e registrar seleção/congelamento.
- [ ] Implementar/liberar a etapa final somente após o registro de congelamento e exposição prévia.

A implementação e o aceite empírico do piloto CPU estão documentados. A qualificação oficial/CUDA e a grade das próximas entregas permanecem explicitamente pendentes.
