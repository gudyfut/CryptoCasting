# Candidata Astra versus OHLCV cru + Huber no mesmo executor

04/11/2026. ADR0023. Autorização explícita do pesquisador: comparar as duas receitas com mesmos dados/executor e oito seeds, verificar reaproveitamento e começar. Nenhuma consulta adicional ao Astra, busca de parâmetros ou mudança de política operacional.

## Comparação e reaproveitamento

A/C05: `janela_relativa`,contexto72,Huber. B: `crua`,contexto168,Huber. Ambas Mamba-1 oficial CUDA,cinco canais,largura32,duas camadas,estado16,dconv4,expand2,pré-LayerNorm residual,dropout0,1,última posição,20.257parâmetros. AdamW,taxa constante0,0002,decay0,001 com isenções oficiais,batch64/micro32,clipping1,até100épocas,paciência10. Seleção por menor MSE real de validação, primeiro empate. Alvo zscore de treino; Huber2×delta1. Fator de saída1,sem edição adicional de pesos.

Importar diretamente as funções congeladas `experimentos.busca_astra.dados.Dados`, `rede.Rede` e `treino.ajustar`. Não copiar/reimplementar ou editar o treinamento da busca encerrada. Novo coordenador e worker só cuidam da identidade, orçamento e fila. Entrada: `python -m experimentos.comparacao_astra_crua qualificar|preparar|executar|publicar`.

Herdar os32modelos C05/oito seeds/quatro blocos e suas previsões da execução `b34bad73d6cef1d10a97`; conferir manifestos, receitas, recargas e correspondência dos dados. O OHLCV cru+Huber da execução anterior `1781f557fdf2b45a3ae2` permanece histórico: não fornece os modelos do contraste atual, pois executor/população diferem. Nenhuma recoleta de mercado.

Orçamento novo: **32principais crus+1repetição real crua B1/42+1reprodução real da C05 B1/42=34ajustes**. Controles não entram nas médias. Ordem: reprodução C05 contra checkpoint herdado; primeiro cru B1/42; repetição crua; demais31crus. Os dois controles devem passar antes das demais seeds: mesma época, diferença de MSE de validação relativa≤1e−4 e máxima diferença absoluta de previsões≤1e−5 em validação/teste. Toda recarga individual continua exata. Mudanças de identidade no vínculo do checkpoint não mudam a inicialização ou o treinamento.

## Dados e divisões

Mesmos candles BTCUSDT1h `93509a1b06b19103ac1c`; alvo `ln(C[t+24]/C[t])`; origens horárias; mesma elegibilidade de336horas observadas consecutivas e índice inicial336, purga24h,sem interpolação. Todas as receitas usam as mesmas origens em treino/validação/teste. C05: ln(O/H/L/C sobre último fechamento conhecido da janela),ln1p(volume) padronizado dentro da janela. Crua: O/H/L/C em USDT e volumeBTC,sem log ou padronização externa de X. Não incluir indicadores. ScalerY reestimado somente no treino, obrigatoriamente idêntico entre receitas.

| Bloco | Fim treino | Fim validação | Fim teste |
|---|---|---|---|
| B1 |2023-10-01|2024-01-01|2024-07-01|
| B2 |2024-04-01|2024-07-01|2025-01-01|
| B3 |2024-10-01|2025-01-01|2025-07-01|
| B4 |2025-04-01|2025-07-01|2026-01-01|

Treino expansivo iniciado2021-01-01,intervalos UTC semiabertos e destino estritamente anterior ao fim da partição. Seeds42/17/2026/7/123/31415/271828/161803. Pesos novos em cada bloco/seed. Reaproveitar modelos C05 é equivalente a executar novamente sua receita apenas se integridade, ambiente, populações e controle de reprodução forem aprovados. Falha interrompe; não refazer até coincidir.

## Qualificação, execução e preservação

Antes de congelar: testes de grade34,orçamento e pedidos; igualdade de populações e observações com as oito seeds herdadas em cada bloco; exatidão dos valores crus; dois ajustes sintéticos CUDA na receita crua com reprodução/recarga; versões CUDA/Python/Torch/Mamba iguais às da busca. Não usar resultado de teste para escolher receita, seed ou época. Congelar fontes e qualificação, identidade própria e autorização antes de mercado.

Preservar integralmente a busca encerrada e o mapa de preservação histórico. Lock exclusivo e processo/host/PID/boot/logs; falha ou timeout interrompe sem retomada automática. Até45min por ajuste, não iniciar novos após12h de fila; publicação adicional. `registros/comparacao_astra_crua/PARAR` interrompe entre ajustes. Não iniciar processo concorrente. Publicação posterior tem ação própria, sem chamar treinamento; tentativas incompletas permanecem.

## Métricas e análise

Principal: diferença Astra−crua em MSE de teste, peso igual entre quatro blocos e oito seeds, sem ensemble. Dois contrastes adicionais: Astra−Naive e crua−Naive. Naive de retorno zero recalculado nos mesmos alvos. RMSE,MAE,direção,balanced accuracy,dispersão e resultados por seed/bloco secundários.

Bootstrap pareado:2.000réplicas,seeds e blocos circulares de dias14, sensibilidades7/28. Mesmas seeds reamostradas entre versões e blocos, dias dentro do próprio bloco. IC95%descritivo e IC98,333%Bonferroni para três contrastes. Diferença negativa favorece o primeiro modelo; conclusão de menor MSE exige limite superior corrigido abaixo de zero. ICincluindo zero é inconclusivo, não igualdade. Intervalos condicionais não corrigem toda a busca/seleção anterior. Protocolar antes desta rodada não torna2024/2025 novamente desconhecidos.

## Operações e publicação

Reaproveitar192carteiras da C05 e24benchmarks da publicação Astra; simular somente192carteiras cruas novas. Total408,com proveniência por carteira. Mesmo motor congelado `backtest_carteira`,Smart/diária24,cenários ideal/base/agravado,10.000USDT por bloco independente,latência1min,comissão0,10% e slippage0,05% por lado no cenário base. Sem futuros,short,stop-loss,alavancagem ou ajuste de limiar. Métricas de carteira são descritivas, não critério de seleção. Não compor retornos entre blocos.

Fechar após34ajustes aprovados,64séries principais,igualdade de alvos/origens/escalas,recálculo de MSE/MAE,192novas+216herdadas conferidas e preservação antes/depois. Relatório único `docs/resultados_comparacao_astra_crua.md`,artefatos em `dados/experimentos/comparacao_astra_crua_<id>/`,índice em `registros/comparacao_astra_crua/`. Comparação de duas receitas, com representação e contexto diferentes; não atribuir ganho a um único fator. Sem promoção automática ou novos ciclos.
