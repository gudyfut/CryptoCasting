import argparse
import logging
import sys

from modelo import config
from modelo.avaliacao import avaliar, salvar_metricas
from modelo.baseline import baseline_ingenuo
from modelo.dataset import criar_dataloader
from modelo.treino import treinar
from modelo.walkforward import walk_forward

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("treino.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Treino Mamba — CryptoCasting")
    parser.add_argument(
        "--pares", nargs="+", default=[config.PAR_PRINCIPAL]
    )
    parser.add_argument("--epochs", type=int, default=config.EPOCHS)
    parser.add_argument("--lr", type=float, default=config.LEARNING_RATE)
    parser.add_argument("--batch-size", type=int, default=config.BATCH_SIZE)
    parser.add_argument(
        "--sem-walkforward",
        action="store_true",
        help="Pular a validação walk-forward",
    )
    args = parser.parse_args()

    logger.info("#" * 60)
    logger.info(f"# TREINO MAMBA — device: {config.DEVICE}")
    logger.info("#" * 60)

    for par in args.pares:
        logger.info(f"\n{'=' * 60}\nProcessando {par}\n{'=' * 60}")

        bl = baseline_ingenuo(par)
        logger.info(f"Baseline {par}: {bl}")

        modelo, hist = treinar(
            par,
            epochs=args.epochs,
            learning_rate=args.lr,
            batch_size=args.batch_size,
        )

        test_loader = criar_dataloader(par, "test", batch_size=args.batch_size)
        metricas = avaliar(modelo, test_loader)
        metricas["baseline"] = bl
        metricas["historico"] = hist

        if not args.sem_walkforward:
            metricas["walk_forward"] = walk_forward(par)

        salvar_metricas(par, metricas)

        resumo = {k: v for k, v in metricas.items() if k != "historico"}
        logger.info(f"Mamba {par} (teste): {resumo}")

    logger.info("\nTreinamento finalizado.")


if __name__ == "__main__":
    main()
