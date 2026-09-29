"""Interface da Entrega 3. Executar somente após a coleta oficial aprovada."""

from __future__ import annotations

import argparse
from pathlib import Path

from pre_processamento import executar_processamento


def main() -> None:
    parser = argparse.ArgumentParser(description="Processa a coleta oficial e gera amostras auditáveis.")
    parser.add_argument(
        "--configuracao", type=Path,
        default=Path(__file__).parent / "configuracoes" / "pre_processamento.json",
        help="Caminho da configuração fechada da Entrega 3.",
    )
    argumentos = parser.parse_args()
    try:
        caminho = executar_processamento(argumentos.configuracao)
    except FileNotFoundError as erro:
        raise SystemExit(f"Pré-requisito ausente: {erro}") from None
    print(f"Dataset da Entrega 3: {caminho}")


if __name__ == "__main__":
    main()
