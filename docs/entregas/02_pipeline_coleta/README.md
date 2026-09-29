# Entrega 2 — camada profissional de dados

## Resultado da entrega

A coleta foi estruturada como uma **camada de dados independente do modelo**. Ela sabe onde obter o dado bruto, como preservá-lo e como provar sua integridade. Ela não conhece Mamba, features, rótulos, folds ou métricas.

Essa separação evita que regras do experimento contaminem a entrada dos dados e permite testar cada responsabilidade isoladamente.

**Ativos:** BTC, ETH, BNB e XRP. A [justificativa científica da escolha e a hipótese de volatilidade](justificativa_ativos.md) distinguem as propriedades das quatro redes e deixam explícito que a ordem de volatilidade ainda precisa ser medida. BNB é nativo da BNB Chain e também tem usos na corretora Binance; essa ligação será considerada na interpretação da amostra.

## O que foi implementado

| Componente | Responsabilidade única |
|---|---|
| `configuracoes/coleta_oficial.json` | congela pares, período, fonte e intervalo |
| `camada_dados/configuracao.py` | lê a configuração e cria o inventário de 240 arquivos |
| `camada_dados/fonte_binance.py` | isola acesso à rede, tentativas e download atômico |
| `camada_dados/armazenamento.py` | calcula SHA-256 e verifica o ZIP |
| `camada_dados/auditoria.py` | detecta unidade temporal, lacunas, duplicatas e OHLCV inválido |
| `camada_dados/manifesto.py` | grava manifesto JSONL e resumo CSV sem duplicar retomadas |
| `camada_dados/servico_coleta.py` | coordena o caso de uso sem misturar responsabilidades |
| `run_coleta.py` | interface de linha de comando usada pelo pesquisador |
| `tests/test_camada_dados.py` | verificações locais, sem baixar o dataset científico |

## Como executar

O usuário executa a coleta oficial:

```powershell
python run_coleta.py --config configuracoes/coleta_oficial.json
```

Para reauditar o que já estiver no disco sem acessar a rede:

```powershell
python run_coleta.py --config configuracoes/coleta_oficial.json --somente-auditoria
```

Para rodar apenas os testes rápidos:

```powershell
python -m unittest discover -s tests -v
```

## Entradas e saídas

Entrada externa planejada: 240 ZIPs mensais oficiais de candles `15m`, correspondentes a quatro pares por 60 meses. A disponibilidade e a integridade efetivas serão confirmadas na coleta do usuário.

Saídas locais:

```text
dados/
├── brutos/binance_spot/{PAR}/15m/*.zip
└── brutos/manifestos/
    ├── manifesto_coleta.jsonl
    └── resumo_cobertura.csv
```

O ZIP original não é alterado. O manifesto registra procedência, período solicitado, hash, checksum, tamanho, unidade do timestamp, cobertura e erros. Uma nova execução substitui o registro da mesma competência, em vez de duplicá-lo. Na coleta oficial realizada em 28/09/2026, 216 arquivos ficaram completos e 24 apresentaram somente lacunas de candles, embora seus checksums oficiais estejam corretos. O comando sinaliza esses meses como falhas para não ocultar a perda de cobertura; a [Entrega 3](../03_pre_processamento_amostras/README.md) aceita apenas esse caso específico, registra as lacunas e exclui amostras afetadas. Repetir o download desses ZIPs de checksum correto não preencherá os candles ausentes.

## O que deliberadamente fica fora

- agregação em `1h`, `4h` e `1d`;
- cálculo de features e alvo;
- normalização e janelas;
- walk-forward;
- baseline, teste PT e Mamba.

Essas etapas consomem dados aprovados por esta camada, mas pertencem às entregas seguintes.

## Material para apresentação

- [Visão visual da camada de dados](visao_visual.md)
- [Plano e critérios de aceite](plano_implementacao.md)
- [Justificativa dos ativos e análise planejada de volatilidade](justificativa_ativos.md)
