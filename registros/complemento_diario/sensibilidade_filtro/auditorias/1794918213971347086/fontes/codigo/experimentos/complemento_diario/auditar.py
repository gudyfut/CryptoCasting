"""Conferência posterior: artefatos, seleção, reamostragem e ledgers completos."""
from collections import Counter
from decimal import Decimal
from pathlib import Path
import argparse
import io
import json
import math
import shutil
import time
import zipfile
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, conferir_arquivos, ler_json, salvar_json, sha256
from experimentos.generalizacao_moedas.avaliacao import carregar_mercado
from simulacao_operacoes.continuidade_diaria.auditoria_grade import conferir
from .comum import contexto, pais, carregar_npz, conferir_unidade, fontes, registrar_estado, exclusividade
from .inventario import REG, relativo
from .fontes_operacionais import carteira_referencia, comparar_carteiras
from .operacoes import ler_carteira


def perto(a, b, atol=1e-12):
    np.testing.assert_allclose(a, b, rtol=1e-10, atol=atol)


def metricas(z, m):
    y = z['alvo_retorno'].astype(float)
    v = z['previsoes_retorno'].astype(float)
    n = len(y)
    mse = math.fsum((float(a)-float(b))**2 for a, b in zip(v, y))/n
    base = math.fsum(float(a)**2 for a in y)/n
    esperados = dict(n=n, mse_retorno=mse, rmse_retorno=math.sqrt(mse),
        mae_retorno=math.fsum(abs(float(a)-float(b)) for a, b in zip(v, y))/n,
        vies_retorno=math.fsum(float(a)-float(b) for a, b in zip(v, y))/n,
        mse_naive_retorno=base, habilidade_mse_retorno_naive=1-mse/base,
        fracao_previsao_alta=sum(v > 0)/n, fracao_previsao_queda=sum(v < 0)/n,
        fracao_abstencao=sum(v == 0)/n)
    for k, valor in esperados.items():
        perto(m[k], valor)
    recalls = [sum(v[y > 0] > 0)/sum(y > 0), sum(v[y < 0] < 0)/sum(y < 0)]
    if np.any(v):
        perto(m['acerto_balanceado'], sum(recalls)/2)
    else:
        assert m['acerto_balanceado'] is None
    return mse


def intervalo_independente(diferencas, comprimento, cfg, seeds):
    # Caminho separado: constrói cada amostra temporal por lista de blocos e
    # agrega com fsum. Não chama o produtor dos intervalos.
    a = np.atleast_2d(np.asarray(diferencas, dtype=float))
    n = a.shape[1]
    gerador = np.random.default_rng(cfg['seed'])
    valores = []
    for _ in range(cfg['replicas']):
        inicios = gerador.integers(n-comprimento+1, size=math.ceil(n/comprimento))
        dias = [d for inicio in inicios for d in range(inicio, inicio+comprimento)][:n]
        linhas = gerador.integers(len(a), size=len(a)) if seeds else range(len(a))
        valores.append(math.fsum(a[s, dias].sum() for s in linhas)/(len(a)*n))
    return np.quantile(valores, [.025, .975])


def contrastes(matrizes, publicados, c, esquerda='LSTM', referencias=('A', 'L', 'naive')):
    feitos = 0
    for ref in referencias:
        for forma in ('individuais', 'ensemble'):
            if forma == 'individuais':
                a = np.array([matrizes[f'{esquerda}_{s}'] for s in c['seeds']])
                b = np.array([matrizes[f'{ref}_{s}'] for s in c['seeds']]) if ref != 'naive' else matrizes['naive']
            else:
                a = matrizes[f'{esquerda}_ensemble']
                b = matrizes[f'{ref}_ensemble'] if ref != 'naive' else matrizes['naive']
            dif = a-b
            for bloco in c['bootstrap']['blocos']:
                pub = publicados[f'{esquerda}_menos_{ref}_{forma}'][str(bloco)]
                perto(pub['media'], np.mean(dif))
                perto(pub['ic95'], intervalo_independente(dif, bloco, c['bootstrap'], forma == 'individuais'))
                assert pub['replicas'] == 2000 and pub['bloco'] == bloco
                assert pub['reamostrar_seeds'] == (forma == 'individuais')
                feitos += 1
    return feitos


