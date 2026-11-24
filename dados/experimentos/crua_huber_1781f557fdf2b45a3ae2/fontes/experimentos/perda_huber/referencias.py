"""Herança/preservação da rodada concluída, sem chamar executores anteriores."""
from infraestrutura.artefatos import RAIZ, ler_json, sha256, conferir_arquivos
from treinamento.preservacao import conferir


def estudo_anterior():
    ptr = ler_json(RAIZ / 'registros/taxa_dinamica/execucao.json')
    p = RAIZ / ptr['pasta']
    conferir_arquivos(p, {'congelamento.json': ptr['congelamento_sha256']})
    f = ler_json(p / 'congelamento.json')
    assert ler_json(p / 'progresso.json')['status'] == 'concluido'
    assert not ler_json(p / 'processo.json')['ativo']
    assert ler_json(RAIZ / 'registros/taxa_dinamica/fechamento.json')['situacao'] == 'concluido_conferido'
    conferir_arquivos(RAIZ, f['contrato']['fontes'])
    conferir_arquivos(p / 'fontes', f['contrato']['fontes'])
    pp = ler_json(p / 'publicacao.json'); pub = p / pp['pasta']
    conferir_arquivos(pub, {'manifesto.json': pp['manifesto_sha256']})
    conferir_arquivos(pub, ler_json(pub / 'manifesto.json')['arquivos'])
    r = ler_json(pub / 'resultados.json')
    assert len(r['por_ajuste']) == 59
    # Candidata scheduler continua preservada; contraste primário usa a constante.
    refs = {k: RAIZ / v['tentativa_origem'] for k, v in r['por_ajuste'].items()
            if not k.startswith('mamba16_scheduler_')}
    assert len(refs) == 53
    for t in refs.values():
        conferir(t)
    return ptr, pub, r, refs


def mapa_preservacao():
    ptr, pub, r, _ = estudo_anterior(); p = RAIZ / ptr['pasta']
    guard = ler_json(RAIZ / 'registros/taxa_dinamica/preservacao_antes.json')['arquivos'].copy()
    f = ler_json(p / 'congelamento.json'); guard.update(f['contrato']['fontes'])
    for nome, h in f['contrato']['fontes'].items():
        guard[(p / 'fontes' / nome).relative_to(RAIZ).as_posix()] = h
    guard[ptr['pasta'] + '/congelamento.json'] = ptr['congelamento_sha256']
    for v in r['por_ajuste'].values():
        t = RAIZ / v['tentativa_origem']
        for nome, h in ler_json(t / 'conclusao.json')['arquivos'].items():
            guard[(t / nome).relative_to(RAIZ).as_posix()] = h
        guard[(t / 'conclusao.json').relative_to(RAIZ).as_posix()] = sha256(t / 'conclusao.json')
    for nome, h in ler_json(pub / 'manifesto.json')['arquivos'].items():
        guard[(pub / nome).relative_to(RAIZ).as_posix()] = h
    guard[(pub / 'manifesto.json').relative_to(RAIZ).as_posix()] = sha256(pub / 'manifesto.json')
    for nome in ('registros/taxa_dinamica/fechamento.json', 'registros/taxa_dinamica/execucao.json',
                 'registros/taxa_dinamica/entrega/20261102/conferencia.json',
                 'registros/taxa_dinamica/entrega/20261102/conferir.py',
                 'registros/referencias/mamba16_ohlcv24_001.json'):
        guard[nome] = sha256(RAIZ / nome)
    conferir_arquivos(RAIZ, guard)
    return guard
