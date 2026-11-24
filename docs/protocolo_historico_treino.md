# Histórico acumulado versus janela móvel de12meses

Autorizado em05/11/2026 pelo pedido “arrume tudo corretamente e pode prosseguir com essa primeira etapa de averiguação”. Identificador lógico `historico_treino_001`; identidade executiva após qualificação em [ponteiro próprio](../registros/historico_treino/execucao.json). Código novo em `experimentos/historico_treino/`, configuração em `configuracoes/historico_treino_001.json`. [ADR0030](adr/0030-historico-acumulado-movel.md).

## Pergunta e fator

Testar se limitar o passado usado para aprender os pesos melhora o sinal e a operação da receita C06 do ciclo operacional `f0dd11f393b5e26edaf8`. O diagnóstico revelou mudança de distribuição de volatilidade, não provou mudança da relação condicional ou superioridade da janela móvel. Acumulado pode ganhar por diversidade/amostra; móvel pode ganhar por relevância recente.

Somente início de T muda. C06: OHLC em log relativo ao fechamento anterior; log1p(V); dois canais de volume relativo24/168h; sete canais padronizados no suporte de T; contexto168h; dois payoffs líquidos24h; MSE; Mamba oficial CUDA estado16,largura32,dois blocos,dropout0,1,pré-LayerNorm; AdamW0,0002,decay0,001 respeitando marcações; batch64,micro32,clipping1,100épocas máximas,paciência10. Seleção por MSE real de V e recarga exata.

Mesmas seeds42/17/2026, rótulos, origens V/C/S, arquitetura, função de perda, regras de parada e operação. Mudanças de scalers/normalização do alvo são consequências da janela, ajustados exclusivamente no respectivo T. Histórico de12meses delimita origens de treino; cada exemplo mantém suas168h anteriores e indicadores causais, inclusive aquecimento anterior ao início. Não interpretá-lo como proibição de contexto pré-fronteira.

Mais dados significam mais atualizações por época sob o batch fixo. Portanto o contraste mede a mudança de histórico sob o mesmo procedimento de treino, não uma comparação de quantidades de informação com orçamento de gradientes igual. Registrar épocas/tempo/escalas; não atribuir causalidade exclusivamente a regime. Não selecionar amostras por retorno futuro.

## Calendário preservado

|Recorte|Fim T / começo V|Começo T acumulado|Começo T móvel12|V|C|S|
|---|---|---|---|---|---|---|
|D1|01/10/2022|01/01/2021|01/10/2021|2022T4|2023T1|2023T2|
|D2|01/01/2023|01/01/2021|01/01/2022|2023T1|2023T2|2023T3|
|D3|01/04/2023|01/01/2021|01/04/2022|2023T2|2023T3|2023T4|

Limites finais exclusivos em UTC; purga1442min compatível com realização24h e latência; aquecimento comum336h. Conferir realizações por origem e igualdade dos alvos e populações V/C/S. O calendário ancestral mantém seis meses entre fim de T e início de S. **Não incorporar agora a proposta de V/C mensais**: seria outro fator. Uma janela móvel reestimada nesses recortes não é adaptação contínua ao último mês.

Todos esses períodos já foram consultados. S é retrospectivo/exploratório. Recortes possuem V/C sobrepostos com S de outros recortes; não somar fases como observações independentes nem usar calibração posterior para política anterior. Não abrir2024–2025,2026 ou buscar nova receita.

## Orçamento fechado

18ajustes principais:2braços×3recortes×3seeds. Dois controles reais adicionais em D1/42, um por braço. Ordem inicial: acumulado42 e repetição; móvel42 e repetição. Ambos aprovados antes dos16principais restantes. Mesma época no controle; previsões atol1e−5,rtol0; dados/alvos/origens iguais. Cada recarga individual exige igualdade exata.

Todos os18principais são novos, apesar de haver C06 acumulado histórico. Isto facilita controle pareado no mesmo ambiente/execução. Nenhuma herança conta como ajuste novo. Não treinar6meses, ampliar seeds, buscar com Astra ou avaliar os anos finais. Não mudar a janela se perder.

Qualificação artificial de duas repetições por braço,2épocas,atol1e−7,sem contar como treino real. Teto de12h desde início executivo; no máximo45min por ajuste com preservação de tentativa parcial. Falha interrompe a fila sem repetição automática. Reexecução de ciclo iniciado é bloqueada. GPU/processo/boot/locks conferidos; nenhuma computação paga ou ordem real.

