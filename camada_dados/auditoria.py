"""Leitura e auditoria causal dos candles brutos, sem alterar o arquivo original."""

from __future__ import annotations

import csv
import io
import zipfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .dominio import ItemColeta, ResultadoAuditoria

INTERVALO = timedelta(minutes=15)


def detectar_unidade_timestamp(valor: int) -> str:
    if valor >= 100_000_000_000_000:
        return "microssegundos"
    if valor >= 100_000_000_000:
        return "milissegundos"
    raise ValueError(f"Timestamp fora das escalas esperadas: {valor}")


def converter_timestamp(valor: int, unidade: str) -> datetime:
    divisor = 1_000_000 if unidade == "microssegundos" else 1_000
    return datetime.fromtimestamp(valor / divisor, tz=timezone.utc)


def auditar_zip(caminho: Path, item: ItemColeta) -> ResultadoAuditoria:
    esperado = int((item.fim - item.inicio) / INTERVALO)
    resultado = ResultadoAuditoria(quantidade_esperada=esperado)
    nome_csv = caminho.with_suffix(".csv").name
    timestamps: dict[datetime, tuple[Decimal, ...]] = {}
    unidades: set[str] = set()
    timestamp_anterior: datetime | None = None
    ocorrencias_fora_de_ordem = 0

    try:
        with zipfile.ZipFile(caminho) as arquivo_zip:
            with arquivo_zip.open(nome_csv) as bruto:
                leitor = csv.reader(io.TextIOWrapper(bruto, encoding="utf-8", newline=""))
                for numero_linha, linha in enumerate(leitor, start=1):
                    try:
                        if len(linha) < 6:
                            raise ValueError("menos de seis colunas")
                        valor_timestamp = int(linha[0])
                        unidade = detectar_unidade_timestamp(valor_timestamp)
                        unidades.add(unidade)
                        instante = converter_timestamp(valor_timestamp, unidade)
                        if timestamp_anterior is not None and instante < timestamp_anterior:
                            ocorrencias_fora_de_ordem += 1
                        timestamp_anterior = instante
                        open_, high, low, close, volume = map(Decimal, linha[1:6])
                        valores = (open_, high, low, close, volume)
                        if min(open_, high, low, close) <= 0 or volume < 0:
                            raise ValueError("preço não positivo ou volume negativo")
                        if high < max(open_, close) or low > min(open_, close) or high < low:
                            raise ValueError("OHLC inconsistente")
                        if instante in timestamps:
                            resultado.duplicatas += 1
                            if timestamps[instante] != valores:
                                resultado.duplicatas_conflitantes += 1
                        else:
                            timestamps[instante] = valores
                    except (ValueError, InvalidOperation) as erro:
                        resultado.erros.append(f"linha {numero_linha}: {erro}")
    except (KeyError, zipfile.BadZipFile) as erro:
        resultado.erros.append(f"falha ao abrir o CSV esperado: {erro}")
        return resultado

    resultado.quantidade_observada = len(timestamps)
    if len(unidades) == 1:
        resultado.unidade_timestamp_origem = next(iter(unidades))
    elif len(unidades) > 1:
        resultado.erros.append(f"unidades de timestamp misturadas: {sorted(unidades)}")

    ordenados = sorted(timestamps)
    if ordenados:
        resultado.timestamp_minimo_utc = ordenados[0].isoformat()
        resultado.timestamp_maximo_utc = ordenados[-1].isoformat()
    dentro = [instante for instante in ordenados if item.inicio <= instante < item.fim]
    fora = len(ordenados) - len(dentro)
    resultado.lacunas = max(esperado - len(set(dentro)), 0)
    desalinhados = sum((instante - item.inicio) % INTERVALO != timedelta(0) for instante in dentro)

    if fora:
        resultado.erros.append(f"{fora} timestamp(s) fora da competência")
    if desalinhados:
        resultado.erros.append(f"{desalinhados} timestamp(s) fora da grade de 15 minutos")
    if resultado.duplicatas:
        resultado.erros.append(f"{resultado.duplicatas} timestamp(s) duplicado(s)")
    if ocorrencias_fora_de_ordem:
        resultado.erros.append(
            f"{ocorrencias_fora_de_ordem} ocorrência(s) fora da ordem temporal"
        )
    if resultado.lacunas:
        resultado.erros.append(f"{resultado.lacunas} candle(s) ausente(s)")
    return resultado
