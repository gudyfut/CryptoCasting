# Decisões do trabalho (ADRs)

ADRs registram uma decisão, seu motivo, alternativas e consequências. Aqui abrangem escolhas científicas e de organização do TCC. Não substituem protocolos executáveis, relatórios de resultados ou logs de execução.

| Registro | Decisão | Situação |
|---|---|---|
| [0001](0001-estudo-retorno-24h.md) | Concentrar o estudo no retorno terminal de 24h | Adotada em 20/10/2026; execução documentada separadamente |
| [0002](0002-penalizacao-mamba.md) | Investigar a correção de weight decay em ciclo separado | Autorizada em 26/10/2026; consultar execução para progresso |
| [0003](0003-preservacao-e-organizacao.md) | Separar orientação, decisões, evidências e distribuição de artefatos | Organização adotada em 27/10/2026; publicação dos pacotes pendente |

## Como registrar

- Usar numeração crescente e o [modelo](modelo.md). Registrar a data da decisão e a data em que o documento foi escrito.
- As ADRs 0001 e 0002 foram reconstruídas em 27/10 a partir de documentos existentes. Não foram escritas antes dos experimentos e não constituem novos pré-registros.
- Uma proposta não altera o protocolo vigente. Identificar quem autorizou e apontar a evidência disponível, sem inventar aprovação do orientador.
- Para substituir uma decisão, criar nova ADR e relacionar as duas; conservar motivos e escopo históricos. Resultados conhecidos não podem ser apresentados como desconhecidos no passado.
- Guardar contagens/progresso em registros de execução e `docs/andamento.md`. Não abrir ADR para cada época, ajuste ou retomada operacional; incidentes ficam em `registros/incidentes/`.
- Não mover ou editar evidências congeladas para reorganizar a documentação. Criar índices e links.

O [registro narrativo anterior](../decisoes.md) permanece preservado como fonte histórica.
