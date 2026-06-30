"""Orquestrador da análise de anomalias.

Uso:
    python -m analise.rodar                           # BTC, 2023+, threshold 3σ
    python -m analise.rodar --par ETHUSDT --threshold 2.5
    python -m analise.rodar --ano-inicio 2024 --contexto 48

Salva resultados em analise/resultados/ (JSON + PNG).
"""

import argparse
import json
import logging
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from analise import anomalias

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
logger = logging.getLogger(__name__)

RESULTADOS = Path(__file__).parent / "resultados"
RESULTADOS.mkdir(exist_ok=True)

FEATURES_TRAJETORIA = (
    "vol_zscore",
    "volume_zscore",
    "rsi_slope",
    "vwap_slope",
)


def main():
    parser = argparse.ArgumentParser(description="Análise de anomalias de preço")
    parser.add_argument("--par", default="BTCUSDT")
    parser.add_argument("--ano-inicio", type=int, default=2023)
    parser.add_argument("--threshold", type=float, default=3.0, help="Z-score minimo")
    parser.add_argument("--min-move", type=float, default=1.0,
                        help="Movimento minimo absoluto (%%) para qualificar como anomalia real")
    parser.add_argument("--vol-janela", type=int, default=168, help="Janela de vol rolling (candles)")
    parser.add_argument("--contexto", type=int, default=24, help="Candles de contexto antes do evento")
    parser.add_argument("--min-gap", type=int, default=3, help="Gap mínimo entre eventos")
    args = parser.parse_args()

    # === 1. Carregar dados ===
    logger.info(f"\n{'='*60}")
    logger.info(f"ANÁLISE DE ANOMALIAS — {args.par} ({args.ano_inicio}+)")
    logger.info(f"{'='*60}")

    df = anomalias.carregar_dados(args.par, ano_inicio=args.ano_inicio)
    logger.info(f"Período: {df.iloc[0]['timestamp']} → {df.iloc[-1]['timestamp']}")
    logger.info(f"Total candles: {len(df):,}")

    # === 2. Detectar anomalias ===
    df = anomalias.detectar(
        df, horizontes=(1, 2, 3), vol_janela=args.vol_janela, threshold=args.threshold
    )
    n_anom = int(df["anomalia"].sum())
    logger.info(f"\nThreshold: {args.threshold}σ | Vol janela: {args.vol_janela}h | Horizontes: 1H, 2H, 3H")
    logger.info(f"Candles anômalos: {n_anom} ({n_anom/len(df)*100:.1f}%)")

    eventos = anomalias.agrupar_eventos(df, min_gap=args.min_gap)
    logger.info(f"Eventos agrupados: {len(eventos)}")

    eventos_filtrados = [e for e in eventos if abs(e["move_pct"]) >= args.min_move]
    descartados = len(eventos) - len(eventos_filtrados)
    logger.info(f"Filtro min-move >= {args.min_move}%: {descartados} descartados, {len(eventos_filtrados)} restantes")
    eventos = eventos_filtrados

    if not eventos:
        logger.info("Nenhum evento apos filtro. Tente baixar --min-move.")
        return

    up = [e for e in eventos if e["direcao"] == "up"]
    down = [e for e in eventos if e["direcao"] == "down"]
    logger.info(f"  UP: {len(up)}  |  DOWN: {len(down)}")

    moves_up = [e["move_pct"] for e in up]
    moves_down = [e["move_pct"] for e in down]
    durations = [e["duration"] for e in eventos]

    logger.info(f"\nTamanho dos movimentos (move_pct):")
    if moves_up:
        logger.info(f"  UP   — mediana: +{np.median(moves_up):.2f}%, p90: +{np.percentile(moves_up, 90):.2f}%, máx: +{max(moves_up):.2f}%")
    if moves_down:
        logger.info(f"  DOWN — mediana: {np.median(moves_down):.2f}%, p90: {np.percentile(moves_down, 10):.2f}%, máx: {min(moves_down):.2f}%")

    logger.info(f"\nDuração dos eventos:")
    logger.info(f"  Mediana: {int(np.median(durations))} candle(s), p90: {int(np.percentile(durations, 90))}, máx: {max(durations)}")

    top5 = sorted(eventos, key=lambda e: e["z_peak"], reverse=True)[:5]
    logger.info(f"\nTop 5 maiores anomalias (por z_peak):")
    for e in top5:
        logger.info(f"  {e['onset']} | z={e['z_peak']:.1f} | {e['direcao']} | {e['move_pct']:+.2f}% | {e['duration']}c")

    # === 3. Salvar eventos em JSON ===
    with open(RESULTADOS / f"{args.par}_anomalias.json", "w", encoding="utf-8") as f:
        json.dump(eventos, f, indent=2, ensure_ascii=False)
    logger.info(f"\nEventos salvos em {RESULTADOS / f'{args.par}_anomalias.json'}")

    # === 4. Plotar preço com anomalias ===
    _plot_preco(df, eventos, args.par)

    # === 5. Plotar distribuição de z-scores ===
    _plot_distribuicao(df, args.par)

    # === 6. Comparar pré-anomalia vs normal ===
    logger.info(f"\n{'='*60}")
    logger.info(f"COMPARAÇÃO: {args.contexto} candles ANTES da anomalia vs NORMAL")
    logger.info(f"{'='*60}")

    janelas_anom, feat_cols = anomalias.extrair_janelas(df, eventos, contexto=args.contexto)
    janelas_norm, _ = anomalias.amostrar_normais(
        df, eventos, contexto=args.contexto, n=len(eventos)
    )

    if len(janelas_anom) == 0 or len(janelas_norm) == 0:
        logger.info("Dados insuficientes para comparação.")
        return

    logger.info(f"Janelas anomalia: {len(janelas_anom)} | Janelas normal: {len(janelas_norm)}")

    # === 7. Testes estatísticos (último candle antes da anomalia) ===
    logger.info(f"\nTeste Mann-Whitney U (último candle antes do onset):")
    logger.info(f"  {'feature':<20} {'anom (med)':>10} {'norm (med)':>10} {'p-valor':>10} {'signif':>8}")
    logger.info(f"  {'-'*20} {'-'*10} {'-'*10} {'-'*10} {'-'*8}")

    testes = []
    for i, feat in enumerate(feat_cols):
        anom_last = janelas_anom[:, -1, i]
        norm_last = janelas_norm[:, -1, i]

        anom_last = anom_last[~np.isnan(anom_last)]
        norm_last = norm_last[~np.isnan(norm_last)]
        if len(anom_last) < 5 or len(norm_last) < 5:
            continue

        u, p = stats.mannwhitneyu(anom_last, norm_last, alternative="two-sided")
        signif = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
        logger.info(f"  {feat:<20} {np.median(anom_last):>10.4f} {np.median(norm_last):>10.4f} {p:>10.4f} {signif:>8}")
        testes.append({"feature": feat, "p_valor": float(p), "med_anom": float(np.median(anom_last)), "med_norm": float(np.median(norm_last))})

    with open(RESULTADOS / f"{args.par}_testes.json", "w", encoding="utf-8") as f:
        json.dump(testes, f, indent=2, ensure_ascii=False)

    # === 8. Trajetórias dos features ===
    _plot_trajetorias(janelas_anom, janelas_norm, feat_cols, args.par, args.contexto)

    # === 9. Comparação DIRECIONAL: UP vs DOWN vs normal ===
    logger.info(f"\n{'='*60}")
    logger.info(f"COMPARAÇÃO DIRECIONAL: UP vs DOWN")
    logger.info(f"{'='*60}")

    up_events = [e for e in eventos if e["direcao"] == "up"]
    down_events = [e for e in eventos if e["direcao"] == "down"]

    jan_up, _ = anomalias.extrair_janelas(df, up_events, contexto=args.contexto)
    jan_down, _ = anomalias.extrair_janelas(df, down_events, contexto=args.contexto)

    if len(jan_up) >= 5 and len(jan_down) >= 5:
        logger.info(f"UP: {len(jan_up)} | DOWN: {len(jan_down)} | Normal: {len(janelas_norm)}")

        logger.info(f"\nMann-Whitney U (UP vs DOWN, último candle antes do onset):")
        logger.info(f"  {'feature':<20} {'UP_med':>10} {'DOWN_med':>10} {'delta':>8} {'p-valor':>10} {'sig':>5}")
        logger.info(f"  {'-'*20} {'-'*10} {'-'*10} {'-'*8} {'-'*10} {'-'*5}")

        for i, feat in enumerate(feat_cols):
            u_vals = jan_up[:, -1, i]
            d_vals = jan_down[:, -1, i]
            u_vals = u_vals[~np.isnan(u_vals)]
            d_vals = d_vals[~np.isnan(d_vals)]
            if len(u_vals) < 5 or len(d_vals) < 5:
                continue

            _, p = stats.mannwhitneyu(u_vals, d_vals, alternative="two-sided")
            sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
            med_u = np.median(u_vals)
            med_d = np.median(d_vals)
            logger.info(f"  {feat:<20} {med_u:>10.4f} {med_d:>10.4f} {med_u-med_d:>+8.4f} {p:>10.4f} {sig:>5}")

        _plot_trajetorias_direcionais(jan_up, jan_down, janelas_norm, feat_cols, args.par, args.contexto)
    else:
        logger.info(f"Dados insuficientes: UP={len(jan_up)}, DOWN={len(jan_down)}")

    logger.info(f"\nPlots salvos em {RESULTADOS}/")
    logger.info("Done.")


