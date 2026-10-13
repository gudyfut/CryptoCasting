"""CLI do pesquisador: planejar ou executar LSTM e Mamba nos folds D1–D4."""

import argparse
import json
from pathlib import Path
from experimentos.configuracao import carregar_configuracao, gerar_celulas


def main():
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument("--configuracao", type=Path, required=True)
    argumentos.add_argument("--planejar", action="store_true", help="Lista células sem carregar dados ou treinar.")
    argumentos.add_argument("--nova-tentativa", action="store_true", help="Reinicia em pasta nova, preservando execuções anteriores.")
    opcoes = argumentos.parse_args()
    configuracao = carregar_configuracao(opcoes.configuracao)
    celulas = gerar_celulas(configuracao)
    if opcoes.planejar:
        print(json.dumps({"fase": "desenvolvimento", "celulas": celulas, "treinos_neurais": 2 * len(celulas),
                          "final_bloqueado": True}, ensure_ascii=False, indent=2))
        return
    from experimentos.execucao import executar_grade
    caminhos = executar_grade(configuracao, nova_tentativa=opcoes.nova_tentativa)
    print(f"Células concluídas/reutilizadas: {len(caminhos)}")


if __name__ == "__main__":
    main()
