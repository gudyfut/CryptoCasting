# Como ler o primeiro ciclo

Este roteiro aplica os critérios do protocolo 2.1; não acrescenta uma regra de seleção depois de observar o resultado. Os dois primeiros casos de BTC verificam execução e custo. Não bastam para concluir qual modelo, moeda, contexto ou prazo é melhor.

## Primeiro: confirmar o que foi executado

Consultar a identidade do ciclo, os hashes do dataset/código, os períodos e a situação da auditoria. A grade inicial completa tem 96 células pareadas e 192 ajustes neurais. Uma célula envolve uma moeda, contexto, prazo, fold e seed. AR(1) é reutilizado entre contextos; isso não cria novas réplicas independentes.

Falhas, tentativas interrompidas, ausência de operações e resultados financeiros não observáveis são categorias diferentes. Todas devem permanecer visíveis. Um arquivo de checkpoint não comprova que a avaliação foi concluída.

Os tempos de execução do ciclo inicial foram medidos com auditorias, consolidações e tarefas do painel ocorrendo em paralelo na mesma máquina. São custos observados nessas condições, sujeitos à concorrência por CPU e disco; não sustentam, isoladamente, uma conclusão controlada de velocidade entre arquiteturas. Quantidade de parâmetros, épocas realizadas e configuração ajudam a interpretar o custo. Um estudo específico de desempenho computacional exigirá medições em condições controladas, documentadas separadamente.

## Segundo: examinar probabilidades

Comparar log-loss de Mamba com LSTM, AR(1) e a frequência constante estimada no treino. A diferença Mamba menos comparador favorece Mamba quando é negativa. Olhar também Brier, calibração, frequência das classes e cada fold. Uma previsão sempre inclinada à classe mais comum pode ter acurácia razoável e probabilidades pouco úteis.

Os escores de teste são calculados nas mesmas origens. Não comparar valores obtidos em populações diferentes sem declarar a mudança. Os intervalos por blocos preservam parte da dependência temporal; milhares de origens horárias com horizonte semanal não equivalem a milhares de apostas independentes.

## Terceiro: separar os efeitos

Para contexto, comparar W24 e W168 dentro da mesma moeda, prazo, fold e seed. Ambos recebem a mesma informação resumida de volatilidade de sete dias. A pergunta é se sete dias de sequência detalhada ajudam além desse resumo.

Para prazo, apresentar H1, H24 e H168 separadamente. Prazo maior também significa barreiras mais largas e dimensionamento menor da posição. Uma diferença de resultado não identifica isoladamente o efeito da duração. O tempo realizado de operação pode ser muito menor que o prazo máximo.

A frequência das três classes também muda com o prazo. Por isso, log-loss bruto menor em H1 do que em H168 não demonstra, sozinho, que H1 é a tarefa mais útil ou que sua rede aprendeu mais. Examinar a referência de frequência do treino e os comparadores dentro de cada tarefa, além da avaliação econômica. O critério global da grade continua sendo a média predefinida entre células; esta ressalva orienta a interpretação, sem trocar a métrica após observar resultados.

Para moedas, usar as origens comuns e os mesmos critérios. Descrever volatilidade observada; não presumir uma ordem entre ativos. Não confundir o efeito da moeda com um único trimestre favorável.

## Quarto: verificar utilidade econômica

Boa probabilidade não é sinônimo de lucro. Consultar retorno líquido, curva marcada a mercado, drawdown, exposição, número de operações e custos. Comparar com a mesma regra de barreiras sem filtro, comprar/manter e caixa. A política sem filtro ajuda a identificar se o modelo acrescenta valor à própria regra de saídas.

Uma estratégia que não opere pode preservar capital, mas não demonstra capacidade de selecionar negócios lucrativos. Um prazo curto pode ser inviável após custos. Não mudar taxas ou limiar retrospectivamente para produzir entradas. A sensibilidade de custos usa os mesmos sinais e frações, com nova contabilidade.

Se uma posição escolhida atravessar um percurso não observado, o resultado integral daquela simulação fica indisponível. Não publicar apenas o trecho anterior ou os outros folds como se fossem o ano completo. É possível analisar separadamente os folds verificáveis, identificando explicitamente suas datas e a ausência do restante.

Há um [complemento descritivo posterior para comprar/manter](../historico/analises/complemento_comprar_manter.md): uma saída fixa permite conferir o retorno entre pontas observadas, preservando a indisponibilidade do risco intermediário quando há lacuna. Essa distinção não recupera saídas por barreiras nem altera os estados do contrato executado. Comparações de exposição e risco continuam necessárias.

## Quinto: propor outro ciclo

Após concluir a grade, registrar o padrão observado e uma hipótese específica. Exemplos: maior contexto só ajuda em um prazo; uma rede maior melhora probabilidades mas aumenta muito o custo; há baixa calibração apesar de boa classificação. Então escolher um fator para a próxima investigação e registrar configuração, orçamento, referência e critério antes de executar.

Mudanças internas do Mamba são ablações de capacidade/dinâmica, não substituições silenciosas da primeira referência. A validação continua escolhendo a época. Os testes DB consultados orientam o desenvolvimento e precisam ser descritos como tal. Confirmar candidatos em outras seeds antes do congelamento; não escolher apenas a seed de maior retorno.

B1–B4 continuam bloqueados durante essa busca. Sua abertura exige registrar a configuração congelada e esclarecer exposição histórica aos anos de avaliação. Apagar arquivos não torna um período previamente consultado independente.

## Arquivos de análise

- `consolidacao/celulas.csv`: todas as células concluídas, métricas e estado financeiro.
- `consolidacao/resumo.json`: cobertura da grade, tentativas, ausências e contrastes globais quando completa.
- `consolidacao/efeito_contexto.json`: diferenças pareadas W24 menos W168.
- `consolidacao/financeiro_concatenado.json`: cada estratégia/seed, curvas e intervalos; nenhum retorno integral quando houver fold ausente ou não verificável.
- `consolidacao/diagnostico_sinais.csv`: confiança, viabilidade nominal após custos e sinais antes do controle de posição. Gerado por `python scripts/diagnosticar_sinais.py <diretorio_do_ciclo>`, sem mudar a estratégia.
- `consolidacao/auditoria_suplementar.json`: conferência dos resumos contra artefatos, fontes, ambiente, checkpoints e recálculo de métricas. A conclusão integral só é aprovada quando a grade esperada está completa.
- `consolidacao/controles/`: curvas e conferência independente de comprar/manter por moeda e fold, incluindo a indisponibilidade de métricas quando houver lacuna.
- `consolidacao/descricao_amostras.csv`: largura efetiva das barreiras, frequências dos três desfechos e quantis de duração para cada moeda/prazo/fold/partição. O contexto não duplica esta tabela porque as origens e os alvos são comuns. As durações descrevem todas as origens preditivas, não somente negócios escolhidos por um modelo; os limites inferior/superior preservam a incerteza dentro do minuto.
- `consolidacao/populacoes_operacionais.csv`: quantidade de origens causais, inclusive desfechos não observados. A diferença para a população preditiva inclui a purga máxima comum, além da qualidade dos dados. Não usar essa diferença para excluir entradas retrospectivamente.
- `consolidacao/figuras/`: gráficos vetoriais com identificação de resultados parciais e manifesto de origem.

Esses caminhos são relativos ao diretório identificado do ciclo em `dados/experimentos/`. Previsões, ordens, scalers, fontes e auditorias detalhadas ficam nos subdiretórios de cada tentativa.
