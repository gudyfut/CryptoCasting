# Arquitetura das simulações de operação

`analises/etapas/ensemble_2026/` aplica o mesmo motor de continuidade a previsões novas dos checkpoints antigos. A [avaliação2026](protocolo_ensemble_2026.md) encerrou24carteiras, com12controles de inferência e quatro financeiros2025. Ensemble e comprar/manter usam o mesmo instrumento/custos/período, com quantidade passiva fixa. `continuacao.py` identifica a continuação técnica da coleta; `publicar.py` confere artefatos, sem treino/inferência/backtest. [Fechamento](../registros/ensemble_2026/fechamento.json). Não repetir executores encerrados para apresentar resultados.

## Continuidade diária — marco de11/11/2026

`codigo/simulacao_operacoes/continuidade_diaria/` separa o sinal diário da obrigação de zerar/reabrir posições. Mantém avaliação diária e alvo95% do patrimônio liquidável, executa somente deltas, fecha em caixa/inversão e liquida no fim. Audita com conta de colateral/preço médio independente do caixa equivalente do simulador. Aberturas/aumentos respeitam mínimo nocional; reduções `reduceOnly` conservam lote/quantidades. Ajustes abaixo do mínimo aguardam nova decisão. Risco usa envelope mark, funding mantém os timestamps reais e não há ordens reais.

A [ADR0037](adr/0037-continuidade-posicoes-diarias.md) registra a descoberta e distingue mudança de política de correção técnica dos filtros. O leitor `codigo/analises/etapas/continuidade_moedas/` aplica a execução a previsões padronizadas preservadas e referências diárias novas, sem retreinar redes. [Método](protocolo_continuidade_moedas.md), [estado](../registros/continuidade_moedas/estado.json). A primeira implementação BTC permanece congelada em `dados/diagnosticos/continuidade_diaria_20261111_001/`; a ampliação não a sobrescreve. A interface financeira anterior conserva sua identidade até uma integração própria.

A ampliação encerrou408carteiras: [fechamento](../registros/continuidade_moedas/fechamento.json). Seu executor é a continuação identificada `analises.etapas.continuidade_moedas.continuacao`, não o `__main__` da tentativa inicial encerrada. Não repetir nenhum desses executores para apresentar resultados. `publicar.py` confere o manifesto e recalcula tabelas/intervalos de ledgers existentes; a entrega já publicada tem recibo próprio, sem reescrever o manifesto científico. Figura PNG/PDF e CSVs estão na pasta científica vinculada ao fechamento.

Para a auditoria atual usar explicitamente `simulacao_operacoes.continuidade_diaria.auditoria_grade.conferir`, junto a `simulador.simular`. `auditoria.py` e o export original de `__init__.py` permanecem fontes congeladas da primeira tentativa: a conta float podia representar resíduo fictício após zerar XRP. `auditoria_grade.py` conserva os eventos e a conferência independente de colateral/preço médio, mas representa quantidade em lotes inteiros. Não afrouxa funding ou tolerâncias de saldo. Incidente e307carteiras herdadas exatas permanecem identificados na continuação.

Custos vigentes: `configuracoes/custos_vigentes_001.json`, slippage provisório de0,01% por lado. `codigo/analises/etapas/custos_vigentes/` reavalia somente execução, reproduz resultados originais antes de recalcular e publica em `dados/reavaliacoes/`, com índice separado. O leitor web valida o novo manifesto e os pais históricos; uma divergência bloqueia a apresentação como vigente. A seleção, os filtros e os alvos antigos continuam os do estudo original; reduzir slippage de execução não retroage ao treinamento.

Os identificadores legados dos cenários permanecem vínculos de proveniência; seus números no nome não definem o custo atual. A configuração vigente e o fator0,2 definem a execução revisada, com estresses proporcionais e zero inalterado. Leituras encerradas, inclusive seus gráficos/documentos vinculados, permanecem históricas; a interface usa as médias recompostas e as fontes vigentes separadas. [Publicação conferida](../registros/custos_vigentes/vigente.json).

Extensão ADR0031: `codigo/simulacao_operacoes/diaria_24h.py` recebe somente origens/previsões/preço conhecido para decidir. O mercado observado pertence à contabilidade. Uma posição diária é encerrada24h após entrada, com funding,comissões,slippage e envelope intraminuto. `codigo/experimentos/cryptomamba_diario/avaliacao.py` publica70carteiras e médias sem escolher política pelo teste. Protocolo: `docs/protocolo_cryptomamba_diario.md`.

## Auditoria posterior de custos — 10/11/2026

A receita diária histórica de0,05% de comissão e0,05% de slippage por lado não foi alterada. A [auditoria posterior](../registros/generalizacao_moedas/custos/ultima.json) separa comissão taker compatível com referência pública de slippage não calibrado. Livros atuais não certificam2024–2025. Sensibilidade mantém previsões/política e registra144carteiras; cenários não são escolhidos pelo lucro. A contabilidade não duplicou comissão/funding.

A divisãofloat do arredondador pode acrescentar um tick em preços exatamente na grade quando slippage adicional é zero; os casos positivos0,5–5bp examinados concordaram comDecimal em ticks inteiros. Não alterar o motor congelado para corrigir recibos antigos; qualquer versão futura de execução deve usar precisão robusta, qualificação e identidade novas. Tick/lot e descontos históricos precisam de proveniência própria. Ver [cronologia](andamento.md).

