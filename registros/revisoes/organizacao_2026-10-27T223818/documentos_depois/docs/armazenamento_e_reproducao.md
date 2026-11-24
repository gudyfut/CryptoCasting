# Preservação e reprodução entre máquinas

Política de 27/10/2026, registrada na [ADR 0003](adr/0003-preservacao-e-organizacao.md). O objetivo é que o TCC possa ser consultado e reproduzido sem depender de um único notebook. Um manifesto ou ponteiro não substitui o arquivo que descreve.

## O que guardar e onde

| Material | Git comum | Pacote completo no GitHub Releases |
|---|---|---|
| Código, configurações, protocolos, ADRs e documentação | Sim | Cópias congeladas junto da execução |
| Métricas, épocas, configuração do otimizador, auditorias e descrição de cada tentativa | Sim, para os ciclos ativos | Sim |
| Logs científicos, falhas e revisões | Sim, quando de tamanho adequado | Completos, inclusive tentativas interrompidas |
| Checkpoints treinados e previsões individuais Parquet | Fora do histórico Git por padrão | Sim, todas as células e seeds, não só vencedoras |
| Dataset processado, máscaras e escalas | Manifestos e recibos JSON | Arquivos completos para evitar nova preparação |
| Portal de previsões | Código no Git | Exportação completa `dados/portal/` |
| Brutos Binance | URLs, checksums e auditorias do estudo ativo | Opcional; manter também cópia externa verificada |
| Cache, ambientes, dependências e locks de processo | Não | Não; registrar versões do ambiente |

Pequenos binários já versionados, como checkpoints sintéticos de qualificação, permanecem preservados. Não reescrever o histórico para removê-los. O tamanho por arquivo e o volume total devem ser medidos no notebook antes da publicação; não assumir que os modelos treinados são grandes apenas pela extensão `.pt`.

O GitHub bloqueia arquivos maiores que 100 MiB no Git comum e recomenda repositórios pequenos. Releases distribuem binários vinculados a uma versão do projeto. Git LFS é uma alternativa para acompanhar binários diretamente pelos caminhos do repositório, mas envolve armazenamento/download de objetos e cotas próprias. Nesta organização, adotam-se pacotes por ciclo em Releases; LFS não foi ativado e nenhum serviço pago foi contratado. Fontes oficiais: [arquivos grandes](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github), [Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases) e [Git LFS](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage).

## Organização dos pacotes

Publicar separadamente o dataset `d25f6a93a9900725f51e`, a referência `1e7c5ed662fba55ddd25`, a extensão `7868a4d847c1410fc681` e a exportação do portal. Preservar a estrutura relativa à raiz do repositório. Incluir fontes congeladas, ambiente, previsões, checkpoints, métricas, logs, tentativas malsucedidas e recibos. O pacote da extensão não deve omitir seus dois controles reexecutados.

Cada publicação deve ter um índice versionado em `registros/distribuicao/`, a criar quando os pacotes estiverem disponíveis, contendo:

- ID do dataset/ciclo, commit usado para distribuição e identidade científica original (não são a mesma coisa).
- Data UTC, máquina de origem, escopo e classificação: parcial ou completo.
- Nome e tamanho em bytes de cada pacote, URL real de download e SHA-256.
- Inventário dos caminhos originais com tamanho e SHA-256 de cada arquivo.
- Resultado da conferência após download/restauração e pendências conhecidas.

O índice não deve conter URLs inventadas nem declarar upload concluído antes da verificação. Dividir pacotes grandes em volumes menores que o limite vigente dos anexos de Releases; não anexar milhares de checkpoints individualmente. Não sobrescrever uma publicação concluída para ocultar falhas; usar nova versão e vínculo com a anterior. Manter cópia de segurança independente do GitHub.

## Procedimento no notebook

1. Identificar a execução e conferir PID, lock e logs. Não iniciar outro treinamento para produzir arquivos ausentes no desktop.
2. Inventariar os arquivos e medir tamanhos. Referência e extensão estão concluídas, conforme fechamento de 27/10 no notebook. Para ciclos futuros em andamento, só produzir snapshot identificado como parcial, contendo arquivos estáveis. Não arquivar um checkpoint enquanto ele está sendo escrito. O pacote final exige grade e auditorias concluídas.
3. Conferir fontes e artefatos contra os manifestos existentes. Se houver divergência, registrar e investigar antes de publicar como reprodução íntegra. Não recalcular recibos antigos para acomodar alterações.
4. Copiar para uma área de empacotamento, preservando bytes e caminhos; produzir inventário e pacotes sem editar os originais. Conferir os arquivos copiados contra a origem.
5. Revisar os arquivos leves elegíveis no Git, incluindo tamanhos e possíveis informações privadas nos logs. Nunca executar `git add dados` sem revisar o inventário. Não incluir caches ou credenciais.
6. Publicar os pacotes no Release correspondente e registrar seus links/hashes. Baixar novamente e conferir em área separada, antes de considerar a preservação externa concluída.

