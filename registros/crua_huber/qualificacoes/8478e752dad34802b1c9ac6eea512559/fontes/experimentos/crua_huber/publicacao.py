"""Completa quatro combinações, audita previsões e simula somente as novas."""
import os
import traceback
import math
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256
from treinamento.preservacao import conferir
from avaliacao.publicacao import conferir_previsoes
from experimentos.huber_blocos.publicacao import auditar_ajuste, media_metricas, janela_operacional
from experimentos.huber_blocos.dados import Verificador
from analises.metricas import analisar
from backtest_carteira.simulador import simular
from backtest_carteira.auditoria import conferir as conferir_carteira
from backtest_carteira.mercado import carregar as carregar_minutos
from .dados import REG, VARIANTES
from .estatisticas import CONTRASTES, contraste


def origem_ajuste(p, f, refs, b, variante, seed):
    if variante == 'crua_huber':
        return p/'celulas'/f'{b}_crua_huber_{seed}', f, f['contrato']['receitas'][b], False
    nome = 'entradas_niveis' if variante == 'crua_mse' else 'huber_blocos'
    ref = refs[nome]
    fator = 'crua' if variante == 'crua_mse' else 'mse' if variante == 'relativa_mse' else 'huber'
    return (ref['pasta']/'celulas'/f'{b}_{fator}_{seed}', ref['congelamento'],
            ref['congelamento']['contrato']['receitas'][b][fator], True)


def herdar_carteiras(refs):
    carteiras = {}
    for nome in ('huber_blocos', 'entradas_niveis'):
        ref = refs[nome]
        for chave, resumo in ref['resultados']['carteiras'].items():
            partes = chave.split('/')
            if nome == 'entradas_niveis':
                if partes[1] != 'crua':
                    continue
                partes[1] = 'crua_mse'
            elif partes[1] in ('mse', 'huber'):
                partes[1] = 'relativa_' + partes[1]
            nova = '/'.join(partes)
            if nova in carteiras:
                raise ValueError('Carteira herdada duplicada.')
            carteiras[nova] = dict(resumo, herdado=True,
                publicacao_origem=ref['publicacao'].relative_to(RAIZ).as_posix(), chave_origem=chave)
    assert len(carteiras) == 600
    return carteiras


def agregar(medias, naives, cfg):
    globais = {}
    for parte in ('validacao', 'teste'):
        globais[parte] = {}
        for v in VARIANTES:
            g = {k: float(np.mean([medias[b][parte][v][k] for b in cfg['blocos']]))
                 for k in ('mse', 'rmse', 'mae', 'vies', 'acuracia_direcional', 'acerto_balanceado_direcional')}
            naive = float(np.mean([naives[b]['metricas'][parte]['mse'] for b in cfg['blocos']]))
            g.update(mse_naive=naive, habilidade_mse=1-g['mse']/naive, blocos=4, seeds_por_bloco=8)
            globais[parte][v] = g
    return globais


