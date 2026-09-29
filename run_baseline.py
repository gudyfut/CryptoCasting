"""Piloto do ARIMA(1,0,0) que o pesquisador executa nos folds de desenvolvimento."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from baseline_ar1.execucao import executar_piloto


def main() -> None:
    parser = argparse.ArgumentParser(description="Piloto AR(1) nos dados da Entrega 3.")
    parser.add_argument(
        "--dataset", type=Path,
        default=Path(__file__).parent / "dados" / "processados" / "daeec76f001afb50a8fe",
        help="Diretório do dataset processado (ID explícito).",
    )
    parser.add_argument("--par", choices=["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT"], default="BTCUSDT")
    parser.add_argument("--fold", choices=["D1", "D2", "D3", "D4"], default="D1")
    parser.add_argument("--tarefa", choices=["principal", "proximo_candle"], default="principal")
    parser.add_argument("--granularidade", choices=["15m", "1h", "4h", "1d"], default="1d")
    argumentos = parser.parse_args()
    try:
        destino = executar_piloto(
            argumentos.dataset, argumentos.par, argumentos.fold,
            argumentos.tarefa, argumentos.granularidade,
        )
    except (FileNotFoundError, ValueError) as erro:
        raise SystemExit(f"Piloto indisponível: {erro}") from None
    resultado = json.loads((destino / "resultado.json").read_text(encoding="utf-8"))
    print(f"Piloto AR(1): {destino}")
    print(f"Ajuste: {resultado['pares_retorno_ajuste']} pares | alfa={resultado['coeficientes']['alfa']:.8g} | phi={resultado['coeficientes']['phi']:.8g}")
    for bloco, metricas in resultado["metricas"].items():
        ba = "indisponível" if metricas["balanced_accuracy"] is None else f"{metricas['balanced_accuracy']:.4f}"
        print(f"{bloco}: n={metricas['amostras']} | BA={ba} | accuracy={metricas['accuracy']:.4f} | F1 macro={metricas['f1_macro']:.4f}")


if __name__ == "__main__":
    main()
