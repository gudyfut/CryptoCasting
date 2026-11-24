"""32 ajustes novos e um controle; referências herdadas sem reabrir executores."""
import contextlib
from copy import deepcopy
from pathlib import Path
import shutil
import traceback
import unittest
from uuid import uuid4

from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, identidade, fontes as listar_fontes
from treinamento.avaliar import avaliar
from treinamento.preservacao import conferir, publicar as selar, exclusividade
from treinamento.ciclo import reproducao
from experimentos.huber_blocos.ciclo import ambiente
from experimentos.huber_blocos.dados import Verificador
from experimentos.perda_huber.treino import ajustar
from .dados import REG, CONFIG, VARIANTES, carregar

PROTOCOLO = 'docs/protocolo_crua_huber.md'


def configuracao():
    c = ler_json(RAIZ/CONFIG)
    base = ler_json(RAIZ/'configuracoes/huber_blocos_001.json')
    assert c['seeds'] == base['seeds'] and c['ordem_seeds'] == base['ordem_seeds']
    assert c['blocos'] == base['blocos'] and c['variantes'] == VARIANTES
    assert (c['principais_novos'], c['controles_reais'], c['reais_novos_total'], c['referencias_herdadas']) == (32, 1, 33, 96)
    assert (c['simulacoes_novas'], c['simulacoes_herdadas'], c['simulacoes_total']) == (192, 600, 792)
    assert c['politicas'] == base['politicas'] and c['cenarios'] == base['cenarios']
    assert c['bootstrap'] == {'dias': [7, 14, 28], 'principal': 14, 'replicas': 2000, 'seed': 20261105, 'familia': 4}
    return c


def grade(c):
    itens = []
    for b in c['blocos']:
        for s in c['ordem_seeds']:
            itens.append({'bloco': b, 'variante': 'crua_huber', 'seed': s, 'controle': False})
            if b == 'B1' and s == 42:
                itens.append({'bloco': b, 'variante': 'crua_huber', 'seed': s, 'controle': True})
    assert len(itens) == 33
    return itens


def chave(i):
    return f'{i["bloco"]}_crua_huber_{i["seed"]}'


def herancas(v=None):
    v = v or Verificador()
    saida = {}
    for nome, pt in configuracao()['origens'].items():
        p = RAIZ/pt['pasta']
        v.arquivos_em(p, {'congelamento.json': pt['congelamento_sha256']})
        f = ler_json(p/'congelamento.json')
        assert identidade(f['contrato'])[:20] == f['id'] == pt['id']
        v.arquivos_em(RAIZ, f['contrato']['fontes'])
        v.arquivos_em(p/'fontes', f['contrato']['fontes'])
        fim = ler_json(RAIZ/f'registros/{nome}/fechamento.json')
        assert fim['situacao'] == 'concluido_conferido' and fim['execucao'] == pt
        assert ler_json(p/'progresso.json')['status'] == 'concluido'
        assert not ler_json(p/'processo.json')['ativo']
        if (p/'processo_publicacao.json').exists():
            assert not ler_json(p/'processo_publicacao.json')['ativo']
        pub = RAIZ/fim['publicacao']
        v.arquivos_em(pub, {'manifesto.json': fim['manifesto_sha256']})
        v.arquivos_em(pub, ler_json(pub/'manifesto.json')['arquivos'])
        saida[nome] = {'pasta': p, 'congelamento': f, 'publicacao': pub,
                       'resultados': ler_json(pub/'resultados.json')}
    return saida


def receita(bloco):
    # Derivação literal da receita crua/MSE publicada: só a perda é científica nova.
    pt = configuracao()['origens']['entradas_niveis']
    f = ler_json(RAIZ/pt['pasta']/'congelamento.json')
    r = deepcopy(f['contrato']['receitas'][bloco]['crua'])
    r.update(versao='crua-huber-1', ciclo='crua_huber_001', variante='huber',
             hipotese='2*Huber(delta1) na mesma entrada OHLCV crua; complemento fatorial.',
             referencia_execucao=pt['id'], controle='Um controle real B1/42 precede demais seeds.')
    r['perda'] = deepcopy(ler_json(RAIZ/'configuracoes/mamba16_perda_huber_001.json')['perda'])
    return r


