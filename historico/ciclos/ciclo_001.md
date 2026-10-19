# Ciclo 001 — referência de barreiras

Definido antes de treinamento em 18/10/2026. Configuração: [ciclo_001.json](../../configuracoes/ciclo_001.json).

Hipótese: a qualidade probabilística e a utilidade econômica variam com moeda, contexto e prazo; Mamba pode ou não acrescentar valor frente a LSTM e AR(1).

Grade: quatro moedas × dois contextos (24/168 horas) × três prazos (1/24/168 horas), candles 1h, origem horária, base de execução 1m. Walk-forward DB1–DB4, seed 42. São 192 ajustes neurais mais baseline probabilístico reutilizável.

Seleção de época: log-loss de validação. Critério para análise do ciclo: log-loss de teste de desenvolvimento, seguida de risco e retorno líquido sob a política predefinida. Não selecionar seed, mudar custos ou apagar células depois de conhecer resultados.

Próximas hipóteses podem alterar grade e parâmetros internos do Mamba, mas terão outro identificador, orçamento e justificativa antes da execução. A primeira qualificação usa duas células da própria grade; o resultado conta nela somente quando a identidade/configuração coincidir integralmente.

Estado em 18/10/2026: implementação, coleta, processamento, qualificação, grade e análise de desenvolvimento concluídos; dataset `9341610dbb329a858784`, identidade `4e232a796fcda0ea34c3`. As 96 células foram auditadas e consolidadas; a auditoria suplementar integral foi aprovada. Os parâmetros iniciais foram mantidos apesar de os dois primeiros casos não produzirem operações. Registros reais ficam em `historico/execucoes/`; resumos consolidados em `resultado_<identidade>.json` nesta pasta. A [análise conjunta](../analises/ciclo_001_resultados.md) e a [proposta não executada do próximo ciclo](ciclo_002_proposto.md) estão documentadas. Nenhuma métrica sintética deve preencher a tabela científica.

Marco de execução em 18/10/2026, 09:10 UTC: DB1 e DB2 completos, com 48 células auditadas e 96 ajustes neurais. DB3 iniciado. Esse marco corresponde à metade da grade de desenvolvimento; a análise conjunta e a proposta de outro ciclo continuam dependendo dos quatro folds.

Marco de execução em 18/10/2026, 10:43 UTC: DB1–DB3 completos, com 72 células auditadas e 144 ajustes neurais. DB4 iniciado. Os parâmetros científicos foram preservados; a auditoria suplementar, as figuras e a consolidação de metade da grade continuam identificadas como retrato de 48 células e serão atualizadas após a conclusão integral.

Fechamento da etapa de células em 18/10/2026, 12:21:17 UTC: 96/96 auditadas, 192 ajustes neurais. O executor terminou com código zero após consolidar a grade. A conferência suplementar aprovou as 96 células; 25 testes sintéticos passaram e 288 registros de comprar/manter foram conferidos, correspondentes a 16 trajetórias únicas. Nenhuma nova configuração de mercado foi treinada durante esse fechamento.