O `.gitignore` agora permite JSON/CSV/Markdown/fontes Python/logs dos ciclos `retorno24_*` e `penalizacao_*`, JSON dos datasets `retorno24_*` e auditorias/checksums da coleta `binance_spot_1m`. Binários, portal e dados antigos continuam excluídos do Git comum. Essas regras não impõem limite de tamanho: logs ou CSVs muito grandes devem entrar no pacote e ter índice leve. Arquivos de PID ativo, locks e escritas parciais não são sincronizados como estado atual; suas cópias históricas nos incidentes continuam preservadas.

## Procedimento na máquina de destino

1. Obter código, documentação e índice de distribuição da versão desejada.
2. Baixar os pacotes relacionados e conferir SHA-256 antes de extrair.
3. Extrair em área separada; validar caminhos, inventário e hashes individuais. Não sobrescrever arquivos locais diferentes nem a execução ativa.
4. Colocar os artefatos nos caminhos originais após a conferência. Verificar os ponteiros, dataset e recibos. Guardar um registro de restauração com data, host, escopo e resultado.
5. A interface deve distinguir resultados históricos disponíveis, artefatos ausentes e progresso observado em outra máquina. Para reproduzir inferência CUDA, qualificar o ambiente local; um download íntegro não certifica o hardware.

Um `git pull` não baixa anexos de Releases. O download dos pacotes é uma etapa explícita. Treinar novamente ou recoletar não substitui recuperar os modelos e previsões que sustentam os resultados já publicados.

## Finais de linha e hashes

Os hashes científicos conferem bytes. LF e CRLF podem produzir o mesmo texto visível e hashes diferentes. A revisão da [ADR 0004](adr/0004-rastreabilidade-de-ciclos.md) mantém `-text` nos artefatos científicos e estende essa preservação a `registros/`, ao arquivo histórico e às fontes/configurações/protocolos/testes congelados. A regra inicial de forçar LF em registros foi substituída: recibos e snapshots podem ter bytes originais diferentes e não devem ser normalizados. Documentos editoriais como AGENTS e ADRs continuam com LF. Nenhuma dessas regras reescreve blobs antigos do Git nem corrige automaticamente checkouts existentes.

Não usar renormalização em massa ou regeneração de manifestos em um ciclo congelado. Restaurar os bytes originais a partir de uma cópia conferida, por arquivo, preservando a evidência da divergência. No notebook que está treinando, não fazer checkout que substitua fontes científicas enquanto o processo está ativo.

## Situação verificada no desktop em 27/10/2026

- Código sincronizado com o commit `8f30f5478852c8a41983e2579e98c7f6773b47da`; dataset e diretórios das duas execuções ausentes nesta máquina.
- Dos 7.082 arquivos do manifesto de preservação da referência, 6.615 estavam ausentes, todos dentro da pasta da execução original. Isso não inventaria todos os dados que devem ser transferidos.
- As duas publicações, com 432 arquivos no total, apresentaram diferenças de hash explicáveis por CRLF. Os manifestos armazenados no Git conferiram com os recibos; o checkout local não foi restaurado nesta organização.
- `previsao24/coleta.py` apresentou hash diferente do congelado, além da conversão comum LF/CRLF. Comparação com a cópia congelada do notebook continua pendente; não atribuir a diferença ao treinamento sem investigação.
- O registro recebido do notebook confirma 299 ajustes corrigidos e dois controles na auditoria de retomada de 27/10. Não é progresso em tempo real.

Esta mudança organiza preservação e documentação. Não transferiu os arquivos ausentes, não publicou Releases e não alterou fontes científicas ou recibos congelados. A publicação completa deve ser feita a partir dos artefatos do notebook, com as verificações acima.

## Conferência posterior no notebook em 27/10/2026

O relato do desktop acima é um snapshot histórico. No notebook, `previsao24/coleta.py` e sua cópia congelada conferiram exatamente com o hash `c9b5e9a31ed803521ed00c3a145299863da61e9e195dcb13250be61e8c116652`. O blob de HEAD `9af48a9` tem hash `65612ad1cbf6129866aea95e006f55036e2849b52239b5454a87a0b5ed7c815e`; neste notebook a diferença para esse blob é exclusivamente CRLF/LF. Isso esclarece a origem local usada no treinamento, mas não certifica nem restaura o arquivo do desktop. Evidência em [início da revisão](../registros/revisoes/organizacao_2026-10-27T223818/inicio.json).

O [catálogo](../registros/catalogo_estudos.json) e sua auditoria distinguem o estado histórico da disponibilidade local. Para conferência no executor: `python manutencao/auditar_catalogo.py --integridade --exigir-completo`. O recibo mede arquivos não rastreados elegíveis e compara fontes locais com HEAD; não executa commit/push nem prova backup. Consultar [andamento](andamento.md) para o resultado desta revisão. Fontes congeladas e documentos anteriores vinculados ao fechamento foram preservados; as publicações externas continuam pendentes.
