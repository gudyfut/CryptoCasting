"""Atalho para a qualificação do piloto; não treina nem atualiza pesos."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_verificacao import main

if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv.extend(["--configuracao", str(Path(__file__).resolve().parents[1] / "configuracoes/treino_piloto_nvidia.json")])
    main()
