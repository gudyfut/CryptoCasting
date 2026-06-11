import os
import sys
import time
import logging
import signal
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd
from binance import Client
from binance.exceptions import BinanceAPIException

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DADOS_DIR = BASE_DIR / "dados"
DADOS_DIR.mkdir(exist_ok=True)

PARES_PADRAO = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "DOGEUSDT",
    "DOTUSDT",
    "MATICUSDT",
    "AVAXUSDT",
]

INTERVALO_PADRAO = Client.KLINE_INTERVAL_5MINUTE
PERIODO_PADRAO = "30 day ago UTC"
MAX_RETRIES = 3
RETRY_DELAY = 10
RATE_LIMIT_DELAY = 0.5
REQUEST_WEIGHT_LIMIT = 1100

shutdown_requested = False


def _handle_signal(signum, frame):
    global shutdown_requested
    shutdown_requested = True
    logger.info("Sinal de encerramento recebido. Finalizando pipeline com segurança...")


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


def criar_client() -> Client:
    try:
        client = Client()
        client.ping()
        logger.info("Conexão com Binance API estabelecida com sucesso.")
        return client
    except Exception as e:
        logger.error(f"Falha ao conectar com Binance API: {e}")
        raise


def ultimo_timestamp(par: str) -> datetime | None:
    csv_path = DADOS_DIR / f"{par}.csv"
    if not csv_path.exists():
        return None
    try:
        df = pd.read_csv(csv_path)
        if df.empty:
            return None
        last_ts = pd.to_datetime(df["timestamp"].iloc[-1])
        if last_ts.tzinfo is None:
            last_ts = last_ts.replace(tzinfo=timezone.utc)
        return last_ts
    except Exception as e:
        logger.warning(f"Erro ao ler CSV existente para {par}: {e}")
        return None


def coletar_klines(
    client: Client,
    par: str,
    intervalo: str,
    start_str: str | None = None,
) -> pd.DataFrame:
    klines = client.get_historical_klines(
        par,
        intervalo,
        start_str or "1 day ago UTC",
    )
    if not klines:
        logger.warning(f"Nenhum kline retornado para {par}.")
        return pd.DataFrame()

    df = pd.DataFrame(klines, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base", "taker_buy_quote", "ignore",
    ])
    df = df[["timestamp", "open", "high", "low", "close", "volume"]]
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df[["open", "high", "low", "close", "volume"]] = (
        df[["open", "high", "low", "close", "volume"]].astype(float)
    )
    return df


def salvar_dados(par: str, df_novo: pd.DataFrame, incremental: bool = True):
    csv_path = DADOS_DIR / f"{par}.csv"

    if incremental and csv_path.exists():
        df_existente = pd.read_csv(csv_path)
        df_existente["timestamp"] = pd.to_datetime(df_existente["timestamp"])
        df_novo["timestamp"] = pd.to_datetime(df_novo["timestamp"])

        ultimo = df_existente["timestamp"].max()
        df_filtrado = df_novo[df_novo["timestamp"] > ultimo]

        if df_filtrado.empty:
            logger.info(f"{par}: Nenhum dado novo para adicionar.")
            return 0

        df_combinado = pd.concat([df_existente, df_filtrado], ignore_index=True)
        df_combinado.drop_duplicates(subset=["timestamp"], keep="last", inplace=True)
        df_combinado.sort_values("timestamp", inplace=True)
        df_combinado.to_csv(csv_path, index=False)
        adicionados = len(df_filtrado)
        logger.info(f"{par}: +{adicionados} candles adicionados (total: {len(df_combinado)}).")
        return adicionados

    df_novo.sort_values("timestamp", inplace=True)
    df_novo.to_csv(csv_path, index=False)
    logger.info(f"{par}: {len(df_novo)} candles salvos em {csv_path.name}.")
    return len(df_novo)


