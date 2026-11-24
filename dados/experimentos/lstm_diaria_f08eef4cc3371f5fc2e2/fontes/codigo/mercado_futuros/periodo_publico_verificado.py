"""Coleta por período com recuperação oficial de lacunas extensas verificadas; preserva a primeira tentativa."""
import concurrent.futures
import json
from pathlib import Path
import urllib.error

import numpy as np
import pandas as pd

from infraestrutura.artefatos import RAIZ, agora, salvar_json, sha256, identidade
from mercado_futuros.multimoeda import baixar, mensal as mensal_original
from mercado_futuros.historico_operacional import ler_zip, COLUNAS
from mercado_futuros.pipeline import validar_candles

DIA = 86400000
BASE = 'https://data.binance.vision/data/futures/um/daily/'


def api(pasta, simbolo, tipo, intervalo, inicio, fim, nome):
    partes, fontes, cursor = [], [], int(inicio)
    passo = DIA if intervalo == '1d' else 60000
    for pagina in range(1000):
        if cursor >= fim:
            break
        url = (f'https://fapi.binance.com/fapi/v1/{tipo}?symbol={simbolo}&interval={intervalo}'
               f'&startTime={cursor}&endTime={int(fim)-1}&limit=1000')
        bruto = baixar(url)
        destino = pasta / 'brutos/api' / f'{nome}_{pagina:04d}.json'
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(bruto)
        valores = json.loads(bruto)
        assert isinstance(valores, list) and valores, 'Página de mercado vazia; não interpolar.'
        q = pd.DataFrame(valores, columns=COLUNAS)
        for col in COLUNAS:
            q[col] = pd.to_numeric(q[col], errors='raise')
        q['open_time'] = q.open_time.astype('int64')
        q['close_time'] = q.close_time.astype('int64')
        assert (q.open_time >= cursor).all() and (q.open_time < fim).all()
        assert q.open_time.is_unique and q.open_time.is_monotonic_increasing
        partes.append(q)
        fontes.append(dict(url=url, arquivo=destino.relative_to(pasta).as_posix(), sha256=sha256(destino), utc=agora()))
        cursor = int(q.open_time.iloc[-1]) + passo
    else:
        raise RuntimeError('Orçamento de páginas esgotado.')
    resultado = pd.concat(partes, ignore_index=True)
    np.testing.assert_array_equal(resultado.open_time, np.arange(inicio, fim, passo))
    return resultado, fontes


def diario_arquivo(pasta, simbolo, tipo, intervalo, dia):
    nome = f'{simbolo}-{intervalo}-{dia:%Y-%m-%d}.zip'
    url = f'{BASE}{tipo}/{simbolo}/{intervalo}/{nome}'
    destino = pasta / 'brutos' / tipo / intervalo / nome
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        checksum = baixar(url + '.CHECKSUM')
    except urllib.error.HTTPError as erro:
        if erro.code != 404:
            raise
        a = int(dia.timestamp() * 1000)
        q, fontes = api(pasta, simbolo, tipo, intervalo, a, a + DIA, f'{tipo}_{intervalo}_{dia:%Y%m%d}')
        fontes[0]['motivo'] = 'Arquivo diário ainda não publicado (404); mesma fonte oficial por API.'
        return q, fontes
    bruto = baixar(url)
    destino.write_bytes(bruto)
    destino.with_suffix('.zip.CHECKSUM').write_bytes(checksum)
    assert sha256(destino) == checksum.decode().split()[0], 'Checksum oficial divergente.'
    return ler_zip(bruto, tipo), [dict(url=url, arquivo=destino.relative_to(pasta).as_posix(), sha256=sha256(destino))]


def completar(q, pasta, simbolo, tipo, intervalo, inicio, fim):
    passo = DIA if intervalo == '1d' else 60000
    faltas = np.setdiff1d(np.arange(inicio, fim, passo), q.open_time)
    assert len(faltas) <= 7*1440, 'Lacuna maior que sete dias; investigar.'
    fontes = []
    grupos = np.split(faltas, np.flatnonzero(np.diff(faltas) != passo)+1)
    for grupo in grupos:
        if not len(grupo):
            continue
        a, b = int(grupo[0]), int(grupo[-1])+passo
        extra, proveniencia = api(pasta, simbolo, tipo, intervalo, a, b, f'lacuna_{tipo}_{intervalo}_{a}')
        np.testing.assert_array_equal(extra.open_time, grupo)
        for origem in proveniencia:
            origem['motivo'] = 'Lacuna no arquivo: recuperada integralmente na API oficial, sem interpolação.'
            origem['minutos_ou_dias_ausentes_no_trecho'] = len(grupo)
        q = pd.concat([q, extra], ignore_index=True).sort_values('open_time').reset_index(drop=True)
        fontes.extend(proveniencia)
    return q, fontes