def fontes():
    fs = {}
    for pt in configuracao()['origens'].values():
        origem = ler_json(RAIZ/pt['pasta']/'congelamento.json')['contrato']['fontes']
        for n, h in origem.items():
            if n in fs and fs[n] != h:
                raise ValueError(f'Fontes herdadas conflitantes: {n}')
            fs[n] = h
    fs.update(listar_fontes('experimentos/crua_huber', 'tests_crua_huber'))
    for n in (CONFIG, PROTOCOLO):
        fs[n] = sha256(RAIZ/n)
    Verificador().arquivos_em(RAIZ, fs)
    return fs


def mapa_preservacao(refs):
    guard = ler_json(RAIZ/'registros/entradas_niveis/preservacao_antes.json')['arquivos'].copy()
    for nome, ref in refs.items():
        p, pub = ref['pasta'], ref['publicacao']
        fs = ref['congelamento']['contrato']['fontes']
        guard.update(fs)
        guard.update({(p/'fontes'/n).relative_to(RAIZ).as_posix(): h for n, h in fs.items()})
        for fim in p.rglob('conclusao.json'):
            if 'fontes' in fim.relative_to(p).parts:
                continue
            guard.update({(fim.parent/n).relative_to(RAIZ).as_posix(): h
                          for n, h in ler_json(fim)['arquivos'].items()})
            guard[fim.relative_to(RAIZ).as_posix()] = sha256(fim)
        guard.update({(pub/n).relative_to(RAIZ).as_posix(): h
                      for n, h in ler_json(pub/'manifesto.json')['arquivos'].items()})
        for q in (p/'congelamento.json', p/'publicacao.json', pub/'manifesto.json',
                  RAIZ/f'registros/{nome}/fechamento.json', RAIZ/f'docs/resultados_{nome}.md'):
            guard[q.relative_to(RAIZ).as_posix()] = sha256(q)
    Verificador().arquivos_em(RAIZ, guard)
    return guard


def qualificar():
    from tests_entradas_niveis.test_ciclo import sinteticos
    p = REG/'qualificacoes'/uuid4().hex
    p.mkdir(parents=True)
    fs = fontes()
    salvar_json(p/'inicio.json', {'utc': agora(), 'fontes': fs, 'treinamentos_mercado': 0})
    for n in fs:
        d = p/'fontes'/n
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(RAIZ/n, d)
    try:
        herancas()
        mapa = ler_json(RAIZ/'registros/entradas_niveis/entradas.json')
        xs = carregar(mapa)
        with (p/'qualificacao.log').open('w', encoding='utf-8', buffering=1) as log:
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromName(n) for n in
                    ('tests_crua_huber.test_ciclo', 'tests_huber.test_ciclo',
                     'tests_entradas_niveis.test_ciclo', 'tests_backtest_carteira.test_carteira',
                     'tests_backtest_carteira.test_mercado')])
                resultado = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
                if not resultado.wasSuccessful() or resultado.skipped:
                    raise ValueError('Qualificação reprovada.')
                x = sinteticos()['crua']
                cfg = receita('B1')
                cfg['treino'] = dict(cfg['treino'], epocas=2, paciencia=2, perda=cfg['perda'])
                for nome in ('a', 'b'):
                    d = p/f'crua_huber_{nome}'
                    d.mkdir()
                    vinc = {'natureza': 'sintetico', 'combinacao': 'crua_huber'}
                    rede, aj = ajustar(x, 'mamba', 42, cfg['treino'], RAIZ/cfg['configuracao_modelos'], d, vinc)
                    assert aj['parametros'] == 20257
                    avaliar(x, x._conjunto.partes, 'mamba', cfg, d, vinc, rede, aj)
                    del rede
                controle = reproducao(p/'crua_huber_a', p/'crua_huber_b', cfg['reproducao'])
        assert fontes() == fs
        salvar_json(p/'qualificacao.json', {'status': 'aprovado', 'utc': agora(), 'fontes': fs,
            'ambiente': ambiente(), 'testes': resultado.testsRun, 'skips': 0,
            'ajustes_sinteticos': 2, 'treinamentos_mercado': 0, 'reproducao': controle,
            'consumos': {b: {v: x.especificacao.identidade for v, x in vs.items()} for b, vs in xs.items()},
            'arquivos': {q.relative_to(p).as_posix(): sha256(q) for q in p.rglob('*') if q.is_file()}})
    except BaseException:
        salvar_json(p/'falha.json', {'utc': agora(), 'erro': traceback.format_exc()})
        raise
    return p/'qualificacao.json'


