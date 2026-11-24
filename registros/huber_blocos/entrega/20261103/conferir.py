"""Conferência posterior de leitura; não importa nem executa treinadores."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
DEST = Path(__file__).resolve().parent


def ler(p):
    return json.loads(p.read_text(encoding='utf-8'))


def sha(p):
    with p.open('rb') as arq:
        return hashlib.file_digest(arq, 'sha256').hexdigest()


def igual(a, b):
    assert math.isclose(float(a), float(b), rel_tol=1e-10, abs_tol=1e-12), (a, b)


def igual_caixa(a, b):
    # Equações algébricas equivalentes acumulam arredondamento ao zerar o caixa.
    assert math.isclose(float(a), float(b), rel_tol=1e-10, abs_tol=1e-8), (a, b)


def conferir_arquivos(base, mapa):
    for nome, esperado in mapa.items():
        p = base / nome
        assert p.resolve().is_relative_to(base.resolve())
        assert sha(p) == esperado, str(p)
    return len(mapa)


def intervalo(blocos, cfg):
    # Reimplementação independente: agrupa erros por data e reamostra índices.
    diarios = []
    for q in blocos.values():
        datas = pd.DatetimeIndex(q['origens']).normalize()
        unicas, ix = np.unique(datas.asi8, return_inverse=True)
        contagens = np.bincount(ix, minlength=len(unicas))
        somas = np.array([np.bincount(ix, weights=linha, minlength=len(unicas))
                          for linha in q['huber'] - q['mse']])
        diarios.append((somas, contagens))
    saida = {}
    for largura in cfg['dias']:
        g = np.random.default_rng(cfg['seed'] + largura)
        amostras = []
        for _ in range(cfg['replicas']):
            seeds = g.integers(0, 8, 8)
            valores = []
            for somas, contagens in diarios:
                inicios = g.integers(0, len(contagens), math.ceil(len(contagens)/largura))
                indices = np.concatenate([(i + np.arange(largura)) % len(contagens)
                                           for i in inicios])[:len(contagens)]
                valores.append(somas[seeds][:, indices].sum() / (8*contagens[indices].sum()))
            amostras.append(np.mean(valores))
        saida[str(largura)] = np.quantile(amostras, [.025, .975]).tolist()
    return saida


def principal():
    ponteiro = ler(RAIZ/'registros/huber_blocos/execucao.json')
    p = RAIZ/ponteiro['pasta']
    assert sha(p/'congelamento.json') == ponteiro['congelamento_sha256']
    f = ler(p/'congelamento.json')['contrato']
    pub = p/ler(p/'publicacao.json')['pasta']
    assert sha(pub/'manifesto.json') == ler(p/'publicacao.json')['manifesto_sha256']
    verificacoes = {'publicacao': conferir_arquivos(pub, ler(pub/'manifesto.json')['arquivos']),
                    'fontes_atuais': conferir_arquivos(RAIZ, f['fontes']),
                    'fontes_congeladas': conferir_arquivos(p/'fontes', f['fontes'])}
    print('Publicação e fontes íntegras.', flush=True)
    verificacoes['preservados'] = conferir_arquivos(
        RAIZ, ler(RAIZ/'registros/huber_blocos/preservacao_antes.json')['arquivos'])
    print('Preservação anterior íntegra.', flush=True)
    r = ler(pub/'resultados.json'); cfg = f['configuracao']
    assert len(r['por_ajuste']) == 64 and len(r['carteiras']) == 408
    assert len(r['auditoria_checkpoint']) == 66
    assert len(list((p/'celulas').glob('*/tentativa_*/conclusao.json'))) == 64
    assert len(list((p/'controles').glob('*/tentativa_*/conclusao.json'))) == 2
    assert len(list((p/'baselines').glob('*/naive/tentativa_*/conclusao.json'))) == 4
    pares = {}; calculados = {}; detalhes_seeds = {}
    for b in cfg['blocos']:
        pares[b] = {}
        for perda in ('mse', 'huber'):
            linhas = []
            for s in cfg['seeds']:
                chave = f'{b}_{perda}_{s}'
                t = RAIZ/r['por_ajuste'][chave]['tentativa_origem']
                verificacoes[chave] = conferir_arquivos(t, ler(t/'conclusao.json')['arquivos'])
                sel = ler(t/'selecao.json'); es = ler(t/'epocas.json')
                melhor = min(es, key=lambda x: (x['mse_validacao'], x['epoca']))
                assert melhor['epoca'] == sel['epoca']
                igual(melhor['mse_validacao'], sel['mse_validacao'])
                assert sha(t/sel['arquivo']) == sel['sha256']
                for parte in ('validacao', 'teste'):
                    q = pd.read_parquet(t/f'previsoes_{parte}.parquet')
                    y = q.alvo.to_numpy(); v = q.previsao.to_numpy(); e = v-y
                    assert np.isfinite(e).all()
                    assert (pd.DatetimeIndex(q.destino_utc)-pd.DatetimeIndex(q.origem_utc)
                            == pd.Timedelta(hours=24)).all()
                    fim = pd.Timestamp(cfg['blocos'][b][parte][1])
                    assert (pd.DatetimeIndex(q.destino_utc) < fim).all()
                    np.testing.assert_allclose(y, np.log(q.preco_destino/q.close), rtol=1e-10, atol=1e-14)
                    met = {'mse': math.fsum(float(x)**2 for x in e)/len(e),
                           'mae': math.fsum(abs(float(x)) for x in e)/len(e)}
                    for k, valor in met.items():
                        igual(valor, r['por_ajuste'][chave]['metricas'][parte][k])
                    calculados[b, perda, s, parte] = met
                    if parte == 'teste':
                        if 'origens' in pares[b]:
                            assert q.origem_utc.tolist() == pares[b]['origens'].tolist()
                            np.testing.assert_array_equal(y, pares[b]['alvo'])
                        else:
                            pares[b].update(origens=q.origem_utc, alvo=y)
                        linhas.append(e**2)
            pares[b][perda] = np.array(linhas)
        for perda in ('mse', 'huber'):
            for parte in ('validacao', 'teste'):
                for metrica in ('mse', 'mae'):
                    valor = np.mean([calculados[b, perda, s, parte][metrica] for s in cfg['seeds']])
                    igual(valor, r['medias_por_bloco'][b][parte][perda][metrica])
        for parte in ('validacao', 'teste'):
            q = pd.read_parquet(p/f'baselines/{b}/naive/tentativa_001/previsoes_{parte}.parquet')
            assert (q.previsao == 0).all()
            igual(np.mean(q.alvo.to_numpy()**2), r['naives'][b]['metricas'][parte]['mse'])
    print('Previsões, alvos, janelas e médias conferidos.', flush=True)
    for parte in ('validacao', 'teste'):
        for perda in ('mse', 'huber'):
            media = np.mean([calculados[b, perda, s, parte]['mse']
                             for b in cfg['blocos'] for s in cfg['seeds']])
            igual(media, r['medias_globais'][parte][perda]['mse'])
    cis = intervalo(pares, cfg['bootstrap'])
    np.testing.assert_allclose(list(cis.values()),
                               list(r['contrastes']['teste']['ic95_seeds_e_tempo'].values()),
                               rtol=1e-10, atol=1e-15)
    for s in cfg['seeds']:
        valores = {v: float(np.mean([calculados[b, v, s, 'teste']['mse'] for b in cfg['blocos']]))
                   for v in ('mse', 'huber')}
        detalhes_seeds[str(s)] = dict(valores, mudanca_percentual=100*(valores['huber']/valores['mse']-1))
    custos = f['carteira']['contrato']['configuracao']['custos']
    ordens_total = 0
    for chave, resumo in r['carteiras'].items():
        d = pub/'carteiras'/chave
        assert ler(d/'verificacao.json')['status'] == 'conferido'
        caixa = 10000.; btc = 0.; taxas = 0.; slip = 0.; n = 0
        c = custos[resumo['cenario']]
        ordens = ler(d/'ordens.json')
        for o in ordens:
            igual_caixa(caixa, o['caixa_antes']); igual(btc, o['btc_antes'])
            preco = o['preco_meio']*(1+c['slippage'] if o['lado']=='comprar' else 1-c['slippage'])
            igual(preco, o['preco_execucao'])
            if o['status'] == 'executada':
                qt = o['quantidade_bruta']; notional = qt*preco
                igual(notional, o['notional_usdt'])
                if o['lado'] == 'comprar':
                    caixa -= notional; btc += qt*(1-c['taxa'])
                else:
                    btc -= qt; caixa += notional*(1-c['taxa'])
                taxas += notional*c['taxa']; slip += qt*abs(preco-o['preco_meio']); n += 1
            assert caixa >= -1e-8 and btc >= -1e-12
            igual_caixa(caixa, o['caixa_depois']); igual(btc, o['btc_depois'])
        igual_caixa(caixa, resumo['caixa_final']); igual(btc, resumo['btc_residual'])
        final = caixa + btc*ordens[-1]['preco_meio']
        igual(final, resumo['capital_final']); igual(final/10000-1, resumo['retorno_liquido'])
        igual(taxas, resumo['comissoes_usdt']); igual(slip, resumo['slippage_usdt'])
        assert n == resumo['ordens_executadas']
        diarios = pd.read_parquet(d/'diarios.parquet')
        igual(diarios.retorno_log.sum(), math.log(final/10000))
        ordens_total += len(ordens)
    saida = {'utc': datetime.now(timezone.utc).isoformat(), 'execucao': ponteiro['id'],
             'situacao': 'conferido_independentemente', 'verificacoes_arquivos': verificacoes,
             'ajustes_principais': 64, 'controles': 2, 'naives': 4, 'carteiras': 408,
             'ordens_reconstruidas': ordens_total, 'ic95_teste_recalculado': cis,
             'por_seed_teste_media_quatro_blocos': detalhes_seeds,
             'limites': ['Sem novos treinos, inferências ou simulações.',
                        'Recarga CUDA e risco minuto a minuto constam dos recibos congelados; nesta fase foram verificados os hashes e reconstruídos os lançamentos salvos.',
                        'Não substitui publicações ou recibos congelados.']}
    (DEST/'conferencia.json').write_text(json.dumps(saida, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({k:v for k,v in saida.items() if k!='verificacoes_arquivos'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    principal()
