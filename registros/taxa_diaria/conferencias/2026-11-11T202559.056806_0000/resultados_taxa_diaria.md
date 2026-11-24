# Ablação da taxa inicial diária — resultado e interpretação

Execução `64c5a9532894252c7b88`, concluída em **11/11/2026 às13h17 BRT**, após cerca de6h15. Reduzir a taxa inicial de Adam de0,01 para0,001, mantendo `weight_decay=0`, **não melhorou a receita estudada**. O erro aumentou nas três seeds; as médias operacionais também pioraram. Não promover esta candidata nem concluir que taxas menores são sempre piores.

[Protocolo congelado](protocolo_taxa_diaria.md) · [Execução](../registros/taxa_diaria/execucao.json) · [Comparação publicada](../dados/experimentos/taxa_diaria_64c5a9532894252c7b88/publicacao/comparacao.json) · [Conferência independente](../registros/taxa_diaria/conferencia_posterior.json).

## O que foi comparado e conferido

Referência `8a0aeee4d78503b7f50d` herdada, sem novo treino; candidata com taxa0,001. Mesmo BTC, candles diários, contexto14dias, seis canais padronizados no treino, alvo retorno simples diário, arquitetura, Adam, lote32,1000épocas e StepLR100/gamma0,5. Treino2020–2023; validação2024 seleciona checkpoint; teste2025 já conhecido, portanto retrospectivo. O scan herdado percorre seis canais; não se altera esse eixo nesta ablação.

Três ajustes principais novos(seeds42/17/2026) e controle42, todos com1000épocas. Controle aprovado com histórico, época, pesos e previsões exatos antes das seeds17/2026. Épocas selecionadas: **2,4,5**. A referência selecionara69,25,32. Controles ficam fora das médias.

Conferência posterior sem treino, nova inferência ou reexecução do backtest:352arquivos publicados,119fontes atuais/congeladas,409arquivos da referência/releitura financeira preservados, seis séries de previsão, seleção pelo mínimo de validação,70carteiras e14.896operações. Métricas e intervalos recalculados; quantidades, preços de entrada/saída, taxas, funding dos ledgers, saldos e drawdown do envelope conferidos. As três referências operacionais mantiveram saldos idênticos aos da publicação de custos vigente. O recibo explicita os limites da verificação.

O launcher Windows gravou `exit_code:null`, portanto esse campo isolado não prova sucesso. A conclusão foi estabelecida pelo processo encerrado, fechamento íntegro, cobertura e conferência dos artefatos. O registro original permanece intacto.

## Previsões: média das três seeds

MSE está em retorno decimal ao quadrado: menor é melhor. MAE/RMSE abaixo estão em pontos percentuais de retorno diário. O RMSE apresentado é a média dos RMSEs individuais, não a raiz da média dos MSEs.

|Período e métrica|Naive|Taxa0,01, referência|Taxa0,001, candidata|
|---|---:|---:|---:|
|2024, MSE|0,000762158|0,000763718|0,000864593|
|2025, MSE|0,000475433|0,000502583|0,001027829|
|2025, MAE(p.p.)|1,5633|1,6262|2,4243|
|2025, RMSE(p.p.)|2,1804|2,2414|3,0997|
|2025, acerto balanceado|Não se aplica ao sinal zero|49,52%|50,38%|

Em2025, o MSE da candidata é **104,51% maior que o da referência e116,19% maior que o Naive**. Pequena melhora de acerto direcional não compensa erros maiores de magnitude. Naive prevê preço inalterado/retorno zero; seu acerto direcional zero registrado pela comparação exata de sinais não deve ser interpretado como classificador que erra todas as altas e quedas.

|Seed|MSE referência|MSE candidata|Retorno líquido referência|Retorno líquido candidata|
|---|---:|---:|---:|---:|
|42|0,000477219|0,000531898|+2,08%|−40,81%|
|17|0,000508877|0,000765417|−29,20%|−45,13%|
|2026|0,000521654|0,001786171|−37,44%|−30,89%|