def medias(individuais, publicada):
    for k, p in publicada.items():
        valores = [x[k] for x in individuais]
        if all(isinstance(x, (int, float)) for x in valores):
            perto(p['media'], math.fsum(valores)/len(valores))
            perto(p['desvio_seeds'], np.std(valores, ddof=1))
            perto([p['minimo'], p['maximo']], [min(valores), max(valores)])
        else:
            assert p['media'] is None


def selecionar(pasta):
    conferir_unidade(pasta)
    h = [json.loads(l) for l in (pasta / 'epocas.jsonl').read_text().splitlines()]
    assert [x['epoca'] for x in h] == list(range(1, 201))
    escolhido = min(h, key=lambda x: x['rmse_global_validacao_retorno'])
    s = ler_json(pasta / 'selecao.json')
    assert s['epoca'] == escolhido['epoca']
    assert s['rmse_validacao'] == escolhido['rmse_global_validacao_retorno']
    assert sha256(pasta / s['checkpoint']) == s['sha256']
    z = carregar_npz(pasta / 'validacao.npz')
    # Campo alvo varia entre receitas preservadas; a trajetória e o checkpoint
    # são conferidos acima; a recarga exata consta do recibo de inferência.
    return dict(epoca=s['epoca'], epocas=len(h), previsoes_validacao=len(z['previsoes']))


def contabilidade(destino, z, mercado, regras, referencia=None):
    recibo = ler_json(destino / 'recibo.json')
    assert sha256(destino / recibo['artefato']) == recibo['sha256']
    if recibo['situacao'] == 'falha_prudencial':
        assert 'Violação prudencial' in ler_json(destino / 'falha.json')['erro']
        return dict(falha_prudencial=True)
    r, cv = ler_carteira(destino)
    assert r['regras'] == regras and r['metricas'] == recibo['metricas']
    np.testing.assert_array_equal(cv['origens_ms'], z['origens_ms'])
    auditoria = conferir(r, cv, mercado, regras, 'liquida', z['origens_ms'], z['previsoes'], z['ultimo_close'], None)
    D = lambda v: Decimal(str(v))
    caixa = D(regras['capital_inicial']) - sum((D(o['delta'])*D(o['preenchimento'])+D(o['comissao']) for o in r['ordens']), D(0))
    caixa += sum((D(e['valor']) for e in r['funding']), D(0))
    assert abs(sum((D(o['delta']) for o in r['ordens']), D(0))) < D('1e-10')
    perto(float(caixa), cv['saldos_diarios'][-1], 1e-7)
    m = r['metricas']
    perto(m['retorno_liquido'], float(caixa)/regras['capital_inicial']-1)
    perto(m['crescimento_log_diario'], math.log(float(caixa)/regras['capital_inicial'])/len(r['dias']))
    for campo, valores in [('comissoes', [o['comissao'] for o in r['ordens']]),
        ('funding', [e['valor'] for e in r['funding']]),
        ('volume_negociado_usdt', [abs(o['delta'])*o['preenchimento'] for o in r['ordens']]),
        ('custo_slippage_ticks', [o['custo_slippage_ticks'] for o in r['ordens']])]:
        perto(m[campo], math.fsum(valores), 1e-7)
    lados = [int(np.sign(d['quantidade'])) for d in r['dias']]
    desc = recibo['descricao']
    assert desc['exposicao_executada'] == {str(k): lados.count(k) for k in (-1, 0, 1)}
    assert desc['reversoes_diretas'] == sum(a*b < 0 for a, b in zip(lados, lados[1:]))
    episodios = []
    for i, lado in enumerate(lados):
        if lado and (i == 0 or lado != lados[i-1]):
            j = i+1
            while j < len(lados) and lados[j] == lado:
                j += 1
            episodios.append((i, j-1, lado, j-i, math.fsum(d['pnl_movimento_contrato'] for d in r['dias'][i:j])))
    assert len(episodios) == desc['quantidade_episodios'] == m['blocos_posicao']
    for e, pub in zip(episodios, desc['episodios']):
        assert list(e[:4]) == [pub[k] for k in ('inicio_indice', 'fim_indice', 'lado', 'dias')]
        perto(e[4], pub['movimento_contrato_usdt'], 1e-7)
    positivos = sorted((e[4] for e in episodios if e[4] > 0), reverse=True)
    concentracao = desc['concentracao']['fracao_tres_maiores_ganhos_movimento']
    if positivos:
        perto(concentracao, math.fsum(positivos[:3])/math.fsum(positivos))
    else:
        assert concentracao is None
    pos = 0
    for semestre in desc['semestres']:
        eq = cv['saldos_diarios'][pos:pos+semestre['dias']+1]
        perto(semestre['retorno_liquido'], eq[-1]/eq[0]-1)
        perto(semestre['crescimento_log_diario'], math.log(eq[-1]/eq[0])/semestre['dias'])
        dd = max(1-eq[j]/max(eq[:j+1]) for j in range(len(eq)))
        perto(semestre['drawdown_fechamentos_diarios'], dd)
        assert not semestre['capital_reiniciado']
        pos += semestre['dias']
    assert pos == len(r['dias'])
    if referencia is not None:
        comparar_carteiras(r, cv, *referencia)
    return auditoria


