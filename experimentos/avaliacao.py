"""Métricas direcionais, PT clássico e pareamento explícito por timestamps."""

from __future__ import annotations

import math
import numpy as np
import pandas as pd

from baseline_ar1.avaliacao import calcular_metricas as metricas_ar1

CHAVES = ["par", "origem_utc", "alvo_fim_utc"]


def calcular_metricas(quadro: pd.DataFrame, coluna: str = "classe_prevista") -> dict:
    if coluna not in quadro or not quadro[coluna].isin([0, 1]).all() or not quadro["classe_alta"].isin([0, 1]).all():
        raise ValueError("Previsões/rótulos devem ser classes binárias completas.")
    return metricas_ar1(quadro.rename(columns={coluna: "classe_prevista_ar1"}))


def testar_pt(reais, previstas) -> dict:
    """PT (1992), variância com correção 4*p_y*p_x*(1-p_y)*(1-p_x)/n².

    P-valor normal bicaudal. Não testa a diferença entre duas arquiteturas.
    Fórmulas (4)–(5): doi:10.1080/07350015.1992.10509922.
    """
    reais, previstas = np.asarray(reais), np.asarray(previstas)
    if reais.ndim != 1 or previstas.shape != reais.shape or not np.isin(reais, [0, 1]).all() or not np.isin(previstas, [0, 1]).all():
        raise ValueError("PT exige vetores binários alinhados.")
    n = len(reais)
    resultado = {"amostras": n, "estatistica": None, "p_valor_bicaudal": None,
                 "disponivel": False, "interpretacao": "Exploratório: pressupõe independência serial; não compara modelos."}
    if n < 3 or len(np.unique(reais)) < 2 or len(np.unique(previstas)) < 2:
        return {**resultado, "motivo": "Amostra insuficiente ou série real/prevista constante."}
    py, px = float(reais.mean()), float(previstas.mean())
    acerto = float(np.mean(reais == previstas))
    esperado = py * px + (1 - py) * (1 - px)
    variancia_acerto = esperado * (1 - esperado) / n
    variancia_esperado = (
        (2 * py - 1) ** 2 * px * (1 - px) / n
        + (2 * px - 1) ** 2 * py * (1 - py) / n
        + 4 * py * px * (1 - py) * (1 - px) / n ** 2
    )
    variancia = variancia_acerto - variancia_esperado
    if variancia <= 0 or not math.isfinite(variancia):
        return {**resultado, "motivo": "Variância PT não positiva."}
    estatistica = (acerto - esperado) / math.sqrt(variancia)
    return {**resultado, "disponivel": True, "motivo": None,
            "acerto_observado": acerto, "acerto_esperado_marginais": esperado,
            "variancia": variancia, "estatistica": estatistica,
            "p_valor_bicaudal": math.erfc(abs(estatistica) / math.sqrt(2))}


def autocorrelacao_lag1(valores) -> float | None:
    valores = np.asarray(valores, dtype=float)
    if len(valores) < 3 or np.std(valores[:-1]) == 0 or np.std(valores[1:]) == 0:
        return None
    return float(np.corrcoef(valores[:-1], valores[1:])[0, 1])


def alinhar_previsoes(referencia: pd.DataFrame, candidata: pd.DataFrame) -> pd.DataFrame:
    """Rejeita cobertura parcial, duplicação ou rótulo diferente; nunca alinha por linha."""
    for quadro in (referencia, candidata):
        if quadro.empty or quadro[CHAVES].isna().any().any() or quadro.duplicated(CHAVES).any():
            raise ValueError("Previsões vazias ou timestamps duplicados.")
    unido = referencia.merge(candidata, on=CHAVES, how="outer", validate="one_to_one",
                            indicator=True, suffixes=("_referencia", "_candidata"))
    if not (unido["_merge"] == "both").all():
        raise ValueError("Populações diferentes: há timestamps ausentes na comparação.")
    if not (unido["classe_alta_referencia"] == unido["classe_alta_candidata"]).all():
        raise ValueError("Rótulos diferentes nos mesmos timestamps.")
    for coluna in ("retorno_futuro", "empate"):
        if coluna in referencia and coluna in candidata:
            esquerda, direita = unido[f"{coluna}_referencia"], unido[f"{coluna}_candidata"]
            iguais = np.allclose(esquerda, direita, rtol=0, atol=1e-12) if coluna == "retorno_futuro" else (esquerda == direita).all()
            if not iguais:
                raise ValueError(f"Desfechos diferentes nos mesmos timestamps: {coluna}.")
    return unido.sort_values(CHAVES).reset_index(drop=True)


def comparar_modelos(previsoes: dict[str, pd.DataFrame]) -> dict:
    for nome in ("ar1", "lstm"):
        alinhar_previsoes(previsoes["mamba"], previsoes[nome])
    metricas = {nome: calcular_metricas(quadro) for nome, quadro in previsoes.items()}
    ba = {nome: valor["balanced_accuracy"] for nome, valor in metricas.items()}
    diferenca = lambda outro: None if ba["mamba"] is None or ba[outro] is None else 100 * (ba["mamba"] - ba[outro])
    return {"metricas": metricas, "diferencas_pp": {
        "mamba_menos_ar1": diferenca("ar1"), "mamba_menos_lstm": diferenca("lstm"),
        "mamba_menos_50": None if ba["mamba"] is None else 100 * (ba["mamba"] - 0.5),
    }, "pt_exploratorio": {nome: testar_pt(q["classe_alta"], q["classe_prevista"]) for nome, q in previsoes.items()},
        "autocorrelacao_lag1_por_modelo": {nome: {
            "reais": autocorrelacao_lag1(q["classe_alta"]),
            "previstas": autocorrelacao_lag1(q["classe_prevista"]),
        } for nome, q in previsoes.items()}}
