"""Estatísticas descritivas e incerteza com dependência temporal explícita."""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr


def correlacao(x, y, postos=False):
    x, y = np.asarray(x), np.asarray(y)
    if len(x) < 3 or np.std(x) < 1e-15 or np.std(y) < 1e-15:
        return None
    return float(spearmanr(x, y).statistic if postos else np.corrcoef(x, y)[0, 1])


def direcao(previsto, real):
    p, y = np.sign(previsto), np.sign(real)
    ativo = (p != 0) & (y != 0)
    def taxa(mascara, evento):
        return float(np.mean(evento[mascara])) if mascara.any() else None
    ru = taxa(y > 0, p > 0); rd = taxa(y < 0, p < 0)
    return {"acuracia": taxa(ativo, p == y), "cobertura_direcao": float(ativo.mean()),
            "fracao_alta_real": float(np.mean(y > 0)), "fracao_previsao_alta": float(np.mean(p > 0)),
            "precisao_alta": taxa((p > 0) & (y != 0), y > 0),
            "precisao_queda": taxa((p < 0) & (y != 0), y < 0),
            "recall_alta": ru, "recall_queda": rd,
            "balanced_accuracy": (ru+rd)/2 if ru is not None and rd is not None else None,
            "n_alta_prevista": int((p > 0).sum()), "n_queda_prevista": int((p < 0).sum())}


def quintis_c(c, s, quantis):
    """Empates ficam no grupo inferior; arestas nunca dependem dos alvos de S."""
    limites = np.quantile(np.asarray(c), quantis)
    return np.searchsorted(limites, s, side="left")+1, limites


def resumo(g):
    n = len(g)
    if not n:
        return {"n": 0}
    ativo = g.score > 0
    certo = g.lado * g.retorno_terminal > 0
    ganho = g.payoff_escolhido > 0
    return {"n": n, "origens_distintas": int(g.origem_ms.nunique()), "dias": int(g.dia.nunique()),
            "celulas": int(g[["recorte", "seed"]].drop_duplicates().shape[0]),
            "seeds": int(g.seed.nunique()), "recortes": int(g.recorte.nunique()),
            "grupo_pequeno": n < 100 or g.dia.nunique() < 20,
            **direcao(g.lado.to_numpy(), g.retorno_terminal.to_numpy()),
            "direcao_saida_modelo": direcao(g.direcao_preco.to_numpy(), g.retorno_terminal.to_numpy()),
            "score_medio": float(g.score.mean()), "payoff_escolhido_medio": float(g.payoff_escolhido.mean()),
            "payoff_compra_medio": float(g.y_long.mean()), "payoff_venda_medio": float(g.y_short.mean()),
            "ganho_sobre_lado_treino": float((g.payoff_escolhido-g.payoff_lado_treino).mean()),
            "taxa_payoff_positivo": float(ganho.mean()), "fracao_score_positivo": float(ativo.mean()),
            "acerto_terminal_mas_perda": float((certo & ~ganho).sum()/certo.sum()) if certo.any() else None,
            "mse": float(g.erro2.mean()), "mse_zero": float(g.erro2_zero.mean()),
            "mse_media_treino": float(g.erro2_media.mean()), "mae": float(g.erro_abs.mean()),
            "correlacao_score_payoff": correlacao(g.score, g.payoff_escolhido),
            "spearman_score_payoff": correlacao(g.score, g.payoff_escolhido, True)}


def estatistica_canal(p, y):
    sd = float(np.std(p)); sy = float(np.std(y))
    slope = float(np.cov(p, y, ddof=0)[0, 1]/sd**2) if sd > 1e-15 else None
    return {"media_prevista": float(np.mean(p)), "media_real": float(np.mean(y)),
            "std_prevista": sd, "std_real": sy, "razao_std": sd/sy if sy else None,
            "vies": float(np.mean(p-y)), "mae": float(np.mean(abs(p-y))),
            "mse": float(np.mean((p-y)**2)), "correlacao": correlacao(p,y),
            "spearman": correlacao(p,y,True), "slope_calibracao_descritivo": slope,
            "intercepto_calibracao_descritivo": float(np.mean(y)-slope*np.mean(p)) if slope is not None else None,
            "quantis_previstos": np.quantile(p,[0,.01,.1,.5,.9,.99,1]).tolist(),
            "quantis_reais": np.quantile(y,[0,.01,.1,.5,.9,.99,1]).tolist()}


