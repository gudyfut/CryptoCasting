"""Histórico 2021–2023 separado de F01/F03; não importa modelos ou simuladores.

Preserva preço de funding ausente como ausente e fornece intervalo de marcação.
Usar ``python -m mercado_futuros.historico_operacional`` para preparar, sem treino.
"""
from __future__ import annotations

import io
import json
import os
import socket
import traceback
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from infraestrutura.artefatos import RAIZ, agora, salvar_json, ler_json, sha256, identidade, conferir_arquivos
from mercado_futuros.pipeline import baixar, validar_candles, BASE

REG = RAIZ / 'registros/operacional_futuros/dados'
COLUNAS = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time',
           'quote_volume', 'count', 'taker_buy_volume', 'taker_buy_quote_volume', 'ignore']


def ler_zip(raw: bytes, tipo: str) -> pd.DataFrame:
    """Arquivos antigos podem não ter cabeçalho; nunca perder a primeira linha."""
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if len(z.namelist()) != 1:
            raise ValueError('Arquivo mensal com conteúdo inesperado.')
        csv = z.read(z.namelist()[0])
    primeira = csv.splitlines()[0].decode('utf-8-sig').split(',')[0]
    cabecalho = not primeira.isdigit()
    q = pd.read_csv(io.BytesIO(csv), header=0 if cabecalho else None)
    if tipo == 'fundingRate':
        if not cabecalho or set(q.columns) != {'calc_time', 'funding_interval_hours', 'last_funding_rate'}:
            raise ValueError('Esquema de funding inesperado; não adivinhar colunas.')
        return q
    if q.shape[1] != 12:
        raise ValueError('Candle fora do esquema oficial de 12 campos.')
    if cabecalho and list(q.columns) != COLUNAS:
        raise ValueError(f'Cabeçalho desconhecido: {list(q.columns)}')
    q.columns = COLUNAS
    for c in ['open_time', 'close_time', 'count']:
        x = pd.to_numeric(q[c], errors='raise')
        if not np.equal(x, np.floor(x)).all():
            raise ValueError('Inteiro fracionário no arquivo de mercado.')
        q[c] = x.astype('int64')
    for c in ['open', 'high', 'low', 'close', 'volume', 'quote_volume', 'taker_buy_volume', 'taker_buy_quote_volume']:
        q[c] = pd.to_numeric(q[c], errors='raise').astype('float64')
        if not np.isfinite(q[c]).all():
            raise ValueError(f'Valor não finito: {c}')
    if (q[['volume', 'quote_volume', 'taker_buy_volume', 'taker_buy_quote_volume', 'count']] < 0).any().any():
        raise ValueError('Volume/contagem negativos.')
    return q