## Dados e preservação

Reutilizar dados futuros2021–2023 `7535d44ba23eb371fe4d`, validando manifestos/hashes. Regerar alvos uma vez e comparar todos os arrays com o contrato antigo C06 (payoff, realização e motivo). Fontes ancestrais importadas somente como bibliotecas, nunca chamar seu coordenador para executar/relatar. Congelar fontes usadas, dados, protocolo, configuração, qualificação e autorização sob nova identidade. Verificar toda a execução ancestral antes/depois; não regenerar seus recibos.

Qualificação exige testes do motor, dados, atualização CUDA e recarga, contraste sem mudança V/C/S e orçamento, bootstrap, diário marcado a mercado. A ausência de tabelas históricas de tarifas/liquidação continua limitação. A coleta anterior tem funding com mark exato ausente em parte dos eventos; manter aproximação adversa identificada.

## Operação e contagem exata

Motor congelado: entrada após1min, comissão0,05% por perna, slippage base0,05%; estresses0,10%/0,15%. Funding histórico; stop=max(sigma24 causal,0,5%),take1,5×stop,prazo24h. Uma posição; ambiguidade stop primeiro; gaps adversos; filtro/nocional/margem prudencial preservados. Custos de pesquisa, não certificação de conta Binance. Rótulo unitário não contém arredondamento de quantidade da carteira.

**Camada histórica secundária:** as12políticas anteriores (limiar0/10/20bps×risco0,5%/1%×cadência1h/4h) calibradas só em C pela regra congelada. Se nenhuma aprovar, S fica em caixa, sem ocultar métricas das previsões. Cada coorte:36carteiras C +15S=51; seis coortes=306.

**Camada fixa principal:** limiar0,risco0,5%,cadência4h para ambos os braços, sem seleção em C/S. Avaliar cada seed, média das previsões das três seeds (ensemble) e previsão constante igual à média de payoff de T. São5unidades×5cenários×6coortes=150carteiras. Cenários: bilateral base,slippage2x,slippage3x,somente compra,somente venda. Comprada/vendida são contrafactuais com carteira própria, não simples atribuição dos trades do bilateral. Caixa tem retorno conhecido zero, sem carteira adicional.

Total **456carteiras novas**, sem simular controles. A política fixa pode operar mesmo se a calibrada reprovar; seus resultados são diagnósticos, não autorização de conta real. Não aplicar agora novos tetos25%/35%, outro risco, novos custos ou novas saídas. O protocolo não promove vencedora automaticamente.

## Métricas, comparação e relatório

Primário preditivo: diferença MSE médio (móvel−acumulado), peso igual entre três recortes e três seeds, com MAE, viés por lado e referências zero/média T. Ordenação por grupos definidos em C e aplicados a S, correlação por lado e preferência compra/venda são diagnósticos. Payoff hipotético sobreposto não é retorno de carteira.

Primário econômico: mesma política fixa; comparar médias de crescimento logarítmico, retorno e drawdown por trimestre, separando carteira ensemble de média de carteiras por seed. Mostrar estresse, operações, pnl por lado e média T. Política selecionada em C é secundária e não substitui o primário se favorecer a candidata. Retornos de carteiras independentes não se somam ou compõem como única conta.

Bootstrap pareado2000réplicas,blocos não circulares14dias,sensibilidades7/28. Seeds sorteadas como unidades com mesmos índices nos dois braços/recortes; dias sincronizados dentro do recorte. Intervalos de MSE usam soma/contagem por dia para preservar pesos por origem. Econômico: deltas de log-retornos diários do ensemble; diário reconstruído pelo ledger e mark-close, não extremos artificiais da curva conservadora de drawdown. Três recortes são estratos fixos, não amostra de todos os regimes. IC95 exploratório; não corrige toda a seleção histórica e não garante lucro futuro.

Conferir métricas das previsões independentemente, cada ledger com auditoria separada e cobertura exata18+2/456. Guardar resumo, dados de diagnóstico, carteiras completas, manifesto e relatório em `publicacao/` da execução. O coordenador atualiza estado até concluído/auditado ou incidente. Resultados positivos isolados não decidem uma configuração final; resultados negativos permanecem integrais.
