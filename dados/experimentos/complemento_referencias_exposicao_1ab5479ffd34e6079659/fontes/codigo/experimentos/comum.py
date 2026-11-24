"""Leitura de referências encerradas sem chamar seus executores recursivamente."""
from infraestrutura.artefatos import RAIZ,ler_json,sha256,conferir_arquivos
from treinamento.preservacao import conferir


def estudo_anterior():
    ptr=ler_json(RAIZ/'registros/otimizador/execucao.json');p=RAIZ/ptr['pasta']
    conferir_arquivos(p,{'congelamento.json':ptr['congelamento_sha256']})
    f=ler_json(p/'congelamento.json')
    assert ler_json(p/'progresso.json')['status']=='concluido' and not ler_json(p/'processo.json')['ativo']
    conferir_arquivos(RAIZ,f['contrato']['fontes']);conferir_arquivos(p/'fontes',f['contrato']['fontes'])
    pp=ler_json(p/'publicacao.json');pub=p/pp['pasta']
    conferir_arquivos(pub,{'manifesto.json':pp['manifesto_sha256']})
    conferir_arquivos(pub,ler_json(pub/'manifesto.json')['arquivos'])
    r=ler_json(pub/'resultados.json');assert len(r['por_ajuste'])==65
    # CryptoMamba mantém seu histórico; o estudo atual se concentra no Mamba temporal.
    refs={k:RAIZ/v['tentativa_origem'] for k,v in r['por_ajuste'].items() if not k.startswith('cryptomamba')}
    assert len(refs)==53
    for t in refs.values():conferir(t)
    return ptr,pub,r,refs


def mapa_preservacao():
    ptr,pub,r,refs=estudo_anterior();p=RAIZ/ptr['pasta']
    guard=ler_json(RAIZ/'registros/otimizador/preservacao_antes.json')['arquivos'].copy()
    f=ler_json(p/'congelamento.json');guard.update(f['contrato']['fontes'])
    for base in (p/'fontes',):
        for nome,h in f['contrato']['fontes'].items():guard[(base/nome).relative_to(RAIZ).as_posix()]=h
    guard[ptr['pasta']+'/congelamento.json']=ptr['congelamento_sha256']
    for v in r['por_ajuste'].values():
        t=RAIZ/v['tentativa_origem']
        for n,h in ler_json(t/'conclusao.json')['arquivos'].items():guard[(t/n).relative_to(RAIZ).as_posix()]=h
        guard[(t/'conclusao.json').relative_to(RAIZ).as_posix()]=sha256(t/'conclusao.json')
    for n,h in ler_json(pub/'manifesto.json')['arquivos'].items():guard[(pub/n).relative_to(RAIZ).as_posix()]=h
    guard[(pub/'manifesto.json').relative_to(RAIZ).as_posix()]=sha256(pub/'manifesto.json')
    for nome in ('registros/otimizador/fechamento.json','registros/referencias/mamba16_ohlcv24_001.json'):
        guard[nome]=sha256(RAIZ/nome)
    bp=ler_json(RAIZ/'registros/backtest_carteira/execucao_atual.json');b=RAIZ/bp['pasta'];bf=ler_json(b/'congelamento.json')
    guard.update(bf['contrato']['fontes'])
    conferir_arquivos(RAIZ,guard)
    return guard
