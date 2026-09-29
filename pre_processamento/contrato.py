"""Contrato fechado da Entrega 3, sem opções experimentais implícitas."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from camada_dados.configuracao import carregar_configuracao
from camada_dados.dominio import ConfiguracaoColeta

PARES = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT")
GRANULARIDADES = ("15m", "1h", "4h", "1d")
DURACOES = {
    "15m": timedelta(minutes=15),
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "1d": timedelta(days=1),
}
FEATURES_OHLCV = ("open", "high", "low", "close", "volume")
FEATURES_AMPLIADAS = FEATURES_OHLCV + (
    "retorno_24h", "distancia_sma_7d", "volatilidade_7d"
)


@dataclass(frozen=True)
class ConfiguracaoProcessamento:
    raiz_projeto: Path
    caminho_configuracao: Path
    coleta: ConfiguracaoColeta
    caminho_manifesto_coleta: Path
    diretorio_saida: Path
    versao_contrato: str
    conteudo: dict[str, object]


def carregar_configuracao_processamento(caminho: Path) -> ConfiguracaoProcessamento:
    caminho = caminho.resolve()
    raiz = caminho.parent.parent
    conteudo = json.loads(caminho.read_text(encoding="utf-8"))
    esperados: dict[str, object] = {
        "versao_contrato": "entrega3-v1",
        "granularidades": list(GRANULARIDADES),
        "contextos_principais_dias": [7, 14],
        "contexto_complementar_dias": 7,
        "features_ohlcv": list(FEATURES_OHLCV),
        "features_ampliadas": list(FEATURES_AMPLIADAS),
    }
    for chave, valor in esperados.items():
        if conteudo.get(chave) != valor:
            raise ValueError(f"Configuração incompatível com o protocolo: {chave}")

    coleta = carregar_configuracao(raiz / str(conteudo["configuracao_coleta"]))
    if coleta.pares != PARES or coleta.intervalo != "15m":
        raise ValueError("A Entrega 3 exige os quatro pares e candles-base de 15m.")

    return ConfiguracaoProcessamento(
        raiz_projeto=raiz,
        caminho_configuracao=caminho,
        coleta=coleta,
        caminho_manifesto_coleta=(raiz / str(conteudo["manifesto_coleta"])).resolve(),
        diretorio_saida=(raiz / str(conteudo["diretorio_saida"])).resolve(),
        versao_contrato="entrega3-v1",
        conteudo=conteudo,
    )


def candles_por_contexto(granularidade: str, dias: int) -> int:
    duracao = DURACOES[granularidade]
    intervalo = timedelta(days=dias)
    if intervalo % duracao:
        raise ValueError("O contexto não é divisível pela granularidade.")
    return intervalo // duracao


def candles_por_horizonte_24h(granularidade: str) -> int:
    return candles_por_contexto(granularidade, 1)