def produzir(p, f, xs, refs, dest):
    c = f['contrato']['configuracao']
    resultados, auditorias, medias, previsoes, diags = {}, {}, {}, {}, {}
    perdas = {parte: {} for parte in ('validacao', 'teste')}
    for b in c['blocos']:
        medias[b] = {parte: {} for parte in perdas}
        for parte in perdas:
            perdas[parte][b] = {}
        for v in VARIANTES:
            consumo = xs[b]['crua' if v.startswith('crua') else 'relativa']
            for seed in c['seeds']:
                raiz, ff, cfg, herdado = origem_ajuste(p, f, refs, b, v, seed)
                ts = list(raiz.glob('tentativa_*/conclusao.json'))
                assert len(ts) == 1, f'Tentativas concluídas ausentes/ambíguas: {raiz}'
                t = ts[0].parent
                conferir(t)
                key = f'{b}_{v}_{seed}'
                auditorias[key] = auditar_ajuste(t, ff, consumo, cfg)
                r = ler_json(t/'resultado.json')
                resultados[key] = dict(r, tentativa_origem=t.relative_to(RAIZ).as_posix(), herdado=herdado)
                diags[key] = {}
                for parte in ('validacao', 'teste', 'operacional'):
                    q = pd.read_parquet(t/f'previsoes_{parte}.parquet')
                    conferir_previsoes(q, consumo._conjunto.partes[parte], r['metricas'].get(parte))
                    previsoes[b, v, seed, parte] = q
                    base = previsoes[b, VARIANTES[0], c['seeds'][0], parte]
                    pd.testing.assert_frame_equal(q.drop(columns='previsao'), base.drop(columns='previsao'), check_exact=True)
                    if parte != 'operacional':
                        e = [float(a)-float(y) for a, y in zip(q.previsao, q.alvo)]
                        assert math.isclose(math.fsum(x*x for x in e)/len(e), r['metricas'][parte]['mse'], rel_tol=1e-12)
                        naive = q.copy()
                        naive['previsao'] = 0.
                        diags[key][parte] = analisar(q, previsoes[b, v, seed, 'validacao'], naive)
            for parte in perdas:
                rs = [resultados[f'{b}_{v}_{s}']['metricas'][parte] for s in c['seeds']]
                medias[b][parte][v] = media_metricas(rs)
                medias[b][parte][v]['mse_por_seed'] = [r['mse'] for r in rs]
                qs = [previsoes[b, v, s, parte] for s in c['seeds']]
                perdas[parte][b][v] = np.stack([(q.previsao-q.alvo).to_numpy()**2 for q in qs])
                perdas[parte][b]['origens'] = pd.DatetimeIndex(qs[0].origem_utc)
    assert len(resultados) == 128 and sum(not r['herdado'] for r in resultados.values()) == 32
    t = p/'controles/B1_crua_huber_42/tentativa_001'
    auditorias['controle_B1_crua_huber_42'] = auditar_ajuste(t, f, xs['B1']['crua'], f['contrato']['receitas']['B1'], True)
    ctrl = ler_json(p/'controle_reproducao.json')
    assert ctrl['mesma_epoca']
    naives = refs['huber_blocos']['resultados']['naives']
    globais = agregar(medias, naives, c)
    contrastes = {parte: {nome: contraste(bs, coef, c['bootstrap']) for nome, coef in CONTRASTES.items()}
                 for parte, bs in perdas.items()}
    carteiras = herdar_carteiras(refs)
    cb = refs['huber_blocos']['congelamento']['contrato']['carteira']
    minutos, primeiro = carregar_minutos(RAIZ/cb['pasta'], cb['contrato'])
    opcfg = cb['contrato']['configuracao']
    novas = 0
    for b in c['blocos']:
        for seed in c['seeds']:
            q = janela_operacional(previsoes[b, 'crua_huber', seed, 'operacional'], c['blocos'][b]['teste'][1])
            for pol in c['politicas']:
                for custo in c['cenarios']:
                    r, o, cur, di, si = simular(q, minutos, primeiro, opcfg, pol, custo)
                    ver = conferir_carteira(q, minutos, primeiro, opcfg, pol, custo, r, o, di)
                    key = f'{b}/crua_huber/{seed}/{pol}/{custo}'
                    d = dest/'carteiras'/key
                    d.mkdir(parents=True)
                    for n, valor in (('resumo', r), ('ordens', o), ('sinais', si), ('verificacao', ver)):
                        salvar_json(d/f'{n}.json', valor)
                    cur.to_parquet(d/'curva.parquet', index=False)
                    di.to_parquet(d/'diarios.parquet', index=False)
                    carteiras[key] = dict(r, herdado=False)
                    novas += 1
                    salvar_json(p/'publicacao_progresso.json', {'utc': agora(), 'fase': 'carteiras',
                        'novas_concluidas': novas, 'total_novas': 192})
    assert novas == 192 and len(carteiras) == 792
    opmedias = {}
    for b in c['blocos']:
        opmedias[b] = {}
        for v in VARIANTES:
            for pol in c['politicas']:
                for custo in c['cenarios']:
                    rs = [carteiras[f'{b}/{v}/{s}/{pol}/{custo}'] for s in c['seeds']]
                    m = {k: float(np.mean([r[k] for r in rs])) for k in ('retorno_liquido', 'capital_final',
                        'drawdown_minuto_close', 'exposicao_media', 'comissoes_usdt', 'slippage_usdt', 'ordens_executadas')}
                    m.update(seeds_lucrativas=sum(r['retorno_liquido'] > 0 for r in rs),
                        retorno_desvio_seeds=float(np.std([r['retorno_liquido'] for r in rs], ddof=1)))
                    opmedias[b][f'{v}/{pol}/{custo}'] = m
    primario = {'contraste': 'huber_na_crua', 'decisao': contrastes['teste']['huber_na_crua']['decisao'],
                'familia': 4, 'ic_principal': '98,75% Bonferroni, seeds/dias14',
                'melhora_clara_contra_tres_referencias': all(contrastes['teste'][n]['decisao'] == 'negativo'
                    for n in ('huber_na_crua', 'crua_na_huber', 'combinacao_menos_referencia')),
                'promocao_automatica': False}
    r = {'utc': agora(), 'execucao': f['id'], 'principais_novos': 32, 'controles_reais': 1,
         'referencias_herdadas': 96, 'por_ajuste': resultados, 'auditoria': auditorias,
         'medias_por_bloco': medias, 'medias_globais': globais, 'contrastes': contrastes,
         'criterio_primario': primario, 'diagnosticos': diags, 'naives': naives, 'carteiras': carteiras,
         'medias_operacionais_por_bloco': opmedias, 'simulacoes_novas': 192, 'simulacoes_herdadas': 600,
         'limites': ['Avaliação retrospectiva 2024/2025 já consultados; sem holdout novo ou certeza.',
                    'Oito seeds por combinação/bloco, médias individuais; não ensemble.',
                    'Pesos iguais entre quatro blocos, histórico expansivo reestimado; não mercados independentes.',
                    'Entrada crua sem padronização de X; alvo log-retorno24h continua zscore de treino.',
                    'Receita fixa: resultado não demonstra ótimo universal de cada representação/perda.',
                    'Carteiras independentes de10.000USDT por bloco; não compor retornos como série contínua.',
                    'Sem promoção, nova busca ou repetição automática de resultados ruins.']}
    salvar_json(dest/'resultados.json', r)
    salvar_json(dest/'manifesto.json', {'arquivos': {q.relative_to(dest).as_posix(): sha256(q)
        for q in dest.rglob('*') if q.is_file()}})
    return r


