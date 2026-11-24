# Experimento controlado de pré-normalização do Mamba

Definido em 28/10/2026 antes da execução, após autorização explícita do pesquisador para implementar a recomendação e treinar/testar somente Mamba. Decisão: ADR 0005. Configuração: `configuracoes/normalizacao_mamba_001.json`. Evidência: `registros/normalizacao/autorizacao.json`.

## Pergunta e intervenção única

Medir o efeito de mudar `LN(x + Mamba(x))` para `x + Mamba(LN(x))` em cada um dos dois blocos. A normalização final, dropout, head, projeção, dimensões, epsilon, inicialização e biblioteca ficam iguais. Mantêm-se 20.129 parâmetros. Não se trata de corrigir um bug comprovado; a hipótese pode melhorar, piorar ou ser inconclusiva.

O comparador direto é o Mamba pós-normalizado com penalização corrigida, execução `7868a4d847c1410fc681`. A referência inicial `1e7c5ed662fba55ddd25` permanece preservada. A pré-normalização herda a classe original e altera somente o forward. O treinador é estruturalmente idêntico ao da extensão de penalização, exceto a fábrica de rede. Testes conferem AST, igualdade dos pesos iniciais/RNG e grupos de parâmetros.

## Penalização e CryptoMamba

O CryptoMamba consultado, commit `fef42727861a9c3a32241283ab981ef21a49e291`, usa Adam com `self.parameters()` e weight decay uniforme. Não implementa a isenção dos marcadores `_no_weight_decay`. Os YAMLs indicam 0,0005 sem volume e 0,001 com volume. Nosso comparador usa AdamW desacoplado, 0 para A_log/D (2.176 escalares), 0,001 para os demais (17.953). Portanto, **a correção anterior não é uma reprodução da penalização do CryptoMamba**. A evidência e a distinção foram apresentadas antes da execução; o objetivo autorizado é testar a normalização, não copiar simultaneamente outro otimizador.

Conservar a política corrigida em ambos os lados. Não excluir novos biases ou normas, nem alterar learning rate, scheduler, loss ou parâmetros do SSM. Fonte dos autores: https://github.com/MShahabSepehri/CryptoMamba/blob/fef42727861a9c3a32241283ab981ef21a49e291/pl_modules/base_module.py . Ver pesquisa e fontes preservadas em `docs/revisao_mamba_criptomamba.md`.

## Dados, informação e orçamento constantes

Reutilizar dataset `d25f6a93a9900725f51e`: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT; Binance Spot; retornos horários como única entrada; origem horária; alvo terminal log-retorno em 24h; W24/72/168/336. Sem nova coleta, indicadores ou interpolação. Datas, população comum, lacunas e purga de 24h seguem `docs/protocolo_experimental.md`. Conferir por célula origens, destinos, índices, alvos e escalas contra o comparador histórico.

Scalers apenas no treino, sem alterar suas populações. Novos pesos por ajuste; seeds 17/42/2026. AdamW lr0,0002, betas0,9/0,999, eps1e-8, penalização corrigida, batch64/microbatch32, clipping1, FP32/TF32 desligado. Teto100 épocas, paciência10, menor MSE de validação com primeiro empate. Mesmo embaralhamento por seed. Melhor época e duração podem mudar como consequências da intervenção; não forçá-las iguais nas variantes.

Datas do protocolo original, intervalos semiabertos UTC, alvo estritamente anterior ao fim de cada partição: DB1–DB4 são desenvolvimento; B1–B4 são avaliação retrospectiva 2024–2025 já conhecida. A autorização não cria holdout novo nem busca adicional de parâmetros. A normalização do bloco não substitui nem modifica o scaler dos dados.

## Grade, controles e gates

- 384 novos ajustes Mamba: quatro moedas × quatro contextos × oito blocos × três seeds, 192 por fase.
- Dois controles Mamba pós-normalizados com penalização corrigida: BTCUSDT/DB1/seed42, W24 e W336, escolhidos antes da execução e comparados aos correspondentes da extensão corrigida.
- Dois pilotos pré-normalizados nessas mesmas células, integrantes da grade de 384, sem duplicação.
- Nenhum novo treinamento ou inferência de teste de LSTM, ARIMA ou Naive. Suas previsões/resultados publicados são referências herdadas; testes de contrato anteriores não constituem novos ajustes dessas famílias.

Orçamento de 386 treinos de mercado antes de falhas preservadas. Gate dos controles: mesma época selecionada, diferença máxima de previsões até 1e-5 de log-retorno em validação/teste/operacional e variação relativa de MSE teste até 1e-4. Registrar igualdade exata também. Fora da tolerância: interromper e investigar, nunca selecionar seed alternativa.