def auditar_lstm(p, f):
    refs, c = pais(), f['configuracao']
    conferir_arquivos(RAIZ, ler_json(p / 'dados_preparados.json'))
    selecoes = {a.name: selecionar(a) for a in (p / 'ajustes').iterdir()}
    esperados = {f"{b['id']}_{s}" for b in c['blocos'] for s in c['seeds']} | {'controle_fixa_42', 'controle_B1_42'}
    assert set(selecoes) == esperados
    from .treinar import conferir_ajustes
    conferir_ajustes(p / 'ajustes/controle_fixa_42', refs['lstm'] / 'BTCUSDT/ajustes/seed_42')
    conferir_ajustes(p / 'ajustes/controle_B1_42', p / 'ajustes/B1_42')
    resultados = ler_json(p / 'publicacao/previsao.json')
    ic = 0
    for bloco in c['blocos']:
        b = bloco['id']
        dados = carregar_npz(p / b / 'dados/teste.npz')
        prev = {q.stem: carregar_npz(q) for q in (p / 'publicacao' / b / 'previsoes').glob('*.npz')}
        assert len(prev) == 13
        for nome, z in prev.items():
            for k, alvo in [('origens_ms', 'origens_ms'), ('ultimo_close', 'ultimo_close'), ('alvo_retorno', 'y')]:
                np.testing.assert_array_equal(z[k], dados[alvo])
            metricas(z, resultados[b]['metricas'][nome])
        for v in c['variantes']:
            np.testing.assert_array_equal(prev[v+'_ensemble']['previsoes'], np.mean([prev[f'{v}_{s}']['previsoes'] for s in c['seeds']], axis=0))
            medias([resultados[b]['metricas'][f'{v}_{s}'] for s in c['seeds']], resultados[b]['medias'][v])
        np.testing.assert_array_equal(prev['naive']['previsoes_retorno'], np.zeros(bloco['n_teste']))
        perdas = {k: (z['previsoes_retorno']-z['alvo_retorno'])**2 for k, z in prev.items()}
        ic += contrastes(perdas, resultados[b]['contrastes_mse'], c)
    wf = ler_json(refs['walkforward'] / 'congelamento.json')
    mercado = carregar_mercado(wf['referencias']['mercado'])
    ops = ler_json(p / 'publicacao/operacoes.json')
    assert len(ops['carteiras'])+len(ops['falhas']) == 48
    auditorias = []
    for linha in ops['carteiras'] + ops['falhas']:
        z = carregar_npz(p / 'publicacao' / linha['bloco'] / 'previsoes' / (linha['unidade']+'.npz'))
        regras = dict(wf['configs_blocos'][linha['bloco']]['operacoes'], slippage_por_lado=c['slippage_cenarios'][linha['custo']-1])
        auditorias.append(contabilidade(p / 'carteiras' / linha['membro'], z, mercado, regras))
    antigos = ler_json(refs['walkforward'] / 'publicacao/operacoes.json')['carteiras']
    for bloco in c['blocos']:
        b = bloco['id']
        for custo in (1, 2, 3):
            locais = [x for x in ops['carteiras'] if x['bloco'] == b and x['custo'] == custo]
            if len(locais) != 4:
                assert ops['contrastes_crescimento_log_diario'][f'{b}/custo_{custo}']['incompleto']
                continue
            matrizes = {x['unidade']: np.diff(np.log(ler_carteira(p / 'carteiras' / x['membro'])[1]['saldos_diarios'])) for x in locais}
            with zipfile.ZipFile(refs['walkforward'] / 'publicacao/carteiras.zip') as arq:
                for x in antigos:
                    if x['bloco'] == b and x['custo'] == custo and x['unidade'].split('_')[0] in ('A', 'L'):
                        with np.load(io.BytesIO(arq.read(x['membro']+'/curva.npz'))) as z:
                            matrizes[x['unidade']] = np.diff(np.log(z['saldos_diarios']))
            matrizes['naive'] = np.zeros(bloco['n_teste'])
            ic += contrastes(matrizes, ops['contrastes_crescimento_log_diario'][f'{b}/custo_{custo}'], c)
            medias([x['metricas'] for x in locais if not x['unidade'].endswith('ensemble')], ops['medias_seeds'][f'{b}/custo_{custo}'])
    return dict(selecoes=selecoes, carteiras=len(auditorias), intervalos_recalculados=ic,
                controles_exatos=2, contabilidade=auditorias)


