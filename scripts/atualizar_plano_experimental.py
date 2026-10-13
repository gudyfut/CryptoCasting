"""Atualiza as tabelas estáticas a partir dos contratos; não lê dados nem treina."""

import json
import sys
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_PROJETO))

from experimentos.planejamento import construir_plano, documento_matriz  # noqa: E402


def main():
    plano = construir_plano()
    destinos = {
        RAIZ_PROJETO / "dataview/src/lib/plano-experimental.json": json.dumps(plano, ensure_ascii=False, indent=2) + "\n",
        RAIZ_PROJETO / "docs/entregas/05_mamba_base/matriz_experimental.md": documento_matriz(plano),
    }
    for caminho, conteudo in destinos.items():
        caminho.write_text(conteudo, encoding="utf-8", newline="\n")
        print(caminho.relative_to(RAIZ_PROJETO))


if __name__ == "__main__":
    main()
