# Fontes de desenvolvimento encerrado

No Git, as fontes técnicas estão em [pesquisa.zip](pesquisa.zip). O [índice público](pesquisa.json) permite conferir os bytes de cada membro. O pacote integral descrito abaixo fica no acervo local de pesquisa e redação.

`fontes.zip` preserva os bytes originais de executores encerrados, testes específicos antigos, ferramentas avulsas e versões editoriais anteriores. `indice.json` associa cada caminho original ao membro do pacote e ao SHA-256. Também identifica os leitores realocados para `analises/etapas/`.

Resultados, modelos treinados, dados e logs científicos permanecem nas pastas originais. As fontes necessárias à rodada ativa e à interface permanecem fora deste pacote. As versões anteriores dos guias editados nesta organização estão em `editoriais_antes/` dentro do ZIP.

Conferir com `python -m manutencao.arquivo_fontes conferir`. Para recuperar os arquivos originais, usar `python -m manutencao.arquivo_fontes extrair --destino <pasta_nova>`. A recuperação preserva os caminhos relativos e não sobrescreve conteúdo existente.

A auditoria atual é `python -m manutencao.auditar_repositorio --integridade --exigir-completo`. Ela compara os hashes científicos originais com os bytes preservados; nenhum hash antigo foi recalculado para aceitar mudanças. Uma fonte local divergente não é encoberta pelo pacote. Os protocolos e comandos dos documentos históricos descrevem o layout da época; consultar este índice para localizar seu código.

O pacote é preservação local, sem comprovação de backup externo. O inventário e as operações da reorganização estão em [registros/organizacao_repositorio](../../registros/organizacao_repositorio/20261110/).