def auditar_grade(etapa, p, f):
    c = f['configuracao']
    publicacao = ler_json(p / 'publicacao/resultados.json')
    linhas = pd.read_csv(p / 'publicacao/carteiras.csv').to_dict('records')
    esperado = 324 if etapa == 'sensibilidade_filtro' else 2376
    assert len(linhas) == esperado and len({x['membro'] for x in linhas}) == esperado
    auditorias, controles = [], 0
    chave, mercado = None, None
    for caso in f['extras']['casos']:
        if chave != caso['mercado']['pasta']:
            del mercado
            mercado = carregar_mercado(caso['mercado'])
            chave = caso['mercado']['pasta']
        z = carregar_npz(RAIZ / caso['previsao'])
        retorno = z['previsoes']/z['ultimo_close']-1
        sinal = np.where((z['previsoes'] > 0) & (abs(retorno) > .002), np.sign(retorno), 0).astype('int8')
        locais = [x for x in linhas if x['populacao'] == caso['populacao'] and x['moeda'] == caso['moeda'] and x['variante'] == caso['variante']]
        sequencias = []
        if etapa == 'deslocamento_exposicao':
            from .contratos import deslocamentos
            ks = f['extras']['deslocamentos_por_n'][str(caso['n'])]
            assert ks == deslocamentos(caso['n'], c['deslocamentos']).tolist()
            assert set(x['deslocamento'] for x in locais) == set(ks)
            zz = dict(z, previsoes=z['ultimo_close']*(1+.01*sinal))
            regras = dict(caso['regras'], filtro_retorno_absoluto=.002, slippage_por_lado=.0001)
            contabilidade(p / 'carteiras' / caso['id'] / 'controle_zero', zz, mercado, regras, carteira_referencia(caso, 1))
            controles += 1
        else:
            assert {(x['filtro'], x['custo']) for x in locais} == {(v, k) for v in c['filtros'] for k in (1, 2, 3)}
        for linha in locais:
            if etapa == 'sensibilidade_filtro':
                filtro, custo = linha['filtro'], int(linha['custo'])
                regras = dict(caso['regras'], filtro_retorno_absoluto=filtro, slippage_por_lado=c['slippage_cenarios'][custo-1])
                referencia = carteira_referencia(caso, custo) if filtro == .002 else None
                controles += int(referencia is not None)
                lados = np.where((z['previsoes'] > 0) & (abs(retorno) > filtro), np.sign(retorno), 0)
                perto(linha['fracao_decisoes_alteradas'], np.mean(lados != sinal))
                zz = z
            else:
                k = int(linha['deslocamento'])
                lados = np.concatenate((sinal[-k:], sinal[:-k]))
                sequencias.append(lados.tobytes())
                assert Counter(lados) == Counter(sinal)
                zz = dict(z, previsoes=z['ultimo_close']*(1+.01*lados))
                referencia = None
            destino = p / 'carteiras' / linha['membro']
            auditorias.append(contabilidade(destino, zz, mercado, regras, referencia))
            recibo = ler_json(destino / 'recibo.json')
            assert linha['situacao'] == recibo['situacao']
            if recibo['metricas'] is not None:
                for campo, valor in recibo['metricas'].items():
                    if valor is not None:
                        perto(linha[campo], valor, 1e-7)
                if etapa == 'deslocamento_exposicao':
                    base = ler_json(p / 'carteiras' / caso['id'] / 'controle_zero/recibo.json')
                    for campo in ('dias_comprado', 'dias_vendido', 'dias_posicionado', 'blocos_posicao', 'ordens', 'volume_negociado_usdt', 'comissoes', 'custo_slippage_ticks'):
                        perto(linha['diferenca_'+campo], recibo['metricas'][campo]-base['metricas'][campo], 1e-7)
        if etapa == 'deslocamento_exposicao':
            resumo = publicacao['resumos'][caso['id']]
            assert resumo['sequencias_distintas'] == len(set(sequencias))
            assert resumo['sequencia_original_constante'] == bool(np.all(sinal == sinal[0]))
            validas = [ler_json(p / 'carteiras' / x['membro'] / 'recibo.json') for x in locais if x['situacao'] == 'concluida_conferida']
            assert resumo['validas'] == len(validas)
            for campo, med in resumo['metricas'].items():
                valores = [x['metricas'][campo] for x in validas]
                if valores:
                    perto(med['quantis_condicionais_validas'], np.quantile(valores, [0, .05, .25, .5, .75, .95, 1]))
                if len(validas) == 99:
                    pos = (sum(v < med['original'] for v in valores)+sum(v == med['original'] for v in valores)/2)/99*100
                    perto(med['percentil_descritivo'], pos)
                else:
                    assert med['percentil_descritivo'] is None
        registrar_estado(etapa, 'auditando', caso=caso['id'], carteiras=len(auditorias))
    assert controles == (108 if etapa == 'sensibilidade_filtro' else 24)
    return dict(carteiras=len(auditorias), controles_exatos=controles, contabilidade=auditorias)


