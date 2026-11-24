"""Coleta pública USD-M por símbolo, com proveniência e calendário explícitos.

Não mistura mercado, entradas ou treinamento. Nunca preenche preços por interpolação.
"""
import concurrent.futures
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, salvar_json, ler_json, sha256, identidade, conferir_arquivos
from mercado_futuros.historico_operacional import ler_zip, validar_cobertura_funding
from mercado_futuros.pipeline import validar_candles

REG = RAIZ / 'registros/generalizacao_moedas/dados'
BASE = 'https://data.binance.vision/data/futures/um/monthly/'
SIMBOLOS = ('ETHUSDT', 'BNBUSDT', 'XRPUSDT')
DIA = 86400000


def baixar(url):
    for tentativa in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as resposta:
                return resposta.read()
        except urllib.error.HTTPError as erro:
            if erro.code in (403, 404, 418, 451):
                raise
            if erro.code == 429:
                espera = int(erro.headers.get('Retry-After', '10'))
                if espera > 60:
                    raise
            elif erro.code >= 500:
                espera = 2 * (tentativa + 1)
            else:
                raise
        except (TimeoutError, urllib.error.URLError):
            espera = 2 * (tentativa + 1)
        if tentativa == 2:
            raise RuntimeError(f'Falha de leitura pública após três tentativas: {url}')
        time.sleep(espera)


