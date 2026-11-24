# Penalização seletiva no Mamba diário — protocolo 001

Autorizado pelo pesquisador em **12/11/2026**: comparar penalização seletiva com a referência A, mantendo o restante igual, três seeds e 200 épocas completas, com organização separada, controles e execução. [Configuração](../configuracoes/penalizacao_seletiva_diaria_001.json). Hipótese motivada pelas sondas do [fatorial encerrado](resultados_eixo_temporal_diario.md): penalização uniforme quase suprimiu a contribuição funcional dos ramos; retirar toda a penalização não estabeleceu melhoria consistente. Não presumir ganho.

## Comparação e atribuição

A é a receita de canais do fatorial `143e7037d9d6cf620cf3`, proveniente da execução padronizada `f3f8772670f244779ad7`. S conserva a mesma arquitetura e inicialização por seed, alterando somente o **alcance da penalização**. Mamba-1 oficial e núcleo derivado do CryptoMamba de Sepehri et al., commit `fef42727861a9c3a32241283ab981ef21a49e291`; fonte/licença MIT continuam preservadas. Não é nova arquitetura original nem reprodução integral do artigo.

| Receita | Adam weight_decay efetivo |
|---|---|
| A | 0,001 em todos os parâmetros |
| S | zero nos parâmetros marcados `_no_weight_decay`, nos parâmetros afins de `nn.LayerNorm` e em todos os `bias`; 0,001 nos demais |

Classificação por identidade do parâmetro, módulo LayerNorm, marcador oficial e nome local `bias`, com motivos registrados. Cada parâmetro aparece exatamente uma vez. Não isentar genericamente todos os vetores; não congelar pesos; não alterar inicialização. Os parâmetros `A_log` e `D` têm marcadores oficiais; a extensão à LayerNorm/bias é hipótese deste projeto. A biblioteca não aplica isenção automaticamente ao Adam. O fator testado é a política conjunta; uma melhora não identifica isoladamente qual isenção foi responsável. Difere da antiga ablação horária que excluía apenas marcadores sob AdamW.

## Receita preservada

BTC USD-M Binance, candles diários, seis canais na ordem Timestamp/Open/High/Low/Close/Volume, contexto 14, entrada `[lote,6,14]`; percurso dos canais, 136.952 parâmetros. Núcleo 14→16→32→1, quatro blocos por estágio, estado64, convolução4, expansão2, LayerNorm prévia e resíduos. Sem projeção temporal nova. Backend Mamba-1 oficial CUDA com scan de referência determinístico FP32, sem fused/fallback.

Mesmos dados, origens, janelas e escalas congelados: treino2020–2023, validação2024, avaliação retrospectiva2025, respectivamente1446/351/350 exemplos. Timestamp em segundos, volume/1e9, z-score exclusivo dos candles únicos das janelas de treino, sem clipping; alvo retorno simples do próximo fechamento, sem padronizar o alvo. Preservar as convenções de cobertura anteriores.2026 excluído; períodos conhecidos não são holdout intocado.

Adam (não AdamW), taxa0,01, betas0,9/0,999, epsilon1e−8; StepLR100/gamma0,5 no fim da época; lote32 com último lote parcial. Perda `sqrt(MSE + 1e-8)` por lote, **200 épocas completas**, sem clipping/early stopping, limite técnico4h por ajuste. Selecionar menor RMSE global de validação, primeiro em empate. Teste e backtest não selecionam checkpoints. Seeds42,17,2026. Mesma ordem de exemplos por seed; agrupamento do otimizador não consome RNG.

## Qualificação, herança e controles

