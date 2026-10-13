"""Qualifica ambiente/dados ou reproduz checkpoints, sem realizar treinamento."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument("--configuracao", type=Path, help="Verifica uma célula antes do treino.")
    modo.add_argument("--execucao", type=Path, help="Audita e reproduz os checkpoints de uma execução concluída.")
    opcoes = parser.parse_args()
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    # Preservar inclusive falhas de importação/instalação sem depender do PyTorch.
    pasta = Path(__file__).resolve().parent / "dados/experimentos" / ("verificacao_" + uuid.uuid4().hex[:12])
    pasta.mkdir(parents=True, exist_ok=False)
    relatorio = {"tipo": "verificacao_tecnica", "estado": "em_execucao",
                 "inicio_utc": datetime.now(timezone.utc).isoformat(),
                 "solicitacao": {k: str(v) if v else None for k, v in vars(opcoes).items()},
                 "treinamento_executado": False}
    codigo_saida = 0
    try:
        dependencias = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True, timeout=60)
        (pasta / "dependencias.txt").write_text(dependencias.stdout + dependencias.stderr, encoding="utf-8")
        from experimentos.configuracao import carregar_configuracao
        from experimentos.qualificacao import verificar_preparacao, verificar_checkpoints
        relatorio["verificacao"] = (verificar_preparacao(carregar_configuracao(opcoes.configuracao))
                                    if opcoes.configuracao else verificar_checkpoints(opcoes.execucao))
        relatorio["estado"] = "concluido"
    except Exception as erro:
        relatorio.update(estado="falhou", erro=str(erro), tipo_erro=type(erro).__name__)
        codigo_saida = 1
        print(f"Verificação interrompida: {erro}", file=sys.stderr)
    finally:
        relatorio["fim_utc"] = datetime.now(timezone.utc).isoformat()
        (pasta / "resultado.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(f"Verificação {relatorio['estado']}: {pasta}")
    raise SystemExit(codigo_saida)


if __name__ == "__main__":
    main()
