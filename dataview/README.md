# Interface de acompanhamento do TCC

Interface local em Next.js para consulta e apresentação do projeto ao orientador. A referência metodológica é `../docs/protocolo_experimental.md`.

## Organização

| Seção | Conteúdo |
|---|---|
| Resumo do projeto | Objetivo, escopo, evidências disponíveis e próxima etapa |
| Metodologia | Função dos modelos, divisão temporal, métricas e limites de interpretação |
| Configurações experimentais | Moedas, resoluções, janelas, timestamps, etapas e folds |
| Dados e ativos | Fonte, justificativa dos ativos, volatilidade e cobertura |
| Entregas e execução | Cronograma, estado das entregas, pendências e comandos |
| Resultados e interpretação | Piloto AR(1) documentado, formato final planejado e execuções locais |

Usar títulos descritivos e linguagem objetiva, sem slogans ou blocos promocionais. Manter definições e evidências visíveis, com tabelas quando ajudam a comparar. Distinguir explicitamente código implementado, experimento executado e análise planejada.

## Origem das informações

- `src/components/SecoesProjeto.tsx`: conteúdo explicativo das seções, baseado no protocolo e nas entregas.
- `src/lib/estudo.ts`: registro editorial dos ativos e entregas; números históricos do relatório oficial.
- `src/lib/plano-experimental.json`: matriz gerada por `../scripts/atualizar_plano_experimental.py`. Não alterar manualmente os números ou as datas.
- `/api/estudo/resultados`: leitura dos resumos reais de desenvolvimento em `../dados/experimentos/pareado_*`. Ausência não equivale a zero.
- `/api/estudo/documentos/[id]`: documentos do repositório permitidos explicitamente, apresentados em texto para consulta.

A interface não executa coleta, pré-processamento ou treinamento. Os controles da matriz alteram somente a visualização do plano. O estado editorial traz uma data de referência e não é atualizado automaticamente pela execução dos experimentos. A auditoria completa dos artefatos continua sob responsabilidade de `run_avaliacao.py`.

## Execução local e verificação

Neste diretório:

```text
npm run dev
npm run lint
npm run test
npm run build
```

As tabelas têm rolagem própria em telas pequenas. A impressão do navegador apresenta a seção selecionada, sem a navegação lateral.
