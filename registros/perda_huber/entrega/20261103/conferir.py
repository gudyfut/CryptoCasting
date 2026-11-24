"""Conferência posterior somente de leitura; não importa executores ou modelos."""
from pathlib import Path
import hashlib
import json
import math
from datetime import datetime, timezone
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
DESTINO = Path(__file__).resolve().parent


def ler(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for bloco in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(bloco)
    return h.hexdigest()


def verificar(base, mapa):
    for nome, esperado in mapa.items():
        assert digest(base / nome) == esperado, nome
    return len(mapa)


def perto(a, b):
    assert math.isclose(a, b, rel_tol=1e-11, abs_tol=1e-14), (a, b)


def executar():
    ponteiro = ler(RAIZ / 'registros/perda_huber/execucao.json')
    pasta = RAIZ / ponteiro['pasta']
    assert digest(pasta / 'congelamento.json') == ponteiro['congelamento_sha256']
    congelamento = ler(pasta / 'congelamento.json')['contrato']
    fontes = verificar(RAIZ, congelamento['fontes'])
    verificar(pasta / 'fontes', congelamento['fontes'])
    assert not ler(pasta / 'processo.json')['ativo']
    assert ler(pasta / 'progresso.json')['status'] == 'concluido'
    fechado = ler(RAIZ / 'registros/perda_huber/fechamento.json')
    pub = RAIZ / fechado['publicacao']
    assert digest(pub / 'manifesto.json') == fechado['manifesto_sha256']
    publicados = verificar(pub, ler(pub / 'manifesto.json')['arquivos'])
    preservados = verificar(RAIZ, ler(RAIZ / 'registros/perda_huber/preservacao_antes.json')['arquivos'])
    r = ler(pub / 'resultados.json')
    assert len(r['por_ajuste']) == 59 and len(r['carteiras']) == 54
    seeds = (17, 42, 2026, 7, 123, 31415)
    dados, metricas = {}, {}
    for chave, ajuste in r['por_ajuste'].items():
        tentativa = RAIZ / ajuste['tentativa_origem']
        conclusao = ler(tentativa / 'conclusao.json')
        assert conclusao['status'] == 'concluido'
        verificar(tentativa, conclusao['arquivos'])
        for parte in ('validacao', 'teste', 'operacional'):
            q = pd.read_parquet(tentativa / f'previsoes_{parte}.parquet')
            assert q.origem_utc.is_monotonic_increasing and not q.origem_utc.duplicated().any()
            assert np.isfinite(q.previsao).all()
            assert ((q.destino_utc - q.origem_utc) == pd.Timedelta(hours=24)).all()
            dados[chave, parte] = q
            if parte == 'operacional':
                continue
            erro = [float(p) - float(y) for p, y in zip(q.previsao, q.alvo)]
            mse = math.fsum(v * v for v in erro) / len(erro)
            mae = math.fsum(abs(v) for v in erro) / len(erro)
            metricas[chave, parte] = {'mse': mse, 'mae': mae, 'rmse': math.sqrt(mse)}
            for nome, valor in metricas[chave, parte].items():
                perto(valor, ajuste['metricas'][parte][nome])
    colunas = ['indice_candle', 'origem_utc', 'destino_utc', 'close', 'preco_destino', 'alvo']
    for (chave, parte), q in dados.items():
        pd.testing.assert_frame_equal(q[colunas].reset_index(drop=True), dados['naive', parte][colunas].reset_index(drop=True), check_exact=True)
    grupos = {
        'huber_seis': [f'mamba16_huber_{s}' for s in seeds],
        'mamba16_seis': [f'estado16_{s}' for s in seeds],
        'huber_tres': [f'mamba16_huber_{s}' for s in seeds[:3]],
        'mamba16_tres': [f'estado16_{s}' for s in seeds[:3]],
        'lstm_tres': [f'lstm_{s}' for s in seeds[:3]], 'naive': ['naive'], 'arima': ['arima']}
    medias, contrastes = {}, {}
    for parte in ('validacao', 'teste'):
        medias[parte] = {}
        for nome, chaves in grupos.items():
            medias[parte][nome] = {m: math.fsum(metricas[k, parte][m] for k in chaves) / len(chaves) for m in ('mse', 'mae', 'rmse')}
            for m, v in medias[parte][nome].items():
                perto(v, r['medias'][parte][nome]['metricas'][m])
        # Reamostragem implementada aqui, sem chamar o publicador congelado.
        dif = np.mean([(dados[f'mamba16_huber_{s}', parte].previsao.to_numpy() - dados[f'mamba16_huber_{s}', parte].alvo.to_numpy()) ** 2
                       - (dados[f'estado16_{s}', parte].previsao.to_numpy() - dados[f'estado16_{s}', parte].alvo.to_numpy()) ** 2 for s in seeds], axis=0)
        dias = pd.DataFrame({'d': dif}, index=pd.DatetimeIndex(dados['naive', parte].origem_utc)).resample('D').agg(['sum', 'count'])['d']
        somas, contagens = dias['sum'].to_numpy(), dias['count'].to_numpy()
        intervalos = {}
        for largura in (7, 14, 28):
            rng = np.random.default_rng(20261020 + largura)
            estimativas = []
            for _ in range(2000):
                inicios = rng.integers(len(dias), size=math.ceil(len(dias) / largura))
                ix = np.concatenate([(np.arange(largura) + i) % len(dias) for i in inicios])[:len(dias)]
                estimativas.append(float(somas[ix].sum() / contagens[ix].sum()))
            intervalos[str(largura)] = np.quantile(estimativas, [.025, .975]).tolist()
            for a, b in zip(intervalos[str(largura)], r['contrastes'][parte]['huber_seis_menos_mamba16_seis']['ic95'][str(largura)]):
                perto(a, b)
        perto(float(dif.mean()), r['contrastes'][parte]['huber_seis_menos_mamba16_seis']['diferenca_mse_a_menos_b'])
        contrastes[parte] = {'delta_mse': float(dif.mean()), 'delta_relativo_pct': 100 * (medias[parte]['huber_seis']['mse'] / medias[parte]['mamba16_seis']['mse'] - 1), 'ic95': intervalos}
    trajetorias = []
    for seed in seeds:
        chave = f'mamba16_huber_{seed}'
        t = RAIZ / r['por_ajuste'][chave]['tentativa_origem']
        epocas, selecao = ler(t / 'epocas.json'), ler(t / 'selecao.json')
        assert digest(t / selecao['arquivo']) == selecao['sha256']
        assert min(epocas, key=lambda e: (e['mse_validacao'], e['epoca']))['epoca'] == selecao['epoca']
        assert r['por_ajuste'][chave]['metricas']['validacao']['mse'] == selecao['mse_validacao']
        assert ler(t / 'resultado.json')['recarga_exata']
        assert ler(t / 'resultado.json')['perda'] == congelamento['configuracao']['perda']
        melhor, parada = math.inf, 0
        for e in epocas:
            assert e['taxa_aprendizado'] == .0002
            assert math.isfinite(e['perda_treino_padronizada'])
            assert 'mse_treino_padronizado' not in e
            if e['mse_validacao'] < melhor: melhor, parada = e['mse_validacao'], 0
            else: parada += 1
        assert len(epocas) <= 100
        if len(epocas) < 100: assert parada == 10
        trajetorias.append({'seed': seed, 'epocas': len(epocas), 'selecionada': selecao['epoca'],
            'delta_mse_pct': {b: 100 * (metricas[chave, b]['mse'] / metricas[f'estado16_{seed}', b]['mse'] - 1) for b in ('validacao', 'teste')}})
    # Comprova presença dos recibos de todas as 54 carteiras, sem repetir simulações.
    verificacoes = sorted(pub.glob('carteira/**/verificacao.json'))
    assert len(verificacoes) == 54
    for v in verificacoes:
        assert ler(v)['status'] == 'conferido'
    anterior = ler(RAIZ / r['referencia_carteira']['arquivo'])
    assert digest(RAIZ / r['referencia_carteira']['arquivo']) == r['referencia_carteira']['sha256']
    carteiras = {}
    for parte in ('validacao', 'teste'):
        valores = [r['carteiras'][f'{parte}/base/smart/mamba16_huber_{s}']['retorno_liquido'] for s in seeds]
        carteiras[parte] = {'retorno_medio': float(np.mean(valores)), 'desvio_seeds': float(np.std(valores, ddof=1)),
            'seeds_lucrativas': sum(v > 0 for v in valores), 'referencia': anterior['medias'][parte]['base']['smart']['mamba16_seis'],
            'retornos_por_seed': dict(zip(map(str, seeds), valores))}
    resultado = {'utc': datetime.now(timezone.utc).isoformat(), 'execucao': ponteiro['id'], 'conferido': True,
        'script_sha256': digest(Path(__file__)), 'fontes_atuais_e_copiadas': fontes, 'arquivos_publicados': publicados, 'anteriores_preservados': preservados,
        'series': 59, 'novas': 6, 'carteiras_com_recibo': 54, 'medias': medias, 'contrastes': contrastes, 'trajetorias': trajetorias, 'smart_base': carteiras, 'comparacao_detalhada': detalhar(r, anterior, dados, seeds, pub),
        'limites': ['Sem treino, inferência ou repetição do executor; recarga exata é a evidência congelada, não nova inferência nesta conferência.',
                   'IC temporal condicional aos modelos existentes; não mede integralmente incerteza de novos treinamentos.',
                   'Seeds iguais não garantem trajetórias CUDA bit a bit; não há controle real extra nesta rodada.',
                   '2024 seleção e 2025 já consultado; exploração retrospectiva.']}
    destino = DESTINO / 'conferencia.json'
    assert not destino.exists(), 'Preservar recibo anterior.'
    destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({'conferido': True, 'fontes': fontes, 'publicados': publicados, 'preservados': preservados, 'contrastes': contrastes, 'trajetorias': trajetorias, 'comparacao_detalhada': resultado['comparacao_detalhada']}, ensure_ascii=False))


