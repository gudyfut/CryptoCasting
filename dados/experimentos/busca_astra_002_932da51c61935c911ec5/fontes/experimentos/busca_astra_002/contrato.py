"""Contrato fechado do ciclo002. Seleção nunca consulta teste ou lucro."""
import numpy as np
from infraestrutura.artefatos import RAIZ, ler_json, identidade
from experimentos.busca_astra.contrato import FINAIS, ambiente_cuda

CFG = RAIZ/'configuracoes/busca_astra_002.json'
REG = RAIZ/'registros/busca_astra_002'
SEEDS = [42,17,2026,7,123,31415,271828,161803]
GRUPOS = ('momentum','volatilidade','volume_relativo')

def configuracao():
    return ler_json(CFG)

def ancoras():
    return {k:dict(v,**{g:False for g in GRUPOS}) for k,v in configuracao()['referencias'].items()}

def validar_receita(r, ancora=False):
    c=configuracao(); base=ancoras()['A0_C05']
    assert set(r)==set(base), 'Campos de receita divergentes.'
    for k,v in r.items():
        assert type(v) is type(base[k]) or (type(v) in (int,float) and type(base[k]) in (int,float)), k
        if k in c['espaco']:
            assert v in c['espaco'][k] or (ancora and k=='representacao' and v=='crua'), k
        else:
            assert v==base[k], f'Fator fixo alterado: {k}'
    if r['representacao']=='crua':
        assert r==ancoras()['R0_crua_huber'], 'Crua restrita à âncora.'
    return dict(r)

def validar_proposta(p, receitas):
    assert set(p)=={'acao','pai','fator','valor','mecanismo','metrica_esperada','risco','custo'}
    assert p['acao'] in ['experimentar','encerrar']
    if p['acao']=='encerrar': return None
    assert p['pai'] in receitas and p['fator'] in configuracao()['espaco']
    r=dict(receitas[p['pai']]);r[p['fator']]=p['valor']
    validar_receita(r)
    assert sum(r[k]!=receitas[p['pai']][k] for k in r)==1
    assert identidade(r) not in {identidade(v) for v in receitas.values()}, 'Receita repetida.'
    return r

def esquema():
    props={k:{'type':'string'} for k in ['acao','pai','fator','mecanismo','metrica_esperada','risco','custo']}
    props['acao']['enum']=['experimentar','encerrar']
    # Valor via texto evita anyOf misto restrito em alguns provedores; decodificado com JSON.
    props['valor']={'type':'string','description':'Valor JSON serializado: true, false, 72, 0.1 ou string entre aspas.'}
    return {'type':'object','properties':props,'required':list(props),'additionalProperties':False}

def grade_chaves(seeds):
    return {(b,s) for b in ['S1','S2','S3'] for s in seeds}

def completo(linhas,seeds):
    return len(linhas)==3*len(seeds) and {(v['bloco'],v['seed']) for v in linhas}==grade_chaves(seeds)

def score(linhas,seeds):
    assert completo(linhas,seeds), 'Cobertura incompleta não pode ser pontuada.'
    return float(np.mean([v['metricas']['q_mse'] for v in linhas]))

def selecionar(candidatas, referencias):
    """Nove pares, cobertura exata, gates fixos e desempate determinístico."""
    ss=SEEDS[:3]
    for v in referencias.values(): assert completo(v,ss)
    rid=min(referencias,key=lambda k:(score(referencias[k],ss),k))
    ref={(v['bloco'],v['seed']):v['metricas'] for v in referencias[rid]}
    limite=.999*min(1.,*(score(v,ss) for v in referencias.values()),
        np.mean([v['media_constante']['q_mse'] for v in referencias[rid]]))
    out={}; elegiveis=[]
    for nome,rows in candidatas.items():
        if not completo(rows,ss):
            out[nome]={'elegivel':False,'motivo':'cobertura_incompleta'};continue
        m={(v['bloco'],v['seed']):v['metricas'] for v in rows}
        razoes={b:float(np.mean([m[b,s]['mse'] for s in ss])/np.mean([ref[b,s]['mse'] for s in ss])) for b in ['S1','S2','S3']}
        q=score(rows,ss); pares=sum(m[k]['mse']<ref[k]['mse'] for k in ref)
        mae=float(np.mean([m[k]['q_mae'] for k in ref])/np.mean([ref[k]['q_mae'] for k in ref]))
        ok=q<=limite and pares>=6 and sum(v<1 for v in razoes.values())>=2 and max(razoes.values())<=1.05 and mae<=1.01
        out[nome]={'elegivel':bool(ok),'Q':q,'limite_Q':float(limite),'pares_melhores':pares,'razoes_recortes':razoes,'razao_mae':mae}
        if ok:elegiveis.append((q,max(razoes.values()),rows[0]['parametros'],nome))
    return {'referencia_portao':rid,'candidatas':out,'escolhida':min(elegiveis)[-1] if elegiveis else None}
