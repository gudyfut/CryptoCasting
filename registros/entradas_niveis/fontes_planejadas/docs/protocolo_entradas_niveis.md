# Entradas OHLCV relativas, cruas e níveis padronizados

Versão1,03/11/2026. ADR0020; autorização explícita do pesquisador após proposta A/B/C, oito seeds e comparação das médias. Escopo66ajustes novos (64principais+2controles),32referências herdadas. Entrada `python -m experimentos.entradas_niveis`; fontes/artefatos próprios e fila após a rodada Huber. Não altera fontes científicas antigas nem recolhe mercado.

## Pergunta e fatores

Entradas em nível melhoram a previsão do log-retorno24h sob a receita fixa Mamba16? A compara a representação vigente; B compara OHLCV totalmente cru; C preserva níveis e ajusta apenas sua escala. B−C isola a padronização de entrada sob esta receita; A−B e A−C comparam representações compostas, não apenas normalização. Resultado negativo é válido. Não procurar variantes até obter lucro.

| Versão | Cinco canais efetivos | Escala de entrada |
|---|---|---|
| A/atual, herdada | ln(O/C_anterior),ln(H/C_anterior),ln(L/C_anterior),ln(C/C_anterior),ln(1+V_BTC) | zscore de treino |
| B/crua | O,H,L,C em USDT e V em BTC | identidade, médias0 e escalas1 declaradas; sem log ou divisor de volume |
| C/niveis_padronizados | mesmos valores de B | média/desvio de horas únicas dos contextos de treino,ddof0; constante recebe escala1 |

Não usar timestamp, indicadores, médias móveis ou volume relativo nesta rodada. A normalização do alvo continua exatamente igual entre A/B/C, ajustada no treino; LayerNorm interna continua igual. Entrada crua não significa remover validação, máscaras ou disponibilidade causal. B/C herdam a máscara horária de A, inclusive a primeira hora sem fechamento anterior, e todas as origens/partições/metadados. Assim não ganham amostras adicionais. Conversão float32 é parte do contrato. Sem clipping, interpolação ou remoção de extremos.

Receitas e artefatos B/C ficam no pacote novo; não editar `entradas_modelo/receitas.py` ou o consumidor congelado. Um adaptador explícito acrescenta o contrato de entrada identidade reutilizando as validações estruturais existentes; o contrato real e sua identidade permanecem registrados. Alvo observado nunca entra no lote neural. Scalers C, alvo e matrizes são conferidos contra treino/candles; testes alteram futuro para provar invariância das janelas anteriores.

## Calendário, treinamento e orçamento

BTCUSDT/Spot Binance, candles1h completos existentes,168h→24h. Mesmas oito seeds17/42/2026/7/123/31415/271828/161803, ordem42/17/2026/7/123/31415/271828/161803. Mesmos quatro blocos da ADR0019, treino expansivo desde01/01/2021, fronteiras UTC semiabertas:

| Bloco | Fim treino/início validação | Início teste | Fim teste |
|---|---|---|---|
| B1 | 01/10/2023 | 01/01/2024 | 01/07/2024 |
| B2 | 01/04/2024 | 01/07/2024 | 01/01/2025 |
| B3 | 01/10/2024 | 01/01/2025 | 01/07/2025 |
| B4 | 01/04/2025 | 01/07/2025 | 01/01/2026 |

Purga24h com destino estritamente anterior ao fim da partição; janela somente de passado disponível, podendo atravessar início da partição. Pesos B/C do zero por bloco/seed. A/MSE herdada somente se checkpoint/recarga/fontes/datas/origens/receita da execução10dac17ea9df2c540c57 conferirem. Nunca transplantar pesos do futuro.

Mamba-1 oficial CUDA, largura32,2blocos,estado16,d_conv4,expand2,dropout0,1,pré-LayerNorm e20.257parâmetros. MSE no alvo padronizado, AdamW0,0002, decay0,001 com isenções oficiais, batch64/microbatch32, clipping1, máximo100épocas,paciência10. Checkpoints imutáveis por melhora; mínimo MSE real de validação seleciona, empate primeira época. Teste não escolhe época,seed,receita ou taxa. Mesmo otimizador fixo pode favorecer uma representação; conclusão é condicional a esta receita, não demonstra ótimo de B/C.

