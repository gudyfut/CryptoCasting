"""Sensibilidades identificadas do backtest público. Não treina nem altera ciclos."""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

PASTA = Path(__file__).resolve().parent


def simular(df, politica, taxa=0., slippage=0., minimo=0., passo=0., abertura=False,
            juros_dia=0.):
    caixa, btc = 100., 0.
    ordens, recusas, comissoes, desvios, juros = [], 0, 0., 0., 0.
    curva = [100.]
    exposicoes, alavancagens = [], []
    for i, row in enumerate(df.itertuples(index=False)):
        # Restaurar float32 das previsões: o código público calcula diff nessa precisão.
        x, y = np.float64(row.preco_anterior), np.float32(row.previsao)
        execucao = row.abertura if abertura else x
        patrimonio = caixa + btc*x
        if btc < 0 and juros_dia:
            custo = -btc*x*juros_dia
            caixa -= custo
            juros += custo
        compra, venda = 0., 0.
        diff = y*2/100
        delta = (y-x)/diff
        if politica == "comprar_manter":
            compra = 1. if i == 0 else 0.
        elif politica == "vanilla":
            if abs(y/x-1) >= .01:
                compra, venda = (1., 0.) if y > x else (0., max(btc, 0.))
        elif politica == "smart":
            if delta > 0:
                compra = min(delta, 1.)
            else:
                venda = max(btc, 0.)*min(-delta, 1.)
        elif politica == "smart_w_short":
            # As quatro ramificações originais, com limite nominal de .002 BTC.
            if x < y:
                compra = min(delta, 1.)
            elif x < y+diff:
                venda = max(btc, 0.)*min(-delta, 1.)
            else:
                venda = btc+.002
        if compra > 0 and caixa > 0:
            preco = execucao*(1+slippage)
            if politica == "smart_w_short":
                # Comissão em caixa permite cobrir short sem inventar BTC recebido.
                quantidade = caixa*compra/(preco*(1+taxa))
                credito = quantidade
            else:
                quantidade = caixa*compra/preco
                credito = quantidade*(1-taxa)
            if passo:
                quantidade = math.floor(quantidade/passo)*passo
                credito = quantidade if politica == "smart_w_short" else quantidade*(1-taxa)
            notional = quantidade*preco
            if notional >= minimo and quantidade > 0:
                antes = caixa+btc*execucao
                caixa -= notional*(1+taxa) if politica == "smart_w_short" else notional
                btc += credito
                comissoes += notional*taxa
                desvios += quantidade*execucao*slippage
                ordens.append({"indice":i,"lado":"compra","quantidade":quantidade,
                               "preco":preco,"taxa":taxa,"caixa":caixa,"btc":btc})
                assert abs((caixa+btc*execucao)-antes+notional*taxa+(quantidade if politica == "smart_w_short" else credito)*execucao*slippage) < 1e-8
            else:
                recusas += 1
        elif venda > 0:
            quantidade = math.floor(venda/passo)*passo if passo else venda
            preco = execucao*(1-slippage)
            notional = quantidade*preco
            if notional >= minimo and quantidade > 0:
                caixa += notional*(1-taxa)
                btc -= quantidade
                comissoes += notional*taxa
                desvios += quantidade*execucao*slippage
                ordens.append({"indice":i,"lado":"venda","quantidade":quantidade,
                               "preco":preco,"taxa":taxa,"caixa":caixa,"btc":btc})
            else:
                recusas += 1
        if politica != "smart_w_short":
            assert caixa >= -1e-9 and btc >= -1e-12
        curva.extend([caixa+btc*execucao, caixa+btc*row.alvo])
        exposicoes.append(btc*x/patrimonio)
        alavancagens.append(abs(btc*x)/patrimonio)
    terminal = df.alvo.iloc[-1]
    if abs(btc) > 1e-14:
        quantidade = math.floor(abs(btc)/passo)*passo if passo else abs(btc)
        preco = terminal*(1-slippage if btc > 0 else 1+slippage)
        notional = quantidade*preco
        if notional >= minimo and quantidade > 0:
            lado = "venda" if btc > 0 else "cobertura"
            caixa += notional*(1-taxa) if btc > 0 else -notional*(1+taxa)
            btc += -quantidade if btc > 0 else quantidade
            comissoes += notional*taxa
            desvios += quantidade*terminal*slippage
            ordens.append({"indice":len(df),"lado":lado,"quantidade":quantidade,
                           "preco":preco,"taxa":taxa,"caixa":caixa,"btc":btc})
        else:
            recusas += 1
    saldo = caixa+btc*terminal
    curva.append(saldo)
    c = np.array(curva)
    return {"saldo":float(saldo),"retorno_pct":float(saldo-100),
            "mdd_diario_terminal_pct":float(np.max(1-c/np.maximum.accumulate(c))*100),
            "ordens":len(ordens),"recusas":recusas,"comissoes":comissoes,"slippage":desvios,
            "juros":juros,"btc_residual":btc,"exposicao_media_assinada":float(np.mean(exposicoes)),
            "exposicao_absoluta_maxima":float(max(alavancagens)),"lancamentos":ordens}


