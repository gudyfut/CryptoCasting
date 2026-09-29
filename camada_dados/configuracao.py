"""Carregamento da configuração fechada e inventário determinístico."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .dominio import ConfiguracaoColeta, ItemColeta

BASE_BINANCE = "https://data.binance.vision/data/spot/monthly/klines"


def _data_utc(valor: str) -> datetime:
    data = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    if data.tzinfo is None or data.utcoffset() is None:
        raise ValueError("Datas da coleta devem informar fuso horário explícito.")
    return data.astimezone(timezone.utc)


def carregar_configuracao(caminho: Path) -> ConfiguracaoColeta:
    caminho = caminho.resolve()
    conteudo = json.loads(caminho.read_text(encoding="utf-8"))
    raiz_projeto = caminho.parent.parent
    diretorio = (raiz_projeto / conteudo["diretorio_dados"]).resolve()
    configuracao = ConfiguracaoColeta(
        fonte=conteudo["fonte"],
        mercado=conteudo["mercado"],
        pares=tuple(conteudo["pares"]),
        intervalo=conteudo["intervalo"],
        inicio=_data_utc(conteudo["inicio"]),
        fim=_data_utc(conteudo["fim"]),
        diretorio_dados=diretorio,
    )
    configuracao.validar()
    return configuracao


def _proximo_mes(data: datetime) -> datetime:
    ano = data.year + (1 if data.month == 12 else 0)
    mes = 1 if data.month == 12 else data.month + 1
    return data.replace(year=ano, month=mes, day=1)


def gerar_itens_coleta(configuracao: ConfiguracaoColeta) -> list[ItemColeta]:
    configuracao.validar()
    meses: list[tuple[datetime, datetime]] = []
    cursor = configuracao.inicio
    while cursor < configuracao.fim:
        seguinte = min(_proximo_mes(cursor), configuracao.fim)
        meses.append((cursor, seguinte))
        cursor = seguinte

    itens: list[ItemColeta] = []
    for par in configuracao.pares:
        for inicio, fim in meses:
            competencia = inicio.strftime("%Y-%m")
            nome = f"{par}-{configuracao.intervalo}-{competencia}.zip"
            url = f"{BASE_BINANCE}/{par}/{configuracao.intervalo}/{nome}"
            itens.append(
                ItemColeta(
                    par=par,
                    intervalo=configuracao.intervalo,
                    competencia=competencia,
                    inicio=inicio,
                    fim=fim,
                    url_dados=url,
                    url_checksum=f"{url}.CHECKSUM",
                    caminho_relativo=Path(par) / configuracao.intervalo / nome,
                )
            )
    return itens