Antes de congelar: conferir fontes/fechamentos dos antecedentes, dados/scalers exatos, contrato de único fator, igualdade AST do algoritmo de treino após as substituições explícitas do otimizador/diagnóstico, cobertura dos grupos e atualização Adam sintética. CUDA: inicialização A/S idêntica, dimensões, forward/backward determinísticos, seis épocas sintéticas repetidas por receita, equivalência exata do treinador uniforme com o anterior, recarga de A nas três seeds reproduzindo validação. Testes herdados conferem alvo/scaler causal e continuidade financeira. Qualificações e falhas ficam identificadas, sem sobrescrita.

Herdar as três redes A somente com a prova existente e reconferida de seleção nas primeiras200 épocas, mesmos dados/receita/scalers e pesos. A execução original teve1000 épocas, mas os mínimos selecionados dentro de200 coincidem; não relatar herança como novo treino. Rodar adicionalmente **controle A42 novo de200 épocas**, comparando trajetória científica prefixo200, todos os checkpoints, seleção e previsões exatamente contra a referência. Falha bloqueia S.

Ordem: **controle A42 → S42 → controle S42 → S17 → S2026**. Controle S42 repete200 épocas e exige igualdade exata de histórico, todos os checkpoints e previsões. Falha bloqueia as demais seeds e a avaliação de teste; não afrouxar tolerâncias nem repetir até passar. São **três ajustes científicos novos e dois controles**,1000 épocas novas; controles fora das médias. Locks de ciclo/GPU, PID/host/boot, conferência de integridade antes/depois e preservação de incidentes. Retomada requer diagnóstico; não duplicar processo vivo.

Sondas nas32 janelas fixas do treino, inicialização, épocas1/5/10/25/50/100/150/200 e checkpoint selecionado. Registrar normas, saída dos12 ramos, efeito de zerá-los temporariamente e gradiente da tarefa versus termo L2 **com coeficiente efetivo de cada grupo**. Observação não modifica pesos/RNG/seleção. A herança não inventa sondas intermediárias ausentes. Atividade do SSM não prova habilidade preditiva.

## Avaliação e encerramento

Mesmas métricas e estimadores do fatorial: MSE principal, RMSE, MAE, viés, direção/recalls/abstenção, correlação e dispersão. Média/desvio das três redes separados do ensemble (média dos preços equivalentes, retorno equivalente também salvo). Naive e Ridge com a mesma grade selecionada em validação, sem novas hipóteses sobre baselines. Contraste primário S−A; contrastes secundários contra Naive/Ridge. Bootstrap pareado por seeds e blocos7/14/28dias,14principal,2000 réplicas; ensemble fixo reamostra apenas dias. Intervalos exploratórios, três seeds e períodos conhecidos, sem correção da busca histórica. Não promover por2025 nem abrir2026 para escolher.

Mesmo motor de continuidade: mantém lado persistente e negocia apenas diferenças para alvo95% do patrimônio liquidável; encerra em caixa/inversão/fim. Filtro±0,2%, capital10milUSDT, latência1min, comissão0,05% por lado, slippage provisório0,01% (estresses0,02%/0,03%), funding histórico, filtros BTC, sem stop/take. Não há fechamento/reabertura diária obrigatória nem certificação de custos históricos/execução real. Auditoria independente por colateral/preço médio e lotes inteiros,30 reproduções A/Naive obrigatórias.60 carteiras: (6 redes + 2 ensembles + Naive + Ridge) × 2 fases × 3 custos. Relatar lucro, drawdown, custos, funding, exposição/lados e crescimento log pareado; falhas prudenciais preservadas, sem excluir maus resultados. Sem ordens reais.

Código/testes/configuração/protocolo com namespace `penalizacao_seletiva_diaria`; recibos em `registros/penalizacao_seletiva_diaria/`, dados/modelos/publicações em `dados/experimentos/penalizacao_seletiva_diaria_<id>/`. Fontes e receita congeladas antes do treino. Concluir após cobertura/controles/auditorias, independentemente do desempenho; não acrescentar busca automática. Registrar interpretação na análise do ciclo ao concluir e incorporar a contribuição sobre regularização/SSM ao TCC.