def _plot_preco(df, eventos, par):
    fig, ax = plt.subplots(figsize=(16, 5), facecolor="#0d1117")
    ax.set_facecolor("#0d1117")
    ax.plot(df["timestamp"], df["close"], color="#6e7681", linewidth=0.5, alpha=0.7)

    for e in eventos:
        idx = e["start_idx"]
        color = "#22c55e" if e["direcao"] == "up" else "#ef4444"
        ax.scatter(df.iloc[idx]["timestamp"], df.iloc[idx]["close"],
                   color=color, s=8, zorder=5, alpha=0.7)

    ax.set_title(f"{par} — anomalias (↑verde / ↓vermelho)", color="#c9d1d9", fontsize=12)
    ax.tick_params(colors="#6e7681")
    for spine in ax.spines.values():
        spine.set_color("#30363d")
    fig.tight_layout()
    fig.savefig(RESULTADOS / f"{par}_preco_anomalias.png", dpi=120)
    plt.close(fig)


def _plot_distribuicao(df, par):
    z = df["z_abs"].dropna()
    z = z[z > 0]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4), facecolor="#0d1117")
    for ax in (ax1, ax2):
        ax.set_facecolor("#0d1117")

    ax1.hist(z, bins=200, color="#58a6ff", alpha=0.7, edgecolor="none")
    ax1.axvline(3, color="#ef4444", linestyle="--", linewidth=1, label="3σ")
    ax1.set_title("Distribuição |z-score|", color="#c9d1d9")
    ax1.legend()

    z_neg = df.loc[df["anomalia"], "z_score"]
    ax2.hist(z_neg, bins=60, color="#f0883e", alpha=0.7, edgecolor="none")
    ax2.axvline(0, color="#6e7681", linewidth=0.5)
    ax2.set_title("Direção das anomalias", color="#c9d1d9")

    for ax in (ax1, ax2):
        ax.tick_params(colors="#6e7681")
        for spine in ax.spines.values():
            spine.set_color("#30363d")

    fig.tight_layout()
    fig.savefig(RESULTADOS / f"{par}_distribuicao_z.png", dpi=120)
    plt.close(fig)


