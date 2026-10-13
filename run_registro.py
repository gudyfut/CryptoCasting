"""Arquiva evidências leves de uma execução, inclusive incompleta; não treina."""

import argparse
from pathlib import Path

from experimentos.historico import registrar_execucao, SITUACOES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execucao", type=Path, required=True)
    parser.add_argument("--titulo", required=True)
    parser.add_argument("--situacao", choices=SITUACOES, default="em_revisao")
    parser.add_argument("--observacao", default="")
    parser.add_argument("--destino", type=Path, default=Path(__file__).resolve().parent / "historico")
    opcoes = parser.parse_args()
    pasta = registrar_execucao(opcoes.execucao, opcoes.destino, titulo=opcoes.titulo,
                              situacao=opcoes.situacao, observacao=opcoes.observacao)
    print(f"Registro preservado: {pasta}")


if __name__ == "__main__":
    main()