64principais novos (4×8×2),32herdados A. Dois controles adicionais B1/42, um B e um C, depois desses principais e antes de qualquer outra seed. Reprodução: mesma época, diferença absoluta máxima1e−5 de log-retorno e relativa máxima1e−4 de MSE; recarga exata individual. Controles fora das médias. Falha interrompe; não consumir novas tentativas para passar.

## Qualificação, autorização e operação desacompanhada

Preparação CPU:8artefatos novos e população comum, testes de contrato/causalidade/escalas, fontes/configuração/protocolo/plano congelados e autorização literal vinculada ao hash do plano. Nenhum treino de mercado nessa fase. Fila com lock exclusivo e host/boot/PID aguarda fechamento conferido da predecessora e término do seu treinamento; não duplica executor nem altera o processo anterior. Falha/encerramento sem fechamento da predecessora interrompe a fila.

Depois da barreira: inspecionar CUDA/ambiente/Mamba oficial e qualificar dimensões,forward/backward/atualização, reprodução de quatro ajustes sintéticos (B/C,duas repetições de duas épocas),seleção/recarga, testes de contabilidade e cobertura. A referência sintética trabalha em preços perto100.000USDT. Sem fallback. Qualificação reprovada preserva falha e impede mercado.

Congelar então a execução com ID próprio incorporando plano,qualificação,ambiente,receitas,entradas,publicação herdada e preservação. A autorização explícita já recebida é vinculada automaticamente ao ID derivado do plano aprovado, sem mudar fatores/orçamento; não há novo pedido de autorização. Execução com lock próprio; duplicação bloqueada; erro mantém tentativa/log e interrompe. Não há retomada automática. Uma retomada futura exige investigação explícita, preservação das anteriores e implementação/qualificação identificadas, nunca reexecutar ciclo encerrado.

## Comparação e conclusão

Publicar cada seed, média e desvio entre oito seeds por bloco/versão. Agregado com peso igual nos quatro blocos, média das oito seeds dentro de cada bloco. Médias de métricas individuais, não ensemble. Principal: MSE de teste em retorno real; validação,RMSE,MAE,viés,direção,habilidadeNaive e operação secundários.

Três contrastes fixos B−A,C−A,B−C. Bootstrap pareado de seeds e dias,2.000réplicas,seed20261104,blocos circulares14dias, sensibilidades7/28. Mesmos índices de seeds reamostrados nas duas versões e nos quatro blocos; dias amostrados dentro de cada bloco sem cruzar fronteiras. Blocos não são mercados independentes. IC95% descritivo e IC98,333% Bonferroni para família de três contrastes. Melhora requer diferença média negativa e limite superior principal corrigido<0; piora exige média positiva e limite inferior>0; demais casos inconclusivos. IC contendo0 não prova igualdade. Sem promoção automática, reabertura por resultado próximo ou busca adicional.

2024/2025 já foram consultados antes desta hipótese. Reamostragem não remove seleção adaptativa nem garante lucro/generalização. Não confundir médias de oito inicializações com oito mercados independentes.

## Avaliação operacional secundária e fechamento

Motor Spot congelado da execução8ec8a66648313caa48e3, Smart2% e diária24, ideal/base/agravado, mesmo calendário e custos da ADR0019. Sem mudanças de política,short,futuros ou stops.384carteiras novas B/C (64×2×3),192A e24benchmarks herdados, total600. Não repetir simulações A ou treinamento A para produzir tabelas. Carteiras independentes por bloco,capital10.000USDT; não somar retornos como histórico contínuo. Comparar risco/exposição/retorno/custos separadamente de MSE. Lançamentos novos reconstruídos por verificador independente.

Publicação posterior nunca chama treinador. Conferir64conclusões principais novas,2controles,32heranças,96resultados principais,384simulações novas e216herdadas; fontes,métricas,checkpoints/recarga,escalas,contrastes e preservação. Resultados em `docs/resultados_entradas_niveis.md`,estado/progresso em `registros/entradas_niveis/` e na execução. Sem backup externo certificado ou promoção automática. Registros anteriores permanecem imutáveis.
