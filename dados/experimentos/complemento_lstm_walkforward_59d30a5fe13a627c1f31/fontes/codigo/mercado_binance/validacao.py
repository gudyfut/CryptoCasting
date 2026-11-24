"""Mesma validação para arquivo oficial e API; unidade temporal é explícita."""
from pathlib import Path
import re
import zipfile
import numpy as np
import pandas as pd
from infraestrutura.artefatos import sha256
from .contratos import COLUNAS_BRUTAS, VALORES, Periodo, conferir_candles


def conferir_checksum(arquivo, checksum):
    arquivo = Path(arquivo)
    linhas = Path(checksum).read_text(encoding='utf-8-sig').strip().splitlines()
    if len(linhas) != 1:
        raise ValueError('CHECKSUM deve conter exatamente um registro.')
    m = re.fullmatch(r'([0-9a-fA-F]{64})\s+\*?([^\s]+)', linhas[0])
    if not m or m[2] != arquivo.name or sha256(arquivo) != m[1].lower():
        raise ValueError('CHECKSUM oficial não corresponde ao nome/conteúdo do ZIP.')
    return m[1].lower()


def ler_zip(arquivo):
    arquivo = Path(arquivo)
    with zipfile.ZipFile(arquivo) as z:
        nome = arquivo.with_suffix('.csv').name
        if z.namelist() != [nome] or z.getinfo(nome).file_size > 128*1024*1024 or z.testzip() is not None:
            raise ValueError('ZIP inválido, inesperado ou excessivo; nada será extraído.')
        with z.open(nome) as f:
            q = pd.read_csv(f, header=None)
    return q


def _inteiros(serie, nome):
    numeros = pd.to_numeric(serie, errors='raise')
    a = numeros.to_numpy()
    if not np.isfinite(a).all() or np.any(a != np.floor(a)) or (a < 0).any() or (a > np.iinfo(np.int64).max).any():
        raise ValueError(f'Campo inteiro inválido: {nome}')
    return a.astype(np.int64)


def normalizar(linhas, periodo: Periodo, unidade):
    q = pd.DataFrame(linhas).copy()
    if q.empty:
        q = pd.DataFrame(columns=COLUNAS_BRUTAS)
    elif q.shape[1] != 12:
        raise ValueError('Kline exige exatamente 12 campos.')
    else:
        q.columns = COLUNAS_BRUTAS
    divisor = {'ms': 60_000, 'us': 60_000_000}.get(unidade)
    if divisor is None:
        raise ValueError('Unidade deve ser declarada como ms ou us.')
    tempos = _inteiros(q['tempo'], 'tempo'); fins = _inteiros(q['fim'], 'fim')
    minutos = tempos // divisor
    a,b = int(periodo.inicio.timestamp()//60),int(periodo.fim.timestamp()//60)
    if (tempos % divisor).any() or (np.diff(minutos) <= 0).any() or ((minutos < a)|(minutos >= b)).any():
        raise ValueError('Unidade, ordenação, duplicação ou limites temporais inválidos.')
    if ((fins < tempos)|(fins > tempos+divisor-1)).any():
        raise ValueError('Fechamento informado fora do candle.')
    valores = q[VALORES].apply(pd.to_numeric, errors='raise').to_numpy(np.float64)
    if not np.isfinite(valores).all() or (valores[:,:4] <= 0).any() or (valores[:,4:] < 0).any():
        raise ValueError('Valores de mercado não finitos, preços não positivos ou volumes negativos.')
    _inteiros(q['negocios'], 'negocios')
    o,h,l,c = valores[:,:4].T
    if (h < np.maximum(o,c)).any() or (l > np.minimum(o,c)).any() or (h < l).any():
        raise ValueError('OHLC inconsistente.')
    completos = fins == tempos+divisor-1
    grade = np.arange(a,b,dtype=np.int64)
    saida = pd.DataFrame(np.nan, index=grade, columns=VALORES)
    saida.loc[minutos[completos], VALORES] = valores[completos]
    saida['inicio_utc'] = pd.to_datetime(grade,unit='m',utc=True)
    saida['fim_utc'] = saida['inicio_utc']+pd.Timedelta(minutes=1)
    saida['observado'] = np.isin(grade,minutos)
    saida['completo'] = np.isin(grade,minutos[completos])
    saida = saida.reset_index(drop=True)
    conferir_candles(saida,1)
    resumo = {'esperados':len(grade),'registros_recebidos':len(q),'completos':int(completos.sum()),
              'interrompidos':int((~completos).sum()), 'ausentes_na_fonte':len(grade)-len(q),
              'indisponiveis':int((~saida['completo']).sum()),
              'completos_sem_negocios':int((valores[completos,5]==0).sum()), 'unidade_fonte':unidade}
    return saida, resumo
