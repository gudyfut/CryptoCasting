# Portal do estudo de retorno em 24 horas

Executar npm neste diretório. `npm run dev`, `npm run build`, `npm run lint`, `npm test`.

O servidor lê a configuração e os registros reais da raiz do projeto. Previsões do explorador são exportadas por `python manutencao/exportar_portal.py`, a partir de tentativas auditadas. O exportador confere os hashes científicos e o endpoint verifica SHA-256 dos JSONs comprimidos. `dados/portal` fica fora do Git.

`npm test` verifica todas as séries exportadas: hashes, alinhamento dos preços de origem/destino, horizonte de 24h e recálculo das métricas contra os registros. Não gera previsões fictícias quando faltam resultados. Dados parciais recebem aviso explícito.

Gráficos usam TradingView Lightweight Charts™; atribuição permanece visível. A linha entre origem e previsão representa apenas a ligação gráfica ao valor terminal, não trajetória prevista. Candles identificados pelo instante de fechamento exclusivo UTC.

Percentuais de retorno menores que 0,01% usam precisão adicional; abaixo de 0,0001%, usam notação científica. Isso evita confundir um retorno pequeno com zero exato. A regra é compartilhada pelo gráfico, cartões e tabela de origens. Modelos ainda ausentes na publicação parcial são identificados pelo nome, sem preenchimento artificial.

O painel agregado lê `registros/analises/<execucao>/<fase>/resumo.json` apenas depois de conferir o manifesto e o recibo de auditoria da publicação. `python manutencao/consolidar_resultados.py --fase desenvolvimento` (ou `avaliacao`) exige a fase inteira, revalida as fontes, consolida médias, bootstrap e simulações e executa uma auditoria independente. Não gera um placar completo com tentativas faltantes. Os controles permitem comparar contextos, moedas, blocos e seeds; os intervalos publicados referem-se à fase completa e têm esse escopo explicitado.

As curvas financeiras e CSVs são servidos por uma lista de arquivos auditados, com hashes e identidade da execução. Séries do explorador usam nomes imutáveis por conteúdo para permitir atualização da exportação sem invalidar leitores antigos. O laboratório interativo é um exemplo didático identificado, não dado de mercado.

Ao concluir e auditar a consolidação de desenvolvimento, a CLI também exporta as séries dessa fase. Assim os resultados completos de 2023 ficam disponíveis antes de terminar a avaliação posterior. Reabrir/atualizar a página consulta os registros mais recentes; a interface não trata ausência temporária de exportação como previsão zero.

## Verificação final concluída — 21/10/2026

Publicação completa de ambas as fases: 832 resultados em 384 séries com os quatro modelos. Build/lint, dois testes de todas as séries e dois da API aprovados. Downloads JSON/CSV e operações foram comparados por hash com os manifestos. Placar, intervalos, simulações e exemplos reais foram conferidos em desktop/celular, incluindo filtros, origem compartilhável, seleção do modelo, busca por data e recarga. Recibo `../registros/interface/aceite_final.json`, com hashes das fontes e imagens. O aceite depende também da auditoria científica global, não apenas da compilação.
