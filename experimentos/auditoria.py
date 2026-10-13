"""Audita previsões e recalcula resumos sem carregar checkpoints nem treinar."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from camada_dados.armazenamento import sha256_arquivo
from pre_processamento.contrato import DURACOES, FEATURES_AMPLIADAS, FEATURES_OHLCV
from pre_processamento.folds import FOLDS
from .avaliacao import CHAVES, comparar_modelos
from .configuracao import gerar_celulas, validar_configuracao
from .registro import assinatura_codigo, verificar_resultado

MODELOS = ("ar1", "lstm", "mamba")
BLOCOS = ("validacao", "teste")
ARQUIVOS_PAREADOS = tuple(f"previsoes_{m}_{b}.parquet" for m in MODELOS for b in BLOCOS) + (
    "normalizador.json", "indices_ajuste_normalizador.npy", "lstm/melhor.pt",
    "lstm/historico.json", "mamba/melhor.pt", "mamba/historico.json",
)


def conferir_resumo(salvo, recalculado, campo: str = "avaliacoes") -> None:
    """Compara toda a estrutura; tolera somente arredondamento numérico mínimo."""
    if isinstance(recalculado, dict):
        if not isinstance(salvo, dict) or salvo.keys() != recalculado.keys():
            raise ValueError(f"Resumo divergente das previsões: {campo}.")
        for chave, valor in recalculado.items():
            conferir_resumo(salvo[chave], valor, f"{campo}.{chave}")
    elif isinstance(recalculado, list):
        if not isinstance(salvo, list) or len(salvo) != len(recalculado):
            raise ValueError(f"Resumo divergente das previsões: {campo}.")
        for i, valor in enumerate(recalculado):
            conferir_resumo(salvo[i], valor, f"{campo}[{i}]")
    elif type(recalculado) in (int, float):
        if type(salvo) not in (int, float) or not math.isfinite(salvo) or not math.isclose(salvo, recalculado, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError(f"Resumo divergente das previsões: {campo}.")
    elif type(salvo) is not type(recalculado) or salvo != recalculado:
        raise ValueError(f"Resumo divergente das previsões: {campo}.")


def validar_previsoes(quadro: pd.DataFrame, celula: dict, modelo: str, bloco: str, quantidade: int) -> None:
    obrigatorias = CHAVES + ["granularidade", "tarefa", "contexto_dias", "fold", "bloco", "modelo",
                             "retorno_futuro", "classe_alta", "classe_prevista", "empate"]
    obrigatorias += ["retorno_previsto_ar1"] if modelo == "ar1" else ["seed", "probabilidade_alta"]
    if not set(obrigatorias).issubset(quadro) or len(quadro) != quantidade or quadro.empty:
        raise ValueError("Previsões sem colunas obrigatórias ou contagem divergente.")
    if quadro[obrigatorias].isna().any().any() or quadro.duplicated(CHAVES).any():
        raise ValueError("Previsões incompletas ou duplicadas.")
    origem, alvo = quadro["origem_utc"], quadro["alvo_fim_utc"]
    if (str(origem.dt.tz) != "UTC" or str(alvo.dt.tz) != "UTC" or not origem.is_monotonic_increasing):
        raise ValueError("Previsões precisam estar ordenadas em UTC.")
    principal = celula["tarefa"] == "principal"
    frequencia = "1d" if principal and modelo == "ar1" else celula["granularidade"]
    horizonte = pd.Timedelta(days=1) if principal else pd.Timedelta(DURACOES[frequencia])
    passo_origem = pd.Timedelta(days=1) if principal else pd.Timedelta(DURACOES[frequencia])
    if not ((alvo - origem == horizonte) & (origem == origem.dt.floor(passo_origem))).all():
        raise ValueError("Horizonte ou instante de previsão fora do protocolo.")
    fold = next(f for f in FOLDS if f.nome == celula["fold"])
    inicio = pd.Timestamp(fold.fim_treino if bloco == "validacao" else fold.fim_validacao, tz="UTC")
    fim = pd.Timestamp(fold.fim_validacao if bloco == "validacao" else fold.fim_teste, tz="UTC")
    if not ((origem >= inicio) & (alvo < fim)).all():
        raise ValueError("Previsões violam fronteiras/purga do fold.")
    esperados = {"par": celula["par"], "granularidade": frequencia,
                 "tarefa": "24h" if principal else "proximo_candle",
                 "contexto_dias": 7 if modelo == "ar1" else celula["contexto_dias"],
                 "fold": celula["fold"], "bloco": bloco, "modelo": modelo}
    if modelo != "ar1":
        esperados["seed"] = celula["seed"]
    elif "seed" in quadro:
        raise ValueError("AR(1) determinístico não recebe seed.")
    if any(not (quadro[chave] == valor).all() for chave, valor in esperados.items()):
        raise ValueError("Metadados das previsões divergentes da execução.")
    retorno = quadro["retorno_futuro"].to_numpy(dtype=float)
    if (not np.isfinite(retorno).all() or not quadro["classe_alta"].isin([0, 1]).all()
            or not quadro["classe_prevista"].isin([0, 1]).all()
            or not quadro["empate"].isin([False, True]).all()
            or not np.array_equal(retorno > 0, quadro["classe_alta"])
            or not np.array_equal(retorno == 0, quadro["empate"])):
        raise ValueError("Classes/empates incompatíveis com os retornos.")
    estimados = quadro["retorno_previsto_ar1" if modelo == "ar1" else "probabilidade_alta"].to_numpy(dtype=float)
    if not np.isfinite(estimados).all() or (modelo != "ar1" and ((estimados < 0) | (estimados > 1)).any()):
        raise ValueError("Estimativas/probabilidades inválidas.")
    if not np.array_equal(estimados > (0 if modelo == "ar1" else 0.5), quadro["classe_prevista"]):
        raise ValueError("Classe prevista diverge do limiar fixo.")


def auditar_execucao(pasta: Path) -> tuple[dict, dict]:
    resultado = verificar_resultado(pasta / "resultado.json", ARQUIVOS_PAREADOS)
    if resultado.get("tipo_fold") != "desenvolvimento" or resultado.get("protocolo") != "1.6":
        raise ValueError("Somente execuções de desenvolvimento do protocolo 1.6 são aceitas.")
    configuracao = validar_configuracao(resultado["configuracao"])
    celula = resultado["celula"]
    if celula not in gerar_celulas(configuracao):
        raise ValueError("Célula não pertence à configuração registrada.")
    fold = next(f for f in FOLDS if f.nome == celula["fold"])
    if resultado["fold"] != fold.__dict__:
        raise ValueError("Fronteiras registradas divergentes do protocolo.")
    for nome, esperado in (("lstm", "torch.nn.LSTM"), ("mamba", configuracao["backend_mamba"])):
        if resultado["modelos"][nome]["backend"] != esperado:
            raise ValueError("Backend executado diverge do solicitado.")
    features = list(FEATURES_OHLCV if configuracao["features"] == "ohlcv" else FEATURES_AMPLIADAS)
    scaler = json.loads((pasta / "normalizador.json").read_text(encoding="utf-8"))
    if (resultado["features"] != features or resultado["dimensao_entrada"] != len(features)
            or scaler["features"] != features or scaler["metodo"] != configuracao["normalizador"]):
        raise ValueError("Features, dimensão ou normalizador divergentes.")
    indices = np.load(pasta / "indices_ajuste_normalizador.npy", allow_pickle=False)
    if (indices.ndim != 1 or not np.issubdtype(indices.dtype, np.integer) or len(indices) == 0
            or (indices < 0).any() or not (np.diff(indices) > 0).all()
            or len(indices) != scaler["quantidade_candles_ajuste"]):
        raise ValueError("Índices de ajuste do normalizador inválidos.")
    # Snapshots foram acrescentados na revisão técnica. Resultados v1 anteriores
    # continuam auditáveis, mas não ganham retroativamente o código preservado.
    if resultado.get("fontes_preservadas"):
        obrigatorios = {"codigo_fonte.json", "protocolo_executado.md", "configuracao.json", "ambiente.json"}
        if not obrigatorios.issubset(resultado["arquivos"]):
            raise ValueError("Snapshot de reprodução incompleto.")
        fontes = json.loads((pasta / "codigo_fonte.json").read_text(encoding="utf-8"))
        if assinatura_codigo(fontes) != resultado["sha256_codigo"] or sha256_arquivo(pasta / "protocolo_executado.md") != resultado["sha256_protocolo"]:
            raise ValueError("Snapshot diverge dos hashes de código/protocolo.")
        for arquivo, conteudo in (("configuracao.json", configuracao), ("ambiente.json", resultado["ambiente"])):
            if json.loads((pasta / arquivo).read_text(encoding="utf-8")) != conteudo:
                raise ValueError(f"Snapshot divergente: {arquivo}.")
    previsoes = {}
    for bloco in BLOCOS:
        previsoes[bloco] = {}
        for modelo in MODELOS:
            quadro = pd.read_parquet(pasta / f"previsoes_{modelo}_{bloco}.parquet")
            validar_previsoes(quadro, celula, modelo, bloco, resultado["contagens"][bloco])
            previsoes[bloco][modelo] = quadro
        conferida = comparar_modelos(previsoes[bloco])
        conferir_resumo(resultado["avaliacoes"][bloco], conferida, f"avaliacoes.{bloco}")
    return resultado, previsoes