def preparar(qualificacao):
    if (REG/'execucao.json').exists():
        raise FileExistsError('Execução já preparada; não duplicar.')
    q = Path(qualificacao).resolve()
    if not q.is_relative_to(REG/'qualificacoes'):
        raise ValueError('Qualificação de outra rodada.')
    qr = ler_json(q)
    assert qr['status'] == 'aprovado' and qr['fontes'] == fontes() and qr['ambiente'] == ambiente()
    assert qr['skips'] == qr['treinamentos_mercado'] == 0
    Verificador().arquivos_em(q.parent, qr['arquivos'])
    refs = herancas()
    guard = mapa_preservacao(refs)
    c = configuracao()
    mapa = ler_json(RAIZ/'registros/entradas_niveis/entradas.json')
    xs = carregar(mapa)
    ct = {'configuracao': c, 'fontes': fontes(), 'ambiente': ambiente(), 'entradas': mapa,
          'receitas': {b: receita(b) for b in c['blocos']}, 'grade': grade(c),
          'identidades_consumo': {b: {v: x.especificacao.identidade for v, x in vs.items()} for b, vs in xs.items()},
          'qualificacao': {'arquivo': q.relative_to(RAIZ).as_posix(), 'sha256': sha256(q)},
          'publicacoes_herdadas': {n: {'pasta': v['publicacao'].relative_to(RAIZ).as_posix(),
              'manifesto_sha256': sha256(v['publicacao']/'manifesto.json')} for n, v in refs.items()},
          'preservacao_sha256': identidade(guard), 'protocolo_sha256': sha256(RAIZ/PROTOCOLO)}
    codigo = identidade(ct)[:20]
    p = RAIZ/f'dados/experimentos/crua_huber_{codigo}'
    p.mkdir(parents=True, exist_ok=False)
    for n in ct['fontes']:
        d = p/'fontes'/n
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(RAIZ/n, d)
    shutil.copyfile(RAIZ/PROTOCOLO, p/'protocolo.md')
    salvar_json(p/'congelamento.json', {'id': codigo, 'utc': agora(), 'contrato': ct})
    salvar_json(p/'progresso.json', {'status': 'preparado', 'principais_concluidos': 0,
        'controles_concluidos': 0, 'total_principais': 32, 'total_reais': 33, 'concluidos': []})
    salvar_json(REG/'preservacao_antes.json', {'utc': agora(), 'arquivos': guard})
    pt = {'id': codigo, 'pasta': p.relative_to(RAIZ).as_posix(), 'congelamento_sha256': sha256(p/'congelamento.json')}
    salvar_json(REG/'execucao.json', pt)
    a = ler_json(REG/'autorizacao_escopo.json')
    assert a['configuracao_sha256'] == sha256(RAIZ/CONFIG)
    assert a['reais_novos_total'] == 33 and a['seeds'] == c['seeds'] and a['mensagem_usuario']
    salvar_json(REG/'autorizacao.json', dict(a, execucao=codigo, congelamento_sha256=pt['congelamento_sha256'],
        vinculacao='Identidade derivada do escopo explicitamente autorizado; sem ampliar fatores ou orçamento.'))
    salvar_json(REG/'estado.json', {'situacao': 'preparado_qualificado', 'utc': agora(), 'execucao': pt,
        'principais_novos': 32, 'controles_reais': 1, 'referencias_herdadas': 96, 'treinamento_mercado_iniciado': False})
    return pt


def conferir_execucao():
    pt = ler_json(REG/'execucao.json')
    p = RAIZ/pt['pasta']
    v = Verificador()
    v.arquivos_em(p, {'congelamento.json': pt['congelamento_sha256']})
    f = ler_json(p/'congelamento.json')
    ct = f['contrato']
    assert identidade(ct)[:20] == f['id'] == pt['id']
    assert ct['configuracao'] == configuracao() and ct['ambiente'] == ambiente()
    v.arquivos_em(RAIZ, ct['fontes'])
    v.arquivos_em(p/'fontes', ct['fontes'])
    v.arquivos_em(p, {'protocolo.md': ct['protocolo_sha256']})
    v.arquivos_em(RAIZ, {ct['qualificacao']['arquivo']: ct['qualificacao']['sha256']})
    q = RAIZ/ct['qualificacao']['arquivo']
    qr = ler_json(q)
    assert qr['status'] == 'aprovado' and qr['fontes'] == ct['fontes'] and qr['ambiente'] == ct['ambiente']
    v.arquivos_em(q.parent, qr['arquivos'])
    guard = ler_json(REG/'preservacao_antes.json')['arquivos']
    assert identidade(guard) == ct['preservacao_sha256']
    v.arquivos_em(RAIZ, guard)
    refs = herancas(v)
    for n, ref in refs.items():
        assert ct['publicacoes_herdadas'][n]['pasta'] == ref['publicacao'].relative_to(RAIZ).as_posix()
    xs = carregar(ct['entradas'])
    for b, vs in xs.items():
        assert ct['receitas'][b] == receita(b)
        assert {n: x.especificacao.identidade for n, x in vs.items()} == ct['identidades_consumo'][b]
    return p, f, xs, refs