def processar_par(
    client: Client,
    par: str,
    intervalo: str,
    periodo: str,
    incremental: bool = True,
) -> int:
    for attempt in range(1, MAX_RETRIES + 1):
        if shutdown_requested:
            return 0
        try:
            start_str = None
            if incremental:
                ultimo = ultimo_timestamp(par)
                if ultimo is not None:
                    start_str = ultimo.strftime("%Y-%m-%d %H:%M:%S")
                    logger.info(f"{par}: Atualização incremental desde {start_str}.")
                else:
                    start_str = periodo
                    logger.info(f"{par}: Nenhum CSV encontrado. Baixando período completo: {periodo}.")
            else:
                start_str = periodo
                logger.info(f"{par}: Coleta completa: {periodo}.")

            df = coletar_klines(client, par, intervalo, start_str)
            if df.empty:
                return 0

            salvos = salvar_dados(par, df, incremental=incremental)
            time.sleep(RATE_LIMIT_DELAY)
            return salvos

        except BinanceAPIException as e:
            logger.warning(f"{par}: Binance API error (tentativa {attempt}/{MAX_RETRIES}): {e}")
            if e.code == -1015 or "rate limit" in str(e).lower():
                wait = RETRY_DELAY * attempt * 2
                logger.info(f"Rate limit atingido. Aguardando {wait}s...")
                time.sleep(wait)
            else:
                time.sleep(RETRY_DELAY)
        except Exception as e:
            logger.error(f"{par}: Erro inesperado (tentativa {attempt}/{MAX_RETRIES}): {e}")
            time.sleep(RETRY_DELAY)

    logger.error(f"{par}: Falha após {MAX_RETRIES} tentativas.")
    return 0


def executar_pipeline(
    pares: list[str] | None = None,
    intervalo: str = INTERVALO_PADRAO,
    periodo: str = PERIODO_PADRAO,
    incremental: bool = True,
):
    pares = pares or PARES_PADRAO
    logger.info("=" * 60)
    logger.info("PIPELINE BINANCE - INÍCIO")
    logger.info(f"Pares: {pares}")
    logger.info(f"Intervalo: {intervalo}")
    logger.info(f"Modo: {'Incremental' if incremental else 'Completo'}")
    logger.info("=" * 60)

    try:
        client = criar_client()
    except Exception:
        return

    resultados = {}
    inicio = time.time()

    for i, par in enumerate(pares, 1):
        if shutdown_requested:
            logger.info("Encerramento solicitado. Parando pipeline.")
            break
        logger.info(f"\n--- [{i}/{len(pares)}] Processando {par} ---")
        salvos = processar_par(client, par, intervalo, periodo, incremental)
        resultados[par] = salvos

    duracao = time.time() - inicio

    logger.info("\n" + "=" * 60)
    logger.info("PIPELINE BINANCE - RESUMO")
    logger.info("=" * 60)
    total = 0
    for par, salvos in resultados.items():
        status = "OK" if salvos >= 0 else "FALHA"
        logger.info(f"  {par}: {salvos} candles ({status})")
        total += max(salvos, 0)
    logger.info(f"  Total: {total} candles processados")
    logger.info(f"  Duração: {duracao:.1f}s")
    logger.info("=" * 60)


def modo_agendado(
    pares: list[str] | None = None,
    intervalo: str = INTERVALO_PADRAO,
    periodo: str = PERIODO_PADRAO,
    intervalo_minutos: int = 30,
):
    logger.info(f"Modo agendado: coleta a cada {intervalo_minutos} minutos.")
    logger.info("Pressione Ctrl+C para encerrar.")

    while not shutdown_requested:
        executar_pipeline(pares, intervalo, periodo, incremental=True)

        if shutdown_requested:
            break

        logger.info(f"\nPróxima execução em {intervalo_minutos} minutos...")
        for _ in range(intervalo_minutos * 60):
            if shutdown_requested:
                break
            time.sleep(1)

    logger.info("Pipeline agendada encerrada.")


def main():
    parser = argparse.ArgumentParser(description="Pipeline de coleta de dados Binance")
    parser.add_argument(
        "--pares", nargs="+", default=None,
        help="Lista de pares (ex: BTCUSDT ETHUSDT). Padrão: lista expandida."
    )
    parser.add_argument(
        "--intervalo", default=INTERVALO_PADRAO,
        help=f"Intervalo de candles. Padrão: {INTERVALO_PADRAO}"
    )
    parser.add_argument(
        "--periodo", default=PERIODO_PADRAO,
        help='Período histórico. Padrão: "30 day ago UTC"'
    )
    parser.add_argument(
        "--completo", action="store_true",
        help="Forçar coleta completa (ignora dados existentes)."
    )
    parser.add_argument(
        "--agendado", action="store_true",
        help="Executar em modo contínuo com agendamento."
    )
    parser.add_argument(
        "--intervalo-agendado", type=int, default=30,
        help="Minutos entre execuções no modo agendado. Padrão: 30"
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Ativar logging de debug."
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    pares = args.pares or PARES_PADRAO
    incremental = not args.completo

    if args.agendado:
        modo_agendado(pares, args.intervalo, args.periodo, args.intervalo_agendado)
    else:
        executar_pipeline(pares, args.intervalo, args.periodo, incremental)


if __name__ == "__main__":
    main()
