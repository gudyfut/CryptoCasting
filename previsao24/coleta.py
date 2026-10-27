"""Coleta mensal 1m, checksum obrigatório e auditoria vetorizada independente."""
from __future__ import annotations

import concurrent.futures
import re
import time
import urllib.request
import zipfile
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from .arquivos import RAIZ, agora, salvar_json, sha256
from .configuracao import PARES

COLUNAS_BRUTAS = ['tempo', 'open', 'high', 'low', 'close', 'volume', 'fim',
                 'volume_cotacao', 'negocios', 'compra_base', 'compra_cotacao', 'ignorar']


def baixar(url: str, caminho: Path):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + '.parcial')
    for tentativa in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'CryptoCasting/retorno24'})
            with urllib.request.urlopen(req, timeout=45) as resposta, temporario.open('wb') as saida:
                while bloco := resposta.read(1024 * 1024):
                    saida.write(bloco)
            temporario.replace(caminho)
            return
        except Exception:
            temporario.unlink(missing_ok=True)
            if tentativa == 2:
                raise
            time.sleep(2 ** tentativa)


def ler_mes(caminho: Path, inicio: pd.Timestamp, fim: pd.Timestamp) -> tuple[pd.DataFrame, dict]:
    with zipfile.ZipFile(caminho) as z:
        nome = caminho.with_suffix('.csv').name
        if z.namelist() != [nome] or z.testzip() is not None:
            raise ValueError(f'ZIP inválido: {caminho}')
        with z.open(nome) as entrada:
            q = pd.read_csv(entrada, header=None, names=COLUNAS_BRUTAS)
    if len(q) == 0:
        raise ValueError('Mês vazio.')
    bruto = q['tempo'].to_numpy(dtype=np.int64)
    divisor = 60_000_000 if inicio.year >= 2025 else 60_000
    if (bruto % divisor).any():
        raise ValueError('Timestamp desalinhado ou unidade incompatível com a competência.')
    minutos = bruto // divisor
    a, b = int(inicio.timestamp() // 60), int(fim.timestamp() // 60)
    if (np.diff(minutos) <= 0).any() or minutos.min() < a or minutos.max() >= b:
        raise ValueError('Ordem, duplicata ou limites de competência inválidos.')
    valores = q[['open', 'high', 'low', 'close', 'volume', 'negocios']].to_numpy(dtype=np.float64)
    o, h, l, c, v, n = valores.T
    if not np.isfinite(valores).all() or np.min(valores[:, :4]) <= 0 or (v < 0).any() or (n < 0).any():
        raise ValueError('Valores OHLCV/negócios inválidos.')
    if (h < np.maximum(o, c)).any() or (l > np.minimum(o, c)).any() or (h < l).any():
        raise ValueError('OHLC inconsistente.')
    esperado_fim = bruto + divisor - 1
    fim_observado = q['fim'].to_numpy(dtype=np.int64)
    if (fim_observado < bruto).any() or (fim_observado > esperado_fim).any():
        raise ValueError('Fim de candle fora do minuto declarado.')
    # A fonte contém minutos interrompidos por manutenção. Preservar o ZIP,
    # registrar e retirar só esses minutos incompletos, sem sintetizar preços.
    completo = fim_observado == esperado_fim
    q = pd.DataFrame(valores[completo], index=pd.Index(minutos[completo], name='minuto_utc'),
                     columns=['open', 'high', 'low', 'close', 'volume', 'negocios'])
    return q, {'observados': len(q), 'esperados': b-a, 'lacunas': b-a-len(q),
               'minutos_interrompidos': int((~completo).sum()),
               'sem_negocios': int((n[completo] == 0).sum()), 'unidade': 'us' if inicio.year >= 2025 else 'ms'}


def coletar(inicio='2021-01-01', fim='2026-01-01', trabalhadores=4):
    meses = pd.date_range(inicio, fim, freq='MS', tz='UTC')
    if len(meses) < 2 or str(meses[0].date()) != inicio or str(meses[-1].date()) != fim:
        raise ValueError('Coleta exige meses completos, com fim exclusivo.')
    raiz = RAIZ / 'dados/brutos/binance_spot_1m'
    def item(par, a, b):
        nome = f'{par}-1m-{a:%Y-%m}.zip'
        caminho = raiz / par / nome
        url = f'https://data.binance.vision/data/spot/monthly/klines/{par}/1m/{nome}'
        checksum = caminho.with_suffix('.zip.CHECKSUM')
        registro = {'par': par, 'mes': f'{a:%Y-%m}', 'url': url, 'coleta_utc': agora()}
        try:
            anterior = RAIZ / 'arquivo/estudo_barreiras_2026-10-20/projeto/dados/brutos/barreiras_1m' / par / nome
            for origem, destino in ((anterior, caminho), (anterior.with_suffix('.zip.CHECKSUM'), checksum)):
                if origem.exists() and not destino.exists():
                    destino.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(origem, destino)
            if not checksum.exists():
                baixar(url + '.CHECKSUM', checksum)
            correspondencia = re.search(r'\b[0-9a-fA-F]{64}\b', checksum.read_text())
            if correspondencia is None:
                raise ValueError('Checksum oficial ausente.')
            esperado = correspondencia.group().lower()
            if not caminho.exists() or sha256(caminho) != esperado:
                baixar(url, caminho)
            if sha256(caminho) != esperado:
                raise ValueError('SHA-256 não corresponde à fonte oficial.')
            _, auditoria = ler_mes(caminho, a, b)
            registro.update(status='auditado', sha256=esperado, **auditoria)
        except Exception as erro:
            registro.update(status='falha', erro=f'{type(erro).__name__}: {erro}')
        salvar_json(caminho.with_suffix('.auditoria.json'), registro)
        return registro
    registros = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=trabalhadores) as executor:
        futuros = [executor.submit(item, par, a, b) for par in PARES for a, b in zip(meses[:-1], meses[1:])]
        for futuro in concurrent.futures.as_completed(futuros):
            r = futuro.result()
            registros.append(r)
            print(f"[{len(registros)}/{len(futuros)}] {r['par']} {r['mes']} {r['status']} lacunas={r.get('lacunas')}", flush=True)
    registros.sort(key=lambda r: (r['par'], r['mes']))
    manifesto = {'inicio': inicio, 'fim': fim, 'intervalo': '1m', 'pares': list(PARES),
                 'registros': registros, 'concluido_utc': agora()}
    salvar_json(raiz / f'manifesto_{inicio}_{fim}.json', manifesto)
    if any(r['status'] != 'auditado' for r in registros):
        raise RuntimeError('Há falhas na coleta; consultar o manifesto. Nenhum treinamento foi iniciado.')
    return manifesto

