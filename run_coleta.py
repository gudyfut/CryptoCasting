"""Ponto de entrada da Entrega 2. A execução científica cabe ao usuário."""

from __future__ import annotations

import argparse
from pathlib import Path

from camada_dados import ServicoColeta, carregar_configuracao


def argumentos() -> argparse.Namespace:
    analisador = argparse.ArgumentParser(description="Coleta auditável de candles da Binance Spot")
    analisador.add_argument(
        "--config",
        type=Path,
        default=Path("configuracoes/coleta_oficial.json"),
        help="Arquivo JSON com a configuração fechada da coleta",
    )
    analisador.add_argument(
        "--somente-auditoria",
        action="store_true",
        help="Não acessa a rede; audita somente os arquivos já presentes",
    )
    return analisador.parse_args()


def main() -> int:
    opcoes = argumentos()
    configuracao = carregar_configuracao(opcoes.config)
    resumo = ServicoColeta(configuracao).executar(opcoes.somente_auditoria)
    print(f"Itens: {resumo.total} | válidos: {resumo.validos} | falhas: {resumo.falhas}")
    return 0 if resumo.falhas == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
