"""Piloto reproduzível AR(1) somente nos folds de desenvolvimento."""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn

from camada_dados.armazenamento import sha256_arquivo
from pre_processamento.contrato import GRANULARIDADES, PARES
from pre_processamento.folds import FOLDS, separar_fold

from .avaliacao import calcular_metricas
from .modelo import ajustar_ar1, construir_pares_autorregressivos, prever_amostras


def _resumo_codigo() -> str:
    resumo = hashlib.sha256()
    for caminho in sorted(Path(__file__).parent.glob("*.py")):
        resumo.update(caminho.name.encode("utf-8"))
        resumo.update(caminho.read_bytes())
    return resumo.hexdigest()


def _carregar_verificado(raiz: Path, manifesto: dict[str, object], relativo: str) -> pd.DataFrame:
    arquivos = manifesto["arquivos"]
    if relativo not in arquivos:
        raise ValueError(f"Arquivo ausente do manifesto do dataset: {relativo}")
    caminho = raiz / relativo
    if not caminho.is_file() or sha256_arquivo(caminho) != arquivos[relativo]["sha256"]:
        raise ValueError(f"Hash divergente ou arquivo ausente: {caminho}")
    quadro = pd.read_parquet(caminho)
    if len(quadro) != arquivos[relativo]["linhas"]:
        raise ValueError(f"Quantidade de linhas divergente: {caminho}")
    return quadro


def _gravar_texto(caminho: Path, conteudo: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(caminho.name + ".tmp")
    temporario.write_text(conteudo, encoding="utf-8")
    temporario.replace(caminho)


def _gravar_parquet(caminho: Path, quadro: pd.DataFrame) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(caminho.name + ".tmp")
    quadro.to_parquet(temporario, index=False)
    temporario.replace(caminho)


def executar_piloto(
    diretorio_dataset: Path,
    par: str = "BTCUSDT",
    fold_nome: str = "D1",
    tarefa: str = "principal",
    granularidade: str = "1d",
) -> Path:
    """Ajusta no treino purgado e avalia validação/teste de desenvolvimento."""
    if par not in PARES:
        raise ValueError(f"Par fora do protocolo: {par}")
    if fold_nome not in ("D1", "D2", "D3", "D4"):
        raise ValueError("O piloto libera somente D1–D4; 2024–2025 permanecem reservados.")
    if tarefa == "principal":
        if granularidade != "1d":
            raise ValueError("A baseline principal de 24h usa exclusivamente retornos diários UTC.")
        relativo_amostras = f"amostras/principal/{par}/1d/7d.parquet"
    elif tarefa == "proximo_candle":
        if granularidade not in GRANULARIDADES[:-1]:
            raise ValueError("A célula 1d reutiliza a baseline principal; escolha 15m, 1h ou 4h.")
        relativo_amostras = f"amostras/proximo_candle/{par}/{granularidade}/7d.parquet"
    else:
        raise ValueError(f"Tarefa desconhecida: {tarefa}")

    raiz = diretorio_dataset.resolve()
    caminho_manifesto = raiz / "manifesto_processamento.json"
    if not caminho_manifesto.is_file():
        raise FileNotFoundError(f"Dataset processado não encontrado: {caminho_manifesto}")
    manifesto = json.loads(caminho_manifesto.read_text(encoding="utf-8"))
    if manifesto.get("identificador") != raiz.name or manifesto.get("contrato") != "entrega3-v1":
        raise ValueError("Manifesto do dataset incompatível com o protocolo.")
    fold = next(fold for fold in FOLDS if fold.nome == fold_nome)
    relativo_candles = f"candles/{par}/{granularidade}.parquet"
    candles = _carregar_verificado(raiz, manifesto, relativo_candles)
    amostras = _carregar_verificado(raiz, manifesto, relativo_amostras)
    if not amostras["origem_utc"].is_monotonic_increasing or amostras["origem_utc"].duplicated().any():
        raise ValueError("Amostras fora de ordem ou com origens repetidas.")
    blocos = separar_fold(amostras, fold)
    for nome, quadro in blocos.items():
        if quadro.empty:
            raise ValueError(f"Bloco {nome} vazio; piloto indisponível.")
    if not (blocos["treino"]["alvo_fim_utc"] < pd.Timestamp(fold.fim_treino, tz="UTC")).all():
        raise ValueError("Alvo de treino cruza fronteira temporal.")

    anteriores, seguintes = construir_pares_autorregressivos(candles, blocos["treino"])
    parametros = ajustar_ar1(anteriores, seguintes)
    codigo = _resumo_codigo()
    identidade = hashlib.sha256(json.dumps({
        "dataset": manifesto["identificador"],
        "sha256_manifesto_dataset": sha256_arquivo(caminho_manifesto),
        "sha256_codigo_baseline": codigo,
        "par": par, "fold": fold_nome, "tarefa": tarefa, "granularidade": granularidade,
    }, sort_keys=True).encode("utf-8")).hexdigest()[:20]
    destino = raiz.parent.parent / "experimentos" / f"piloto_ar1_{identidade}"
    previsoes = {}
    metricas = {}
    for bloco in ("validacao", "teste"):
        quadro = prever_amostras(candles, blocos[bloco], parametros)
        quadro.insert(0, "fold", fold_nome)
        quadro.insert(1, "bloco", bloco)
        previsoes[bloco] = quadro
        metricas[bloco] = calcular_metricas(quadro)
    arquivos = {}
    for bloco, quadro in previsoes.items():
        caminho = destino / f"previsoes_{bloco}.parquet"
        _gravar_parquet(caminho, quadro)
        arquivos[caminho.name] = {"sha256": sha256_arquivo(caminho), "linhas": len(quadro)}
    resultado = {
        "tipo": "piloto_descritivo_baseline_ar1",
        "id_piloto": identidade,
        "id_dataset": manifesto["identificador"],
        "sha256_manifesto_dataset": sha256_arquivo(caminho_manifesto),
        "sha256_codigo_baseline": codigo,
        "metodo": "ARIMA(1,0,0) nos log-retornos, AR(1) com intercepto estimado por MQO condicional",
        "serie": "retornos de fechamentos diários UTC" if tarefa == "principal" else f"retornos de candles {granularidade}",
        "par": par, "fold": fold_nome, "tipo_fold": fold.tipo,
        "tarefa": tarefa, "granularidade": granularidade, "contexto_dias_amostras": 7,
        "fronteiras_utc": {"fim_treino": fold.fim_treino, "fim_validacao": fold.fim_validacao, "fim_teste": fold.fim_teste},
        "coeficientes": {"alfa": parametros.alfa, "phi": parametros.phi},
        "pares_retorno_ajuste": parametros.quantidade_pares,
        "metricas": metricas,
        "versoes": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "scikit_learn": sklearn.__version__},
        "arquivos": arquivos,
        "interpretacao": "Este piloto de desenvolvimento não mede ganho do Mamba, distância de BA_Mamba a 50% ou teste PT.",
    }
    _gravar_texto(destino / "resultado.json", json.dumps(resultado, ensure_ascii=False, indent=2) + "\n")
    return destino
