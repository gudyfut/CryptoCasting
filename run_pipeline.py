from pipeline import config
from pipeline.coleta import executar_coleta
from pipeline.limpeza import executar_limpeza
from pipeline.features import executar_feature_engineering
from pipeline.normalizacao import executar_normalizacao
from pipeline.janelas import executar_janelas
import logging
import argparse
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def executar_pipeline_completa(
    pares: list[str] | None = None,
    intervalo: str | None = None,
    periodo: str | None = None,
    tamanho_janela: int | None = None,
    metodo_normalizacao: str | None = None,
    incremental: bool = True,
    saltar_coleta: bool = False,
) -> dict:
    pares = pares or config.PARES
    intervalo = intervalo or config.INTERVALO_CANDLES
    periodo = periodo or config.PERIODO_HISTORICO
    tamanho_janela = tamanho_janela or config.TAMANHO_JANELA
    metodo_normalizacao = metodo_normalizacao or config.NORMALIZADOR

    resultados = {}

    if not saltar_coleta:
        logger.info("\n" + "#" * 60)
        logger.info("# PIPELINE COMPLETA — CRYPTOCASHING")
        logger.info("#" * 60)
        coleta_result = executar_coleta(pares, intervalo, periodo, incremental)
        resultados["coleta"] = coleta_result
    else:
        logger.info("Coleta ignorada (modo --sem-coleta)")

    for par in pares:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Processando pipeline para {par}")
        logger.info(f"{'=' * 60}")

        df_limpo = executar_limpeza(par)
        if df_limpo.empty:
            logger.error(f"{par}: limpeza falhou, pulando")
            resultados[par] = "falha_limpeza"
            continue

        df_features = executar_feature_engineering(par)
        if df_features.empty:
            logger.error(f"{par}: feature engineering falhou, pulando")
            resultados[par] = "falha_features"
            continue

        df_norm, scaler = executar_normalizacao(par, metodo_normalizacao)
        if df_norm.empty:
            logger.error(f"{par}: normalização falhou, pulando")
            resultados[par] = "falha_normalizacao"
            continue

        datasets = executar_janelas(par, tamanho_janela)
        if datasets is None:
            logger.error(f"{par}: janelas falharam")
            resultados[par] = "falha_janelas"
            continue

        resultados[par] = {
            "treino": len(datasets["train"]),
            "validacao": len(datasets["val"]),
            "teste": len(datasets["test"]),
        }

    logger.info("\n" + "#" * 60)
    logger.info("# RESUMO FINAL")
    logger.info("#" * 60)
    for par, res in resultados.items():
        if isinstance(res, dict) and "treino" in res:
            logger.info(f"  {par}: treino={res['treino']}, val={res['validacao']}, teste={res['teste']}")
        else:
            logger.info(f"  {par}: {res}")

    return resultados


def main():
    parser = argparse.ArgumentParser(description="Pipeline CryptoCasting")
    parser.add_argument("--pares", nargs="+", default=None)
    parser.add_argument("--intervalo", default=None)
    parser.add_argument("--periodo", default=None)
    parser.add_argument("--janela", type=int, default=None)
    parser.add_argument("--normalizacao", choices=["standard", "minmax"], default=None)
    parser.add_argument("--completo", action="store_true", help="Forçar coleta completa")
    parser.add_argument("--sem-coleta", action="store_true", help="Pular etapa de coleta")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    executar_pipeline_completa(
        pares=args.pares,
        intervalo=args.intervalo,
        periodo=args.periodo,
        tamanho_janela=args.janela,
        metodo_normalizacao=args.normalizacao,
        incremental=not args.completo,
        saltar_coleta=args.sem_coleta,
    )


if __name__ == "__main__":
    main()