def _plot_trajetorias(jan_anom, jan_norm, feat_cols, par, contexto):
    plot_feats = [f for f in FEATURES_TRAJETORIA if f in feat_cols]
    n = len(plot_feats)
    if n == 0:
        return

    fig, axes = plt.subplots(1, n, figsize=(5 * n, 4), facecolor="#0d1117")
    if n == 1:
        axes = [axes]

    x = np.arange(-contexto, 0)

    for ax, feat in zip(axes, plot_feats):
        ax.set_facecolor("#0d1117")
        idx = feat_cols.index(feat)

        a = jan_anom[:, :, idx]
        nr = jan_norm[:, :, idx]

        a_mean = np.nanmean(a, axis=0)
        a_std = np.nanstd(a, axis=0)
        nr_mean = np.nanmean(nr, axis=0)
        nr_std = np.nanstd(nr, axis=0)

        ax.plot(x, nr_mean, color="#6e7681", linewidth=1.5, label="Normal")
        ax.fill_between(x, nr_mean - nr_std, nr_mean + nr_std, color="#6e7681", alpha=0.15)

        ax.plot(x, a_mean, color="#f0883e", linewidth=1.5, label="Pré-anomalia")
        ax.fill_between(x, a_mean - a_std, a_mean + a_std, color="#f0883e", alpha=0.15)

        ax.set_title(feat, color="#c9d1d9", fontsize=11)
        ax.legend(fontsize=8, facecolor="#161b22", edgecolor="#30363d")
        ax.tick_params(colors="#6e7681")
        for spine in ax.spines.values():
            spine.set_color("#30363d")

    fig.suptitle(f"{par} — trajetória dos features antes da anomalia", color="#c9d1d9", fontsize=13)
    fig.tight_layout()
    fig.savefig(RESULTADOS / f"{par}_trajetorias.png", dpi=120)
    plt.close(fig)


def _plot_trajetorias_direcionais(jan_up, jan_down, jan_norm, feat_cols, par, contexto):
    plot_feats = [f for f in FEATURES_TRAJETORIA if f in feat_cols]
    n = len(plot_feats)
    if n == 0:
        return

    fig, axes = plt.subplots(1, n, figsize=(5 * n, 4), facecolor="#0d1117")
    if n == 1:
        axes = [axes]

    x = np.arange(-contexto, 0)

    for ax, feat in zip(axes, plot_feats):
        ax.set_facecolor("#0d1117")
        idx = feat_cols.index(feat)

        for data, color, label in [
            (jan_norm, "#6e7681", "Normal"),
            (jan_up, "#22c55e", "UP"),
            (jan_down, "#ef4444", "DOWN"),
        ]:
            d = data[:, :, idx]
            mean = np.nanmean(d, axis=0)
            std = np.nanstd(d, axis=0)
            ax.plot(x, mean, color=color, linewidth=1.5, label=label)
            ax.fill_between(x, mean - std, mean + std, color=color, alpha=0.1)

        ax.set_title(feat, color="#c9d1d9", fontsize=11)
        ax.legend(fontsize=8, facecolor="#161b22", edgecolor="#30363d")
        ax.tick_params(colors="#6e7681")
        for spine in ax.spines.values():
            spine.set_color("#30363d")

    fig.suptitle(f"{par} - UP vs DOWN vs Normal", color="#c9d1d9", fontsize=13)
    fig.tight_layout()
    fig.savefig(RESULTADOS / f"{par}_trajetorias_direcionais.png", dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    main()
