"""Custos: evidência pública de livro e sensibilidade com previsões congeladas, sem treino."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import platform
import time
import urllib.error
import urllib.request
from zipfile import ZipFile, ZIP_DEFLATED
import numpy as np
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, conferir_arquivos
from experimentos.generalizacao_moedas.avaliacao import carregar_mercado
from simulacao_operacoes.diaria_24h import simular, conferir

SEEDS = (42, 17, 2026)
CASOS = {'slip_0bp': (.0005, 0.), 'slip_05bp': (.0005, .00005),
         'slip_1bp': (.0005, .0001), 'slip_2bp': (.0005, .0002),
         'referencia_5bp': (.0005, .0005), 'fee_045_slip_5bp': (.00045, .0005)}


def vwap(niveis, quantidade):
    restante = quantidade; total = 0.; usados = 0
    for preco, qtd in niveis:
        tomada = min(restante, float(qtd)); total += tomada*float(preco)
        restante -= tomada; usados += 1
        if restante <= quantidade*1e-12:
            return total/quantidade, usados
    return None, usados


def conferir_vwap():
    assert vwap([['100', '1'], ['102', '2']], 2) == (101., 2)
    assert vwap([['100', '1']], 2)[0] is None
    assert vwap([['100', '2']], 1) == (100., 1)
    assert vwap([['100', '1'], ['98', '2']], 2) == (99., 2)


def consultar(simbolo):
    url = f'https://fapi.binance.com/fapi/v1/depth?symbol={simbolo}&limit=100'
    inicio = time.monotonic()
    req = urllib.request.Request(url, headers={'User-Agent': 'CryptoCasting-research-cost-audit', 'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(req, timeout=20) as resposta:
        corpo = resposta.read(); cab = {k: v for k, v in resposta.headers.items() if k.lower() in ('date', 'age', 'x-mbx-used-weight-1m')}
    q = json.loads(corpo); bids = np.array(q['bids'], dtype=float); asks = np.array(q['asks'], dtype=float)
    assert np.isfinite(bids).all() and np.isfinite(asks).all() and (bids>0).all() and (asks>0).all()
    assert np.all(np.diff(bids[:, 0])<0) and np.all(np.diff(asks[:, 0])>0) and bids[0, 0] < asks[0, 0]
    mid = float((bids[0, 0]+asks[0, 0])/2); medidas = []
    for nocional in (9500., 50000.):
        quantidade = nocional/mid
        compra, nc = vwap(asks, quantidade); venda, nv = vwap(bids, quantidade)
        medidas.append({'nocional_usdt_mid': nocional, 'compra_custo_mid_bp': (compra/mid-1)*10000 if compra else None,
            'venda_custo_mid_bp': (1-venda/mid)*10000 if venda else None,
            'compra_impacto_vs_ask_bp': (compra/asks[0, 0]-1)*10000 if compra else None,
            'venda_impacto_vs_bid_bp': (1-venda/bids[0, 0])*10000 if venda else None, 'niveis_compra': nc, 'niveis_venda': nv})
    return {'simbolo': simbolo, 'utc_consulta': agora(), 'url': url, 'http': 200, 'cabecalhos': cab,
            'duracao_requisicao_seg': time.monotonic()-inicio, 'E': q['E'], 'T': q['T'], 'lastUpdateId': q['lastUpdateId'],
            'mid': mid, 'spread_completo_bp': float((asks[0, 0]-bids[0, 0])/mid*10000), 'medidas': medidas}, corpo


def executar():
    conferir_vwap()
    reg = RAIZ/'registros/generalizacao_moedas'; cp = ler_json(reg/'comparacao_quatro_moedas.json')
    assert sha256(RAIZ/cp['arquivo']) == cp['sha256']; anterior = ler_json(RAIZ/cp['arquivo'])
    ptr = ler_json(reg/'execucao.json'); p = RAIZ/ptr['pasta']; assert sha256(p/'congelamento.json') == ptr['congelamento_sha256']
    f = ler_json(p/'congelamento.json'); btc = RAIZ/f['referencia']['pasta']; fb = ler_json(btc/'congelamento.json')
    fontes = {Path(__file__).relative_to(RAIZ).as_posix(): sha256(__file__),
              'simulacao_operacoes/diaria_24h.py': sha256(RAIZ/'simulacao_operacoes/diaria_24h.py'),
              'simulacao_operacoes/envelopes_marcacao.py': sha256(RAIZ/'simulacao_operacoes/envelopes_marcacao.py'),
              'experimentos/generalizacao_moedas/avaliacao.py': sha256(RAIZ/'experimentos/generalizacao_moedas/avaliacao.py')}
    dest = reg/'custos'/agora().replace(':', '').replace('+', '_'); dest.mkdir(parents=True, exist_ok=False)
    plano = {'utc': agora(), 'autorizacao': 'Pesquisador solicitou verificar realismo de slippage e taxas, sem novos treinamentos, em10/11/2026.',
        'fontes': fontes, 'pais': anterior['referencias'], 'receita_original': ptr,
        'escopo': 'Sensibilidade contábil mantendo sinais/filtro/horários/gestão/candles/previsões. Somente taxa e slippage variam. Não selecionar cenário pelo lucro.',
        'casos': {k: {'comissao_por_lado': v[0], 'slippage_por_lado': v[1]} for k, v in CASOS.items()},
        'ajustes_novos': 0, 'carteiras_previstas': 144, 'seeds': list(SEEDS), 'fases': ['validacao', 'teste'],
        'livro': {'amostras_por_moeda': 12, 'intervalo_segundos': 5, 'limite_niveis': 100, 'nocionais_usdt_mid': [9500, 50000],
            'limites': 'Amostra atual curta, sem ordens reais; VWAP estático vs midpoint e melhor oferta. Não mede latência, cancelamentos ou slippage histórico2024/2025; RPI não aparece no endpoint.'},
        'taxas': {'fonte': 'https://www.binance.com/en/support/faq/detail/360033544231',
            'conclusao': 'Exemplo oficial .05% taker/.02% maker e desconto BNB10%; FAQ declara valores hipotéticos. Tabela atual pública retornou No records found. Não confirmar tarifa específica de conta ou histórico2024/2025.',
            'tabela': 'https://www.binance.com/en/fee/futureFee', 'api_conta_nao_acessada': '/fapi/v1/commissionRate',
            'maker': 'Não simular maker com preenchimento garantido. .045% é sensibilidade de desconto equivalente em USDT; não simula carteiraBNB ou comprova elegibilidade.'}}
    salvar_json(dest/'plano.json', plano); print('PLANO', dest, flush=True)
    livros = []; falhas = []
    with ZipFile(dest/'livros_publicos.zip', 'w', ZIP_DEFLATED) as z:
        with ThreadPoolExecutor(max_workers=4) as pool:
            for amostra in range(12):
                futuros = {s: pool.submit(consultar, s) for s in ('BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT')}
                bloqueio = False
                for simbolo, futuro in futuros.items():
                    try:
                        obs, corpo = futuro.result(); obs['amostra'] = amostra
                        livros.append(obs); z.writestr(f'{simbolo}_{amostra:02d}.json', corpo)
                    except Exception as ex:
                        falhas.append({'simbolo': simbolo, 'amostra': amostra, 'utc': agora(), 'erro': str(ex)})
                        if isinstance(ex, urllib.error.HTTPError) and ex.code in (403, 418, 429, 451): bloqueio = True
                print('LIVRO', amostra+1, len(livros), len(falhas), flush=True)
                if bloqueio: break
                if amostra<11: time.sleep(5)
    salvar_json(dest/'observacoes_livro.json', {'amostras': livros, 'falhas': falhas})
    receita = {'BTC': (btc, fb['configuracao'], fb['mercado_minuto'])}
    for moeda in ('ETH', 'BNB', 'XRP'):
        m = f['moedas'][moeda+'USDT']; receita[moeda] = (RAIZ/anterior['referencias'][moeda]['pasta'], m['configuracao'], m['mercado'])
    resultados = []; curvas = {}; preservados = {}; capital_ordens = {}; inicio = time.monotonic()
    with ZipFile(dest/'carteiras_sensibilidade.zip', 'w', ZIP_DEFLATED) as z:
        for moeda, (base, cfg, mptr) in receita.items():
            assert sha256(base/'fechamento.json') == anterior['referencias'][moeda]['fechamento_sha256']
            fecho = ler_json(base/'fechamento.json'); conferir_arquivos(base, fecho['arquivos'])
            preservados[moeda] = {q.relative_to(RAIZ).as_posix(): sha256(q) for q in (base/'fechamento.json', base/'publicacao/resumo.json')}
            mercado = carregar_mercado(mptr); nocionais = []
            for fase in ('validacao', 'teste'):
                for seed in SEEDS:
                    obs = np.load(base/'publicacao/previsoes'/f'{fase}_{seed}.npz')
                    velha = base/'publicacao/carteiras'/fase/str(seed)/'base'
                    original = ler_json(velha/'resultado.json')
                    nocionais.extend(o['quantidade']*o['preco_entrada'] for o in original['operacoes'])
                    for nome, (fee, slip) in CASOS.items():
                        regras = deepcopy(cfg['operacoes']); regras.update(comissao_por_lado=fee, slippage_por_lado=slip)
                        try:
                            r, cv = simular(obs['origens_ms'], obs['previsoes'], obs['ultimo_close'], mercado, regras, {'lado': 0, 'slippage_multiplicador': 1})
                            conferir(r, cv, regras)
                            assert r['metricas']['operacoes'] == original['metricas']['operacoes'], 'Custos alteraram atividade por limites de saldo: declarar separadamente'
                            assert all(a['origem_ms'] == b['origem_ms'] and a['lado'] == b['lado'] for a, b in zip(r['operacoes'], original['operacoes']))
                            if nome == 'referencia_5bp':
                                ant = np.load(velha/'curva.npz')['saldos_diarios']
                                np.testing.assert_allclose(cv['saldos_diarios'], ant, atol=1e-7, rtol=0)
                                for chave, v in original['metricas'].items():
                                    if v is not None: np.testing.assert_allclose(r['metricas'][chave], v, atol=1e-7, rtol=1e-12)
                            linha = {'moeda': moeda, 'fase': fase, 'seed': seed, 'caso': nome, 'situacao': 'conferido', 'metricas': r['metricas']}
                            z.writestr(f'{moeda}/{fase}/{seed}/{nome}.json', json.dumps(r, ensure_ascii=False, allow_nan=False))
                            curvas[f'{moeda}_{fase}_{seed}_{nome}'] = cv['saldos_diarios']
                            del cv
                        except Exception as ex:
                            linha = {'moeda': moeda, 'fase': fase, 'seed': seed, 'caso': nome, 'situacao': 'falha_preservada', 'erro': str(ex)}
                        resultados.append(linha); print('CARTEIRA', len(resultados), moeda, fase, seed, nome, linha['situacao'], flush=True)
                conferir_arquivos(RAIZ, fontes)
            capital_ordens[moeda] = {'n': len(nocionais), 'min': float(min(nocionais)), 'mediana': float(np.median(nocionais)), 'max': float(max(nocionais))}
            del mercado
    np.savez_compressed(dest/'saldos_sensibilidade.npz', **curvas)
    salvar_json(dest/'carteiras.json', resultados)
    assert len(resultados) == 144
    medias = {}
    for moeda in receita:
        medias[moeda] = {}
        for fase in ('validacao', 'teste'):
            medias[moeda][fase] = {}
            for nome in CASOS:
                itens = [q for q in resultados if q['moeda'] == moeda and q['fase'] == fase and q['caso'] == nome]
                assert len(itens) == 3
                if all(q['situacao'] == 'conferido' for q in itens):
                    vals = [q['metricas'] for q in itens]
                    medias[moeda][fase][nome] = {k: float(np.mean([v[k] for v in vals])) for k in vals[0] if all(v[k] is not None for v in vals)}
                else: medias[moeda][fase][nome] = {'falha': True}
        conferir_arquivos(RAIZ, preservados[moeda])
    resumo_livro = {}
    for simbolo in ('BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT'):
        itens = [x for x in livros if x['simbolo'] == simbolo]; saida = {'n': len(itens), 'updates_distintos': len({x['lastUpdateId'] for x in itens}), 'nocionais': {}}
        for nocional in (9500., 50000.):
            custos = [v[k] for x in itens for v in x['medidas'] if v['nocional_usdt_mid'] == nocional for k in ('compra_custo_mid_bp', 'venda_custo_mid_bp') if v[k] is not None]
            saida['nocionais'][str(nocional)] = {'n_lados_preenchidos': len(custos), 'mediana_bp': float(np.median(custos)) if custos else None, 'max_bp': float(max(custos)) if custos else None,
                'mediana_pct': float(np.median(custos)/100) if custos else None, 'max_pct': float(max(custos)/100) if custos else None}
        resumo_livro[simbolo] = saida
    conferido = all(q['situacao'] == 'conferido' for q in resultados)
    resumo = {'utc': agora(), 'situacao': 'conferido' if conferido else 'concluido_com_falhas', 'plano_sha256': sha256(dest/'plano.json'), 'duracao_sensibilidade_seg': time.monotonic()-inicio,
        'ambiente': {'python': platform.python_version(), 'numpy': np.__version__}, 'fontes': fontes, 'novos_treinos': 0, 'carteiras': len(resultados),
        'livro': resumo_livro, 'nocionais_operacoes_originais': capital_ordens, 'medias_tres_seeds': medias,
        'limites': 'Custos são hipóteses, não foram escolhidos por lucro. Livro atual estático curto não identifica execução2024/2025 nem a00:01UTC. Candle1m não contém spread/profundidade; slippage não foi medido historicamente. Fee de conta não consultada. Zero slippage é limite otimista com ticks/fees/funding mantidos. Redução de feeBNB é equivalência USDT sem contabilizar estoqueBNB. A política continua encerrando e reabrindo cada24h; retenção é outra hipótese. Resultados antigos preservados.'}
    salvar_json(dest/'resumo.json', resumo)
    (dest/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    salvar_json(dest/'fechamento.json', {'utc': agora(), 'arquivos': {q.name: sha256(q) for q in dest.iterdir() if q.is_file() and q.name != 'fechamento.json'}})
    salvar_json(reg/'custos/ultima.json', {'arquivo': (dest/'resumo.json').relative_to(RAIZ).as_posix(), 'sha256': sha256(dest/'resumo.json')})
    print('CONCLUIDO', dest, resumo['situacao'], flush=True)


if __name__ == '__main__': executar()
