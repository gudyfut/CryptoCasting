"""Executa AR(1) nos quatro folds de desenvolvimento; o pesquisador roda este script."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from baseline_ar1.execucao import executar_piloto
from camada_dados.armazenamento import sha256_arquivo
from pre_processamento.contrato import PARES


def resumir_resultados(resultados: list[dict[str, object]]) -> dict[str, object]:
    """Média não ponderada entre folds, mantendo os scores individuais auditáveis."""
    if not resultados:
        raise ValueError("Nenhum fold de desenvolvimento foi executado.")
    linhas = []
    por_par: dict[str, list[dict[str, object]]] = {}
    for resultado in resultados:
        if resultado["fold"] not in ("D1", "D2", "D3", "D4") or resultado["tarefa"] != "principal":
            raise ValueError("Resumo aceita somente a matriz principal de desenvolvimento.")
        metricas = resultado["metricas"]["teste"]
        linha = {
            "par": resultado["par"],
            "fold": resultado["fold"],
            "pares_treino": resultado["pares_retorno_ajuste"],
            "amostras_teste_desenvolvimento": metricas["amostras"],
            "balanced_accuracy": metricas["balanced_accuracy"],
            "accuracy": metricas["accuracy"],
            "f1_macro": metricas["f1_macro"],
            "recall_alta": metricas["por_classe"]["1"]["recall"],
            "predicoes_alta": metricas["predicoes_alta"],
            "suporte_alta": metricas["suporte_alta"],
            "caminho_resultado": resultado["caminho_resultado"],
            "sha256_resultado": resultado["sha256_resultado"],
        }
        linhas.append(linha)
        por_par.setdefault(resultado["par"], []).append(linha)
    medias = {}
    for par, linhas_par in por_par.items():
        disponiveis = [linha["balanced_accuracy"] for linha in linhas_par if linha["balanced_accuracy"] is not None]
        medias[par] = {
            "folds": len(linhas_par),
            "folds_com_ba": len(disponiveis),
            "ba_media_nao_ponderada": sum(disponiveis) / len(disponiveis) if disponiveis else None,
            "ba_minima": min(disponiveis) if disponiveis else None,
            "ba_maxima": max(disponiveis) if disponiveis else None,
        }
    return {
        "tipo": "resumo_baseline_ar1_desenvolvimento",
        "folds": linhas,
        "resumo_por_par": medias,
        "interpretacao": (
            "Os treinos crescem entre D1 e D4, mas os períodos de teste também mudam; "
            "diferenças de score não isolam causalmente o efeito da quantidade de treino. "
            "2024–2025 permanecem reservados."
        ),
    }


def main() -> None:
    analisador = argparse.ArgumentParser(description="AR(1) em D1–D4, sem acessar 2024–2025.")
    analisador.add_argument(
        "--dataset", type=Path,
        default=Path(__file__).parent / "dados" / "processados" / "daeec76f001afb50a8fe",
    )
    grupo = analisador.add_mutually_exclusive_group()
    grupo.add_argument("--par", choices=PARES, default="BTCUSDT")
    grupo.add_argument("--todos-pares", action="store_true")
    argumentos = analisador.parse_args()
    pares = PARES if argumentos.todos_pares else (argumentos.par,)
    resultados = []
    for par in pares:
        for fold in ("D1", "D2", "D3", "D4"):
            try:
                destino = executar_piloto(argumentos.dataset, par, fold, "principal", "1d")
            except (FileNotFoundError, ValueError) as erro:
                raise SystemExit(f"Execução interrompida em {par}/{fold}: {erro}") from None
            caminho = destino / "resultado.json"
            resultado = json.loads(caminho.read_text(encoding="utf-8"))
            resultado["caminho_resultado"] = str(caminho.resolve())
            resultado["sha256_resultado"] = sha256_arquivo(caminho)
            resultados.append(resultado)
            teste = resultado["metricas"]["teste"]
            ba = teste["balanced_accuracy"]
            texto_ba = "indisponível" if ba is None else f"{ba:.4f}"
            print(
                f"{par} {fold}: treino={resultado['pares_retorno_ajuste']} "
                f"| teste_desenvolvimento={teste['amostras']} | BA={texto_ba} "
                f"| accuracy={teste['accuracy']:.4f} | F1_macro={teste['f1_macro']:.4f} "
                f"| recall_alta={teste['por_classe']['1']['recall']:.4f}",
                flush=True,
            )
    resumo = resumir_resultados(resultados)
    resumo["id_dataset"] = argumentos.dataset.resolve().name
    destino_resumo = argumentos.dataset.resolve().parent.parent / "experimentos"
    nome = "todos_pares" if argumentos.todos_pares else argumentos.par
    caminho_resumo = destino_resumo / f"resumo_ar1_desenvolvimento_{resumo['id_dataset']}_{nome}.json"
    destino_resumo.mkdir(parents=True, exist_ok=True)
    temporario = caminho_resumo.with_name(caminho_resumo.name + ".tmp")
    temporario.write_text(json.dumps(resumo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporario.replace(caminho_resumo)
    for par, metricas in resumo["resumo_por_par"].items():
        media = metricas["ba_media_nao_ponderada"]
        print(f"{par}: BA média dos folds de desenvolvimento = {media:.4f}" if media is not None else f"{par}: BA indisponível")
    print(f"Resumo: {caminho_resumo}")


if __name__ == "__main__":
    main()
