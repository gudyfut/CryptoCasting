# Preservação, organização e reprodução

O catálogo em `registros/catalogo_estudos.json` identifica os ciclos, suas heranças e as evidências. Um índice ou manifesto não substitui os arquivos descritos. Organização local e presença no Git não comprovam backup externo. Este guia complementa as [diretrizes de pesquisa](diretrizes_pesquisa.md) nas tarefas de preservação, limpeza e transferência.

## Separação dos materiais

| Material | Local |
|---|---|
| Núcleo reutilizável | `codigo/`: módulos de mercado, entradas, modelos, treinamento, avaliação, simulação e infraestrutura |
| Receitas e decisões | `configuracoes/`, `docs/adr/` e protocolos identificados |
| Modelos, previsões e resultados | `dados/experimentos/<identidade>/`, com os layouts originais de cada ciclo |
| Recibos, controles, logs e incidentes | `registros/` e as próprias execuções |
| Leitores posteriores úteis | `codigo/analises/`, agrupados em `codigo/analises/etapas/` |
| Executores e ferramentas encerrados, testes específicos antigos e versões editoriais anteriores | `arquivo/desenvolvimento_encerrado/fontes.zip`, com índice de caminhos e hashes |
| Redação futura | `escrita_tcc/`, com narrativa e LaTeX em redação |

Os snapshots em `dados/**/fontes/` fazem parte da evidência científica. Checkpoints, dados, controles e tentativas malsucedidas não são caches. Os ciclos concluídos mantêm suas fontes originais nos snapshots e pacotes; a versão de trabalho em `codigo/` não substitui a identidade congelada.

## Fontes históricas e verificação

A reorganização física não altera identidades científicas. Os índices em `arquivo/fontes_referencia/indice.json`, `arquivo/fontes_referencia/editoriais.json` e `arquivo/desenvolvimento_encerrado/indice.json` identificam seus pacotes, caminhos e SHA-256 dos originais. Os ZIPs contêm os bytes originais, incluindo finais de linha. Não modificar esses índices para aceitar alterações nas fontes.

As versões editoriais anteriores à revisão das orientações de 11/11/2026 estão no [pacote de orientações](../arquivo/orientacoes_2026-11-11/fontes.zip), com [manifesto próprio](../arquivo/orientacoes_2026-11-11/manifesto.json). Esse snapshot editorial é conferido pelo seu manifesto e não integra o índice de resolução das fontes científicas. Uma revisão de guia vigente não muda o conteúdo que um fechamento histórico descreve.

Usar `python -m manutencao.auditar_repositorio --integridade --exigir-completo` para conferir o catálogo organizado. Ele reutiliza os critérios do auditor original e acrescenta a localização explícita das fontes históricas. Um arquivo local divergente continua sendo divergência; o pacote não encobre alterações. O recibo distingue arquivos locais e originais localizados no arquivo histórico.

Usar `python -m manutencao.arquivo_fontes conferir` para conferir o pacote, seus membros e os leitores realocados. Para recuperar fontes, `python -m manutencao.arquivo_fontes extrair --destino <pasta_nova>`. O destino precisa ser novo; não há sobrescrita nem execução automática. Para reproduzir um executor encerrado, preparar uma área isolada com os caminhos originais, as fontes congeladas, o ambiente e os dados daquele ciclo, conforme seu protocolo. Não usar a extração como autorização para retreinar.

## Transporte e backup

1. Identificar a execução e distinguir materiais estáveis de arquivos ainda sendo escritos. Conferir processo, locks e logs antes de qualquer retomada.
2. Verificar os manifestos e congelamentos existentes. Não regenerar hashes para aceitar divergências.
3. Preparar pacotes por ciclo com fontes, ambiente, configurações, dados preparados, escalas, todos os modelos/seeds, previsões, logs, controles, incidentes e publicações necessários à reprodução.
4. Registrar commit de distribuição, identidade científica, caminhos, tamanhos, SHA-256 e escopo parcial ou completo. O código versionado e os pacotes de artefatos são materiais complementares.
5. Transferir para armazenamento externo e registrar URLs reais quando existirem. Um commit local, `git push` de código ou arquivo ignorado pelo Git não demonstra preservação dos binários.
6. Baixar ou restaurar em área separada e comparar os hashes antes de declarar o backup externo conferido. Um `git pull` não baixa automaticamente anexos de Releases.

A política de distribuição por ciclo foi definida na [ADR0003](adr/0003-preservacao-e-organizacao.md). Nenhuma publicação externa é presumida nesta organização. As observações antigas de disponibilidade entre desktop e notebook estão preservadas na versão anterior deste guia, dentro do pacote histórico; não representam o estado atual.

## Limpeza e manutenção documental

Antes de editar documentos vinculados a fechamentos, conservar os bytes anteriores em versão recuperável. Protocolos, configurações, fontes e recibos congelados são anexos científicos imutáveis; a atualização editorial não autoriza reescrevê-los. Não editar o PDF acadêmico original nem reescrever o histórico Git.

Excluir apenas caches, builds e temporários comprovadamente regeneráveis, ou conteúdo editorial redundante após verificar dependências e preservação. Checkpoints, previsões, dados, controles, incidentes e tentativas malsucedidas não são lixo por terem resultado ruim ou terem sido produzidos com IA. Conferir caminhos de destino, dependências e hashes antes de mover ou excluir; não substituir arquivos em uso por processo ativo.

Depois da manutenção, conferir vínculos, catálogo e integridade pertinente. Declarar o que foi preservado, movido ou eliminado, o alcance da auditoria e eventuais limitações. Para comandos e ambientes, consultar [ambiente e execução](ambiente_e_execucao.md).

## Finais de linha e ambiente

Os hashes científicos conferem bytes. LF e CRLF podem representar texto visível equivalente e ainda assim produzir hashes diferentes. Preservar `.gitattributes`, fontes congeladas, configurações, protocolos e recibos. Não fazer renormalização em massa nem checkout que substitua fontes durante uma execução ativa.

Restaurar dados e checkpoints não qualifica automaticamente CUDA, bibliotecas ou hardware. Qualificação, reprodução numérica e recuperação de artefatos são verificações distintas. As auditorias locais não recalculam todas as métricas nem certificam toda fonte bruta ou execução real de mercado; seus recibos delimitam o escopo.

## Distribuição pelo Git

O clone inclui código, configurações, recibos e tabelas de síntese. A redação e os pacotes que contêm cópias dela ficam no acervo local. Em `arquivo/fontes_referencia/` e `arquivo/desenvolvimento_encerrado/`, o índice público `pesquisa.json` identifica as fontes técnicas e seus hashes. O executor local também pode ler o índice integral preservado. Dados completos, checkpoints e históricos detalhados de operações são distribuídos separadamente conforme a ADR0003.