def diagnostico(q):
    y, p = q.alvo.to_numpy(float), q.previsao.to_numpy(float)
    e = p - y
    a = np.abs(e)
    recalls = [np.mean(np.sign(p[y > 0]) == 1), np.mean(np.sign(p[y < 0]) == -1)]
    return {'n': len(q), 'mse': float(np.mean(e ** 2)), 'rmse': float(np.sqrt(np.mean(e ** 2))),
            'mae': float(a.mean()), 'mediana_erro_absoluto': float(np.median(a)),
            'p95_erro_absoluto': float(np.quantile(a, .95)), 'vies': float(e.mean()),
            'acuracia_direcional': float(np.mean(np.sign(p) == np.sign(y))),
            'acerto_balanceado_direcional': float(np.mean(recalls)),
            'pearson': float(np.corrcoef(p, y)[0, 1]),
            'spearman': float(pd.Series(p).corr(pd.Series(y), method='spearman')),
            'vitorias_naive': float(np.mean(a < abs(y))),
            'desvio_previsao': float(p.std()), 'desvio_alvo': float(y.std()),
            'fracao_previsoes_alta': float(np.mean(p > 0)),
            'fracao_reais_alta': float(np.mean(y > 0))}


def agregar(vs):
    return {k: float(np.mean([v[k] for v in vs])) for k in vs[0] if isinstance(vs[0][k], (int, float)) and not isinstance(vs[0][k], bool)}


