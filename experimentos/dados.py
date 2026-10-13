"""Leitura íntegra da Entrega 3, verificação vetorial e janelas sob demanda."""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from torch.utils.data import Dataset

from camada_dados.armazenamento import sha256_arquivo
from pre_processamento.contrato import FEATURES_OHLCV, FEATURES_AMPLIADAS, DURACOES, candles_por_contexto, PARES, GRANULARIDADES
from pre_processamento.folds import FOLDS, separar_fold, indices_candles_unicos


class DatasetProcessado:
    def __init__(self, raiz: Path):
        self.raiz = raiz.resolve()
        caminho = self.raiz / "manifesto_processamento.json"
        self.manifesto = json.loads(caminho.read_text(encoding="utf-8"))
        self.resumo_manifesto = sha256_arquivo(caminho)
        if (self.manifesto.get("contrato") != "entrega3-v1" or self.manifesto.get("identificador") != self.raiz.name
                or self.manifesto.get("pares") != list(PARES) or self.manifesto.get("granularidades") != list(GRANULARIDADES)
                or self.manifesto.get("folds") != [f.__dict__ for f in FOLDS]):
            raise ValueError("Manifesto da Entrega 3 incompatível com o protocolo/folds vigentes.")

    def ler(self, relativo: str) -> pd.DataFrame:
        caminho = (self.raiz / relativo).resolve()
        if not caminho.is_relative_to(self.raiz):
            raise ValueError("Arquivo fora do dataset.")
        registro = self.manifesto["arquivos"].get(relativo)
        if not registro or sha256_arquivo(caminho) != registro["sha256"]:
            raise ValueError(f"Arquivo ausente ou hash divergente: {relativo}")
        quadro = pd.read_parquet(caminho)
        if len(quadro) != registro["linhas"]:
            raise ValueError(f"Contagem divergente: {relativo}")
        return quadro

    def carregar(self, celula: dict) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
        par, granularidade = celula["par"], celula["granularidade"]
        candles = self.ler(f"candles/{par}/{granularidade}.parquet")
        amostras = self.ler(f"amostras/{celula['tarefa']}/{par}/{granularidade}/{celula['contexto_dias']}d.parquet")
        validar_amostras(candles, amostras, celula)
        fold = next(f for f in FOLDS if f.nome == celula["fold"])
        blocos = separar_fold(amostras, fold)
        for nome, quadro in blocos.items():
            if quadro.empty:
                raise ValueError(f"Bloco {nome} vazio: célula indisponível.")
        if blocos["treino"]["classe_alta"].nunique() != 2 or blocos["validacao"]["classe_alta"].nunique() != 2:
            raise ValueError("Treino/validação sem ambas as classes: seleção por BA indisponível.")
        return candles, blocos