def associar_funding(api: pd.DataFrame, arquivo: pd.DataFrame, marca: pd.DataFrame) -> pd.DataFrame:
    """Sem preencher markPrice com preço inventado; intervalos são observações."""
    a = api.copy()
    a['fundingTime'] = pd.to_numeric(a.fundingTime, errors='raise').astype('int64')
    a['fundingRate'] = pd.to_numeric(a.fundingRate, errors='raise').astype(float)
    # Somente campo realmente ausente pode virar NaN; conteúdo inválido é erro.
    a['markPrice'] = pd.to_numeric(a.markPrice.replace('', np.nan), errors='raise').astype(float)
    if not a.fundingTime.is_unique or not a.fundingTime.is_monotonic_increasing:
        raise ValueError('Funding duplicado ou desordenado.')
    if len(a) != len(arquivo) or not np.isfinite(a.fundingRate).all():
        raise ValueError('Cobertura/taxas de funding inválidas.')
    np.testing.assert_array_equal(a.fundingTime.to_numpy() // 60000, arquivo.calc_time.to_numpy() // 60000)
    np.testing.assert_allclose(a.fundingRate, arquivo.last_funding_rate, rtol=0, atol=1e-12)
    presentes = a.markPrice.notna()
    if not np.isfinite(a.loc[presentes, 'markPrice']).all() or (a.loc[presentes, 'markPrice'] <= 0).any():
        raise ValueError('Marca de funding inválida.')
    ix = pd.Index(marca.open_time).get_indexer((a.fundingTime.to_numpy() // 60000) * 60000)
    if (ix < 0).any():
        raise ValueError('Funding sem minuto de marcação.')
    a['markPrice_exato_disponivel'] = presentes
    for c in ['open', 'high', 'low']:
        a['marca_minuto_' + c] = marca.iloc[ix][c].to_numpy(float)
    a['intervalo_horas'] = arquivo.funding_interval_hours.to_numpy(float)
    return a[['fundingTime', 'fundingRate', 'markPrice', 'markPrice_exato_disponivel',
              'marca_minuto_open', 'marca_minuto_high', 'marca_minuto_low', 'intervalo_horas']]


def agregar_horas(q: pd.DataFrame) -> pd.DataFrame:
    grupo = q.open_time // 3600000
    if not (q.groupby(grupo).size() == 60).all():
        raise ValueError('Hora incompleta; não preencher dados.')
    h = q.groupby(grupo).agg(open_time=('open_time', 'first'), open=('open', 'first'),
        high=('high', 'max'), low=('low', 'min'), close=('close', 'last'),
        volume=('volume', 'sum'), close_time=('close_time', 'last')).reset_index(drop=True)
    if not ((h.open_time % 3600000 == 0) & (h.close_time == h.open_time + 3599999)).all():
        raise ValueError('Alinhamento horário incorreto.')
    return h


def intervalos_faltantes(faltas: np.ndarray, limite: int = 1500):
    """Paginação somente de lacunas contíguas, sem sobrescrever candles existentes."""
    if limite < 1:
        raise ValueError('Limite inválido.')
    f = np.asarray(faltas, dtype=np.int64)
    if len(f) and (np.diff(f) <= 0).any():
        raise ValueError('Lacunas devem ser únicas e crescentes.')
    for trecho in np.split(f, np.flatnonzero(np.diff(f) != 60000) + 1):
        for i in range(0, len(trecho), limite):
            grupo = trecho[i:i+limite]
            yield int(grupo[0]), int(grupo[-1]), len(grupo)


def validar_cobertura_funding(arquivo, inicio, fim):
    # Timestamps originais preservados. Settlements históricos têm alguns ms
    # depois da fronteira; cobertura é conferida em minutos, como a API.
    minutos = arquivo.calc_time.to_numpy() // 60000
    if not len(minutos) or minutos[0] != inicio // 60000:
        raise ValueError('Primeiro funding ausente.')
    np.testing.assert_array_equal(np.diff(minutos), arquivo.funding_interval_hours.iloc[1:].to_numpy() * 60)
    if minutos[-1] * 60000 + arquivo.funding_interval_hours.iloc[-1] * 3600000 != fim:
        raise ValueError('Último intervalo de funding incompleto.')


def coletar() -> dict:
    REG.mkdir(parents=True, exist_ok=True)
    ponteiro = REG / 'execucao.json'
    if ponteiro.exists():
        p = ler_json(ponteiro)
        d = RAIZ / p['pasta']
        if sha256(d / 'manifesto.json') != p['manifesto_sha256']:
            raise ValueError('Manifesto publicado divergente.')
        conferir_arquivos(d, ler_json(d / 'manifesto.json')['arquivos'])
        print('HISTORICO_JA_PUBLICADO_CONFERIDO', p, flush=True)
        return p
    # Exclusive creation is intentionally fail-closed after a crash. An operator
    # must inspect PID/host and preserve the stale lock before explicitly retrying.
    lock = REG / 'coleta.lock'
    with lock.open('x', encoding='utf-8') as f:
        json.dump({'pid': os.getpid(), 'host': socket.gethostname(), 'utc': agora()}, f)
    d = RAIZ / 'dados/mercado/futuros_operacional/tentativas' / agora().replace(':', '').replace('+', '_')
    d.mkdir(parents=True, exist_ok=False)
    nomes_fontes = ['mercado_futuros/historico_operacional.py', 'mercado_futuros/pipeline.py', 'infraestrutura/artefatos.py']
    fontes = {p: sha256(RAIZ / p) for p in nomes_fontes}
    fontes_dir = d / 'fontes'
    for nome in nomes_fontes:
        dest = fontes_dir / nome
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((RAIZ / nome).read_bytes())
    inicio = int(pd.Timestamp('2021-01-01', tz='UTC').timestamp() * 1000)
    fim = int(pd.Timestamp('2024-01-01', tz='UTC').timestamp() * 1000)
    origens, paginas = [], []
    acumulados = {t: [] for t in ['klines', 'markPriceKlines', 'fundingRate']}
    salvar_json(d / 'inicio.json', {'utc': agora(), 'fontes': fontes, 'inicio': inicio, 'fim_exclusivo': fim})
    try:
        for mes in pd.date_range('2021-01-01', '2023-12-01', freq='MS', tz='UTC'):
            for tipo in acumulados:
                nome = f'BTCUSDT-fundingRate-{mes:%Y-%m}.zip' if tipo == 'fundingRate' else f'BTCUSDT-1m-{mes:%Y-%m}.zip'
                sub = f'BTCUSDT/{nome}' if tipo == 'fundingRate' else f'BTCUSDT/1m/{nome}'
                url = BASE + tipo + '/' + sub
                checksum = baixar(url + '.CHECKSUM')
                esperado = checksum.decode().split()[0]
                caches = (RAIZ / 'dados/mercado/futuros_operacional/tentativas').glob(f'*/brutos/{tipo}/{nome}')
                cache = next((p for p in caches if sha256(p) == esperado), None)
                raw = cache.read_bytes() if cache else baixar(url)
                path = d / 'brutos' / tipo / nome
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                path.with_suffix('.zip.CHECKSUM').write_bytes(checksum)
                if sha256(path) != esperado:
                    raise ValueError('Checksum remoto divergente.')
                q = ler_zip(raw, tipo)
                ini = int(mes.timestamp() * 1000)
                fim_mes = int((mes + pd.offsets.MonthBegin()).timestamp() * 1000)
                if tipo != 'fundingRate':
                    faltas = np.setdiff1d(np.arange(ini, fim_mes, 60000), q.open_time.to_numpy())
                    # O mensal de markPrice de julho/2021 omite cinco dias que a
                    # API oficial possui. Recuperar observações, nunca interpolar.
                    for primeiro, ultimo, quantidade in intervalos_faltantes(faltas):
                        u = f'https://fapi.binance.com/fapi/v1/{tipo}?symbol=BTCUSDT&interval=1m&startTime={primeiro}&endTime={ultimo+59999}&limit={quantidade}'
                        bruto = baixar(u)
                        v = json.loads(bruto)
                        if not isinstance(v, list) or len(v) != quantidade:
                            raise ValueError('Cobertura oficial da lacuna incompleta.')
                        np.testing.assert_array_equal([x[0] for x in v], np.arange(primeiro, ultimo+1, 60000))
                        a = d / 'brutos' / tipo / f'complemento_{primeiro}_{ultimo}.json'
                        a.write_bytes(bruto)
                        salvar_json(a.with_suffix('.proveniencia.json'), {'url': u, 'sha256': sha256(a), 'linhas': quantidade, 'motivo': 'Observações oficiais ausentes no mensal; sem interpolação.'})
                        extra = pd.DataFrame(v, columns=COLUNAS).astype(q.dtypes.to_dict())
                        q = pd.concat([q, extra], ignore_index=True).sort_values('open_time').reset_index(drop=True)
                    validar_candles(q, ini, fim_mes, tipo == 'klines')
                else:
                    if not q.calc_time.is_unique or not q.calc_time.is_monotonic_increasing:
                        raise ValueError('Funding mensal duplicado/desordenado.')
                    if not ((q.calc_time >= ini) & (q.calc_time < fim_mes)).all():
                        raise ValueError('Funding fora do mês.')
                    if not np.isfinite(q.last_funding_rate).all() or not (q.funding_interval_hours > 0).all():
                        raise ValueError('Funding mensal inválido.')
                acumulados[tipo].append(q)
                origens.append({'url': url, 'checksum': esperado, 'arquivo': path.relative_to(d).as_posix(), 'linhas': len(q)})
                salvar_json(REG / 'estado.json', {'utc': agora(), 'situacao': 'coletando', 'arquivos': len(origens), 'total_arquivos': 108, 'pasta': d.relative_to(RAIZ).as_posix()})
                print(f'COLETA {len(origens)}/108 {tipo} {mes:%Y-%m}', flush=True)
        dados = {t: pd.concat(v, ignore_index=True) for t, v in acumulados.items()}
        for t in ['klines', 'markPriceKlines']:
            validar_candles(dados[t], inicio, fim, t == 'klines')
            dados[t].to_parquet(d / (t + '.parquet'), index=False)
        arquivo = dados['fundingRate']
        validar_cobertura_funding(arquivo, inicio, fim)
        cursor, eventos = inicio, []
        while cursor < fim:
            url = f'https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&startTime={cursor}&endTime={fim-1}&limit=1000'
            raw = baixar(url)
            q = json.loads(raw)
            if not isinstance(q, list):
                raise ValueError('Resposta de funding inesperada.')
            arq = d / 'brutos' / f'funding_api_{len(paginas):03}.json'
            arq.write_bytes(raw)
            paginas.append({'url': url, 'arquivo': arq.relative_to(d).as_posix(), 'sha256': sha256(arq)})
            if not q:
                break
            if not all(x['symbol'] == 'BTCUSDT' and cursor <= x['fundingTime'] < fim for x in q):
                raise ValueError('Paginação de funding inválida.')
            eventos.extend(q)
            cursor = int(q[-1]['fundingTime']) + 1
        funding = associar_funding(pd.DataFrame(eventos), arquivo, dados['markPriceKlines'])
        funding.to_parquet(d / 'funding.parquet', index=False)
        horas = agregar_horas(dados['klines'])
        horas.to_parquet(d / 'candles_1h.parquet', index=False)
        conferir_arquivos(RAIZ, fontes)
        contrato = {'simbolo': 'BTCUSDT', 'mercado': 'USD-M perpetuo', 'inicio': '2021-01-01', 'fim_exclusivo': '2024-01-01',
            'unidade_temporal': 'milissegundos', 'fontes': fontes, 'origens': origens, 'funding_api': paginas,
            'precos_funding_ausentes': int((~funding.markPrice_exato_disponivel).sum()),
            'tratamento_marca_ausente': 'NaN preservado; OHLC de marcação do minuto em colunas separadas. Política de custo é responsabilidade do simulador.',
            'minutos': len(dados['klines']), 'candles_1h': len(horas), 'eventos_funding': len(funding),
            'derivados': {p.name: sha256(p) for p in d.glob('*.parquet')}}
        codigo = identidade(contrato)[:20]
        salvar_json(d / 'manifesto.json', {'id': codigo, 'utc': agora(), 'contrato': contrato,
            'arquivos': {p.relative_to(d).as_posix(): sha256(p) for p in d.rglob('*') if p.is_file()}})
        conferir_arquivos(d, ler_json(d / 'manifesto.json')['arquivos'])
        ptr = {'id': codigo, 'pasta': d.relative_to(RAIZ).as_posix(), 'manifesto_sha256': sha256(d / 'manifesto.json')}
        salvar_json(ponteiro, ptr)
        salvar_json(REG / 'estado.json', {'utc': agora(), 'situacao': 'concluido_conferido', 'execucao': ptr,
            'minutos': len(dados['klines']), 'candles_1h': len(horas), 'eventos_funding': len(funding),
            'precos_funding_ausentes': contrato['precos_funding_ausentes']})
        print('HISTORICO_CONCLUIDO', ptr, flush=True)
        return ptr
    except BaseException:
        incidente = {'utc': agora(), 'situacao': 'interrompido', 'pasta': d.relative_to(RAIZ).as_posix(), 'erro': traceback.format_exc()}
        salvar_json(d / 'incidente.json', incidente)
        salvar_json(REG / 'estado.json', incidente)
        raise
    finally:
        lock.unlink()


if __name__ == '__main__':
    coletar()
