import argparse
import logging
import sys

from modelo import config
from modelo.avaliacao import avaliar, avaliar_seletivo, avaliar_trade, avaliar_regime, salvar_metricas
from modelo.baseline import baseline_ingenuo
from modelo.dataset import criar_dataloader
from modelo.mamba_modelo import carregar_modelo
from modelo.previsao import gerar_previsoes
from modelo.treino import treinar
from modelo.walkforward import walk_forward
from pipeline import config as pipe_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("treino.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def _log_trade(par: str, trade: dict):
    """Loga tabela de expectancy (R) por nível de RR + trades de exemplo."""
    logger.info(f"\n{'=' * 60}\nTrade expectancy {par}\n{'=' * 60}")
    logger.info(f"{'RR':>5} {'n':>7} {'win_rate':>10} {'exp_R':>10} {'soma_R':>10}")
    for chave, t in trade.items():
        if not chave.startswith("rr_"):
            continue
        n = t["n_trades"]
        wr = "-" if t["win_rate"] is None else f"{t['win_rate']:.4f}"
        ex = "-" if t["expectancy_r"] is None else f"{t['expectancy_r']:+.4f}"
        sr = "-" if t["soma_r"] is None else f"{t['soma_r']:+.1f}"
        logger.info(f"{t['rr']:>5.1f} {n:>7} {wr:>10} {ex:>10} {sr:>10}")
        if "debug" in t:
            logger.info("  Amostras de exemplo:")
            for d in t["debug"]:
                logger.info(
                    f"    {d['direcao']:>5} entry={d['entry']} "
                    f"tp={d['tp']} sl={d['sl']} atr={d['atr']} "
                    f"conf={d['conf']} → R={d['r']:+.3f}"
                )


def _log_regime(par: str, regime: list[dict]):
    """Loga acuracia + expectancy por regime de volatilidade."""
    logger.info(f"\n{'=' * 60}\nAvaliacao por regime — {par}\n{'=' * 60}")
    logger.info(f"{'regime':>8} {'faixa':<12} {'n':>7} {'acc':>7} {'exp@1':>8} {'exp@2':>8}")
    for r in regime:
        n = r["n"]
        if n == 0:
            logger.info(f"{r['regime']:>8} {r['faixa']:<12} {0:>7}")
            continue
        acc = f"{r['accuracy']:.4f}" if r["accuracy"] is not None else "-"
        e1 = r.get("expectancy_rr_1")
        e2 = r.get("expectancy_rr_2")
        e1s = f"{e1:+.4f}" if e1 is not None else "-"
        e2s = f"{e2:+.4f}" if e2 is not None else "-"
        logger.info(f"{r['regime']:>8} {r['faixa']:<12} {n:>7} {acc:>7} {e1s:>8} {e2s:>8}")


def main():
    parser = argparse.ArgumentParser(description="Treino Mamba — CryptoCasting")
    parser.add_argument(
        "--pares", nargs="+", default=[config.PAR_PRINCIPAL]
    )
    parser.add_argument("--nome", default="mamba",
                        help="Nome do modelo (define os arquivos de saída: {par}_{nome}.pt, etc)")
    parser.add_argument("--epochs", type=int, default=config.EPOCHS)
    parser.add_argument("--lr", type=float, default=config.LEARNING_RATE)
    parser.add_argument("--batch-size", type=int, default=config.BATCH_SIZE)
    parser.add_argument("--d-model", type=int, default=None, help="Override D_MODEL")
    parser.add_argument("--n-layers", type=int, default=None, help="Override N_LAYERS")
    parser.add_argument("--dropout", type=float, default=None, help="Override DROPOUT")
    parser.add_argument("--weight-decay", type=float, default=None, help="Override WEIGHT_DECAY")
    parser.add_argument(
        "--sem-walkforward",
        action="store_true",
        help="Pular a validação walk-forward",
    )
    parser.add_argument(
        "--seletivo",
        action="store_true",
        help="Apenas avaliação seletiva por confiança (carrega checkpoint, sem retreino)",
    )
    args = parser.parse_args()

    if args.d_model is not None:
        config.D_MODEL = args.d_model
    if args.n_layers is not None:
        config.N_LAYERS = args.n_layers
    if args.dropout is not None:
        config.DROPOUT = args.dropout
    if args.weight_decay is not None:
        config.WEIGHT_DECAY = args.weight_decay

    logger.info("#" * 60)
    logger.info(f"# TREINO MAMBA — device: {config.DEVICE} | modelo: '{args.nome}'")
    logger.info("#" * 60)
    logger.info(
        f"Config: D_MODEL={config.D_MODEL}, N_LAYERS={config.N_LAYERS}, "
        f"DROPOUT={config.DROPOUT}, WD={config.WEIGHT_DECAY}, "
        f"LR={args.lr}, BATCH={args.batch_size}, EPOCHS={args.epochs}"
    )
    logger.info(
        f"Dados: k={pipe_config.REGIME_K}, horizonte={pipe_config.HORIZONTE}, "
        f"janela={pipe_config.TAMANHO_JANELA}"
    )

    if args.seletivo:
        for par in args.pares:
            ckpt = config.RESULTADOS_DIR / f"{par}_{args.nome}.pt"
            if not ckpt.exists():
                logger.error(f"Checkpoint não encontrado: {ckpt} — treine primeiro.")
                continue
            modelo = carregar_modelo(par, args.nome)
            test_loader = criar_dataloader(par, "test", batch_size=args.batch_size, apenas_direcionais=True)
            seletivo = avaliar_seletivo(modelo, test_loader)
            trade = avaliar_trade(par, modelo, n_amostras_debug=5)
            regime = avaliar_regime(par, modelo)

            logger.info(f"\n{'=' * 60}\nAvaliação seletiva {par}\n{'=' * 60}")
            logger.info(f"{'limiar':>7} {'cobertura':>10} {'accuracy':>10} {'f1':>8} {'n':>7}")
            for s in seletivo:
                acc = "-" if s["accuracy"] is None else f"{s['accuracy']:.4f}"
                f1 = "-" if s["f1"] is None else f"{s['f1']:.4f}"
                logger.info(f"{s['limiar']:>7.2f} {s['cobertura']:>10.3f} {acc:>10} {f1:>8} {s['n_amostras']:>7}")

            _log_trade(par, trade)
            _log_regime(par, regime)
        logger.info("\nAvaliação seletiva finalizada.")
        return

    for par in args.pares:
        logger.info(f"\n{'=' * 60}\nProcessando {par}\n{'=' * 60}")

        bl = baseline_ingenuo(par)
        logger.info(f"Baseline {par}: {bl}")

        modelo, hist = treinar(
            par,
            nome=args.nome,
            epochs=args.epochs,
            learning_rate=args.lr,
            batch_size=args.batch_size,
        )

        test_loader = criar_dataloader(par, "test", batch_size=args.batch_size, apenas_direcionais=True)
        metricas = avaliar(modelo, test_loader)
        metricas["baseline"] = bl
        metricas["historico"] = hist
        metricas["seletivo"] = avaliar_seletivo(modelo, test_loader)
        metricas["trade"] = avaliar_trade(par, modelo, n_amostras_debug=5)
        metricas["config"] = {
            "modelo": {
                "D_MODEL": config.D_MODEL,
                "N_LAYERS": config.N_LAYERS,
                "DROPOUT": config.DROPOUT,
                "WEIGHT_DECAY": config.WEIGHT_DECAY,
                "LEARNING_RATE": args.lr,
                "BATCH_SIZE": args.batch_size,
                "EPOCHS": args.epochs,
                "D_INPUT": config.D_INPUT,
                "SEED": config.SEED,
            },
            "dados": {
                "TAMANHO_JANELA": pipe_config.TAMANHO_JANELA,
                "HORIZONTE": pipe_config.HORIZONTE,
                "REGIME_K": pipe_config.REGIME_K,
                "NORMALIZADOR": pipe_config.NORMALIZADOR,
            },
        }

        _log_trade(par, metricas["trade"])

        metricas["regime"] = avaliar_regime(par, modelo)
        _log_regime(par, metricas["regime"])

        if not args.sem_walkforward:
            metricas["walk_forward"] = walk_forward(par, args.nome)

        salvar_metricas(par, metricas, args.nome)

        gerar_previsoes(par, args.nome)

        resumo = {k: v for k, v in metricas.items() if k != "historico"}
        logger.info(f"Mamba {par} (teste): {resumo}")

    logger.info("\nTreinamento finalizado.")


if __name__ == "__main__":
    main()