def main():
    publico = json.loads((PASTA/"reproducao_publica.json").read_text())
    resultados = {"treinamentos":0,"hipoteses":{
        "saldo_inicial":100,"taxas_por_lado":True,"spread_slippage": "piora multiplicativa por lado",
        "juros": "cenários hipotéticos debitados em USD, sem margem/liquidação; não taxas históricas",
        "abertura": "open diário do candle alvo; sem livro/latência intradiária",
        "filtros": "mínimo5 USD e passo0.00001 BTC assumidos, não certificados"},"series":{}}
    cenarios = {"ideal":{}, "taxa_010":{"taxa":.001},
                "taxa_010_slip_005":{"taxa":.001,"slippage":.0005},
                "taxa_020_slip_010":{"taxa":.002,"slippage":.001},
                "abertura_custos_filtros":{"taxa":.001,"slippage":.0005,"minimo":5.,"passo":.00001,"abertura":True},
                "short_juros_001dia":{"taxa":.001,"slippage":.0005,"juros_dia":.0001},
                "short_juros_005dia":{"taxa":.001,"slippage":.0005,"juros_dia":.0005}}
    for nome in ("cmamba_nv", "cmamba_v"):
        for parte in ("val", "test"):
            df = pd.read_csv(PASTA/f"{nome}_{parte}_previsoes.csv")
            dados = pd.read_csv(PASTA/f"fontes_publicas/data/2018-09-17_2024-09-16_86400/{parte}.csv",index_col=0)
            df["abertura"] = [float(dados.loc[dados.Timestamp==int(t),"Open"].iloc[0]) for t in df.timestamp]
            df.to_csv(PASTA/f"{nome}_{parte}_insumos.csv",index=False)
            chave=f"{nome}_{parte}"
            resultados["series"][chave]={}
            for politica in ("vanilla","smart","smart_w_short","comprar_manter"):
                saidas={}
                for cenario, args in cenarios.items():
                    if cenario.startswith("short_") and politica != "smart_w_short":
                        continue
                    if cenario == "abertura_custos_filtros" and politica == "smart_w_short":
                        continue
                    r=simular(df,politica,**args)
                    lancamentos=r.pop("lancamentos")
                    (PASTA/f"ordens_{chave}_{politica}_{cenario}.json").write_text(json.dumps(lancamentos,indent=2),encoding="utf-8")
                    saidas[cenario]=r
                ref=publico["series"][chave]["politicas"]["no_strategy" if politica=="comprar_manter" else politica]["saldo"]
                assert abs(saidas["ideal"]["saldo"]-ref)<1e-8,(chave,politica,ref,saidas["ideal"])
                resultados["series"][chave][politica]=saidas
                if parte=="test":
                    print(chave,politica,json.dumps(saidas),flush=True)
    (PASTA/"custos_resultados.json").write_text(json.dumps(resultados,indent=2),encoding="utf-8")
    arquivos={str(p.relative_to(PASTA)):hashlib.sha256(p.read_bytes()).hexdigest()
              for p in PASTA.rglob("*") if p.is_file() and "__pycache__" not in p.parts and not p.name.startswith("manifesto")}
    (PASTA/"manifesto_final.json").write_text(json.dumps(arquivos,indent=2),encoding="utf-8")


if __name__=="__main__":
    main()
