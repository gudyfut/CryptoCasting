"""Consolidação de resultados íntegros, por configuração, sem selecionar vencedores."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import numpy as np
import pandas as pd

from .avaliacao import testar_pt, CHAVES
from .auditoria import auditar_execucao
from .registro import gravar_json, identidade


def consolidar(caminhos: list[Path], destino: Path) -> dict:
    if not caminhos:
        raise ValueError("Informe ao menos uma execução pareada concluída.")
    if destino.exists():
        raise FileExistsError("O destino já existe; use outro nome para preservar o relatório.")
    grupos = defaultdict(list)
    vistos = set()
    for pasta in caminhos:
        resultado, _ = auditar_execucao(pasta)
        if resultado["tipo_fold"] != "desenvolvimento":
            raise ValueError("Esta consolidação aceita somente desenvolvimento.")
        celula, configuracao = resultado["celula"], resultado["configuracao"]
        chave = {k: celula[k] for k in ("par", "granularidade", "contexto_dias", "tarefa", "seed")}
        chave.update({k: configuracao[k] for k in ("features", "normalizador", "largura_mamba", "largura_lstm", "backend_mamba", "dispositivo", "microbatch")})
        chave.update({k: resultado[k] for k in ("sha256_manifesto_dataset", "sha256_codigo", "sha256_protocolo")})
        chave["versoes"] = resultado["ambiente"]["versoes"]
        chave["hardware"] = {k: resultado["ambiente"].get(k) for k in ("cpu", "gpu", "sistema", "cuda_pytorch", "cudnn")}
        chave["execucao_numerica"] = resultado["ambiente"].get("execucao_numerica")
        chave["fontes_backend"] = resultado["ambiente"].get("fontes_backend")
        identificador = identidade(chave)
        repeticao = (identificador, celula["fold"])
        if repeticao in vistos:
            raise ValueError("Há mais de uma execução da mesma célula/fold. Escolha explicitamente qual registrar.")
        vistos.add(repeticao)
        grupos[identificador].append((chave, resultado, pasta))
    saida = []
    linhas = []
    for identificador, registros in grupos.items():
        registros.sort(key=lambda registro: registro[1]["celula"]["fold"])
        folds = [r[1]["celula"]["fold"] for r in registros]
        ausentes = [f for f in ("D1", "D2", "D3", "D4") if f not in folds]
        resumo = {"id": identificador, "configuracao": registros[0][0], "folds": folds,
                  "folds_ausentes": ausentes, "cobertura_completa_desenvolvimento": not ausentes,
                  "modelos": {}, "diferencas_pp": {}}
        for nome in ("ar1", "lstm", "mamba"):
            valores = [r[1]["avaliacoes"]["teste"]["metricas"][nome]["balanced_accuracy"] for r in registros]
            quadros = [pd.read_parquet(r[2] / f"previsoes_{nome}_teste.parquet") for r in registros]
            concatenado = pd.concat(quadros).sort_values(CHAVES)
            if concatenado.duplicated(CHAVES).any():
                raise ValueError("Previsões fora da amostra sobrepostas entre folds.")
            validos = [v for v in valores if v is not None]
            resumo["modelos"][nome] = {
                "ba_media_folds": float(np.mean(validos)) if len(validos) == len(valores) else None,
                "desvio_padrao_folds": float(np.std(validos, ddof=1)) if len(validos) > 1 and len(validos) == len(valores) else None,
                "pt_concatenado_exploratorio": testar_pt(concatenado["classe_alta"], concatenado["classe_prevista"]),
                "quantidade_folds_ba_disponivel": len(validos),
            }
            for (_, resultado, _), ba in zip(registros, valores):
                linhas.append({**resultado["celula"], "modelo": nome, "grupo": identificador, "balanced_accuracy": ba})
        for comparacao in ("mamba_menos_ar1", "mamba_menos_lstm", "mamba_menos_50"):
            valores = [r[1]["avaliacoes"]["teste"]["diferencas_pp"][comparacao] for r in registros]
            validos = [v for v in valores if v is not None]
            resumo["diferencas_pp"][comparacao] = {"media": float(np.mean(validos)) if len(validos) == len(valores) else None,
                                                   "folds_positivos": sum(v > 0 for v in validos), "folds_disponiveis": len(validos)}
        saida.append(resumo)
    resultado = {"contrato": "resumo-desenvolvimento-v1", "tipo": "desenvolvimento", "grupos": saida,
                 "execucoes": [str(p.resolve()) for p in caminhos],
                 "auditoria": "Hashes e contratos conferidos; métricas recalculadas a partir das previsões de validação e teste.",
                 "interpretacao": "Médias não ponderadas entre folds; cobertura parcial explícita. PT não testa diferenças entre modelos. Nenhuma avaliação final."}
    destino.mkdir(parents=True, exist_ok=False)
    gravar_json(destino / "resumo.json", resultado)
    pd.DataFrame(linhas).to_csv(destino / "metricas_por_fold.csv", index=False)
    return resultado
