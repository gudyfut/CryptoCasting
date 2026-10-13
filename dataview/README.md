# Interface do projeto

Next.js local para apresentar o TCC ao orientador. Metodologia: `../docs/protocolo_experimental.md`. Revisão visual: 13/10/2026.

## Leitura em cinco etapas

| Seção | Conteúdo |
|---|---|
| O estudo | Quatro eixos da combinação, estado da decisão, exemplo temporal e ativos |
| O que prever | Cinco cartões com representação visual, razão de uso, fontes e impacto metodológico |
| Combinar testes | Moeda, candle, prazo, alvo, contexto, agenda e política; lista temporária para discussão |
| Como avaliar | Modelos, treino expansivo, comparações distintas e variáveis controladas |
| Andamento e resultados | Etapas, piloto real em revisão, formato de registro e leitura de execuções locais |

A página principal apresenta o essencial. Detalhes e fontes são expansíveis. A pesquisa está em `../docs/estudo_tarefas_previsao.md`, também disponível em `/api/estudo/documentos/tarefas`. Os cinco cartões são formulações úteis, não categorias mutuamente exclusivas: quantis podem descrever retorno ou volatilidade. Próximo candle é horizonte; abstenção é política de resposta.

## Componentes ativos

- `src/components/Dashboard.tsx`: navegação, visão do estudo, avaliação e andamento; pilotos documentados têm referência explícita.
- `src/components/TiposPrevisao.tsx` e `src/lib/tarefas-previsao.ts`: catálogo editorial e fontes; não são contratos executáveis.
- `src/components/CombinadorExperimentos.tsx`: rascunho de combinação, classificação de compatibilidade com o protocolo e lista em memória. Mantida ao navegar entre seções; recarregar limpa a lista. Não grava configuração científica.
- `src/components/VisuaisPrevisao.tsx`: diagramas SVG acessíveis, fictícios e identificados. Contagens de contexto são exatas; desenho de candles é esquemático, fora de escala.
- `src/app/caderno.css`: layout responsivo da interface atual. Estilos/componentes anteriores permanecem no repositório, mas não compõem a página principal.
- `src/lib/estudo.ts`: dados editoriais de ativos/entregas e tipos dos resultados.
- `/api/estudo/resultados`: resumos reais de desenvolvimento em `../dados/experimentos/pareado_*`; ausente não é zero; erros de leitura e resumos inconsistentes são expostos.
- `/api/estudo/documentos/[id]`: lista explícita de documentos permitidos. Não aceita caminhos arbitrários.

O painel não executa coleta, treinamento nem ordens. “Prevista no protocolo” não significa tarefa treinada ou backend qualificado. A lista de prazos é candidata, não uma grade aprovada. Nenhuma alteração libera F1–F8. O estado editorial é datado; execuções locais são lidas separadamente e requerem auditoria científica por `run_avaliacao.py`.

## Verificação local

Neste diretório: `npm run dev`, `npm run lint`, `npm test` e `npm run build`.

Verificar no navegador: cinco seções, expansão das fontes, alteração de combinações e contexto, distinção entre protocolo/proposta, inclusão/remoção sem duplicatas, persistência ao navegar, estados vazio/erro dos resultados e layout móvel. As tabelas possuem rolagem interna. Não há dependência de uma API Python.