def validar_amostras(candles: pd.DataFrame, amostras: pd.DataFrame, celula: dict) -> None:
    if candles.empty or amostras.empty:
        raise ValueError("Candles ou amostras vazios.")
    duracao = pd.Timedelta(DURACOES[celula["granularidade"]])
    if not (candles["fim_utc"] - candles["abertura_utc"] == duracao).all():
        raise ValueError("Duração do candle divergente; possível lacuna ou timestamp incorreto.")
    for quadro, coluna in ((candles, "fim_utc"), (amostras, "origem_utc")):
        if not quadro[coluna].is_monotonic_increasing or quadro[coluna].duplicated().any():
            raise ValueError("Timestamps duplicados ou fora de ordem.")
        if str(quadro[coluna].dt.tz) != "UTC":
            raise ValueError("Timestamps devem estar em UTC.")
        for chave in ("par", "granularidade"):
            if not (quadro[chave] == celula[chave]).all():
                raise ValueError("Identidade da célula divergente.")
    tamanho = candles_por_contexto(celula["granularidade"], celula["contexto_dias"])
    horizonte = candles_por_contexto(celula["granularidade"], 1) if celula["tarefa"] == "principal" else 1
    tarefa = "24h" if celula["tarefa"] == "principal" else "proximo_candle"
    if not ((amostras["contexto_dias"] == celula["contexto_dias"]) & (amostras["horizonte_candles"] == horizonte) & (amostras["tarefa"] == tarefa)).all():
        raise ValueError("Contexto/horizonte/tarefa divergentes.")
    passo_origem = pd.Timedelta(days=1) if celula["tarefa"] == "principal" else duracao
    if not (amostras["origem_utc"] == amostras["origem_utc"].dt.floor(passo_origem)).all():
        raise ValueError("Timestamp de origem fora da grade UTC da tarefa.")
    indices = amostras[["indice_contexto_inicio", "indice_contexto_fim", "indice_alvo"]].to_numpy()
    if not np.isfinite(indices).all() or not np.equal(indices, indices.astype(np.int64)).all():
        raise ValueError("Índices devem ser inteiros finitos.")
    inicio, fim, alvo = indices.astype(np.int64).T
    if (inicio < 0).any() or (alvo >= len(candles)).any() or not ((fim - inicio + 1 == tamanho) & (alvo - fim == horizonte)).all():
        raise ValueError("Dimensão ou índices da janela inválidos.")
    for coluna, origem, posicoes in (
        ("contexto_inicio_utc", "abertura_utc", inicio), ("contexto_fim_utc", "fim_utc", fim),
        ("origem_utc", "fim_utc", fim), ("alvo_fim_utc", "fim_utc", alvo),
    ):
        if not pd.DatetimeIndex(amostras[coluna]).equals(pd.DatetimeIndex(candles[origem].iloc[posicoes])):
            raise ValueError(f"Timestamp não corresponde ao parquet: {coluna}")
    tempos = pd.DatetimeIndex(candles["fim_utc"]).as_unit("ns").asi8
    segmentos = np.cumsum(np.r_[True, np.diff(tempos) != pd.Timedelta(DURACOES[celula["granularidade"]]).value])
    if not (segmentos[inicio] == segmentos[alvo]).all():
        raise ValueError("A janela ou alvo atravessa lacuna.")
    precos = candles["close"].to_numpy(dtype=float)
    retornos = np.log(precos[alvo] / precos[fim])
    if (not np.isfinite(retornos).all() or not np.allclose(retornos, amostras["retorno_futuro"], atol=1e-12, rtol=0)
            or not np.array_equal(retornos > 0, amostras["classe_alta"])
            or not np.array_equal(precos[alvo] == precos[fim], amostras["empate"])):
        raise ValueError("Rótulo/retorno divergente do alvo.")


def preparar_entradas(candles: pd.DataFrame, blocos: dict, grupo: str, metodo: str):
    if grupo not in ("ohlcv", "ampliadas") or metodo not in ("standard", "minmax"):
        raise ValueError("Features ou método de normalização fora do protocolo.")
    features = FEATURES_OHLCV if grupo == "ohlcv" else FEATURES_AMPLIADAS
    indices = indices_candles_unicos(blocos["treino"], len(candles))
    valores = candles[list(features)].to_numpy(dtype=np.float64)
    if not np.isfinite(valores[indices]).all():
        raise ValueError("Feature não finita no treino.")
    scaler = StandardScaler() if metodo == "standard" else MinMaxScaler(clip=False)
    scaler.fit(valores[indices])
    # Transformar somente a união de entradas dos três blocos, sem ajustar no futuro.
    usados = indices_candles_unicos(pd.concat(list(blocos.values())), len(candles))
    matriz = np.full(valores.shape, np.nan, dtype=np.float32)
    matriz[usados] = scaler.transform(valores[usados]).astype(np.float32)
    if not np.isfinite(matriz[usados]).all():
        raise ValueError("Feature não finita nas entradas transformadas.")
    estado = {"metodo": metodo, "features": list(features), "quantidade_candles_ajuste": len(indices),
              "primeiro_candle_ajuste_utc": candles.iloc[indices[0]]["fim_utc"].isoformat(),
              "ultimo_candle_ajuste_utc": candles.iloc[indices[-1]]["fim_utc"].isoformat(),
              "atributos": {}}
    for chave in ("mean_", "var_", "scale_", "min_", "data_min_", "data_max_", "data_range_", "n_samples_seen_", "n_features_in_"):
        if hasattr(scaler, chave):
            estado["atributos"][chave] = np.asarray(getattr(scaler, chave)).tolist()
    return matriz, estado, indices


class JanelasTemporais(Dataset):
    def __init__(self, matriz: np.ndarray, amostras: pd.DataFrame):
        self.matriz = matriz
        self.inicios = amostras["indice_contexto_inicio"].to_numpy(dtype=np.int64)
        self.fins = amostras["indice_contexto_fim"].to_numpy(dtype=np.int64)
        self.rotulos = amostras["classe_alta"].to_numpy(dtype=np.int64)

    def __len__(self):
        return len(self.rotulos)

    def __getitem__(self, indice):
        return torch.from_numpy(self.matriz[self.inicios[indice]:self.fins[indice] + 1]), int(self.rotulos[indice])