def mensal(pasta, simbolo, tipo, intervalo, mes):
    nome = f'{simbolo}-{tipo if tipo == "fundingRate" else intervalo}-{mes:%Y-%m}.zip'
    sub = f'brutos/{tipo}/{intervalo or "eventos"}/{nome}'
    caches = list((RAIZ/'dados/mercado/ensemble_2026').glob(f'*/{simbolo}/{sub}'))
    destino = pasta/sub
    for cache in caches:
        if cache == destino:
            continue
        url = f'https://data.binance.vision/data/futures/um/monthly/{tipo}/{simbolo}/' + ('' if tipo == 'fundingRate' else f'{intervalo}/') + nome
        checksum = baixar(url+'.CHECKSUM')
        if sha256(cache) != checksum.decode().split()[0]:
            continue
        destino.parent.mkdir(parents=True, exist_ok=True)
        assert not destino.exists()
        destino.write_bytes(cache.read_bytes())
        destino.with_suffix('.zip.CHECKSUM').write_bytes(checksum)
        return dict(url=url, arquivo=destino.relative_to(pasta).as_posix(), sha256=sha256(destino), tipo=tipo,
                    intervalo=intervalo, mes=f'{mes:%Y-%m}', cache_preservado=cache.relative_to(RAIZ).as_posix())
    return mensal_original(pasta, simbolo, tipo, intervalo, mes)


def validar_diario(q, inicio, fim):
    np.testing.assert_array_equal(q.open_time, np.arange(inicio, fim, DIA))
    np.testing.assert_array_equal(q.close_time, q.open_time + DIA - 1)
    v = q[['open', 'high', 'low', 'close']].to_numpy(float)
    assert np.isfinite(v).all() and (v > 0).all()
    assert (q.low <= q[['open', 'close']].min(axis=1)).all()
    assert (q.high >= q[['open', 'close']].max(axis=1)).all()
    assert np.isfinite(q.volume).all() and (q.volume >= 0).all()


