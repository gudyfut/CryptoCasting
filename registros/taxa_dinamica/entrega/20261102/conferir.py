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
    ponteiro = ler(RAIZ / 'registros/taxa_dinamica/execucao.json')
    pasta = RAIZ / ponteiro['pasta']
    assert digest(pasta / 'congelamento.json') == ponteiro['congelamento_sha256']
    congelamento = ler(pasta / 'congelamento.json')['contrato']
    fontes = verificar(RAIZ, congelamento['fontes'])
    verificar(pasta / 'fontes', congelamento['fontes'])
    assert not ler(pasta / 'processo.json')['ativo']
    assert ler(pasta / 'progresso.json')['status'] == 'concluido'
    fechado = ler(RAIZ / 'registros/taxa_dinamica/fechamento.json')
    pub = RAIZ / fechado['publicacao']
    assert digest(pub / 'manifesto.json') == fechado['manifesto_sha256']
    publicados = verificar(pub, ler(pub / 'manifesto.json')['arquivos'])
    preservados = verificar(RAIZ, ler(RAIZ / 'registros/taxa_dinamica/preservacao_antes.json')['arquivos'])
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
        'scheduler_seis': [f'mamba16_scheduler_{s}' for s in seeds],
        'mamba16_seis': [f'estado16_{s}' for s in seeds],
        'scheduler_tres': [f'mamba16_scheduler_{s}' for s in seeds[:3]],
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
        dif = np.mean([(dados[f'mamba16_scheduler_{s}', parte].previsao.to_numpy() - dados[f'mamba16_scheduler_{s}', parte].alvo.to_numpy()) ** 2
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
            for a, b in zip(intervalos[str(largura)], r['contrastes'][parte]['scheduler_seis_menos_mamba16_seis']['ic95'][str(largura)]):
                perto(a, b)
        perto(float(dif.mean()), r['contrastes'][parte]['scheduler_seis_menos_mamba16_seis']['diferenca_mse_a_menos_b'])
        contrastes[parte] = {'delta_mse': float(dif.mean()), 'delta_relativo_pct': 100 * (medias[parte]['scheduler_seis']['mse'] / medias[parte]['mamba16_seis']['mse'] - 1), 'ic95': intervalos}
    trajetorias = []
    for s in seeds:
        chave = f'mamba16_scheduler_{s}'
        t = RAIZ / r['por_ajuste'][chave]['tentativa_origem']
        epocas, selecao = ler(t / 'epocas.json'), ler(t / 'selecao.json')
        assert digest(t / selecao['arquivo']) == selecao['sha256']
        assert min(epocas, key=lambda e: (e['mse_validacao'], e['epoca']))['epoca'] == selecao['epoca']
        taxa, melhor, ruins, parada, cortes = .0002, math.inf, 0, 0, []
        for e in epocas:
            assert e['taxa_usada'] == taxa
            if e['mse_validacao'] < melhor:
                melhor, ruins, parada = e['mse_validacao'], 0, 0
            else:
                ruins += 1
                parada += 1
            if ruins > 2:
                nova = max(taxa / 2, .000025)
                if nova < taxa:
                    cortes.append(e['epoca'])
                taxa, ruins = nova, 0
            assert e['taxa_proxima'] == taxa
        assert parada == 10 and len(epocas) < 100
        trajetorias.append({'seed': s, 'epocas': len(epocas), 'selecionada': selecao['epoca'], 'taxa_selecionada': epocas[selecao['epoca'] - 1]['taxa_usada'], 'cortes': cortes,
            'delta_mse_pct': {b: 100 * (metricas[chave, b]['mse'] / metricas[f'estado16_{s}', b]['mse'] - 1) for b in ('validacao', 'teste')}})
    # Comprova presença dos recibos de todas as 54 carteiras, sem repetir simulações.
    verificacoes = sorted(pub.glob('carteira/**/verificacao.json'))
    assert len(verificacoes) == 54
    for v in verificacoes:
        assert ler(v)  # Conteúdo e arquivos associados já conferidos no manifesto.
    anterior = ler(RAIZ / r['referencia_carteira']['arquivo'])
    assert digest(RAIZ / r['referencia_carteira']['arquivo']) == r['referencia_carteira']['sha256']
    carteiras = {}
    for parte in ('validacao', 'teste'):
        valores = [r['carteiras'][f'{parte}/base/smart/mamba16_scheduler_{s}']['retorno_liquido'] for s in seeds]
        carteiras[parte] = {'retorno_medio': float(np.mean(valores)), 'desvio_seeds': float(np.std(valores, ddof=1)),
            'seeds_lucrativas': sum(v > 0 for v in valores), 'referencia': anterior['medias'][parte]['base']['smart']['mamba16_seis'],
            'retornos_por_seed': dict(zip(map(str, seeds), valores))}
    resultado = {'utc': datetime.now(timezone.utc).isoformat(), 'execucao': ponteiro['id'], 'conferido': True,
        'script_sha256': digest(Path(__file__)), 'fontes_atuais_e_copiadas': fontes, 'arquivos_publicados': publicados, 'anteriores_preservados': preservados,
        'series': 59, 'novas': 6, 'carteiras_com_recibo': 54, 'medias': medias, 'contrastes': contrastes, 'trajetorias': trajetorias, 'smart_base': carteiras,
        'limites': ['Sem treino, inferência ou repetição do executor; recarga exata é a evidência congelada, não nova inferência nesta conferência.',
                   'IC temporal condicional aos modelos existentes; não mede integralmente incerteza de novos treinamentos.',
                   'Seeds iguais não garantem trajetórias CUDA bit a bit; não há controle real extra nesta rodada.',
                   '2024 seleção e 2025 já consultado; exploração retrospectiva.']}
    destino = DESTINO / 'conferencia.json'
    assert not destino.exists(), 'Preservar recibo anterior.'
    destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({'conferido': True, 'fontes': fontes, 'publicados': publicados, 'preservados': preservados, 'contrastes': contrastes, 'trajetorias': trajetorias}, ensure_ascii=False))


if __name__ == '__main__':
    executar()
