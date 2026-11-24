# ADR0026 — Auditoria e revisão operacional F03

Data: 04/11/2026. Decisão autorizada pelo pedido explícito de revisar/corrigir os simuladores e apresentar novas simulações. **Zero treinamento e nenhuma ordem real.**

F01/F02 são preservadas. A F02 já demonstrou que Spot e futuro comprado sem funding se aproximam sob premissas iguais. Seu braço bilateral, porém, também acelera a redução de compras: não isola apenas permitir short. A comissão Spot em USDT era uma aproximação deliberada. A verificação de exposição podia ignorar reversão de menor quantidade absoluta; não houve recusa/violação registrada na F02, mas a implementação deve cobrir esse caso.

Criar `simulacao_operacoes/revisada/` com comissão no ativo recebido, quantização conservadora, ordens reduceOnly separadas da abertura, mínimo dispensado apenas na redução de futuros, tratamento de resíduos e verificação de margem em toda nova exposição. Auditor independente não reutiliza a fórmula da política. Manter leitores de mercado e previsões congelados, com seus hashes.

Separar três políticas previamente fixadas: Smart original; encerramento integral ao sinal contrário seguido de eventual abertura proporcional; a segunda com filtro somente para entrada/aumento. As duas últimas são hipóteses de política, **não correções de erro nem garantia de lucro**. Comissão/filtros/executor revistos constituem um pacote técnico, não ablação isolada de cada item.

Orçamento: 1.152 carteiras de modelos + 48 controles caixa/comprar-manter, 1.200 no total. Dois modelos já treinados, quatro blocos, oito seeds, três mercados/políticas e dois cenários de custo. Sem busca, treino, promoção ou seleção pelo lucro. Qualificar e congelar antes de executar; falha interrompe e é preservada.

Método e limitações em [protocolo F03](../protocolo_revisao_operacional.md). Resultados serão retrospectivos; custos privados, livro de ofertas, filtros históricos e liquidação real não são certificados.
