from pathlib import Path
from infraestrutura.artefatos import RAIZ, ler_json, sha256, conferir_arquivos
from experimentos.busca_astra.contrato import REFERENCIA, SEEDS, FINAIS

REG = RAIZ/'registros/comparacao_astra_crua'
ORIGEM = RAIZ/'dados/experimentos/busca_astra_b34bad73d6cef1d10a97'
CRUA = dict(REFERENCIA, representacao='crua', perda='huber')
ASTRA = dict(REFERENCIA, representacao='janela_relativa', contexto=72, perda='huber')

def grade():
    itens=[{'bloco':'B1','seed':42,'tipo':'controle_astra','receita':ASTRA}]
    for b in FINAIS:
        for s in SEEDS:
            itens.append({'bloco':b,'seed':s,'tipo':'crua','receita':CRUA})
            if b=='B1' and s==42:
                itens.append({'bloco':b,'seed':s,'tipo':'controle_crua','receita':CRUA})
    return itens

def fontes():
    herdadas=ler_json(ORIGEM/'congelamento.json')['fontes']
    conferir_arquivos(RAIZ,herdadas)
    novas={p.relative_to(RAIZ).as_posix():sha256(p)
           for grupo in ['experimentos/comparacao_astra_crua','tests_comparacao_astra_crua']
           for p in (RAIZ/grupo).glob('*.py')}
    for nome in ['configuracoes/comparacao_astra_crua_001.json','docs/protocolo_comparacao_astra_crua.md','experimentos/__init__.py']:
        novas[nome]=sha256(RAIZ/nome)
    return dict(herdadas,**novas)

def conferir_execucao(p,ptr):
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    f=ler_json(p/'congelamento.json')
    conferir_arquivos(RAIZ,f['fontes']);conferir_arquivos(p/'fontes',f['fontes'])
    assert ler_json(p/'autorizacao.json')['execucao']==ptr
    assert sha256(REG/'preservacao_antes.json')==f['preservacao_sha256']
    assert sha256(RAIZ/f['qualificacao']['arquivo'])==f['qualificacao']['sha256']
    for nome,h in f['ancoras'].items(): assert sha256(RAIZ/nome)==h
    assert f['grade']==grade()
    return f

def validar_pedido(q,p,ptr,jobs):
    assert q['execucao']==ptr
    n=q['numero'];assert type(n) is int and 1<=n<=len(grade())
    assert len(jobs)==n and jobs[-1]==dict(q,status='iniciado')
    assert q['item']==grade()[n-1]
    i=q['item'];esperado=p/i['tipo']/f"{i['bloco']}_{i['seed']}"
    assert (RAIZ/q['destino']).resolve()==esperado.resolve()
    assert esperado.resolve().is_relative_to(p.resolve())
    assert q['limite_segundos']==2700
    return esperado
