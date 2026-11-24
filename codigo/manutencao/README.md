# Manutenção do repositório organizado

| Ferramenta | Função |
|---|---|
| `python -m manutencao.auditar_repositorio --integridade --exigir-completo` | Auditoria atual de vínculos, cobertura e hashes, incluindo a localização explícita das fontes encerradas. |
| `python -m manutencao.arquivo_fontes conferir` | Confere o pacote histórico, os originais e os leitores realocados. |
| `python -m manutencao.arquivo_fontes listar --prefixo manutencao/` | Localiza ferramentas antigas, sem executá-las. |
| `auditar_catalogo.py` | Biblioteca original preservada. Sua execução isolada pressupõe o layout anterior; o comando atual acima adiciona a localização das fontes arquivadas. |

Para recuperar fontes, usar `python -m manutencao.arquivo_fontes extrair --destino <pasta_nova>`. O destino precisa ser novo e nenhum arquivo existente é sobrescrito. A extração não executa código. Os executores históricos continuam sujeitos ao protocolo e à autorização do respectivo ciclo.

Scripts avulsos de consolidação, retomada, aceite e geração de figuras de ciclos encerrados estão no [arquivo histórico](../../arquivo/desenvolvimento_encerrado/README.md). Seus resultados e recibos permanecem em `dados/` e `registros/`. Leituras posteriores úteis estão em [codigo/analises/etapas](../analises/README.md).