def validar_autorizacao(caminho, f):
    a = ler_json(caminho)
    if (a.get('execucao') != f['id'] or a.get('reais_novos_total') != 33
            or a.get('seeds') != f['contrato']['configuracao']['seeds'] or not a.get('mensagem_usuario')):
        raise ValueError('Autorização incompatível com esta execução.')
    return a


def executar(autorizacao):
    p, f, xs, _ = conferir_execucao()
    a = validar_autorizacao(autorizacao, f)
    assert a['congelamento_sha256'] == sha256(p/'congelamento.json')
    if ler_json(p/'progresso.json')['status'] != 'preparado':
        raise ValueError('Executor já iniciado/encerrado; não repetir.')
    with exclusividade(p):
        salvar_json(p/'autorizacao.json', a)
        prontas = []
        piloto = None
        try:
            for item in f['contrato']['grade']:
                b, seed = item['bloco'], item['seed']
                cfg = f['contrato']['receitas'][b]
                x = xs[b]['crua']
                t = p/('controles' if item['controle'] else 'celulas')/chave(item)/'tentativa_001'
                t.mkdir(parents=True, exist_ok=False)
                vinc = {'execucao': f['id'], 'bloco': b, 'variante': 'crua_huber', 'controle': item['controle'],
                        'seed': seed, 'familia': 'mamba', 'identidade_consumo': x.especificacao.identidade, 'configuracao': cfg}
                salvar_json(t/'inicio.json', {'utc': agora(), 'vinculo': vinc})
                prog = {'status': 'executando', 'utc': agora(), 'concluidos': prontas, 'atual': item,
                        'principais_concluidos': sum(not i['controle'] for i in prontas),
                        'controles_concluidos': sum(i['controle'] for i in prontas), 'total_principais': 32, 'total_reais': 33}
                salvar_json(p/'progresso.json', prog)
                salvar_json(REG/'estado.json', {'situacao': 'executando', 'utc': agora(), 'execucao': ler_json(REG/'execucao.json'),
                    'progresso': (p/'progresso.json').relative_to(RAIZ).as_posix(), 'atual': item, 'treinamento_mercado_iniciado': True})
                try:
                    with (t/'treinamento.log').open('w', encoding='utf-8', buffering=1) as log:
                        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                            rede, aj = ajustar(x, 'mamba', seed, dict(cfg['treino'], perda=cfg['perda']),
                                              RAIZ/cfg['configuracao_modelos'], t, vinc)
                            assert aj['parametros'] == 20257
                            avaliar(x, x._conjunto.partes, 'mamba', cfg, t, vinc, rede, aj)
                            del rede
                    selar(t)
                    if item['controle']:
                        salvar_json(p/'controle_reproducao.json', reproducao(piloto, t, cfg['reproducao']))
                    elif b == 'B1' and seed == 42:
                        piloto = t
                except BaseException:
                    salvar_json(t/'falha.json', {'utc': agora(), 'erro': traceback.format_exc()})
                    raise
                prontas.append(item)
            conferir_execucao()
            salvar_json(p/'progresso.json', {'status': 'concluido', 'utc': agora(), 'concluidos': prontas,
                'principais_concluidos': 32, 'controles_concluidos': 1, 'total_principais': 32, 'total_reais': 33})
        except BaseException:
            erro = traceback.format_exc()
            salvar_json(p/'progresso.json', {'status': 'interrompido', 'utc': agora(), 'concluidos': prontas, 'erro': erro})
            salvar_json(REG/'estado.json', {'situacao': 'interrompido', 'utc': agora(), 'execucao': ler_json(REG/'execucao.json'), 'erro': erro})
            raise
