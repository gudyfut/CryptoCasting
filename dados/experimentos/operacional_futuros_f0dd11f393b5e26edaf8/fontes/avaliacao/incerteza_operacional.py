"""Bootstrap pareado de seeds/dias; preserva drawdown intradiário por estatísticas suficientes."""
import math
import numpy as np


def comprimir_dias(patrimonio,segundos):
    e=np.asarray(patrimonio,float);t=np.asarray(segundos,float)
    if e.shape!=t.shape or e.ndim!=1 or (np.diff(t)<0).any() or e[0]<=0:
        raise ValueError('Curva inválida.')
    # Último instante é limite exclusivo, não um dia extra.
    primeiro=int(t[0]//86400);ultimo=int(np.ceil(t[-1]/86400));anterior=e[0];linhas=[]
    for dia in range(primeiro,ultimo):
        v=e[(t>=dia*86400)&(t<(dia+1)*86400)]
        if dia==ultimo-1: v=np.r_[v,e[-1]]
        v=np.r_[anterior,v]
        if anterior<=0 or np.any(v<=0):
            raise ValueError('Bootstrap de crescimento não definido para insolvência; não excluir célula.')
        z=v/anterior;dd=float(np.max(1-z/np.maximum.accumulate(z)))
        linhas.append([float(z[-1]),float(z.max()),float(z.min()),dd]);anterior=v[-1]
    return np.asarray(linhas)


def reconstruir(dias):
    d=np.asarray(dias,float)
    if d.ndim!=2 or d.shape[1]!=4 or not len(d): raise ValueError('Dias inválidos.')
    capital=pico=1.;dd=0.
    for fator,alto,baixo,interno in d:
        # Interno mantém a ordem pico/vale original; contra pico anterior usa mínimo.
        dd=max(dd,float(interno),1-capital*baixo/pico)
        pico=max(pico,capital*alto);capital*=fator
    g=math.log(capital)/len(d);cagr=math.expm1(365*g)
    return np.array([capital-1,dd,cagr/dd if dd>1e-12 else np.nan,g])


def bootstrap_pareado(candidata,referencia,recortes,seeds,bloco=14,repeticoes=2000,seed=10973):
    """Dicionários (recorte,seed)->[dias,4]. Mesmos sorteios nas duas receitas."""
    esperado={(b,s) for b in recortes for s in seeds}
    if set(candidata)!=esperado or set(referencia)!=esperado: raise ValueError('Coorte incompleta.')
    for b in recortes:
        formas={candidata[b,s].shape for s in seeds}|{referencia[b,s].shape for s in seeds}
        if len(formas)!=1: raise ValueError('Calendários não pareados.')
    rng=np.random.default_rng(seed);amostras=[]
    for _ in range(repeticoes):
        ss=rng.choice(seeds,size=len(seeds),replace=True);aa=[];bb=[]
        for b in recortes:
            n=len(candidata[b,seeds[0]]);k=min(bloco,n)
            starts=rng.integers(0,n-k+1,size=math.ceil(n/k))
            ids=np.concatenate([np.arange(i,i+k) for i in starts])[:n]
            for s in ss:
                aa.append(reconstruir(candidata[b,int(s)][ids]));bb.append(reconstruir(referencia[b,int(s)][ids]))
        a,b=np.array(aa),np.array(bb)
        # Retorno, DD, crescimento: médias iguais por célula. Calmar: mediana do ranking.
        delta=a.mean(axis=0)-b.mean(axis=0);delta[2]=np.median(a[:,2])-np.median(b[:,2]);amostras.append(delta)
    a=np.asarray(amostras);nomes=['retorno_liquido_medio','drawdown_medio','calmar_mediano','crescimento_log_medio']
    return {'bloco_dias':bloco,'repeticoes':repeticoes,'seed_bootstrap':seed,'ic95_delta_candidata_menos_referencia':{
        nome:np.quantile(a[:,i],[.025,.975]).tolist() if np.isfinite(a[:,i]).all() else None for i,nome in enumerate(nomes)},
        'limite':'IC condicional às receitas e blocos observados; não corrige a seleção adaptativa nem prova lucro futuro.'}