A seed2026 agrava bastante a média de erro, mas a piora preditiva ocorre nos três pares; não é somente uma seed desfavorável. O IC95% exploratório principal(blocos14dias,2000réplicas pareadas de seeds/dias) da diferença candidata−referência de MSE é **[0,00006414;0,00127194]**. Os blocos7/28dias também ficam acima de zero. Isso sustenta piora no recorte observado, sem corrigir a busca adaptativa anterior ou fornecer certeza universal.

## Operações de futuros: política original de saída24h

Mesma política nos dois braços: decisão diária, filtro±0,20%,95%nocional, latência1min, fechamento24h depois; comissão0,05% e slippage **provisório0,01% por lado**, funding observado. São350decisões entre15/01 e30/12/2025, não o ano civil inteiro. Esta ablação conserva a saída24h para isolar a taxa; a [avaliação de continuidade das posições](adr/0037-continuidade-posicoes-diarias.md) é outro contraste, com outra referência padronizada, e não substitui estas carteiras.

|Média de três carteiras independentes|Referência0,01|Candidata0,001|
|---|---:|---:|
|Retorno líquido2024, validação|+36,01%|−23,44%|
|Retorno líquido2025|−21,52%|−38,94%|
|Drawdown máximo2025, média por seed|38,90%|48,89%|
|Operações2025, média|196|309|
|Dias posicionado2025|56,00%|88,29%|
|Comissões2025, médiaUSDT|1.492,90|2.644,38|
|Funding líquido2025, médiaUSDT|−47,32|−302,18|

Naive permanece em caixa e tem retorno/drawdown zero sob essa política. Média de retornos não é retorno do ensemble, nem drawdown médio é o drawdown de uma curva média. A piora média operacional é17,42p.p.; o IC95% da diferença de crescimento log diário inclui zero(−0,002935 a+0,001300 no bloco14). Portanto, descrever **piora operacional observada**, com incerteza considerável, sem afirmar confirmação estatística da diferença de lucro. A seed2026 perde menos dinheiro embora preveja pior, mostrando novamente que MSE e retorno financeiro são eixos distintos.

## O que aprendemos

As previsões ganharam dispersão, mas não informação útil demonstrada. Em2025, o desvio previsto passou de18,31% para53,15% do desvio observado; a correlação média permaneceu negativa(−0,0224→−0,0471). A candidata previu em média **+1,5026% ao dia**, enquanto o retorno observado médio foi aproximadamente−0,0012%. Esse viés de alta acompanha maior exposição comprada e giro. São descrições dos artefatos, não identificação causal definitiva do mecanismo interno.

Os ramos Mamba continuaram funcionalmente ativos nas sondas de32janelas de treino. Ao longo das1000épocas, a perda de treino chegou perto do piso0,0001 introduzido pelo epsilon da raiz, enquanto o erro de validação final ficou acima do mínimo selecionado nas primeiras épocas. Esse padrão é compatível com forte sobreajuste. Mais épocas foram executadas conforme o protocolo, mas não selecionadas por seu número ou resultado de teste.

Conclusão para o artigo: **neste desenho, reduzir somente a taxa inicial com penalização zero não resolveu a generalização e aumentou o erro de retorno**. Ativar o SSM, ampliar a variação dos sinais ou acertar um pouco mais a direção não garante calibração, menor MSE ou lucro. Encerrar esta hipótese com resultado negativo documentado; não buscar outra seed favorável nem substituir a referência. O [diagnóstico consolidado](../registros/taxa_diaria/diagnostico.json) e a avaliação operacional separada ajudam a distinguir aprendizado do modelo de política de execução.

Limites: três seeds, um instrumento nesta ablação, divisão fixa, validação reutilizada e2025retrospectivo, custos hipotéticos e simulação sem certificação de liquidação oficial. Não houve avaliação2026, novas ordens ou novo treinamento após o encerramento. Preservação local não comprova backup externo. O ensaio de cache economizou apenas0,71% em média e não foi adotado; não há alegação de aceleração substancial. A cronometragem registrada foi do ajuste sintético completo em ordemABBA; a decomposição separada em treino/validação/escrita prevista como investigação técnica não foi produzida. Essa limitação não altera a receita executada, pois a otimização foi rejeitada.