def relatar(r):
    linhas = ['# OHLCV cru com Huber: complemento fatorial', '',
        f'Execução `{r["execucao"]}`:32principais novos+1controle;96referências herdadas,128resultados principais.',
        '', '[Protocolo](protocolo_crua_huber.md), [estado](../registros/crua_huber/estado.json).', '',
        '## Médias de oito seeds por bloco', '',
        '| Bloco | Parte | Relativa/MSE | Relativa/Huber | Crua/MSE | Crua/Huber |',
        '|---|---|---:|---:|---:|---:|']
    for b, partes in r['medias_por_bloco'].items():
        for parte, vs in partes.items():
            vals = ' | '.join(f'{vs[v]["mse"]:.10f}' for v in VARIANTES)
            linhas.append(f'| {b} | {parte} | {vals} |')
    linhas += ['', '## Agregado com peso igual entre quatro blocos', '',
        '| Parte | Combinação | MSE | RMSE×100 | MAE×100 | Habilidade Naive |',
        '|---|---|---:|---:|---:|---:|']
    for parte, vs in r['medias_globais'].items():
        for v, m in vs.items():
            linhas.append(f'| {parte} | {v} | {m["mse"]:.10f} | {100*m["rmse"]:.4f} | {100*m["mae"]:.4f} | {100*m["habilidade_mse"]:+.3f}% |')
    linhas += ['', '## Contrastes fixados antes da execução nova', '',
        '| Contraste | Diferença MSE de teste | IC98,75% principal | Decisão |', '|---|---:|---|---|']
    for n, t in r['contrastes']['teste'].items():
        linhas.append(f'| {n} | {t["diferenca_mse"]:.10g} | {t["intervalos"]["14"]["ic_bonferroni_98_75"]} | {t["decisao"]} |')
    linhas += ['', 'A interação é (crua/Huber−crua/MSE)−(relativa/Huber−relativa/MSE). Negativa indica ganho além da soma dos efeitos nesta escala de MSE; não significa lucro ou causalidade universal.',
        '', '## Spot Smart, custos base', '',
        '| Bloco | Relativa/MSE | Relativa/Huber | Crua/MSE | Crua/Huber |', '|---|---:|---:|---:|---:|']
    for b, vs in r['medias_operacionais_por_bloco'].items():
        vals = ' | '.join(f'{100*vs[v+"/smart/base"]["retorno_liquido"]:+.2f}%' for v in VARIANTES)
        linhas.append(f'| {b} | {vals} |')
    linhas += ['', '192carteiras novas e600herdadas; diárias24, cenários ideal/agravado, risco, exposição, custos e todas as seeds na publicação estruturada.', '', *r['limites']]
    p = RAIZ/'docs/resultados_crua_huber.md'
    if p.exists():
        raise FileExistsError('Relatório existente; preservar e usar conferência posterior.')
    p.write_text('\n'.join(linhas)+'\n', encoding='utf-8')
    return p.relative_to(RAIZ).as_posix()


