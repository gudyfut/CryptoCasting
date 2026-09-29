"""Objetos de domínio da coleta, sem dependências de rede ou de arquivos."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class ConfiguracaoColeta:
    fonte: str
    mercado: str
    pares: tuple[str, ...]
    intervalo: str
    inicio: datetime
    fim: datetime
    diretorio_dados: Path

    def validar(self) -> None:
        if self.fonte != "binance_public_data" or self.mercado != "spot":
            raise ValueError("A entrega 2 aceita somente Binance Public Data Spot.")
        if self.pares != ("BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT"):
            raise ValueError("Os pares oficiais devem ser BTCUSDT, ETHUSDT, BNBUSDT e XRPUSDT, nessa ordem.")
        if self.intervalo != "15m":
            raise ValueError("A fonte oficial da coleta deve usar candles de 15m.")
        if self.inicio.tzinfo is None or self.fim.tzinfo is None:
            raise ValueError("Início e fim devem possuir fuso horário.")
        if (
            self.inicio != datetime(2021, 1, 1, tzinfo=timezone.utc)
            or self.fim != datetime(2026, 1, 1, tzinfo=timezone.utc)
        ):
            raise ValueError("O período oficial deve ser 2021-01-01 a 2026-01-01 UTC, fim exclusivo.")
        if self.inicio >= self.fim:
            raise ValueError("O início deve ser anterior ao fim.")


@dataclass(frozen=True)
class ItemColeta:
    par: str
    intervalo: str
    competencia: str
    inicio: datetime
    fim: datetime
    url_dados: str
    url_checksum: str
    caminho_relativo: Path

    @property
    def chave(self) -> str:
        return f"{self.par}:{self.intervalo}:{self.competencia}"


@dataclass
class ResultadoAuditoria:
    quantidade_esperada: int
    quantidade_observada: int = 0
    timestamp_minimo_utc: str | None = None
    timestamp_maximo_utc: str | None = None
    unidade_timestamp_origem: str | None = None
    duplicatas: int = 0
    duplicatas_conflitantes: int = 0
    lacunas: int = 0
    erros: list[str] = field(default_factory=list)

    @property
    def valido(self) -> bool:
        return not self.erros
