"""Adaptador isolado para o repositório público de dados da Binance."""

from __future__ import annotations

import time
from pathlib import Path
from urllib.request import Request, urlopen


class FonteBinancePublica:
    def __init__(self, timeout_segundos: int = 60, tentativas: int = 3) -> None:
        self.timeout_segundos = timeout_segundos
        self.tentativas = tentativas

    def baixar(self, url: str, destino: Path, forcar: bool = False) -> bool:
        """Baixa de forma atômica. Retorna False quando reutiliza o destino."""
        if destino.exists() and not forcar:
            return False
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporario = destino.with_name(f"{destino.name}.parcial")
        ultimo_erro: Exception | None = None
        for tentativa in range(1, self.tentativas + 1):
            try:
                requisicao = Request(url, headers={"User-Agent": "CryptoCasting-TCC/1.0"})
                with urlopen(requisicao, timeout=self.timeout_segundos) as resposta:
                    with temporario.open("wb") as arquivo:
                        while bloco := resposta.read(1024 * 1024):
                            arquivo.write(bloco)
                temporario.replace(destino)
                return True
            except Exception as erro:  # a fronteira de rede é registrada pelo serviço
                ultimo_erro = erro
                temporario.unlink(missing_ok=True)
                if tentativa < self.tentativas:
                    time.sleep(2 ** (tentativa - 1))
        raise RuntimeError(f"Falha após {self.tentativas} tentativas em {url}: {ultimo_erro}")