def detalhar(r, anterior, dados, seeds, pub):
    grupos = {'referencia': [f'estado16_{s}' for s in seeds], 'huber': [f'mamba16_huber_{s}' for s in seeds]}
    ds, precos, trimestres, spots, smart = {}, {}, {}, {}, {}
    for parte in ('validacao', 'teste'):
        ds[parte], precos[parte], trimestres[parte], smart[parte] = {}, {}, {}, {}
        for nome, chaves in grupos.items():
            ds[parte][nome] = {}
            for diario in (False, True):
                vs = []
                for k in chaves:
                    q = dados[k, parte]
                    if diario:
                        q = q.loc[pd.DatetimeIndex(q.origem_utc).hour == 0]
                    d = diagnostico(q); vs.append(d)
                    if not diario:
                        for campo in ('mse', 'mae', 'rmse', 'vies', 'acuracia_direcional', 'acerto_balanceado_direcional'):
                            perto(d[campo], r['por_ajuste'][k]['metricas'][parte][campo])
                ds[parte][nome]['diario' if diario else 'horario'] = agregar(vs)
            pv = []
            for k in chaves:
                q = dados[k, parte]; e = q.close.to_numpy() * np.exp(q.previsao.to_numpy()) - q.preco_destino.to_numpy()
                pv.append({'rmse_usdt': float(np.sqrt(np.mean(e ** 2))), 'mae_usdt': float(np.mean(abs(e))),
                           'mape_preco_pct': float(100 * np.mean(abs(e / q.preco_destino.to_numpy())))})
            precos[parte][nome] = agregar(pv)
            trimestres[parte][nome] = {}
            for trimestre in (1, 2, 3, 4):
                vs = [diagnostico(dados[k, parte].loc[pd.DatetimeIndex(dados[k, parte].origem_utc).quarter == trimestre]) for k in chaves]
                trimestres[parte][nome][str(trimestre)] = agregar(vs)
        for cenario in ('ideal', 'base', 'agravado'):
            smart[parte][cenario] = {}
            for nome, chaves in grupos.items():
                for politica in (['smart', 'smart_constante'] if parte == 'teste' else ['smart']):
                    vs = [r['carteiras'][f'{parte}/{cenario}/{politica}/{k}'] if nome == 'huber'
                          else anterior['por_simulacao'][f'{parte}/{cenario}/{politica}/{k}'] for k in chaves]
                    a = agregar(vs); retornos = [v['retorno_liquido'] for v in vs]
                    a.update(desvio_retorno_seeds=float(np.std(retornos, ddof=1)),
                             seeds_lucrativas=sum(v > 0 for v in retornos), retorno_min=min(retornos), retorno_max=max(retornos))
                    smart[parte][cenario][f'{nome}/{politica}'] = a
    for nome, chaves in grupos.items():
        spots[nome] = {}
        for perfil in ('base', 'agravado', 'bruto_mesmos_sinais'):
            vs = [r['por_ajuste'][k]['spot'][perfil] for k in chaves]
            a = agregar(vs); retornos = [v['retorno_liquido'] for v in vs]
            a.update(desvio_retorno_seeds=float(np.std(retornos, ddof=1)),
                     seeds_lucrativas=sum(v > 0 for v in retornos), retorno_min=min(retornos), retorno_max=max(retornos))
            spots[nome][perfil] = a
    # Reconstrói saldos a partir dos lançamentos, sem gerar ordens ou nova simulação.
    for caminho in pub.glob('carteira/**/ordens.json'):
        resumo = ler(caminho.parent / 'resumo.json'); caixa, btc = 10000., 0.
        custo = 0.
        for o in ler(caminho):
            perto(caixa, o['caixa_antes']); perto(btc, o['btc_antes'])
            if o['status'] == 'executada':
                perto(o['notional_usdt'], o['quantidade_bruta'] * o['preco_execucao'])
                if o['lado'] == 'comprar':
                    assert o['comissao_ativo'] == 'BTC'
                    caixa -= o['notional_usdt']; btc += o['quantidade_bruta'] - o['comissao_quantidade']
                else:
                    assert o['comissao_ativo'] == 'USDT'
                    caixa += o['notional_usdt'] - o['comissao_quantidade']; btc -= o['quantidade_bruta']
                custo += o['comissao_usdt']
            perto(caixa, o['caixa_depois']); perto(btc, o['btc_depois'])
        perto(caixa, resumo['caixa_final']); perto(btc, resumo['btc_residual'])
        perto(caixa + resumo['valor_residual_usdt'], resumo['capital_final'])
        perto(custo, resumo['comissoes_usdt'])
    return {'diagnosticos': ds, 'precos_derivados': precos, 'trimestres': trimestres,
            'spot_r0': spots, 'smart': smart, 'carteiras_reconstruidas_de_ordens': 54,
            'benchmarks': {b: anterior['medias'][b]['base']['benchmarks'] for b in ('validacao', 'teste')}}

if __name__ == '__main__':
    executar()
