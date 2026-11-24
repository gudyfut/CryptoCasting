# CryptoMamba diário — reexecução técnica reproduzível

Autorização em 05/11/2026: investigar/corrigir reprodução e iniciar novamente treinamento, validação e teste. [ADR0032](adr/0032-reproducao-numerica-cryptomamba.md). Identidade própria preparada somente após qualificação; tentativa anterior `6de6464912e674da1540` preservada integralmente. Este protocolo complementa, sem reescrever, o [protocolo001](protocolo_cryptomamba_diario.md).

## Receita e orçamento

Herdar integralmente os dados Binance USD-M BTCUSDT 2020–2025, versão mensal diária, tratamento das divergências de volume, divisão fixa2020–2023/2024/2025, canais timestamp+OHLCV, contexto14, alvo de fechamento seguinte, arquitetura64/3×4, Adam0,01/decay0,001, RMSE, StepLR100/0,5, lote32, 1.000 épocas e seleção pelo menor RMSE global em validação. Mesmos exemplos1446/351/350. Limite4h por ajuste permanece. Nenhuma recoleta, nova feature ou busca de configurações. 2024–2025 continuam retrospectivos já consultados.

Reiniciar seeds42/17/2026 e repetição42, quatro ajustes novos. Não herdar pesos, épocas ou resultados antigos para completar esta grade. Ordem42→controle42→17→2026. Mesma época selecionada e `rtol=1e-5, atol=0,01 USDT` no controle real; não relaxar após observar resultados. Controle fora das médias. Teste somente após os quatro ajustes e aprovação do controle.

## Correção numérica explícita

`execucao_numerica=mamba1_oficial_scan_ref_cuda`: instanciar a mesma rede Mamba-1 do pacote oficial, usar o forward oficial não fundido e substituir apenas sua referência local ao selective scan pela função `selective_scan_ref` do próprio pacote, executada na GPU. Não modificar globals do pacote instalado ou instâncias de outros ciclos. Convolução causal oficial, projeções, normalizações, resíduos e parâmetros idênticos; sem conversão para CPU, modelo substituto ou fallback silencioso. O kernel fused customizado anterior não é utilizado nesta receita numérica.

Fixar sementes, CUBLAS_WORKSPACE_CONFIG antes de inicializar CUDA, TF32/benchmark desativados e `torch.use_deterministic_algorithms(True, warn_only=False)`. Registrar versões, GPU e hashes das fontes/binários do backend; conferir ambiente novamente antes do treino. Não atualizar bibliotecas compartilhadas.

Qualificação: contratos herdados de dados e contabilidade; sonda por operação; 20 repetições de forward/backward da rede completa para cada caso de seed/lote42/32,17/6,2026/1; igualdade exata entre repetições e equivalência numérica com original (`rtol1e-5/atol1e-4` saída; `rtol1e-3/atol1e-6` gradientes). Essas tolerâncias verificam caminhos de somas diferentes, não alteram o controle real. Dois treinamentos artificiais de50épocas e192exemplos exigem históricos, checkpoints e previsões exatos, recarga exata e teste inacessível. Esses ensaios não são novas seeds de mercado. O controle real de1.000épocas continua obrigatório.

## Operações, análise e preservação

Mesma política diária fechada24h depois, filtro±0,20%, nocional95%, custos, funding e minuto de execução do protocolo001. Mesmos sete grupos, cinco cenários e duas fases:70carteiras. Preservar as métricas, médias de seeds, ensemble separado e bootstrap7/14/28dias; não escolher lado, seed ou cenário por lucro posterior. Não há ordens reais.

Congelar configuração, protocolo, fontes, ambiente, qualificação e vínculos de dados. Preservar os arquivos da execução anterior, inclusive logs/controle reprovado. Novo executor verifica PID, lock exclusivo e GPU livre. Não retoma execução iniciada automaticamente. Nova falha interrompe; não repetir até obter resultado favorável. Publicação e fechamento próprios; nenhuma alteração às fontes originais congeladas.

Comandos: `python -B -m experimentos.cryptomamba_reproducivel.qualificacao` (com CUBLAS_WORKSPACE_CONFIG definido antes da importação); depois `python -B -m experimentos.cryptomamba_reproducivel preparar|conferir-preservacao|executar`. Preparação e conferência de arquivos podem usar Python nativo Windows; treino/qualificação exigem WSL/CUDA. Execução em segundo plano local, sem tarefa agendada.
