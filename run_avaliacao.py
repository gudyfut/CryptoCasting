"""Consolida artefatos de desenvolvimento sem treinar modelos."""

import argparse
from pathlib import Path
from experimentos.consolidacao import consolidar


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execucoes", type=Path, nargs="+", required=True, help="Diretórios pareado_* escolhidos explicitamente.")
    parser.add_argument("--saida", type=Path, required=True, help="Diretório novo para resumo JSON e tabela CSV.")
    opcoes = parser.parse_args()
    resultado = consolidar(opcoes.execucoes, opcoes.saida)
    print(f"Grupos documentados: {len(resultado['grupos'])} | Saída: {opcoes.saida.resolve()}")


if __name__ == "__main__":
    main()