Antes de congelar: verificar fontes históricas e seus snapshots, identidades, dataset, artefatos e publicações; executar contratos existentes e específicos. Qualificar **somente Mamba** em pós/pré-normalização nos quatro contextos, 64 exemplos sintéticos por caso e duas repetições. Verificar forward, finitude de perdas/gradientes, atualização em três passos com microbatch/clipping/otimizador real, sensibilidade a mudança da entrada, recarga exata e repetição até 1e-6. Ambiente Python/Torch/CUDA/GPU/versões/fonte Mamba deve coincidir com a qualificação do comparador. Esses testes não comprovam capacidade preditiva de mercado.

Após qualificação e congelamento: controles, pilotos, desenvolvimento completo, avaliação completa e publicação. Gates entre fases são técnicos e de integridade, não condicionados a superar baselines. Não mudar método entre fases nem omitir a avaliação por resultado ruim.

## Evidências e retomada

Código novo em `experimento_normalizacao/`, entrada `run_normalizacao.py`, ponteiro exclusivo `registros/normalizacao/execucao.json`. Identidade inclui fontes, configuração, protocolo, autorização, dataset, comparador e qualificação. Artefatos em `dados/experimentos/normalizacao_<id>/`; cópia das fontes em `fontes/`, tentativas por célula e controles separados.

Preservar ambos os ciclos anteriores e publicações por hashes antes/depois. Não alterar código científico congelado ou seus recibos. Cada tentativa conserva configuração efetiva (`normalizacao_mamba=pre` nos novos checkpoints), pesos, épocas, otimizador, previsões de validação/teste/operacional, recarga exata e auditoria independente de MSE e alinhamento. Cobertura deve coincidir com o conjunto exato das 384 células e dos dois controles; contagem isolada não basta.

Lock exclusivo antes da preparação e durante a execução. Conferir host/PID/logs antes de retomar; jamais duplicar processo vivo. Interrupções conservam os registros anteriores e a tentativa, nova tentativa usa a mesma seed e configuração, sem seleção por resultado. Fontes congeladas divergentes bloqueiam a execução. Ciclo concluído não é reexecutado para refazer relatórios; conferências posteriores terão recibos próprios. Não comprar computação.

## Análise predefinida e operação

Contraste principal: MSE pré-normalização menos MSE pós-normalização corrigida na avaliação retrospectiva. Negativo favorece pré-normalização. Desenvolvimento separado. Média de escores entre seeds e pesos iguais entre moedas/contextos/blocos, sem ensemble. Reportar magnitude absoluta/relativa, RMSE, MAE, viés, direção como diagnóstico e estabilidade entre seeds. Os resultados herdados devem ser identificados como tal.

Bootstrap pareado em blocos de dias UTC, 2.000 réplicas, seed20261020, 14 dias principal e sensibilidades7/28; mesmas reamostragens, sem atravessar folds. Contrastes com LSTM/Naive/ARIMA e decomposições por contexto/moeda são secundários. Não selecionar subconjuntos favoráveis nem interpretar contagem de vitórias como teste estatístico. Os intervalos não cobrem toda a seleção de hipóteses retrospectivas entre ciclos.

Simular somente as novas previsões Mamba com a política Spot já fixada: decisão00:00UTC, execução00:01, saída24h depois, comprado/caixa, sem futuros/alavancagem/stop, capital10.000USDT; taxas/slippage/limiar base e agravados iguais ao protocolo original. Comparar ao par pós-normalizado corrigido, reutilizando resultados financeiros antigos. Mesmos sinais base no cenário agravado, ausências explícitas e contas auditadas contra os minutos. Não confundir melhor MSE com lucro.

Publicar apenas fases completas, com 192 novos resultados, 192 pares diretos e 416 referências herdadas por fase (Mamba pós-normalizado corrigido e LSTM/ARIMA/Naive). Os Mamba da primeira execução continuam disponíveis historicamente, mas não substituem o comparador corrigido neste contraste. Relatório automático permanece dentro da execução; relatório interpretativo e conferência posterior em caminhos próprios.

## Aceite e encerramento

Exigir qualificação, controles, grade exata, recargas, duas publicações, preservação antes/depois e conferência posterior independente antes da conclusão científica. Documentar incidentes, resultado nulo/desfavorável, limitações e classificação retrospectiva. Não continuar buscando parâmetros até obter vitória. Atualizar andamento e catálogo pelo estado real; o protocolo não declara treinamentos concluídos.