def publicar():
    from .ciclo import conferir_execucao
    if (REG/'fechamento.json').exists():
        raise FileExistsError('Ciclo já encerrado; não repetir publicação.')
    p, f, xs, refs = conferir_execucao()
    assert ler_json(p/'progresso.json')['status'] == 'concluido' and not ler_json(p/'processo.json')['ativo']
    import fcntl
    with (p/'publicacao.lock').open('a+b') as trava:
        fcntl.flock(trava, fcntl.LOCK_EX | fcntl.LOCK_NB)
        salvar_json(p/'processo_publicacao.json', {'pid': os.getpid(), 'ativo': True, 'inicio_utc': agora()})
        dest = p/'publicacoes'/f'tentativa_{len(list((p/"publicacoes").glob("tentativa_*")))+1:03d}'
        dest.mkdir(parents=True)
        try:
            r = produzir(p, f, xs, refs, dest)
            Verificador().arquivos_em(dest, ler_json(dest/'manifesto.json')['arquivos'])
            conferir_execucao()
            rel = relatar(r)
            salvar_json(p/'publicacao.json', {'pasta': dest.relative_to(p).as_posix(), 'manifesto_sha256': sha256(dest/'manifesto.json')})
            fim = {'situacao': 'concluido_conferido', 'utc': agora(), 'execucao': ler_json(REG/'execucao.json'),
                'principais_novos': 32, 'controles_reais': 1, 'referencias_herdadas': 96,
                'simulacoes_novas': 192, 'simulacoes_herdadas': 600,
                'publicacao': dest.relative_to(RAIZ).as_posix(), 'manifesto_sha256': sha256(dest/'manifesto.json'),
                'relatorio': rel, 'criterio_primario': r['criterio_primario'], 'promocao_automatica': False}
            salvar_json(REG/'fechamento.json', fim)
            salvar_json(REG/'estado.json', fim)
            cat = ler_json(RAIZ/'registros/catalogo_estudos.json')
            for row in cat.get('rodadas_ohlcv', []):
                if row.get('chave') == 'crua_huber_001':
                    row.update(situacao='concluido_conferido', execucao=f['id'], ajustes_neurais_novos_concluidos=33,
                               publicacao=fim['publicacao'], relatorio=rel)
            cat['etapa_atual'].update(situacao='crua_huber_concluido_conferido', crua_huber=fim)
            salvar_json(RAIZ/'registros/catalogo_estudos.json', cat)
            with (RAIZ/'docs/andamento.md').open('a', encoding='utf-8') as doc:
                doc.write(f'\n## Combinação crua/Huber concluída\n\nExecução `{f["id"]}`:32principais novos+1controle,96referências herdadas,192simulações novas+600herdadas. [Resultados](resultados_crua_huber.md). Sem promoção automática;2024/2025 retrospectivos.\n')
            return fim
        except BaseException:
            erro = traceback.format_exc()
            salvar_json(dest/'falha.json', {'utc': agora(), 'erro': erro})
            salvar_json(REG/'estado.json', {'situacao': 'falha_publicacao', 'utc': agora(), 'erro': erro,
                'instrucao': 'Não chamar treinador; investigar e preservar a tentativa de publicação.'})
            raise
        finally:
            salvar_json(p/'processo_publicacao.json', {'pid': os.getpid(), 'ativo': False, 'fim_utc': agora()})