## Revisão F03

`codigo/simulacao_operacoes/revisada/` separa `regras.py` (lotes, filtros e redução), `conta.py` (comissão recebida e colateral), `politica.py` (decisão causal), `simulador.py` (tempo, funding e execução) e `auditoria.py` (fórmulas independentes). O coordenador é `python -B -m experimentos.revisao_operacional preparar|executar`; ações distintas, autorização/identidade próprias e bloqueio de repetição. Consultar [protocolo](protocolo_revisao_operacional.md) e [estado](../registros/revisao_operacional/estado.json). Fontes F01/F02 abaixo são históricas imutáveis. A conferência posterior `python -B -m analises.revisao_operacional` lê ledgers e recalcula risco, sem repetir carteiras.

Nenhum simulador promete reproduzir integralmente uma conta Binance. Custos, filtros conservadores, preço de execução aproximado e envelope prudencial são identificados. Não chamar melhoria de fidelidade de melhoria garantida da previsão ou do lucro.

As avaliações de previsão e de operação são camadas diferentes. MSE/MAE usam alvo observado na avaliação estatística. Uma política de operação recebe somente a previsão e informações disponíveis na origem. Os módulos operacionais não importam modelos nem iniciam treinamento.

```text
publicações de previsões já encerradas
                 ↓ leitura e checksum
codigo/simulacao_operacoes/previsoes.py  → contrato sem alvo/preço futuro
                 ↓
codigo/simulacao_operacoes/politicas.py  → direção decidida causalmente
                 ↓
codigo/simulacao_operacoes/futuros/     ← codigo/mercado_futuros/ (negócios, mark, funding)
  contabilidade + simulador + auditoria separada
                 ↓
codigo/experimentos/futuros/            → grade, identidade, lock e publicação
                 ↓
dados/experimentos/futuros_<id>/  + registros/futuros/
```

| Responsabilidade | Local | Contrato |
|---|---|---|
| Coleta pública de perpétuos | `codigo/mercado_futuros/pipeline.py` | Arquivos/checksums/API; não calcula sinais ou lucro |
| Contexto anterior à primeira origem | `codigo/mercado_futuros/contexto.py` | Complemento identificado; não altera pai publicado |
| Previsões para operação | `codigo/simulacao_operacoes/previsoes.py` | UTC, horizonte24h, origens únicas, sem coluna de alvo |
| Política | `codigo/simulacao_operacoes/politicas.py` | Previsão/configuração → −1/0/+1; sem acesso ao mercado futuro observado |
| Contabilidade | `codigo/simulacao_operacoes/futuros/contabilidade.py` | Quantidade assinada, PnL, funding, custos |
| Mercado carregado | `codigo/simulacao_operacoes/futuros/mercado.py` | Cobertura contínua e arrays de observações; não contém previsões |
| Simulação | `codigo/simulacao_operacoes/futuros/simulador.py` | Operações, curva, funding e resumo; buffer de margem bloqueante |
| Conferência | `codigo/simulacao_operacoes/futuros/auditoria.py` | Recalcula saldo e ledger sem chamar simulador |
| Rodada identificada | `codigo/experimentos/futuros/` | Grade fixa, preservação, snapshot, autorização e execução exclusiva |
| Qualificação | `testes/simulacao_operacoes/` | Cenários sintéticos causais, não otimização em mercado |

Os executores Spot históricos (`backtest_carteira/`, módulos de ciclos e avaliações congeladas) permanecem intactos. Não movê-los para criar aparência de unificação: seus hashes e caminhos fazem parte da evidência. Novas políticas/mercados poderão usar contratos semelhantes, mas exigem novo protocolo e identidade; resultados de uma identidade nunca são sobrescritos.

Método: [protocolo F01](protocolo_futuros.md). Estado real: [registros](../registros/futuros/estado.json). Dados públicos têm [estado próprio](../registros/mercado_futuros/estado.json). Textos/recibos podem ser versionados; ZIPs, curvas e checkpoints continuam sujeitos à [política de armazenamento](armazenamento_e_reproducao.md).


Análise posterior: `python -B -m analises.futuros` verifica fechamento e ledgers publicados, grava recibo novo em `registros/futuros/conferencias/` e recompõe o relatório editorial. Não chama treinamento ou execução. A conferência já entregue fica preservada; não repetir para obter outro resultado. Interpretações editoriais adicionais devem permanecer no relatório canônico, sem alterar publicações congeladas.


## Smart retida compartilhada — F02

`codigo/simulacao_operacoes/smart/` acrescenta política de ajuste líquido, conta Spot/colateral de futuros, leitor dos dois mercados, simulador retido e auditor por caixa equivalente. O teste de preços idênticos/funding zero exige equivalência entre contas. `codigo/experimentos/smart_mercados/` congela e executa a grade autorizada; `tests_smart_mercados/` qualifica. [Protocolo](protocolo_smart_mercados.md), [estado](../registros/smart_mercados/estado.json). Fontes deF01 permanecem inalteradas. Nova política/gestão comum não substitui a Smart histórica e não exige novos checkpoints.
