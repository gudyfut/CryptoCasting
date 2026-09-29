"""Leitura de ZIPs aprovados pela Entrega 2 e verificação da procedência."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from camada_dados.armazenamento import sha256_arquivo, validar_zip
from camada_dados.configuracao import gerar_itens_coleta
from camada_dados.dominio import ItemColeta

from .contrato import ConfiguracaoProcessamento

COLUNAS_OHLCV = ("open", "high", "low", "close", "volume")
PASSO_15M = pd.Timedelta(minutes=15)


def carregar_manifesto_aprovado(
    configuracao: ConfiguracaoProcessamento,
) -> tuple[dict[str, dict[str, object]], str]:
    """Exige inventário completo; aceita apenas lacunas explícitas em ZIP íntegro."""
    caminho = configuracao.caminho_manifesto_coleta
    if not caminho.is_file():
        raise FileNotFoundError(
            f"Manifesto da Entrega 2 ausente: {caminho}. "
            "Na raiz do projeto, execute primeiro "
            "'python run_coleta.py --config configuracoes/coleta_oficial.json' "
            "e confira o resumo da auditoria antes de repetir o pipeline."
        )
    registros: dict[str, dict[str, object]] = {}
    for numero_linha, linha in enumerate(caminho.read_text(encoding="utf-8").splitlines(), 1):
        if not linha.strip():
            continue
        registro = json.loads(linha)
        chave = str(registro.get("chave", ""))
        if chave in registros:
            raise ValueError(f"Chave duplicada no manifesto, linha {numero_linha}: {chave}")
        registros[chave] = registro

    itens = gerar_itens_coleta(configuracao.coleta)
    esperado = {item.chave for item in itens}
    if set(registros) != esperado:
        faltando = sorted(esperado - set(registros))
        extras = sorted(set(registros) - esperado)
        raise ValueError(
            f"Inventário da coleta incompleto ou divergente: {len(faltando)} faltantes, "
            f"{len(extras)} extras. Exemplos: {faltando[:3]} {extras[:3]}"
        )

    assinaturas: list[tuple[str, str]] = []
    for item in itens:
        registro = registros[item.chave]
        if (
            registro.get("par") != item.par
            or registro.get("intervalo") != item.intervalo
            or registro.get("competencia") != item.competencia
        ):
            raise ValueError(f"Identidade divergente no manifesto: {item.chave}")
        if registro.get("zip_valido") is not True:
            raise ValueError(f"ZIP não aprovado no manifesto: {item.chave}")
        if registro.get("checksum_valido") is False:
            raise ValueError(f"Checksum divergente no manifesto: {item.chave}")
        quantidade_esperada = int((item.fim - item.inicio) / PASSO_15M)
        quantidade_observada = registro.get("quantidade_observada")
        lacunas = registro.get("lacunas")
        if registro.get("quantidade_esperada") != quantidade_esperada:
            raise ValueError(f"Quantidade esperada divergente no manifesto: {item.chave}")
        if not isinstance(quantidade_observada, int) or not isinstance(lacunas, int):
            raise ValueError(f"Contagens ausentes no manifesto: {item.chave}")
        if registro.get("duplicatas", 0) != 0 or registro.get("duplicatas_conflitantes", 0) != 0:
            raise ValueError(f"Duplicatas no manifesto: {item.chave}")
        status = registro.get("status")
        if status == "valido":
            if lacunas != 0 or quantidade_observada != quantidade_esperada or registro.get("erros"):
                raise ValueError(f"Registro válido com inconsistência: {item.chave}")
        elif status == "invalido":
            erro_exclusivo = f"{lacunas} candle(s) ausente(s)"
            if (
                lacunas <= 0
                or quantidade_observada != quantidade_esperada - lacunas
                or registro.get("erros") != erro_exclusivo
                or registro.get("checksum_valido") is not True
            ):
                raise ValueError(f"Falha além de lacunas auditadas: {item.chave}: {registro.get('erros')}")
        else:
            raise ValueError(f"Status não aprovado no manifesto: {item.chave}")
        resumo = str(registro.get("sha256", ""))
        if len(resumo) != 64 or any(c not in "0123456789abcdef" for c in resumo.lower()):
            raise ValueError(f"SHA-256 ausente ou inválido: {item.chave}")
        assinaturas.append((item.chave, resumo.lower()))

    carga = json.dumps(
        {"contrato": configuracao.conteudo, "entradas": assinaturas},
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    identificador = hashlib.sha256(carga).hexdigest()[:16]
    return registros, identificador


def ler_zip_aprovado(
    configuracao: ConfiguracaoProcessamento,
    item: ItemColeta,
    registro: dict[str, object],
) -> pd.DataFrame:
    """Relê o ZIP, confirma integridade e preserva lacunas auditadas sem preenchê-las."""
    caminho = configuracao.coleta.diretorio_dados / item.caminho_relativo
    if not caminho.is_file():
        raise FileNotFoundError(f"ZIP aprovado no manifesto não existe: {caminho}")
    if sha256_arquivo(caminho) != registro["sha256"]:
        raise ValueError(f"ZIP alterado depois da auditoria: {item.chave}")
    nome_csv = caminho.with_suffix(".csv").name
    validar_zip(caminho, nome_csv)

    with zipfile.ZipFile(caminho) as arquivo_zip:
        with arquivo_zip.open(nome_csv) as bruto:
            quadro = pd.read_csv(bruto, header=None, usecols=list(range(6)))
    quadro.columns = ["timestamp_origem", *COLUNAS_OHLCV]
    if quadro.empty:
        raise ValueError(f"CSV vazio: {item.chave}")

    unidade = registro.get("unidade_timestamp_origem")
    if unidade not in ("milissegundos", "microssegundos"):
        raise ValueError(f"Unidade de timestamp não auditada: {item.chave}")
    bruto_numerico = pd.to_numeric(quadro.pop("timestamp_origem"), errors="raise")
    if bruto_numerico.isna().any() or not np.isfinite(bruto_numerico.to_numpy(dtype="float64")).all():
        raise ValueError(f"Timestamp inválido: {item.chave}")
    if not (bruto_numerico % 1 == 0).all():
        raise ValueError(f"Timestamp não inteiro: {item.chave}")
    valores_timestamp = bruto_numerico.astype("int64")
    if unidade == "milissegundos" and (valores_timestamp >= 100_000_000_000_000).any():
        raise ValueError(f"Escala de timestamp divergente: {item.chave}")
    if unidade == "microssegundos" and (valores_timestamp < 100_000_000_000_000).any():
        raise ValueError(f"Escala de timestamp divergente: {item.chave}")
    quadro.insert(
        0,
        "abertura_utc",
        pd.to_datetime(valores_timestamp, unit="ms" if unidade == "milissegundos" else "us", utc=True),
    )
    for coluna in COLUNAS_OHLCV:
        quadro[coluna] = pd.to_numeric(quadro[coluna], errors="raise").astype("float64")
    if not np.isfinite(quadro[list(COLUNAS_OHLCV)].to_numpy()).all():
        raise ValueError(f"OHLCV não finito: {item.chave}")
    if (quadro[["open", "high", "low", "close"]] <= 0).any().any() or (quadro["volume"] < 0).any():
        raise ValueError(f"Preço/volume inválido: {item.chave}")
    if (
        (quadro["high"] < quadro[["open", "close"]].max(axis=1)).any()
        or (quadro["low"] > quadro[["open", "close"]].min(axis=1)).any()
        or (quadro["high"] < quadro["low"]).any()
    ):
        raise ValueError(f"OHLC inconsistente: {item.chave}")

    inicio = pd.Timestamp(item.inicio)
    fim = pd.Timestamp(item.fim)
    aberturas = quadro["abertura_utc"]
    if (
        len(quadro) != registro["quantidade_observada"]
        or (aberturas < inicio).any()
        or (aberturas >= fim).any()
        or ((aberturas - inicio) % PASSO_15M != pd.Timedelta(0)).any()
        or not aberturas.is_monotonic_increasing
        or aberturas.duplicated().any()
    ):
        raise ValueError(f"Grade mensal divergente da auditoria: {item.chave}")
    quadro.insert(1, "fim_utc", aberturas + PASSO_15M)
    return quadro


def carregar_candles_base(
    configuracao: ConfiguracaoProcessamento,
    registros: dict[str, dict[str, object]],
    par: str,
) -> pd.DataFrame:
    itens = [item for item in gerar_itens_coleta(configuracao.coleta) if item.par == par]
    quadros = [ler_zip_aprovado(configuracao, item, registros[item.chave]) for item in itens]
    base = pd.concat(quadros, ignore_index=True)
    if base["abertura_utc"].duplicated().any():
        raise ValueError(f"Timestamps duplicados entre competências: {par}")
    return base
