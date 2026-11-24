"""Mapas de preservação obtidos dos fechamentos, sem executar estudos anteriores."""
from infraestrutura.artefatos import RAIZ, ler_json, sha256


def mapa_anterior():
    reg=RAIZ/'registros/perda_huber';pt=ler_json(reg/'execucao.json');p=RAIZ/pt['pasta']
    assert ler_json(reg/'fechamento.json')['situacao']=='concluido_conferido'
    assert ler_json(p/'progresso.json')['status']=='concluido' and not ler_json(p/'processo.json')['ativo']
    f=ler_json(p/'congelamento.json');guard=ler_json(reg/'preservacao_antes.json')['arquivos'].copy()
    guard.update(f['contrato']['fontes'])
    for n,h in f['contrato']['fontes'].items():guard[(p/'fontes'/n).relative_to(RAIZ).as_posix()]=h
    guard[pt['pasta']+'/congelamento.json']=pt['congelamento_sha256']
    pp=ler_json(p/'publicacao.json');pub=p/pp['pasta']
    guard[(pub/'manifesto.json').relative_to(RAIZ).as_posix()]=pp['manifesto_sha256']
    for n,h in ler_json(pub/'manifesto.json')['arquivos'].items():guard[(pub/n).relative_to(RAIZ).as_posix()]=h
    r=ler_json(pub/'resultados.json')
    for item in r['por_ajuste'].values():
        t=RAIZ/item['tentativa_origem']
        for n,h in ler_json(t/'conclusao.json')['arquivos'].items():guard[(t/n).relative_to(RAIZ).as_posix()]=h
        guard[(t/'conclusao.json').relative_to(RAIZ).as_posix()]=sha256(t/'conclusao.json')
    revisao=reg/'entrega/20261103';m=ler_json(revisao/'manifesto.json')
    for n,h in m['arquivos'].items():guard[(revisao/n).relative_to(RAIZ).as_posix()]=h
    for q in (reg/'execucao.json',reg/'fechamento.json',revisao/'manifesto.json',
              RAIZ/'registros/backtest_carteira/execucao_atual.json'):
        guard[q.relative_to(RAIZ).as_posix()]=sha256(q)
    return guard
