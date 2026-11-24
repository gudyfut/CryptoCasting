# Busca adaptativa assistida por Astra — protocolo 1

Autorizada pelo pesquisador com “ok” após o plano de até12horas de exploração,12candidatas, triagem com uma seed/dois recortes, até3promovidas/três seeds e uma finalista/oito seeds/quatro blocos. Registro em03/11/2026 de Brasília (preparação técnica atravessa04/11UTC). ADR0022; configuração `configuracoes/busca_astra_001.json`; fontes `experimentos/busca_astra/`; ponteiro `registros/busca_astra/execucao.json`. Este ciclo não reabre os anteriores.

## Pergunta e natureza

Uma busca adaptativa guiada por diagnósticos de treino/validação encontra uma receita Mamba que melhora a referência sob orçamento limitado? Não promete ótimo, lucro ou significância. É exploração adaptativa assistida por IA, não uma sequência inteiramente pré-especificada de ablações. A escolha retrospectiva de estudar este domínio e todas as consultas anteriores são declaradas.

## Separação de responsabilidades

O coordenador Windows consulta `gpt-6-astra`, esforço `max`, via Codex CLI autenticado pela assinatura ChatGPT. Cada consulta é efêmera, em pasta temporária externa, sem ferramentas, plugins, navegação ou leitura do repositório. Recebe no prompt apenas receitas e resumos de desenvolvimento; devolve JSON validado. Comando, prompt, resposta, eventos, consumo e ausência de ferramentas são registrados. Sem API paga, troca automática de modelo, consumo de créditos de reset ou consulta substituta automática em falha.

Um worker WSL executa Mamba-1 oficial CUDA. O agente não altera fontes/evaluador/políticas e não executa Python arbitrário. Sua liberdade ocorre no espaço de receitas versionado em `contrato.py`, incluindo representação, indicadores, contexto24/72/168, largura, camadas, estados, dropout, pooling, Adam/AdamW, taxa, decay, perda, scheduler e contração dos pesos da cabeça. A seleção da receita é adaptativa; uma combinação de fatores não é descrita como efeito isolado.

## Dados e causalidade

BTCUSDT Spot Binance, candles1h já auditados, alvo `ln(C[t+24]/C[t])`, origens horárias. Desenvolvimento recebe somente candles com fim até2024-01-01. D1: treino2021–2022 e validação2023H1; D2: treino2021–2023H1 e validação2023H2. Destino do alvo deve ser estritamente anterior ao fim da partição: purga24h.

Representações: relativa=ln(O/H/L/C sobre C anterior) e ln1p(volume), zscoretreino; crua=OHLCV sem escala X; níveis=OHLCV zscoretreino; logníveis=ln(OHLC)/ln1pV zscoretreino; janela relativa=ln(OHLC/C final conhecido da própria janela), volume ln1p com zscore dentro da janela. Indicadores opcionais: logretornos24/168, desvios de retornos horários24/168 (ddof0) e ln1pV menos média168; todos causais, padronizados no treino. Contextos em ordem temporal; alvo nunca vira canal.

Disponibilidade comum começa no índice336, suficiente ao maior atraso composto indicador+contexto. Além do início, janelas afetadas por lacunas exigem336horas observadas consecutivas. Isso pode excluir mais origens de treino que nos ciclos anteriores; não se interpola ou compacta o tempo. Todas as candidatas e a referência nova usam exatamente as mesmas origens. Scalers X usam união de horas únicas nos contextos do treino; scaler Y usa somente alvos do treino. Cada bloco reestima pesos/escalas do zero. Por essa mudança de suporte e pelo executor novo, a avaliação final retreina32referências e não apresenta herança como equivalência automática.

## Treinamento e edição

Referência: relativa, contexto168, largura32,2camadas,estado16,dconv4,expand2,pré-LayerNorm residual,dropout0,1,última posição,AdamW0,0002,decay0,001,MSE. Preservar isenções oficiais A_log/D. Todas as receitas: batch64/micro32,clipping1,até100épocas,paciência10,escolha pelo menor MSE real de validação, primeiro empate. Huber=2×Huber(delta1 no alvo padronizado). Plateau opcional=fator0,5/paciência2/mínimo0,000025.