def coletar(pasta, simbolo, inicio, fim_diario):
    """fim_diario é meia-noite UTC exclusiva; inclui dois minutos para saída00:01."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=False)
    fim_minuto = fim_diario + 120000
    primeiro = pd.Timestamp(inicio, unit='ms', tz='UTC')
    final = pd.Timestamp(fim_diario, unit='ms', tz='UTC')
    meses = list(pd.date_range(primeiro, final, freq='MS', inclusive='left'))
    completos = [mes for mes in meses if mes + pd.offsets.MonthBegin() <= final]
    tarefas = [(tipo, intervalo, mes) for mes in completos
               for tipo, intervalo in [('klines', '1d'), ('klines', '1m'), ('markPriceKlines', '1m'), ('fundingRate', None)]]
    partes = {('klines', '1d'): [], ('klines', '1m'): [], ('markPriceKlines', '1m'): [], ('fundingRate', None): []}
    origens = []
    def buscar(tarefa):
        tipo, intervalo, mes = tarefa
        origem = mensal(pasta, simbolo, tipo, intervalo, mes)
        return tarefa, origem, ler_zip((pasta / origem['arquivo']).read_bytes(), tipo)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        for contador, (tarefa, origem, q) in enumerate(executor.map(buscar, tarefas), 1):
            tipo, intervalo, mes = tarefa
            if tipo != 'fundingRate':
                a, b = int(mes.timestamp() * 1000), int((mes + pd.offsets.MonthBegin()).timestamp() * 1000)
                q, extras = completar(q, pasta, simbolo, tipo, intervalo, a, b)
                origens.extend(extras)
                if intervalo == '1m':
                    validar_candles(q, a, b, tipo == 'klines')
                else:
                    validar_diario(q, a, b)
            partes[(tipo, intervalo)].append(q)
            origens.append(origem)
            print('MENSAL', simbolo, contador, '/', len(tarefas), flush=True)
    cauda = primeiro if not completos else completos[-1] + pd.offsets.MonthBegin()
    for dia in pd.date_range(cauda, final, freq='D', inclusive='left'):
        for tipo, intervalo in [('klines', '1d'), ('klines', '1m'), ('markPriceKlines', '1m')]:
            q, fontes = diario_arquivo(pasta, simbolo, tipo, intervalo, dia)
            a = int(dia.timestamp() * 1000)
            q, extras = completar(q, pasta, simbolo, tipo, intervalo, a, a + DIA)
            origens.extend(fontes + extras)
            partes[(tipo, intervalo)].append(q)
        print('DIARIO', simbolo, dia.strftime('%Y-%m-%d'), flush=True)
    diario = pd.concat(partes[('klines', '1d')], ignore_index=True)
    validar_diario(diario, inicio, fim_diario)
    diario.to_parquet(pasta / 'diario.parquet', index=False)
    for tipo in ['klines', 'markPriceKlines']:
        extra, fontes = api(pasta, simbolo, tipo, '1m', fim_diario, fim_minuto, f'fronteira_{tipo}')
        origens.extend(fontes)
        q = pd.concat(partes[(tipo, '1m')] + [extra], ignore_index=True)
        validar_candles(q, inicio, fim_minuto, tipo == 'klines')
        q.to_parquet(pasta / f'{tipo}.parquet', index=False)
    cursor, eventos, paginas = inicio, [], []
    # Uma fronteira observada após o encerramento ajuda a conferir a cobertura.
    funding_fim = fim_diario + 8 * 3600000 + 1
    while cursor < funding_fim:
        url = f'https://fapi.binance.com/fapi/v1/fundingRate?symbol={simbolo}&startTime={cursor}&endTime={funding_fim-1}&limit=1000'
        raw = baixar(url)
        destino = pasta / 'brutos' / f'funding_api_{len(paginas):03d}.json'
        destino.write_bytes(raw)
        valores = json.loads(raw)
        assert isinstance(valores, list)
        paginas.append(dict(url=url, arquivo=destino.relative_to(pasta).as_posix(), sha256=sha256(destino)))
        if not valores:
            break
        assert all(e['symbol'] == simbolo and cursor <= e['fundingTime'] < funding_fim for e in valores)
        eventos.extend(valores)
        cursor = int(valores[-1]['fundingTime']) + 1
        assert len(paginas) <= 20
    funding = pd.DataFrame(eventos)
    funding['fundingTime'] = pd.to_numeric(funding.fundingTime).astype('int64')
    for col in ['fundingRate', 'markPrice']:
        funding[col] = pd.to_numeric(funding[col], errors='raise').astype(float)
    assert funding.fundingTime.is_unique and funding.fundingTime.is_monotonic_increasing
    assert np.isfinite(funding[['fundingRate', 'markPrice']]).all().all() and (funding.markPrice > 0).all()
    assert funding.fundingTime.iloc[0] // 60000 == inicio // 60000
    assert funding.fundingTime.iloc[-1] >= fim_diario + 60000
    gaps = np.diff(funding.fundingTime.to_numpy() // 60000)
    assert ((gaps > 0) & (gaps <= 480)).all(), 'Funding com lacuna superior a8h; investigar.'
    if completos:
        arquivo = pd.concat(partes[('fundingRate', None)], ignore_index=True)
        a = funding[funding.fundingTime < int(cauda.timestamp() * 1000)]
        np.testing.assert_array_equal(a.fundingTime.to_numpy() // 60000, arquivo.calc_time.to_numpy() // 60000)
        np.testing.assert_allclose(a.fundingRate, arquivo.last_funding_rate, atol=1e-12, rtol=0)
    funding = funding[(funding.fundingTime >= inicio) & (funding.fundingTime < fim_minuto)]
    funding[['fundingTime', 'fundingRate', 'markPrice']].to_parquet(pasta / 'funding.parquet', index=False)
    minuto = pd.read_parquet(pasta / 'klines.parquet')
    minuto = minuto[minuto.open_time < fim_diario]
    agrupado = minuto.groupby(minuto.open_time // DIA).agg(open=('open', 'first'), high=('high', 'max'),
                  low=('low', 'min'), close=('close', 'last'), volume=('volume', 'sum'))
    np.testing.assert_allclose(agrupado[['open', 'high', 'low', 'close']], diario[['open', 'high', 'low', 'close']], rtol=1e-10, atol=1e-8)
    divergente = ~np.isclose(agrupado.volume.to_numpy(), diario.volume.to_numpy(), rtol=1e-8, atol=1e-4)
    volumes = [dict(dia_ms=int(diario.open_time.iloc[i]), diario=float(diario.volume.iloc[i]),
                    minutos=float(agrupado.volume.iloc[i])) for i in np.flatnonzero(divergente)]
    contrato = dict(simbolo=simbolo, inicio_ms=inicio, fim_diario_exclusivo_ms=fim_diario,
                    fim_minuto_exclusivo_ms=fim_minuto, origens=origens, funding_api=paginas,
                    dias=len(diario), minutos=len(minuto) + 2, eventos_funding=len(funding),
                    reconciliacao_ohlc=True, divergencias_volume=volumes,
                    decisao_volume='Diário oficial como fonte de entrada, sem substituir pela soma dos minutos.',
                    limite='Funding mensal confere meses completos; cauda API e fronteiras/intervalos conferidos, sem certificação externa integral.')
    manifesto = dict(id=identidade(contrato)[:20], utc=agora(), contrato=contrato,
                     arquivos={q.relative_to(pasta).as_posix(): sha256(q) for q in pasta.rglob('*') if q.is_file()})
    salvar_json(pasta / 'manifesto.json', manifesto)
    return dict(id=manifesto['id'], pasta=pasta.as_posix(), manifesto_sha256=sha256(pasta / 'manifesto.json'))
