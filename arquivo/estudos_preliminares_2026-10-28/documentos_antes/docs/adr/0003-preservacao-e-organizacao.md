# 0003 — Organizar decisões e preservar artefatos entre máquinas

- Decisão e registro: 27/10/2026.
- Situação: organização adotada; distribuição completa dos artefatos pendente.
- Origem: solicitação do pesquisador para preservar o TCC no GitHub e tornar o AGENTS.md um guia geral com referências a decisões e registros.

## Contexto

O Git transportou código e relatórios, mas o `.gitignore` excluía toda a pasta de experimentos, inclusive descrições das tentativas e métricas. Os diretórios do dataset atual e das duas execuções não estavam no desktop. O AGENTS.md misturava instruções permanentes, decisões e contagens de execução.

## Decisão e alternativas

- AGENTS.md permanece orientativo; ADRs explicam escolhas; andamento descreve evolução; registros sustentam os fatos; artefatos permanecem nos diretórios originais de cada tentativa.
- Versionar metadados, resultados tabulares, auditorias e logs científicos de tamanho adequado. Não excluir todos os resultados por estarem em `dados/`.
- Distribuir checkpoints, previsões completas, dataset processado e portal como pacotes por execução em GitHub Releases, com inventário e SHA-256. Git LFS é alternativa se tamanho, frequência e cotas justificarem; não ativado nesta mudança.
- Brutos podem ficar fora do Git, mantendo URLs, checksums e auditorias. Conservar cópia de segurança externa, inclusive dos artefatos insubstituíveis, além da distribuição pelo GitHub.

Colocar todos os binários no histórico Git dificulta clonagem e acumula versões. Deixá-los apenas no notebook torna a reprodução dependente daquela máquina. Releases permitem vinculá-los ao mesmo projeto sem incorporá-los ao histórico de cada commit.

## Consequências e limites

Um clone simples terá código e evidências leves; a reprodução completa também requer baixar os pacotes. A exceção no gitignore apenas torna arquivos elegíveis: não os adiciona, publica ou sincroniza automaticamente. Pacotes só serão considerados publicados após upload e conferência de download; a publicação ainda depende dos arquivos do notebook.

Nenhuma fonte científica congelada, protocolo ou resultado anterior foi modificado por esta organização. Não reescrever o Git para migrar arquivos antigos. Divergências de bytes e de fontes são pendências de integridade, não motivo para regenerar recibos.

## Aplicação

Detalhes, responsabilidades e pendências estão na [política de preservação](../armazenamento_e_reproducao.md) e no [mapa de registros](../../registros/README.md).