def executar(etapa):
    with exclusividade(etapa):
        ptr, p, f = contexto(etapa)
        destino = REG / etapa / 'auditorias' / str(time.time_ns())
        destino.mkdir(parents=True)
        codigos = fontes()
        for nome in codigos:
            q = destino / 'fontes' / nome
            q.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(RAIZ / nome, q)
        salvar_json(destino / 'inicio.json', dict(utc=agora(), fontes=codigos, execucao=ptr))
        fecho = ler_json(REG / etapa / 'fechamento.json')
        assert sha256(RAIZ / fecho['arquivo']) == fecho['sha256']
        conferir_arquivos(p, ler_json(p / 'fechamento.json')['arquivos'])
        resultado = auditar_lstm(p, f) if etapa == 'lstm_walkforward' else auditar_grade(etapa, p, f)
        conferir_arquivos(RAIZ, codigos)
        salvar_json(destino / 'resultado.json', dict(utc=agora(), situacao='aprovada', **resultado))
        salvar_json(REG / etapa / 'conferencia_posterior.json', dict(utc=agora(), situacao='aprovada',
                    arquivo=relativo(destino / 'resultado.json'), sha256=sha256(destino / 'resultado.json'),
                    inicio=relativo(destino / 'inicio.json'), fechamento=fecho))
        registrar_estado(etapa, 'auditado', **{k: v for k, v in resultado.items() if k != 'contabilidade'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('etapa', choices=['lstm_walkforward', 'sensibilidade_filtro', 'deslocamento_exposicao'])
    executar(parser.parse_args().etapa)