def indices_blocos(n, tamanho, rng):
    """Moving blocks não circulares; preserva a ordem dentro de cada bloco."""
    tamanho = min(tamanho,n)
    inicios = rng.integers(0,n-tamanho+1,size=int(np.ceil(n/tamanho)))
    return (inicios[:,None]+np.arange(tamanho)).ravel()[:n]


def bootstrap(g, config):
    """Razões agrupadas; mesmas datas para todas as seeds, mesmas seeds nos folds.

    Pontos e IC usam ponderação por origem/seed (não média igual das células).
    Folds são estratos fixos, não uma amostra de novos regimes de mercado.
    """
    g = g.copy(); ativo = (g.score > 0).to_numpy(); topo = (g.quintil_c == 5).to_numpy()
    valido = (g.retorno_terminal != 0).to_numpy(); acerto = (g.lado*g.retorno_terminal > 0).to_numpy()
    pares = {
        "acuracia_direcional": (acerto*valido, valido),
        "vantagem_acuracia_maioria_treino": ((acerto-g.acerto_maioria_treino.to_numpy(dtype=float))*valido, valido),
        "delta_mse_media_treino": ((g.erro2-g.erro2_media).to_numpy(), np.ones(len(g))),
        "payoff_score_positivo": (g.payoff_escolhido.to_numpy()*ativo,ativo),
        "ganho_lado_score_positivo": ((g.payoff_escolhido-g.payoff_lado_treino).to_numpy()*ativo,ativo),
        "payoff_quintil_superior_c": (g.payoff_escolhido.to_numpy()*topo,topo),
    }
    colunas=[]
    for k,(a,b) in pares.items():
        g[k+'_num']=a; g[k+'_den']=b; colunas += [k+'_num',k+'_den']
    seeds=sorted(g.seed.unique()); arrays=[]
    for _,f in g.groupby('recorte',sort=True):
        dias=np.arange(f.dia.min(),f.dia.max()+1)
        q=f.groupby(['seed','dia'])[colunas].sum().reindex(pd.MultiIndex.from_product([seeds,dias],names=['seed','dia']),fill_value=0)
        arrays.append(q.to_numpy(float).reshape(len(seeds),len(dias),len(colunas)))
    totais=sum(a.sum(axis=(0,1)) for a in arrays)
    pontos=np.divide(totais[::2],totais[1::2],out=np.full(len(pares),np.nan),where=totais[1::2]>0)
    saida=[]
    for tamanho in config['dias']:
        rng=np.random.default_rng(config['seed']); valores=[]
        for _ in range(config['repeticoes']):
            ss=rng.integers(0,len(seeds),size=len(seeds)); total=np.zeros(len(colunas))
            for a in arrays:
                dd=indices_blocos(a.shape[1],tamanho,rng)
                total += a[ss][:,dd,:].sum(axis=(0,1))
            valores.append(np.divide(total[::2],total[1::2],out=np.full(len(pares),np.nan),where=total[1::2]>0))
        valores=np.array(valores)
        for i,k in enumerate(pares):
            v=valores[:,i]; v=v[np.isfinite(v)]
            saida.append({'metrica':k,'bloco_dias':tamanho,'ponto':pontos[i],
                          'ic95':np.quantile(v,[.025,.975]).tolist() if len(v) else None,
                          'replicas_validas':len(v),'n_denominador':int(totais[2*i+1])})
    return saida


def decompor_operacao(o):
    q=o['quantidade']; bruto=q*o['pnl_bruto_por_btc']; taxa=q*o['comissao_por_btc']; funding=q*o['funding_por_btc']
    liquido=bruto-taxa+funding
    if not np.isclose(liquido,o['pnl_liquido'],atol=1e-8,rtol=1e-10):
        raise ValueError('Identidade contábil inválida.')
    return {'bruto_com_slippage':bruto,'comissao':taxa,'funding':funding,'liquido':liquido}
