# Complemento diário — protocolo 001

Autorizado pelo Goal de 17/11/2026. O texto integral do pedido é preservado em `registros/complemento_diario/autorizacao.txt`; a configuração em `configuracoes/complemento_diario_001.json` e o recibo de início fixam orçamento e prazo. A autorização inclui implementação, controles, treinamento, simulação, auditoria e documentação científica. Não inclui revisão de `escrita_tcc`, busca de receitas, ordens reais ou computação paga.

## Ordem, critérios e exposição

Inventariar e conferir pais → qualificar → congelar a etapa → controles reais → grade LSTM → avaliação/auditoria → sensibilidade → deslocamentos → auditoria do núcleo → decisão condicional timestamp → auditoria final. Trabalho técnico independente pode avançar durante esperas ou impedimentos de outra camada, sem dispensar seus controles. Novos resultados não determinam expansão de grade ou seleção de vencedores. Falhas técnicas são preservadas; resultados negativos não interrompem a matriz.

2024–2025 e 01/01–10/11/2026 são retrospectivos, com seleção histórica/adaptativa. Não há confirmação prospectiva ou correção completa da multiplicidade. Fontes e publicações anteriores permanecem intactas. Cada etapa possui identidade, snapshots, dependências, estado e fechamento próprios; o congelamento geral de escopo antecede resultados novos.

## LSTM reestimada em BTC

Reutilizar os quatro blocos e preparações do walk-forward A/L, conforme `docs/protocolo_walkforward_diario.md`, reconstruindo e comparando janelas/escalas. Populações de teste 167/169/166/169, contexto interno de 14 dias, última janela excluída. Não misturar divisão fixa. Receber os mesmos seis canais padronizados no treino e prever retorno simples diário sem padronizar alvo.

Receita LSTM preservada: duas camadas de 32 unidades, dropout zero, unidirecional, entrada física B×6×14 transposta internamente; Adam 0,001, decay 0,001, lote32, 200 épocas, StepLR100/0,5, sqrt(MSE+1e-8), sem clipping/early stopping, primeiro menor RMSE global de validação. Seeds42/17/2026. Teste ausente do treinador. São12 ajustes científicos; dois controles: reprodução BTC42 fixa e repetição B1/42. Exigir trajetória científica, seleção e previsões de validação exatas, excluindo tempos e metadados de identidade; pesos recarregados devem reproduzir previsões exatamente. Não relaxar após observar resultados. Aprovar controle fixo antes do ajuste B1 e repetição B1 antes da grade restante.

MSE principal, RMSE/MAE/skill Naive, BA, sinais, dispersão; médias individuais e ensemble de preços equivalentes separados. Contrastes LSTM−A/L/Naive por bloco e forma; bootstrap pareado de blocos consecutivos7/14/28,2.000réplicas,14principal, seeds pareadas reamostradas somente para médias individuais. Não atravessar blocos nem declarar vencedor global por IC isolado. Carteiras individuais e ensemble nos3custos; blocos independentes. Diferenças de taxas e arquitetura são diferenças de receitas.

## Sensibilidade operacional

Ensembles A/L/LSTM ×4moedas×2períodos fixos (24populações) e ×4blocos BTC (12populações), cruzados com filtros0,0015/0,002/0,0025 e slippages0,0001/0,0002/0,0003:324combinações. Herdar/certificar cenários originais e reproduzir controles antes da interpretação. Sem treino ou alteração de previsões; preservar regras por instrumento, comissão0,0005, funding, latência1min, alvo95%, capital10mil, continuidade e encerramento final.

Medir retorno, DD intraminuto, exposição efetiva por lado/caixa, episódios, reversões, ordens, giro, custos/funding, falhas e mudança das decisões contra0,002. Semestres da mesma curva não reiniciam patrimônio; retornos não são somados. Concentração de ganhos de movimento do contrato não é participação no lucro líquido. Não escolher filtro/custo vencedor.

## Diagnóstico de exposição

24ensembles fixos, filtro0,002 e slippage0,0001. Sortear antes das simulações99 offsets sem reposição entre14 e n−14, inclusive, com seed2026111705, os mesmos para cada n; preservar lista. Deslocamento np.roll das decisões -1/0/+1, nunca dos preços/funding. Adaptar decisões em sinais de preço estritamente dentro dos lados desejados e verificar sua decodificação; o simulador original depende somente do lado para dimensionar. Deslocamento zero deve reproduzir integralmente a carteira original (ledger, curva, métricas). Se a aritmética/contrato impedir equivalência, investigar antes da grade.

2376carteiras deslocadas, mais24controles zero. Mesmo simulador e auditoria independente, mercado carregado uma vez por população quando possível, sem aproximar contabilidade. Preservar resultados/ledgers/curvas ou falha identificada para cada offset. Não eliminar duplicatas, casos constantes ou resultados adversos. Quantificar contagens de decisões, exposição executada, bordas, episódios, giro e custos; não alegar pareamento exato de risco.

Distribuições e percentil descritivo do original para retorno/crescimento log diário/DD. Percentil definido como100×(quantidade inferior+0,5×quantidade igual)/N, com sentido de cada métrica explícito. Não é p-valor, IC, estratégia causal ou correção da seleção; circularidade pode misturar regimes. Se houver falhas prudenciais, reportar incidência e resumos condicionais identificados; não emitir percentil que exclua falhas favoravelmente. Degeneração é resultado. Referências passivas/constantes são herdadas e conferidas, sem selecionar o lado ex post.

## Timestamp condicional

Executar somente depois do núcleo auditado sem divergências e com estimativa baseada em tempos medidos que permita concluir auditoria até início+5dias, reservando2dias para artigo. Registrar decisão antes de iniciar; independe do sinal/significância dos achados. BTC, mesmos4blocos×3seeds×A/L:24ajustes novos. Canal0 padronizado recebe zero desde treino até inferência; dimensões, demais canais/escalas, metadados, init/RNG, lotes e receitas A/L preservados. Quatro controles: A42/L42 B1 originais e repetição das variantes A42/L42 B1 sem timestamp. Heranças não contam como treino.

Comparar previsões/ICs/sinais/operações com filtro original e3custos; nos12novos checkpoints A, desativar ramos na inferência e medir contribuição em todas as populações. Não atribuir causalidade durante aprendizado nem generalizar mecanismo. Não ampliar canais/moedas/receitas ou repetir deslocamentos/grade de filtros.

## Entrega e encerramento

Máximo planejado36ajustes científicos+6controles. Fontes/ambiente/configurações, dados/escalas, checkpoints/épocas/seleção, previsões, carteiras/ledgers, tabelas e figuras fora de escrita_tcc; auditoria independente e interpretação em documentos canônicos. Preservar originais antes de atualizar documentos vinculados. Completar núcleo e executar/dispensar condicional pelos critérios registrados, com matriz de requisitos e evidências verificadas. Falha de parte obrigatória impede declarar objetivo completo. Não esperar dados futuros nem ampliar períodos.