def inicio_completo(onboard):
    return max(1577836800000, ((int(onboard) + DIA - 1) // DIA) * DIA)


def regras_simbolo(info):
    filtros = {x['filterType']: x for x in info['filters']}
    lote = filtros['MARKET_LOT_SIZE']
    return {'tick_preco': float(filtros['PRICE_FILTER']['tickSize']),
            'passo_quantidade': float(lote['stepSize']),
            'quantidade_minima': float(lote['minQty']),
            'quantidade_maxima': float(lote['maxQty']),
            'nocional_minimo': float(filtros['MIN_NOTIONAL']['notional'])}


def validar_diario(q, inicio):
    esperado = np.arange(inicio, 1767225600000, DIA, dtype=np.int64)
    np.testing.assert_array_equal(q.open_time, esperado)
    np.testing.assert_array_equal(q.close_time, esperado + DIA - 1)
    x = q[['open', 'high', 'low', 'close', 'volume']].to_numpy(float)
    assert np.isfinite(x).all() and (x[:, :4] > 0).all() and (x[:, 4] >= 0).all()
    assert (q.high >= q[['open', 'low', 'close']].max(axis=1)).all()
    assert (q.low <= q[['open', 'high', 'close']].min(axis=1)).all()


def mensal(pasta, simbolo, tipo, intervalo, mes):
    nome = f'{simbolo}-{tipo if tipo == "fundingRate" else intervalo}-{mes:%Y-%m}.zip'
    sub = f'{simbolo}/' + ('' if tipo == 'fundingRate' else f'{intervalo}/')
    url = BASE + tipo + '/' + sub + nome
    checksum = baixar(url + '.CHECKSUM')
    destino = pasta / 'brutos' / tipo / (intervalo or 'eventos') / nome
    destino.parent.mkdir(parents=True, exist_ok=True)
    assert not destino.exists()
    destino.write_bytes(baixar(url))
    destino.with_suffix('.zip.CHECKSUM').write_bytes(checksum)
    esperado = checksum.decode().split()[0]
    assert sha256(destino) == esperado, 'Checksum oficial divergente'
    return {'url': url, 'arquivo': destino.relative_to(pasta).as_posix(),
            'sha256': esperado, 'tipo': tipo, 'intervalo': intervalo, 'mes': f'{mes:%Y-%m}'}


def completar_minutos(q, pasta, simbolo, tipo, inicio, fim):
    faltas = np.setdiff1d(np.arange(inicio, fim, 60000), q.open_time)
    assert len(faltas) <= 10, 'Lacuna extensa: exige diagnóstico, não interpolação'
    for t in faltas:
        url = f'https://fapi.binance.com/fapi/v1/{tipo}?symbol={simbolo}&interval=1m&startTime={int(t)}&endTime={int(t)+59999}&limit=1'
        raw = baixar(url); linhas = json.loads(raw)
        assert len(linhas) == 1 and linhas[0][0] == int(t)
        arq = pasta / 'brutos' / tipo / f'complemento_{int(t)}.json'
        arq.write_bytes(raw)
        salvar_json(arq.with_suffix('.proveniencia.json'), {'url': url, 'sha256': sha256(arq), 'utc': agora()})
        extra = pd.DataFrame(linhas, columns=q.columns).astype(q.dtypes.to_dict())
        q = pd.concat([q, extra], ignore_index=True).sort_values('open_time').reset_index(drop=True)
    validar_candles(q, inicio, fim, tipo == 'klines')
    return q, len(faltas)


def conferir(ponteiro):
    pasta = RAIZ / ponteiro['pasta']
    assert sha256(pasta / 'manifesto.json') == ponteiro['manifesto_sha256']
    manifesto = ler_json(pasta / 'manifesto.json')
    conferir_arquivos(pasta, manifesto['arquivos'])
    return manifesto


def coletar_simbolo(simbolo):
    registro = REG / simbolo
    if (registro / 'execucao.json').exists():
        ptr = ler_json(registro / 'execucao.json'); conferir(ptr); return ptr
    registro.mkdir(parents=True, exist_ok=True)
    info = ler_json(RAIZ / 'registros/generalizacao_moedas/preparacao/exchangeInfo.json')
    info = next(x for x in info['symbols'] if x['symbol'] == simbolo)
    assert info['contractType'] == 'PERPETUAL' and info['quoteAsset'] == info['marginAsset'] == 'USDT'
    inicio = inicio_completo(info['onboardDate'])
    pasta = RAIZ / 'dados/mercado/generalizacao_moedas' / simbolo / agora().replace(':', '').replace('+', '_')
    pasta.mkdir(parents=True, exist_ok=False)
    salvar_json(pasta / 'instrumento.json', info)
    tarefas = []
    for mes in pd.date_range(pd.Timestamp(inicio, unit='ms', tz='UTC').replace(day=1), pd.Timestamp('2025-12-01', tz='UTC'), freq='MS'):
        tarefas.append(('klines', '1d', mes))
    for mes in pd.date_range('2024-01-01', '2025-12-01', freq='MS', tz='UTC'):
        tarefas.extend((tipo, None if tipo == 'fundingRate' else '1m', mes)
                       for tipo in ('klines', 'markPriceKlines', 'fundingRate'))
    origens = []
    def estado(situacao, **extras):
        salvar_json(registro / 'estado.json', {'utc': agora(), 'situacao': situacao, 'simbolo': simbolo,
                    'pasta': pasta.relative_to(RAIZ).as_posix(), 'arquivos': len(origens), 'total': len(tarefas), **extras})
    try:
        estado('coletando')
        # Quatro leituras simultâneas; tentativas limitadas e bloqueios HTTP respeitados.
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futuros = [executor.submit(mensal, pasta, simbolo, *tarefa) for tarefa in tarefas]
            for futuro in concurrent.futures.as_completed(futuros):
                origens.append(futuro.result()); estado('coletando')
                if len(origens) % 12 == 0: print('COLETA', simbolo, len(origens), '/', len(tarefas), flush=True)
        origens.sort(key=lambda x: (x['tipo'], x['intervalo'] or '', x['mes']))
        partes = {}; complementos = 0
        for origem in origens:
            q = ler_zip((pasta / origem['arquivo']).read_bytes(), origem['tipo'])
            if origem['intervalo'] == '1m':
                mes = pd.Timestamp(origem['mes'] + '-01', tz='UTC')
                a = int(mes.timestamp()*1000); b = int((mes + pd.offsets.MonthBegin()).timestamp()*1000)
                q, n = completar_minutos(q, pasta, simbolo, origem['tipo'], a, b); complementos += n
            partes.setdefault((origem['tipo'], origem['intervalo']), []).append(q)
        diario_bruto = pd.concat(partes.pop(('klines', '1d')), ignore_index=True)
        diario = diario_bruto[diario_bruto.open_time >= inicio].copy().reset_index(drop=True)
        validar_diario(diario, inicio); diario.to_parquet(pasta / 'diario.parquet', index=False)
        for tipo in ('klines', 'markPriceKlines'):
            q = pd.concat(partes.pop((tipo, '1m')), ignore_index=True)
            validar_candles(q, 1704067200000, 1767225600000, tipo == 'klines')
            q.to_parquet(pasta / (tipo + '.parquet'), index=False)
        arquivo = pd.concat(partes[('fundingRate', None)], ignore_index=True)
        validar_cobertura_funding(arquivo, 1704067200000, 1767225600000)
        cursor = 1704067200000; fim = 1767225600000; eventos = []; paginas = []
        for _ in range(30):
            if cursor >= fim: break
            url = f'https://fapi.binance.com/fapi/v1/fundingRate?symbol={simbolo}&startTime={cursor}&endTime={fim-1}&limit=1000'
            raw = baixar(url); lista = json.loads(raw)
            assert isinstance(lista, list)
            arq = pasta / 'brutos' / f'funding_api_{len(paginas):03}.json'; arq.write_bytes(raw)
            paginas.append({'url': url, 'arquivo': arq.relative_to(pasta).as_posix(), 'sha256': sha256(arq)})
            if not lista: break
            assert all(x['symbol'] == simbolo and cursor <= x['fundingTime'] < fim for x in lista)
            eventos.extend(lista); cursor = int(lista[-1]['fundingTime']) + 1
        else: raise RuntimeError('Orçamento de páginas de funding esgotado')
        api = pd.DataFrame(eventos)
        api['fundingTime'] = pd.to_numeric(api.fundingTime).astype('int64')
        for col in ('fundingRate', 'markPrice'): api[col] = pd.to_numeric(api[col], errors='raise').astype(float)
        assert api.fundingTime.is_unique and api.fundingTime.is_monotonic_increasing
        np.testing.assert_array_equal(api.fundingTime.to_numpy() // 60000, arquivo.calc_time.to_numpy() // 60000)
        np.testing.assert_allclose(api.fundingRate, arquivo.last_funding_rate, rtol=0, atol=1e-12)
        assert np.isfinite(api[['fundingRate', 'markPrice']].to_numpy()).all() and (api.markPrice > 0).all()
        api[['fundingTime', 'fundingRate', 'markPrice']].to_parquet(pasta / 'funding.parquet', index=False)
        contrato = {'simbolo': simbolo, 'mercado': 'USD-M perpetuo', 'inicio_diario_ms': inicio,
                    'inicio_operacional_ms': 1704067200000, 'fim_exclusivo_ms': fim,
                    'dia_inaugural_parcial_excluido': int((diario_bruto.open_time < inicio).sum()),
                    'diarios': len(diario), 'minutos': len(q), 'eventos_funding': len(api),
                    'minutos_complementados_api': complementos, 'origens': origens, 'funding_api': paginas,
                    'regras_simbolo': regras_simbolo(info), 'fontes': {str(Path(__file__).relative_to(RAIZ).as_posix()): sha256(__file__)},
                    'limites': 'Filtros de exchangeInfo atuais, não histórico de filtros. Sem interpolação. Escalas/seleção fora da coleta.'}
        salvar_json(pasta / 'manifesto.json', {'id': identidade(contrato)[:20], 'utc': agora(), 'contrato': contrato,
                    'arquivos': {a.relative_to(pasta).as_posix(): sha256(a) for a in pasta.rglob('*') if a.is_file()}})
        ptr = {'id': identidade(contrato)[:20], 'pasta': pasta.relative_to(RAIZ).as_posix(), 'manifesto_sha256': sha256(pasta / 'manifesto.json')}
        salvar_json(registro / 'execucao.json', ptr); estado('concluido_conferido', execucao=ptr)
        print('DADOS_CONCLUIDOS', simbolo, contrato['diarios'], flush=True)
        return ptr
    except BaseException:
        import traceback
        incidente = {'utc': agora(), 'erro': traceback.format_exc()}
        salvar_json(pasta / 'incidente.json', incidente); estado('interrompido', **incidente); raise


if __name__ == '__main__':
    REG.mkdir(parents=True, exist_ok=True)
    # Lock nativo: a coleta é iniciada no Windows e não pode ser duplicada.
    import msvcrt
    with (REG / 'coleta.lock').open('a+b') as lock:
        if lock.tell() == 0: lock.write(b'0'); lock.flush()
        lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        for simbolo in SIMBOLOS: coletar_simbolo(simbolo)
