"""Caso de uso que orquestra fonte, armazenamento, auditoria e manifesto."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zipfile import BadZipFile

from .armazenamento import extrair_checksum, sha256_arquivo, validar_zip
from .auditoria import auditar_zip
from .configuracao import gerar_itens_coleta
from .dominio import ConfiguracaoColeta, ItemColeta
from .fonte_binance import FonteBinancePublica
from .manifesto import RepositorioManifesto


@dataclass(frozen=True)
class ResumoColeta:
    total: int
    validos: int
    falhas: int


class ServicoColeta:
    def __init__(self, configuracao: ConfiguracaoColeta, fonte: FonteBinancePublica | None = None) -> None:
        self.configuracao = configuracao
        self.fonte = fonte or FonteBinancePublica()
        self.manifesto = RepositorioManifesto(configuracao.diretorio_dados.parent / "manifestos")

    def executar(self, somente_auditoria: bool = False) -> ResumoColeta:
        itens = gerar_itens_coleta(self.configuracao)
        validos = 0
        for item in itens:
            registro = self._processar(item, somente_auditoria)
            self.manifesto.salvar(registro)
            validos += int(registro["status"] == "valido")
        return ResumoColeta(total=len(itens), validos=validos, falhas=len(itens) - validos)

    def _processar(self, item: ItemColeta, somente_auditoria: bool) -> dict[str, object]:
        caminho = self.configuracao.diretorio_dados / item.caminho_relativo
        caminho_checksum = caminho.with_name(f"{caminho.name}.CHECKSUM")
        erros: list[str] = []
        avisos: list[str] = []
        checksum_oficial: str | None = None
        checksum_valido: bool | None = None
        zip_valido = False

        if not somente_auditoria:
            try:
                self.fonte.baixar(item.url_dados, caminho)
            except Exception as erro:
                erros.append(str(erro))
            try:
                self.fonte.baixar(item.url_checksum, caminho_checksum, forcar=True)
            except Exception as erro:
                avisos.append(f"falha ao atualizar checksum oficial: {erro}")

        if not caminho.exists():
            erros.append("arquivo ZIP ausente")
            return self._registro_base(item, caminho, "ausente", erros, avisos)

        sha256 = sha256_arquivo(caminho)
        if caminho_checksum.exists():
            try:
                checksum_oficial = extrair_checksum(caminho_checksum.read_text(encoding="utf-8"))
                checksum_valido = checksum_oficial == sha256
                if not checksum_valido and not somente_auditoria:
                    self.fonte.baixar(item.url_dados, caminho, forcar=True)
                    sha256 = sha256_arquivo(caminho)
                    checksum_valido = checksum_oficial == sha256
                    avisos.append("arquivo divergente foi baixado novamente")
                if not checksum_valido:
                    erros.append("SHA-256 diverge do checksum oficial após validação")
            except (OSError, ValueError, RuntimeError) as erro:
                erros.append(str(erro))

        nome_csv = caminho.with_suffix(".csv").name
        try:
            validar_zip(caminho, nome_csv)
            zip_valido = True
        except (OSError, ValueError, BadZipFile) as erro:
            if somente_auditoria:
                erros.append(f"ZIP inválido: {erro}")
            else:
                try:
                    self.fonte.baixar(item.url_dados, caminho, forcar=True)
                    sha256 = sha256_arquivo(caminho)
                    validar_zip(caminho, nome_csv)
                    zip_valido = True
                    avisos.append("ZIP inválido foi baixado novamente")
                    if checksum_oficial is not None:
                        checksum_valido = checksum_oficial == sha256
                        if not checksum_valido:
                            erros.append("SHA-256 diverge do checksum oficial após novo download")
                except (OSError, ValueError, BadZipFile, RuntimeError) as erro_recuperacao:
                    erros.append(f"ZIP inválido e recuperação falhou: {erro_recuperacao}")

        auditoria = None
        if zip_valido:
            try:
                auditoria = auditar_zip(caminho, item)
                erros.extend(auditoria.erros)
            except (OSError, ValueError, BadZipFile) as erro:
                erros.append(f"falha na auditoria do CSV: {erro}")

        registro = self._registro_base(
            item, caminho, "valido" if not erros else "invalido", erros, avisos
        )
        registro.update(
            {
                "sha256": sha256,
                "checksum_oficial": checksum_oficial,
                "checksum_valido": checksum_valido,
                "zip_valido": zip_valido,
                "tamanho_bytes": caminho.stat().st_size,
            }
        )
        if auditoria:
            registro.update(
                {
                    "quantidade_esperada": auditoria.quantidade_esperada,
                    "quantidade_observada": auditoria.quantidade_observada,
                    "timestamp_minimo_utc": auditoria.timestamp_minimo_utc,
                    "timestamp_maximo_utc": auditoria.timestamp_maximo_utc,
                    "unidade_timestamp_origem": auditoria.unidade_timestamp_origem,
                    "duplicatas": auditoria.duplicatas,
                    "duplicatas_conflitantes": auditoria.duplicatas_conflitantes,
                    "lacunas": auditoria.lacunas,
                }
            )
        return registro

    def _registro_base(
        self,
        item: ItemColeta,
        caminho: Path,
        status: str,
        erros: list[str],
        avisos: list[str],
    ) -> dict[str, object]:
        try:
            relativo = caminho.relative_to(self.configuracao.diretorio_dados.parent.parent)
        except ValueError:
            relativo = caminho
        return {
            "versao_manifesto": 1,
            "chave": item.chave,
            "fonte": self.configuracao.fonte,
            "mercado": self.configuracao.mercado,
            "par": item.par,
            "intervalo": item.intervalo,
            "competencia": item.competencia,
            "url_dados": item.url_dados,
            "url_checksum": item.url_checksum,
            "caminho_relativo": relativo.as_posix(),
            "periodo_solicitado_inicio_utc": item.inicio.isoformat(),
            "periodo_solicitado_fim_utc": item.fim.isoformat(),
            "quantidade_esperada": int((item.fim - item.inicio).total_seconds() // 900),
            "data_coleta_utc": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "erros": " | ".join(erros),
            "avisos": " | ".join(avisos),
        }
