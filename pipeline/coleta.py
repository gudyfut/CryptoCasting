from pathlib import Path

import pandas as pd

from pipeline import config


def carregar_bruto(par: str) -> pd.DataFrame | None:
    path = config.DADOS_DIR / "brutos" / f"{par}.parquet"
    if not path.exists():
        return None
    return pd.read_parquet(path)


def salvar_bruto(par: str, df: pd.DataFrame) -> Path:
    path = config.DADOS_DIR / "brutos" / f"{par}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return path


def ultimo_timestamp(par: str) -> pd.Timestamp | None:
    df = carregar_bruto(par)
    if df is None or df.empty:
        return None
    return pd.to_datetime(df["timestamp"].iloc[-1])


def coletar_par(client, par: str, intervalo: str, periodo: str, incremental: bool = True) -> pd.DataFrame:
    from binance.exceptions import BinanceAPIException
    import time
    import logging

    logger = logging.getLogger(__name__)

    start_str = None
    if incremental:
        ultimo = ultimo_timestamp(par)
        if ultimo is not None:
            start_str = ultimo.strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"{par}: incremental desde {start_str}")
        else:
            start_str = periodo
            logger.info(f"{par}: coleta completa ({periodo})")
    else:
        start_str = periodo
        logger.info(f"{par}: coleta forçada ({periodo})")

    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            klines = client.get_historical_klines(par, intervalo, start_str)
            break
        except BinanceAPIException as e:
            logger.warning(f"{par}: API error tentativa {attempt}/{config.MAX_RETRIES}: {e}")
            if "rate limit" in str(e).lower():
                wait = config.RETRY_DELAY_SEGUNDOS * attempt * 2
                logger.info(f"Aguardando {wait}s...")
                time.sleep(wait)
            else:
                time.sleep(config.RETRY_DELAY_SEGUNDOS)
        except Exception as e:
            logger.error(f"{par}: erro tentativa {attempt}/{config.MAX_RETRIES}: {e}")
            time.sleep(config.RETRY_DELAY_SEGUNDOS)
    else:
        logger.error(f"{par}: falha após {config.MAX_RETRIES} tentativas")
        return pd.DataFrame()

    if not klines:
        logger.warning(f"{par}: nenhum kline retornado")
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


def mesclar_incremental(par: str, df_novo: pd.DataFrame) -> pd.DataFrame:
    df_existente = carregar_bruto(par)

    if df_existente is not None and not df_existente.empty:
        df_existente["timestamp"] = pd.to_datetime(df_existente["timestamp"])
        df_novo["timestamp"] = pd.to_datetime(df_novo["timestamp"])

        ultimo = df_existente["timestamp"].max()
        df_filtrado = df_novo[df_novo["timestamp"] > ultimo]

        if df_filtrado.empty:
            return df_existente

        df_combinado = pd.concat([df_existente, df_filtrado], ignore_index=True)
        df_combinado.drop_duplicates(subset=["timestamp"], keep="last", inplace=True)
        df_combinado.sort_values("timestamp", inplace=True)
        df_combinado.reset_index(drop=True, inplace=True)
        return df_combinado

    df_novo.sort_values("timestamp", inplace=True)
    df_novo.reset_index(drop=True, inplace=True)
    return df_novo


def executar_coleta(
    pares: list[str] | None = None,
    intervalo: str | None = None,
    periodo: str | None = None,
    incremental: bool = True,
) -> dict[str, int]:
    from binance import Client
    import logging
    import time

    logger = logging.getLogger(__name__)

    pares = pares or config.PARES
    intervalo = intervalo or config.INTERVALO_CANDLES
    periodo = periodo or config.PERIODO_HISTORICO

    logger.info("=" * 60)
    logger.info("ETAPA 1 — COLETA DE DADOS")
    logger.info(f"Pares: {pares}")
    logger.info(f"Intervalo: {intervalo}")
    logger.info("=" * 60)

    client = Client()
    client.ping()
    logger.info("Conexão Binance OK")

    resultados = {}
    for i, par in enumerate(pares, 1):
        logger.info(f"[{i}/{len(pares)}] {par}")
        df = coletar_par(client, par, intervalo, periodo, incremental)
        if df.empty:
            resultados[par] = 0
            continue

        if incremental:
            df_final = mesclar_incremental(par, df)
        else:
            df_final = df.sort_values("timestamp").reset_index(drop=True)
        path = salvar_bruto(par, df_final)
        logger.info(f"{par}: {len(df_final)} registros salvos em {path.name}")
        resultados[par] = len(df_final)
        time.sleep(config.RATE_LIMIT_DELAY_SEGUNDOS)

    logger.info(f"Coleta finalizada: {resultados}")
    return resultados
