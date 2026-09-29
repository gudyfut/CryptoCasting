# Entrega 2 — camada de dados em uma imagem

## Ideia central

> Primeiro provamos de onde o dado veio e se ele está íntegro. Só depois o dado pode entrar no experimento.

```mermaid
flowchart LR
    A[Configuração oficial<br/>4 pares × 60 meses] --> B[Adaptador Binance<br/>download retomável]
    B --> C[(ZIP bruto<br/>preservado)]
    C --> D[Integridade<br/>SHA-256 + ZIP]
    D --> E[Auditoria OHLCV<br/>tempo + lacunas + duplicatas]
    E --> F{Arquivo aprovado?}
    F -- Sim --> G[(Manifesto<br/>válido e rastreável)]
    F -- Não --> H[(Falha visível<br/>não corrigir silenciosamente)]
    G --> I[Próxima entrega<br/>transformação causal]
```

## As camadas não se misturam

```mermaid
flowchart TB
    CLI[run_coleta.py<br/>interface] --> S[Serviço de coleta<br/>orquestra]
    S --> F[Fonte externa<br/>rede]
    S --> A[Armazenamento<br/>hash e ZIP]
    S --> Q[Auditoria<br/>qualidade OHLCV]
    S --> M[Manifesto<br/>evidência]
    D[Domínio e configuração<br/>regras fechadas] --> S

    style S fill:#dbeafe,stroke:#2563eb
    style D fill:#ecfdf5,stroke:#059669
    style F fill:#fff7ed,stroke:#ea580c
    style A fill:#fff7ed,stroke:#ea580c
    style Q fill:#fff7ed,stroke:#ea580c
    style M fill:#fff7ed,stroke:#ea580c
```

## Explicação de 30 segundos para o professor

1. A configuração congela **o que deve existir**: 240 arquivos planejados.
2. A fonte cuida somente de **obter** esses arquivos.
3. A auditoria verifica **se podemos confiar** neles.
4. O manifesto deixa uma **prova reproduzível** de cada decisão.
5. Mamba e baseline só recebem dados aprovados; eles não fazem parte da coleta.
