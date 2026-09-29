"""Orquestra a Entrega 3; nenhum treinamento ou coleta é iniciado aqui."""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow
import sklearn

from camada_dados.armazenamento import sha256_arquivo

from .amostras import (
    construir_amostras,
    origens_da_tarefa_complementar,
    origens_da_tarefa_principal,
)
from .contrato import (
    FEATURES_AMPLIADAS,
    FEATURES_OHLCV,
    GRANULARIDADES,
    PARES,
    carregar_configuracao_processamento,
    candles_por_horizonte_24h,
)
from .folds import FOLDS, separar_fold
from .origem import carregar_candles_base, carregar_manifesto_aprovado
from .relatorios import calcular_volatilidade_comum, resumir_lacunas_15m
from .transformacoes import agregar_candles, associar_indicadores, indicadores_diarios


def _gravar_parquet(quadro: pd.DataFrame, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(caminho.name + ".tmp")
    quadro.to_parquet(temporario, index=False)
    temporario.replace(caminho)


def _gravar_texto(conteudo: str, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(caminho.name + ".tmp")
    temporario.write_text(conteudo, encoding="utf-8")
    temporario.replace(caminho)


def _assinatura_codigo() -> str:
    resumo = hashlib.sha256()
    raiz_projeto = Path(__file__).parent.parent
    fontes = list((raiz_projeto / "pre_processamento").glob("*.py"))
    fontes += list((raiz_projeto / "camada_dados").glob("*.py"))
    for caminho in sorted(fontes):
        resumo.update(caminho.relative_to(raiz_projeto).as_posix().encode("utf-8"))
        resumo.update(caminho.read_bytes())
    return resumo.hexdigest()


def _registrar_arquivo(arquivos: dict[str, dict[str, object]], raiz: Path, caminho: Path, linhas: int) -> None:
    relativo = caminho.relative_to(raiz).as_posix()
    arquivos[relativo] = {"sha256": sha256_arquivo(caminho), "linhas": linhas}


def _relatorio_volatilidade(tabela: pd.DataFrame, cobertura: pd.DataFrame) -> str:
    linhas = [
        "# Volatilidade observada — Entrega 3",
        "",
        "Retornos logarítmicos de fechamentos diários UTC nos mesmos dias válidos dos quatro pares.",
        "Desvio anualizado = desvio diário × √365; medida descritiva, não previsão.",
        "A ordem BTC < ETH < BNB < XRP era hipótese prévia e deve ser conferida por período.",
        "",
        "| Período | Par | Dias comuns | Desvio diário | Anualizado | Mediana | P95 absoluto |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for item in tabela.itertuples():
        linhas.append(
            f"| {item.periodo} | {item.par} | {item.dias_comuns} | "
            f"{item.desvio_padrao_diario:.6f} | {item.desvio_padrao_anualizado_sqrt365:.6f} | "
            f"{item.mediana_retorno_absoluto:.6f} | {item.p95_retorno_absoluto:.6f} |"
        )
    linhas += ["", "## Cobertura", "", "| Par | Dias individuais | Dias comuns |", "|---|---:|---:|"]
    for item in cobertura.itertuples():
        linhas.append(f"| {item.par} | {item.dias_com_retorno_individual} | {item.dias_comuns} |")
    linhas += ["", "Não inferir volatilidade a partir do papel econômico de cada moeda.", ""]
    return "\n".join(linhas)


def executar_processamento(caminho_configuracao: Path) -> Path:
    """Produz dataset versionado e manifesto; depende da coleta oficial completa."""
    configuracao = carregar_configuracao_processamento(caminho_configuracao)
    registros, assinatura_coleta = carregar_manifesto_aprovado(configuracao)
    assinatura_codigo = _assinatura_codigo()
    resumo_manifesto_coleta = sha256_arquivo(configuracao.caminho_manifesto_coleta)
    resumo_configuracao = sha256_arquivo(configuracao.caminho_configuracao)
    versoes = {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "pyarrow": pyarrow.__version__, "scikit_learn": sklearn.__version__}
    identificador = hashlib.sha256(
        json.dumps(
            [assinatura_coleta, resumo_manifesto_coleta, resumo_configuracao, assinatura_codigo, versoes],
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()[:20]
    raiz = configuracao.diretorio_saida / identificador
    manifesto_final = raiz / "manifesto_processamento.json"
    if manifesto_final.exists():
        existente = json.loads(manifesto_final.read_text(encoding="utf-8"))
        if existente.get("identificador") != identificador:
            raise ValueError("Identificador de dataset ocupado por manifesto divergente.")
        for relativo, informacao in existente["arquivos"].items():
            caminho = raiz / relativo
            if not caminho.is_file() or sha256_arquivo(caminho) != informacao["sha256"]:
                raise ValueError(f"Dataset existente alterado/incompleto: {caminho}")
        return raiz

    arquivos: dict[str, dict[str, object]] = {}
    elegibilidade: dict[tuple[str, str], pd.DatetimeIndex] = {}
    diarios_por_par: dict[str, pd.DataFrame] = {}
    cobertura_candles: list[dict[str, object]] = []
    lacunas_base: list[pd.DataFrame] = []
    for par in PARES:
        base = carregar_candles_base(configuracao, registros, par)
        lacunas_manifesto = sum(
            int(registro["lacunas"]) for registro in registros.values() if registro["par"] == par
        )
        lacunas_base.append(resumir_lacunas_15m(
            base, par, pd.Timestamp(configuracao.coleta.inicio),
            pd.Timestamp(configuracao.coleta.fim), lacunas_manifesto,
        ))
        diarios = agregar_candles(base, "1d")
        diarios_por_par[par] = diarios
        indicadores = indicadores_diarios(diarios)
        for granularidade in GRANULARIDADES:
            candles = associar_indicadores(
                diarios if granularidade == "1d" else agregar_candles(base, granularidade),
                indicadores,
            )
            candles.insert(0, "par", par)
            candles.insert(1, "granularidade", granularidade)
            caminho = raiz / "candles" / par / f"{granularidade}.parquet"
            _gravar_parquet(candles, caminho)
            _registrar_arquivo(arquivos, raiz, caminho, len(candles))
            origens = origens_da_tarefa_principal(candles, granularidade)
            elegibilidade[(par, granularidade)] = pd.DatetimeIndex(candles.iloc[origens]["fim_utc"])
            cobertura_candles.append({
                "par": par,
                "granularidade": granularidade,
                "candles": len(candles),
                "origens_elegiveis_24h_14d": len(origens),
                "candles_com_features_ampliadas": int(np.isfinite(candles[list(FEATURES_AMPLIADAS)].to_numpy()).all(axis=1).sum()),
            })
        print(f"Candles processados: {par}", flush=True)
        del base

    quadro_lacunas = pd.concat(lacunas_base, ignore_index=True)
    caminho_lacunas = raiz / "relatorios" / "lacunas_15m.csv"
    _gravar_texto(quadro_lacunas.to_csv(index=False), caminho_lacunas)
    _registrar_arquivo(arquivos, raiz, caminho_lacunas, len(quadro_lacunas))

    volatilidade, cobertura_volatilidade = calcular_volatilidade_comum(diarios_por_par)
    for nome, quadro in (("volatilidade_dias_comuns.csv", volatilidade), ("cobertura_volatilidade.csv", cobertura_volatilidade)):
        caminho = raiz / "relatorios" / nome
        _gravar_texto(quadro.to_csv(index=False), caminho)
        _registrar_arquivo(arquivos, raiz, caminho, len(quadro))
    caminho_md = raiz / "relatorios" / "volatilidade.md"
    _gravar_texto(_relatorio_volatilidade(volatilidade, cobertura_volatilidade), caminho_md)
    _registrar_arquivo(arquivos, raiz, caminho_md, len(volatilidade))

    grade_comum = pd.DatetimeIndex(elegibilidade[(PARES[0], GRANULARIDADES[0])])
    for chave in [(p, g) for p in PARES for g in GRANULARIDADES][1:]:
        grade_comum = grade_comum.intersection(elegibilidade[chave], sort=True)
    grade_comum = grade_comum.sort_values()
    if grade_comum.empty:
        raise ValueError("A interseção das 16 células não contém origens elegíveis.")
    for linha in cobertura_candles:
        linha["origens_grade_comum"] = len(grade_comum)
        linha["origens_excluidas_pela_intersecao"] = linha["origens_elegiveis_24h_14d"] - len(grade_comum)
    cobertura_quadro = pd.DataFrame(cobertura_candles)
    caminho_cobertura = raiz / "relatorios" / "cobertura_candles.csv"
    _gravar_texto(cobertura_quadro.to_csv(index=False), caminho_cobertura)
    _registrar_arquivo(arquivos, raiz, caminho_cobertura, len(cobertura_quadro))
    grade = pd.DataFrame({"origem_utc": grade_comum})
    caminho_grade = raiz / "grade_comum_utc.parquet"
    _gravar_parquet(grade, caminho_grade)
    _registrar_arquivo(arquivos, raiz, caminho_grade, len(grade))

    contagens: list[dict[str, object]] = []
    for par in PARES:
        referencia: pd.DataFrame | None = None
        for granularidade in GRANULARIDADES:
            candles = pd.read_parquet(raiz / "candles" / par / f"{granularidade}.parquet")
            posicoes = pd.Index(candles["fim_utc"]).get_indexer(grade_comum)
            if (posicoes < 0).any():
                raise ValueError("Grade comum não encontrada no parquet da célula.")
            if not np.isin(posicoes, origens_da_tarefa_principal(candles, granularidade)).all():
                raise ValueError("Grade comum contém origem não elegível.")
            for contexto in (7, 14):
                amostras = construir_amostras(
                    candles, posicoes, par, granularidade, contexto,
                    candles_por_horizonte_24h(granularidade), "24h",
                )
                if contexto == 7:
                    chave_preco = amostras[["origem_utc", "alvo_fim_utc", "preco_origem", "preco_alvo", "classe_alta"]]
                    if referencia is None:
                        referencia = chave_preco.reset_index(drop=True)
                    elif not chave_preco.reset_index(drop=True).equals(referencia):
                        raise ValueError(f"Preço/rótulo principal difere entre granularidades: {par}")
                caminho = raiz / "amostras" / "principal" / par / granularidade / f"{contexto}d.parquet"
                _gravar_parquet(amostras, caminho)
                _registrar_arquivo(arquivos, raiz, caminho, len(amostras))
                _contar_folds(contagens, amostras, par, granularidade, "24h", contexto)

            if granularidade != "1d":
                origens_curto = origens_da_tarefa_complementar(candles, granularidade)
                proximas = construir_amostras(
                    candles, origens_curto, par, granularidade, 7, 1, "proximo_candle",
                )
                caminho = raiz / "amostras" / "proximo_candle" / par / granularidade / "7d.parquet"
                _gravar_parquet(proximas, caminho)
                _registrar_arquivo(arquivos, raiz, caminho, len(proximas))
                _contar_folds(contagens, proximas, par, granularidade, "proximo_candle", 7)
        print(f"Amostras processadas: {par}", flush=True)

    quadro_contagens = pd.DataFrame(contagens)
    caminho_contagens = raiz / "relatorios" / "contagens_folds.csv"
    _gravar_texto(quadro_contagens.to_csv(index=False), caminho_contagens)
    _registrar_arquivo(arquivos, raiz, caminho_contagens, len(quadro_contagens))
    manifesto = {
        "identificador": identificador,
        "contrato": configuracao.versao_contrato,
        "assinatura_coleta": assinatura_coleta,
        "sha256_manifesto_coleta": resumo_manifesto_coleta,
        "sha256_configuracao": resumo_configuracao,
        "sha256_codigo_processamento": assinatura_codigo,
        "fonte": "Binance Public Data Spot; ZIPs aprovados pela Entrega 2",
        "pares": PARES,
        "granularidades": GRANULARIDADES,
        "periodo_inicio_utc": "2021-01-01T00:00:00+00:00",
        "periodo_fim_exclusivo_utc": "2026-01-01T00:00:00+00:00",
        "features_ohlcv": FEATURES_OHLCV,
        "features_ampliadas": FEATURES_AMPLIADAS,
        "dimensoes_entrada": {"ohlcv": 5, "ampliada": 8},
        "contextos_principais_dias": [7, 14],
        "contexto_complementar_dias": 7,
        "origens_principais_comuns": len(grade_comum),
        "arquivos_mensais_com_lacunas": sum(int(registro["lacunas"]) > 0 for registro in registros.values()),
        "candles_15m_ausentes": int(quadro_lacunas["candles_15m_ausentes"].sum()),
        "tarefa_diaria_complementar": "Reutilizar amostras/principal/{par}/1d/7d.parquet",
        "folds": [fold.__dict__ for fold in FOLDS],
        "normalizacao": "StandardScaler por célula/fold, ajustar em candles únicos das entradas de treino purgadas; aplicar sem reajuste",
        "versoes": versoes,
        "arquivos": arquivos,
    }
    _gravar_texto(json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n", manifesto_final)
    return raiz


def _contar_folds(
    destino: list[dict[str, object]], amostras: pd.DataFrame,
    par: str, granularidade: str, tarefa: str, contexto: int,
) -> None:
    for fold in FOLDS:
        for bloco, quadro in separar_fold(amostras, fold).items():
            destino.append({
                "par": par, "granularidade": granularidade, "tarefa": tarefa,
                "contexto_dias": contexto, "fold": fold.nome, "tipo_fold": fold.tipo,
                "bloco": bloco, "amostras": len(quadro),
                "altas": int(quadro["classe_alta"].sum()),
                "nao_altas": int((quadro["classe_alta"] == 0).sum()),
                "empates": int(quadro["empate"].sum()),
            })
