"""Reconstrói lançamentos independentemente e aplica trade público ao Mamba16."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

PASTA=Path(__file__).resolve().parent
RAIZ=PASTA.parents[2]


def main():
    resultados=json.loads((PASTA/"custos_resultados.json").read_text())
    conferidos=0
    for chave, politicas in resultados["series"].items():
        df=pd.read_csv(PASTA/f"{chave}_insumos.csv")
        for politica, cenarios in politicas.items():
            for cenario, resumo in cenarios.items():
                ordens=json.loads((PASTA/f"ordens_{chave}_{politica}_{cenario}.json").read_text())
                caixa,btc,custos,slips,juros=100.,0.,0.,0.,0.
                # Juros apurados independentemente ao início de cada dia.
                taxa_juros={"short_juros_001dia":.0001,"short_juros_005dia":.0005}.get(cenario,0.)
                indice=0
                for o in ordens:
                    while indice<=o["indice"] and indice<len(df):
                        custo=max(-btc,0.)*df.preco_anterior.iloc[indice]*taxa_juros
                        caixa-=custo;juros+=custo;indice+=1
                    q,p,f=o["quantidade"],o["preco"],o["taxa"]
                    if o["lado"]=="compra":
                        if politica=="smart_w_short":
                            caixa-=q*p*(1+f);btc+=q
                        else:
                            caixa-=q*p;btc+=q*(1-f)
                    elif o["lado"]=="cobertura":
                        caixa-=q*p*(1+f);btc+=q
                    else:
                        caixa+=q*p*(1-f);btc-=q
                    np.testing.assert_allclose([caixa,btc],[o["caixa"],o["btc"]],rtol=1e-10,atol=1e-10)
                    custos+=q*p*f
                    meio=(df.abertura.iloc[o["indice"]] if cenario=="abertura_custos_filtros" else df.preco_anterior.iloc[o["indice"]]) if o["indice"]<len(df) else df.alvo.iloc[-1]
                    slips+=q*abs(p-meio)
                while indice<len(df):
                    custo=max(-btc,0.)*df.preco_anterior.iloc[indice]*taxa_juros
                    caixa-=custo;juros+=custo;indice+=1
                np.testing.assert_allclose([caixa+btc*df.alvo.iloc[-1],custos,slips,juros],
                    [resumo["saldo"],resumo["comissoes"],resumo["slippage"],resumo["juros"]],rtol=1e-10,atol=1e-10)
                conferidos+=1
    # Aplicação literal, somente long-only: mesmos checkpoints locais, sem treino/inferência.
    config=json.loads((RAIZ/"configuracoes/backtest_carteira_001.json").read_text())
    congelado=json.loads((RAIZ/"dados/experimentos/backtest_carteira_8ec8a66648313caa48e3/congelamento.json").read_text())["contrato"]
    spec=importlib.util.spec_from_file_location("trade_original",PASTA/"fontes_publicas/utils/trade.py")
    tr=importlib.util.module_from_spec(spec);spec.loader.exec_module(tr)
    nossos={};insumos={}
    for serie,pasta in config["series"].items():
        if not serie.startswith("estado16_"):
            continue
        arq=RAIZ/pasta/"previsoes_teste.parquet"
        h=hashlib.sha256(arq.read_bytes()).hexdigest()
        assert h==congelado["insumos"][arq.relative_to(RAIZ).as_posix()]
        insumos[arq.relative_to(RAIZ).as_posix()]=h
        d=pd.read_parquet(arq)
        q=d.loc[pd.DatetimeIndex(d.origem_utc).hour==0].reset_index(drop=True)
        assert len(q)==364
        dados=pd.DataFrame({"Timestamp":[int(t.timestamp()) for t in q.origem_utc]+[int(q.destino_utc.iloc[-1].timestamp())],
                            "Close":list(q.close)+[q.preco_destino.iloc[-1]]})
        ts=[int(t.timestamp()) for t in q.destino_utc]
        # Predição preço a partir do log-retorno; alvo só no assert/marcação terminal públicos.
        previsoes=q.close.to_numpy()*np.exp(q.previsao.to_numpy())
        nossos[serie]={}
        for pol in ("vanilla","smart","no_strategy"):
            saldo,curva=tr.trade(dados,"Timestamp",ts,q.preco_destino.to_numpy(),previsoes,balance=10000,mode=pol,risk=2)
            nossos[serie][pol]={"saldo":saldo,"retorno_pct":(saldo/10000-1)*100}
    medias={pol:float(np.mean([r[pol]["retorno_pct"] for r in nossos.values()])) for pol in ("vanilla","smart","no_strategy")}
    nossos={"seeds":nossos,"medias_retorno_pct":medias,"insumos":insumos,
            "limites":"Aplicação literal sem custos/latência/filtros; não substitui publicação369. Dados2025, não período do artigo."}
    (PASTA/"nossos_codigo_literal.json").write_text(json.dumps(nossos,indent=2),encoding="utf-8")
    print('Nossos, código literal:',json.dumps(medias))
    # Indicadores descritivos do sinal público; não seleção de modelo.
    diagnosticos={}
    for nome in ("cmamba_nv_test","cmamba_v_test"):
        d=pd.read_csv(PASTA/f"{nome}_insumos.csv")
        prev=d.previsao.to_numpy().astype(np.float32).astype(float)
        real=d.alvo.to_numpy();anterior=d.preco_anterior.to_numpy()
        modelo_mse=float(np.mean((prev-real)**2));naive_mse=float(np.mean((anterior-real)**2))
        diagnosticos[nome]={"rmse_naive":float(np.sqrt(naive_mse)),"habilidade_mse_pct":(1-modelo_mse/naive_mse)*100,
                           "direcao_pct":float(np.mean((prev>anterior)==(real>anterior))*100)}
    recibo={"situacao":"conferido","cenarios_lancamentos_reconstruidos":conferidos,
            "reproducao_ideal_compativel":True,"treinamentos":0,
            "diagnosticos":diagnosticos,"medias_nosso_literal":medias,
            "limites":["Custos assumidos, não taxas históricas de conta", "Sem livro de ofertas/execução real",
                       "Short sem simulação de colateral/liquidação; juros apenas sensibilidade",
                       "Dados diários não medem drawdown intradiário", "Uma seed pública por versão"]}
    (PASTA/"conferencia.json").write_text(json.dumps(recibo,indent=2),encoding="utf-8")
    arquivos={str(p.relative_to(PASTA)):hashlib.sha256(p.read_bytes()).hexdigest()
              for p in PASTA.rglob("*") if p.is_file() and "__pycache__" not in p.parts and not p.name.startswith("manifesto")}
    (PASTA/"manifesto_final.json").write_text(json.dumps(arquivos,indent=2),encoding="utf-8")
    print(json.dumps(recibo,indent=2))


if __name__=="__main__":
    main()
