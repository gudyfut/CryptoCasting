# Caderno visual do estudo

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