Contração opcional α é fator da receita, escolhido antes do ajuste. Após selecionar checkpoint, criar cópia e aplicar y_novo=α*y_original em log-retorno real; para y=s*z+μ, alterar cabeça para z_novo=α*z+(α−1)μ/s. Preservar checkpoint anterior, testar equivalência e recarregar exatamente. Não selecionar α adicional pelo teste nem por seed. O checkpoint pré-edição é escolhido por MSE antes da edição; esta regra faz parte da receita, sem busca posterior de épocas/α.

## Seleção, orçamento e interrupções

Score de desenvolvimento: média de MSE/Naive, peso igual entre D1/D2 e seeds. Triagem de até12candidatas com42:24ajustes. Até3melhores recebem17/2026:12novos. Referência:6ajustes + repetição real D1/42 antes das demais seeds. Elegibilidade final exige os seis ajustes completos, melhora de score de pelo menos0,1%, MSE médio menor nos dois recortes e pelo menos4/6pares melhores. Ordenar score, pior razão, parâmetros e ID. Não usar lucro, acurácia ou teste para selecionar.

Exploração inclui referência, consultas, triagem e promoção:12h; triagem não inicia após8h, reservando até4h à promoção. Até30min por consulta Astra e45min por ajuste; prazo restante pode reduzir este limite. Tentativa que excede prazo é preservada, não considerada concluída. Ausência de candidata elegível encerra sem finalista. Falha de formato, receita repetida, OOM, NaN, divergência, reprodução ou cota interrompe sem repetição automática. Arquivo `registros/busca_astra/PARAR` impede iniciar próximos trabalhos. Retomada exige revisão humana/técnica do incidente e do PID real; timeout do wrapper WSL não prova término do worker.

Finalista congelada antes de qualquer teste final; nenhuma chamada adicional ao agente depois disso. Fase final:32candidata+32referência+1controle real B1/42, até12h de treinamento. Total máximo108ajustes reais (43desenvolvimento+65final), além de ensaios sintéticos separados. Controle final antecede as demais seeds da candidata. Reprodução: mesma época, diferença absoluta de previsões≤1e−5 e relativa de MSE≤1e−4. Recarga de cada checkpoint exige igualdade exata. Modelo, seed e tentativa não são substituídos para completar orçamento.

## Avaliação final e operação

B1: treino até2023-10/validação até2024-01/teste2024H1; B2: treino até2024-04/validação até2024-07/teste2024H2; B3: treino até2024-10/validação até2025-01/teste2025H1; B4: treino até2025-04/validação até2025-07/teste2025H2. Treinos começam em2021, respetando aquecimento comum. Oito seeds42/17/2026/7/123/31415/271828/161803, mesmas entre versões. Médias de modelos individuais, não ensemble.

MSE principal; MAE/RMSE/direção/dispersão e diagnóstico secundários. Dois contrastes definidos: candidata−referência e candidata−Naive. Bootstrap pareado seeds/dias,2.000réplicas,14diasprincipal,7/28sensibilidade; IC95%descritivo e97,5%Bonferroni para dois contrastes. Esses intervalos são condicionais e não corrigem toda a seleção adaptativa.2024/2025já consultados; nenhum holdout intocado ou confirmação independente alegada.

408carteiras no máximo:64modelos×2políticas(Smart/diária24)×3custos=384,mais24benchmarks(compra/manutenção e caixa). Motor congelado `backtest_carteira_8ec8a66648313caa48e3`, custos e regras intactos;10.000USDT por bloco independente. Resultado operacional não escolhe a receita. Sem futuros ou operações reais.

## Evidências e encerramento

Qualificação antes de mercado: testes de causalidade, população comum, escalas, purga, dimensão, seleção, equivalência ao Mamba de referência, acumulação/Huber, edição em retorno real, atualização, reprodução sintética e recarga. Congelar fontes/configuração/protocolo/qualificação, vincular autorização à identidade e conferir preservação. Tentativas, comunicações do agente, épocas, checkpoints e resultados por identidade; falhas jamais apagadas. Revisão local não equivale a backup externo. Encerrar com ou sem melhora, sem promoção automática e sem abrir nova busca.

Publicação interrompida usa `python -m experimentos.busca_astra publicar`, somente após o coordenador encerrar. Cada tentativa de publicação tem pasta própria; a ação não chama treinamento e uma publicação concluída não se repete.
