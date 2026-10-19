# Dados e artefatos

Fonte: Binance Public Data Spot, BTCUSDT/ETHUSDT/BNBUSDT/XRPUSDT, OHLCV de 1 minuto. Desenvolvimento inicial de 2021-01-01 até 2024-01-01 exclusivo, UTC.

- `brutos/barreiras_1m/{par}/`: ZIP, checksum oficial e auditoria mensal.
- `brutos/barreiras_1m/manifesto_*.json`: inventário da coleta.
- `processados/barreiras_{id}/`: minutos regulares com lacunas explícitas, entradas horárias, rótulos, origens comuns e hashes.
- `processados/dataset_barreiras_atual.json`: referência ao dataset concluído e auditado.
- `experimentos/barreiras_{id}/`: ciclo identificado por dados/código/configuração/ambiente, tentativas, snapshots, checkpoints, probabilidades e simulações.

Minutos ausentes ou interrompidos não são interpolados. Um arquivo aprovado por checksum ainda pode conter lacunas reais. Validação e teste não ajustam a normalização; scalers pertencem a cada fold de treinamento.

A lista de origens preditivas exige observabilidade futura, mas esse filtro não decide entradas financeiras. Uma posição cujo percurso não seja observável torna sua curva integral não auditável. Consulte o [protocolo](../docs/protocolo_experimental.md).

Dados e checkpoints ficam fora do Git e precisam de backup. Registros leves de tentativas e qualificações são mantidos em `historico/`.
