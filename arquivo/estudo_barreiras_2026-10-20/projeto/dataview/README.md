# Portal científico do estudo

Revisão de 19/10/2026: a página `/` organiza os seis marcos concluídos do ciclo inicial, sua cronologia e pendências. `/previsoes` é um explorador de todas as previsões reais dos três modelos, com gráfico financeiro Lightweight Charts 5.1.0, candles de 1/5/15/60 minutos, volume, probabilidades, limites e desfecho da origem selecionada. Zoom, cursor, lista paginada, filtros, busca por data UTC, link por origem, matriz de confusão e métricas por célula. O projeto continua local; nenhuma publicação externa foi realizada.

## Exportação do explorador

Na raiz do repositório, com Python, NumPy, pandas e suporte Parquet disponíveis:

```bash
python scripts/exportar_explorador.py
```

No ambiente WSL verificado nesta sessão, o executável é `/home/murilorfm/.venvs/cc/bin/python`. Executar o arquivo no checkout montado, sem modificar o ciclo científico. A exportação verifica o relatório fechado, os hashes de integridade, probabilidades, timestamps, rótulos e métricas de 96 células × três modelos. Gera `dataview/.dados/explorador/` (ignorado pelo Git) e o recibo `historico/qualificacoes/explorador_previsoes_2026-10-19.json`. Não treina, não recalibra e não executa backtests.

São 189.792 previsões por modelo somando as configurações; 7.908 origens distintas por combinação. A exportação contém as previsões de teste de desenvolvimento e preços de 24/12/2022 a 31/12/2023; os últimos dias de 2022 são apenas contexto visual. As origens operacionais e B1–B4 não são expostos. O servidor lê os pacotes locais sob inventário fechado, verifica seu SHA-256 e agrega candles somente quando todos os minutos existem. Dados ausentes geram mensagem explícita, nunca substituição fictícia.

Para outra máquina, copiar os artefatos científicos e executar o exportador, ou copiar a exportação completa com o recibo correspondente. Não sincronizar apenas o recibo. Os testes integrais do explorador exigem essa exportação; eles recalculam as métricas de todas as 288 séries e verificam uma lacuna real.

```bash
# Dentro de dataview/
npm test
npm run lint
npm run build
npm run dev
```

Os documentos `docs/registro_entregas.md` e `docs/guia_avaliacao.md` registram a organização e interpretação. A implementação financeira e o protocolo executado permanecem preservados. Uma apresentação não certifica rentabilidade ou teste final independente.

## Conteúdo didático

Além dos três laboratórios originais, `AvaliacaoDidatica.tsx` apresenta matriz de confusão interativa, comparação de acurácia comum/balanceada, calibração e efeito dos custos. Todos os exemplos são identificados como fictícios. As probabilidades reais mantêm a precisão original; valores muito pequenos não são apresentados como zero por arredondamento. As métricas por célula usam todas as suas origens, independentemente dos filtros visuais.

TradingView Lightweight Charts™ — Copyright (с) 2025 TradingView, Inc. https://www.tradingview.com/ — Apache 2.0. A atribuição fica visível no gráfico e na proveniência. O produto não é o terminal TradingView e não consulta cotações em tempo real.

## Estrutura da leitura

Next.js/React para explicar o estudo de barreiras em uma leitura linear de nove capítulos: pergunta do TCC, fundamento do alvo, dados, treinamento temporal, métricas, resultados preditivos, simulação, resultados financeiros e conclusões. Inclui glossário, referências primárias e documentos do projeto.

## Leitura guiada e dados

`src/lib/caderno.ts` lê o relatório fechado `../historico/analises/ciclo_001_completo/`, vinculado ao ciclo `4e232a796fcda0ea34c3` e dataset `9341610dbb329a858784`. Confere o SHA-256 fixado do resumo e os hashes dos CSVs financeiro e de barreiras antes de exibir os resultados. Ausência ou divergência bloqueia esses resultados, mantendo a explicação disponível. Para publicar outro ciclo, revisar explicitamente identidade, fontes e narrativa; não substituir o relatório histórico.

`Laboratorios.tsx` contém três exemplos interativos claramente identificados como fictícios: trajetória com primeiro toque, cálculo de log-loss/Brier e contabilidade de uma operação. `src/lib/didatica.ts` implementa somente essas calculadoras; não executa treino, previsão de mercado ou backtest científico. Os testes verificam referência uniforme, erro confiante, custo nos dois lados, caixa e risco nominal.

`LeituraResultados.tsx` apresenta médias por prazo/moeda/trimestre, contraste pareado, efeito do contexto e mapa de todas as 24 estratégias de cada modelo. A métrica financeira é anual concatenada, com custos, exposição, operações e intervalos. O controle sem filtro permanece indisponível quando sua trajetória não é auditável. Exemplos didáticos nunca entram nas médias reais.

## Registros detalhados

`src/lib/registros.ts` lê e valida os resumos de `../historico/execucoes/`. Uma execução somente aparece como concluída quando declara auditoria aprovada e métricas dos três modelos. Ausência de resultado permanece ausência; falhas são apresentadas.

A página não inicia treinamento nem altera parâmetros. As rotas de documentos permitem apenas protocolo, andamento, ciclo inicial, plano, resultados e proposta seguinte. As configurações científicas ficam no projeto Python. A tabela de execuções está em uma seção recolhível, separada do relatório fechado: pode receber novos registros sem alterar o ciclo explicado no caderno.

A tabela permite filtrar moeda, contexto, prazo, período e identidade do ciclo. As colunas mantêm Mamba, LSTM e AR(1) no mesmo recorte. É possível alternar log-loss, Brier, acerto balanceado, retorno líquido, drawdown e número de operações. Retorno zero com nenhuma operação identifica permanência em caixa; percursos financeiros incompletos aparecem como indisponíveis.

Os registros são consultados novamente a cada 30 segundos. O último estado registrado não certifica que o processo continue ativo; essa verificação é feita separadamente no executor. Falhas permanecem visíveis mesmo quando um filtro esvazia a tabela.

```bash
npm install
npm test
npm run lint
npm run build
npm run dev
```

Os testes usam fixtures de software e verificam a leitura íntegra do relatório real. Fixtures não aparecem como resultados de mercado. Os gráficos usam SVG e HTML acessíveis, com valores textuais, controles de teclado e distinção por rótulos além das cores. A interface adapta-se a celular e respeita a preferência por movimento reduzido.
