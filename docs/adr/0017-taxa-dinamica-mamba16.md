# ADR0017 — Voltar ao Mamba16 e testar redução automática da taxa

Decisão/registro:30/10/2026, antes dos novos diagnósticos e ajustes. O pesquisador autorizou seguir a recomendação, organizar o projeto e executar o necessário; delimitam-se seis ajustes e54carteiras secundárias, sem busca indefinida.

Usar Mamba16 como referência de trabalho e alterar somente a política de taxa constante para ReduceLROnPlateau, mantendo dados,arquitetura,perda,otimizador e parada. Menor taxa constante não equivale a reduzir depois de uma fase inicial. Não se presume que o scheduler resolva sobreajuste. Comparação primária pareada por MSE de validação; demais diagnósticos não escolhem um vencedor pelo teste ou pelo lucro.

Novos ciclos passam a usar o namespace `experimentos/`, com ferramentas de análise em `analises/`, testes e registros próprios. Não mover os pacotes antigos: seus caminhos/códigos/recibos congelados são evidências. Consolidar navegação editorial, limpar apenas caches/sobras comprovadamente descartáveis e preservar versões vinculadas aos fechamentos. Não criar explicações avulsas a cada conversa.

[Protocolo](../protocolo_taxa_dinamica.md), configuração `configuracoes/mamba16_taxa_dinamica_001.json`, entrada `run_experimento.py taxa_dinamica`, estado `registros/taxa_dinamica/estado.json`. CryptoMamba encerra essa linha de investigação sem apagar seus estudos. Nenhuma futura hipótese de Huber,normalização,dropout ou arquitetura fica automaticamente autorizada por este orçamento.
