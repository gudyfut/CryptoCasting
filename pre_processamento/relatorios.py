"""Descrição de volatilidade em dias UTC comuns aos quatro ativos."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .contrato import PARES


def resumir_lacunas_15m(
    base: pd.DataFrame,
    par: str,
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
    quantidade_manifesto: int,
) -> pd.DataFrame:
    """Enumera sequências ausentes e confere o total contra a auditoria da coleta."""
    passo = pd.Timedelta(minutes=15)
    esperadas = pd.date_range(inicio, fim, freq=passo, inclusive="left")
    ausentes = esperadas.difference(pd.DatetimeIndex(base["abertura_utc"]))
    if len(ausentes) != quantidade_manifesto:
        raise ValueError(f"Lacunas dos candles-base divergem do manifesto: {par}")
    colunas = ["par", "abertura_inicio_utc", "abertura_fim_exclusivo_utc", "candles_15m_ausentes"]
    if len(ausentes) == 0:
        return pd.DataFrame(columns=colunas)
    grupos = ausentes.to_series().diff().ne(passo).cumsum()
    linhas = [
        {"par": par, "abertura_inicio_utc": grupo.iloc[0],
         "abertura_fim_exclusivo_utc": grupo.iloc[-1] + passo,
         "candles_15m_ausentes": len(grupo)}
        for _, grupo in ausentes.to_series().groupby(grupos)
    ]
    return pd.DataFrame(linhas, columns=colunas)


def calcular_volatilidade_comum(
    diarios_por_par: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retornos de fechamentos completos; compara somente datas válidas para todos."""
    retornos: list[pd.Series] = []
    cobertura: list[dict[str, object]] = []
    for par in PARES:
        diarios = diarios_por_par[par].sort_values("fim_utc")
        serie = diarios.set_index("fim_utc")["close"]
        anteriores = serie.index.to_series().diff().eq(pd.Timedelta(days=1))
        retorno = np.log(serie / serie.shift(1)).where(anteriores.to_numpy())
        retorno.name = par
        retornos.append(retorno)
        cobertura.append({"par": par, "dias_com_retorno_individual": int(retorno.notna().sum())})
    comuns = pd.concat(retornos, axis=1, join="inner").dropna()
    if comuns.empty:
        raise ValueError("Nenhum retorno diário válido comum aos quatro ativos.")

    linhas: list[dict[str, object]] = []
    # O candle diário iniciado em 31/12 termina em 01/01: o retorno pertence a 31/12.
    anos_dia_candle = (comuns.index - pd.Timedelta(days=1)).year
    for periodo, tabela in [("completo", comuns), *[(str(ano), grupo) for ano, grupo in comuns.groupby(anos_dia_candle)]]:
        for par in PARES:
            valores = tabela[par].to_numpy(dtype="float64")
            desvio = float(np.std(valores, ddof=1)) if len(valores) >= 2 else np.nan
            linhas.append({
                "periodo": periodo,
                "par": par,
                "dias_comuns": len(valores),
                "primeiro_fim_utc": tabela.index.min(),
                "ultimo_fim_utc": tabela.index.max(),
                "desvio_padrao_diario": desvio,
                "desvio_padrao_anualizado_sqrt365": desvio * np.sqrt(365),
                "mediana_retorno_absoluto": float(np.median(np.abs(valores))),
                "p95_retorno_absoluto": float(np.percentile(np.abs(valores), 95)),
            })
    cobertura_quadro = pd.DataFrame(cobertura)
    cobertura_quadro["dias_comuns"] = len(comuns)
    cobertura_quadro["primeiro_fim_comum_utc"] = comuns.index.min()
    cobertura_quadro["ultimo_fim_comum_utc"] = comuns.index.max()
    return pd.DataFrame(linhas), cobertura_quadro
