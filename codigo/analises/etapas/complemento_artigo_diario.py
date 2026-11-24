"""Gera a tabela semestral e a figura do limiar a partir da publicação auditada."""
import csv
from collections import defaultdict
from statistics import median

import matplotlib.pyplot as plt

from infraestrutura.artefatos import RAIZ, ler_json, sha256


def tabela_semestres(previsoes, destino):
    por_chave = {(linha["bloco"], linha["unidade"]): linha for linha in previsoes}
    periodos = ("jan--jun/2024", "jul--dez/2024", "jan--jun/2025", "jul--dez/2025")
    unidades = [f"{modelo}_{tipo}" for tipo in ("media_seeds", "ensemble")
                for modelo in ("A", "L", "LSTM")] + ["naive"]
    linhas = [
        r"\begin{tabular}{llrrrrrrr}", r"\toprule",
        r"& & \multicolumn{3}{c}{MSE individual médio} & \multicolumn{3}{c}{MSE do ensemble} & Referência \\",
        r"\cmidrule(lr){3-5}\cmidrule(lr){6-8}",
        r"Semestre de teste & Origens & A & L & LSTM & A & L & LSTM & Naive \\", r"\midrule",
    ]
    for indice, periodo in enumerate(periodos, 1):
        bloco = f"B{indice}"
        origens = int(float(por_chave[bloco, "naive"]["n"]))
        valores = [float(por_chave[bloco, unidade]["mse_retorno"]) * 1e4 for unidade in unidades]
        campos = [f"{bloco} ({periodo})", str(origens)] + [f"{v:.4f}".replace(".", ",") for v in valores]
        linhas.append(" & ".join(campos) + r" \\")
    destino.write_text("\n".join(linhas + [r"\bottomrule", r"\end{tabular}", ""]), encoding="utf-8")


def figura_limiar(carteiras, destino):
    retornos = defaultdict(dict)
    for linha in carteiras:
        if linha["custo"] == "1":
            caso = (linha["populacao"], linha["moeda"], linha["variante"])
            retornos[caso][float(linha["filtro"])] = float(linha["retorno_liquido"])

    grupos = ("fixa_2025", "fixa_2026", "semestral")
    rotulos = ("Fixa 2025", "Fixa 2026", "BTC semestral")
    figura, eixos = plt.subplots(1, 2, sharey=True, sharex=True, figsize=(4.1, 2.1))
    for eixo, filtro, titulo in zip(eixos, (0.0015, 0.0025), ("Limiar de 0,15%", "Limiar de 0,25%")):
        eixo.axvline(0, color="0.45", linewidth=0.9, linestyle="--", zorder=1)
        for posicao, grupo in enumerate(grupos):
            diferencas = [100 * (v[filtro] - v[0.002]) for (populacao, _, _), v in retornos.items()
                          if (populacao if populacao.startswith("fixa_") else "semestral") == grupo]
            assert len(diferencas) == 12
            eixo.plot([min(diferencas), max(diferencas)], [posicao] * 2, color="#386785",
                      marker="|", markersize=9, linewidth=2)
            eixo.scatter(median(diferencas), posicao, marker="D", s=27, color="#172e41", zorder=3)
        eixo.set_title(titulo, fontsize=10)
        eixo.set_xticks([-40, 0, 40])
        eixo.set_xlim(-44, 72)
        eixo.set_ylim(2.5, -0.5)
        eixo.tick_params(labelsize=8, length=0, pad=4)
        eixo.spines[["top", "left", "right"]].set_visible(False)
    eixos[0].set_yticks(range(3), rotulos)
    figura.supxlabel("Mudança de retorno (pontos percentuais)", fontsize=9, y=0.04)
    figura.subplots_adjust(left=0.25, right=0.99, bottom=0.27, top=0.84, wspace=0.2)
    figura.savefig(destino, metadata={"CreationDate": None, "ModDate": None})
    plt.close(figura)


def main():
    registro = RAIZ / "registros/complemento_diario"
    assert ler_json(registro / "fechamento.json")["situacao"] == "concluido_auditado"
    versao = ler_json(registro / "sintese_complemento/versao_final.json")
    fechamento = RAIZ / versao["fechamento"]["arquivo"]
    assert sha256(fechamento) == versao["fechamento"]["sha256"]
    hashes = ler_json(fechamento)["arquivos"]
    latex = RAIZ / "escrita_tcc/latex"
    for nome, gerar, destino in [
        ("lstm_walkforward_previsoes", tabela_semestres, latex / "tabelas/reestimacao_btc.tex"),
        ("sensibilidade_carteiras", figura_limiar, latex / "figs/limiar_artigo.pdf"),
    ]:
        relativo = f"publicacao/{nome}.csv"
        caminho = fechamento.parent / relativo
        assert sha256(caminho) == hashes[relativo]
        with caminho.open(encoding="utf-8", newline="") as arquivo:
            gerar(csv.DictReader(arquivo), destino)


if __name__ == "__main__":
    main()
