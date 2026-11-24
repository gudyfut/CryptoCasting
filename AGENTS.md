# Guia base do CryptoCasting

Este é um repositório de pesquisa e produção do TCC: reúne código, dados, experimentos, análises, referências e materiais de escrita. O objetivo é investigar configurações de entrada, pesos, hiperparâmetros, estruturas e tipos de previsão, registrando conclusões fundamentadas para um bom artigo. A contribuição acadêmica pode incluir resultados negativos ou inconclusivos; obter um modelo lucrativo não é condição de sucesso.

## Leitura e orientação

Antes de agir, ler as [diretrizes de pesquisa](docs/diretrizes_pesquisa.md) e o [plano atual](plano.md). Depois, abrir os documentos pertinentes à tarefa na tabela abaixo. Esses links indicam instruções a consultar explicitamente; não presumir que seu conteúdo foi carregado com este arquivo.

| Trabalho | Consultar antes de executar |
|---|---|
| Propor, treinar, validar, testar ou analisar | [Procedimento de pesquisa e registro](docs/registro_de_experimentos.md); protocolo/configuração e estado do ciclo no [catálogo](registros/catalogo_estudos.json) |
| Alterar código, ambiente, comandos ou interface | [Ambiente e execução](docs/ambiente_e_execucao.md); arquitetura da camada no [índice documental](docs/README.md) |
| Organizar, limpar, preservar ou transferir | [Armazenamento e reprodução](docs/armazenamento_e_reproducao.md) |
| Interpretar evidências e escrever o TCC | Roteiro de redação (local: `docs/roteiro_redacao_tcc.md`) e espaço de escrita (local: `escrita_tcc/README.md`) |
| Retomar contexto histórico | [Cronologia](docs/andamento.md), [síntese da exploração com IA](docs/exploracao_ia.md) e [decisões históricas](docs/adr/README.md) |

Usar o [README](README.md) para localizar materiais. Ler o necessário para a tarefa, sem carregar todos os protocolos ou restaurar o legado por rotina. Receitas, resultados e autorizações antigas valem para suas identidades; não são regras gerais para novos estudos. Havendo divergência de estado, conferir os artefatos e o computador executor antes de agir.

## Regras gerais

- Respeitar o pedido atual e o escopo já autorizado. Separar proposta, autorização, qualificação, execução e auditoria; não iniciar ou retomar treino/busca por inferência de um documento histórico. Não pedir novamente uma autorização que já cobre a ação.
- Preservar causalidade, seleção independente do teste e rastreabilidade. Distinguir observação, interpretação e hipótese; não inventar resultados, referências ou aprovação acadêmica.
- Manter fontes, dados, configurações e artefatos congelados intactos. Alterações científicas precisam de identidade própria; nunca atualizar hashes para aceitar divergências nem apagar tentativas por desempenho ruim.
- Antes de iniciar ou retomar processos, conferir ambiente, host, PID, locks, logs e progresso. Não duplicar processo vivo, substituir implementação silenciosamente ou treinar para compensar artefatos ausentes.
- Não enviar ordens reais. Uso de conta de negociação, alavancagem real ou computação paga exige autorização específica; tarefas de simulação e pesquisa não a concedem.
- Atualizar o documento que já cumpre a função. Não criar um relatório por conversa nem duplicar resultados nos guias; registrar achados relevantes com vínculo às evidências.
- Usar identificadores novos em português, preservando nomes oficiais das APIs. Conferir o que mudou com verificações pertinentes e informar limites, falhas e testes não executados.
