"""Adaptação explícita dos minutos publicados para a política Spot preservada."""
from pathlib import Path
import numpy as np
import pandas as pd
from infraestrutura.artefatos import ler_json


def carregar_minutos(pasta, par):
    pasta = Path(pasta)
    partes = [q for q in ler_json(pasta / 'qualidade.json')['partes'] if q['par'] == par]
    partes.sort(key=lambda q: q['periodo']['inicio'])
    if not partes:
        raise ValueError('Sem minutos do par solicitado.')
    dados = pd.concat([pd.read_parquet(pasta / q['arquivo']) for q in partes], ignore_index=True)
    tempos = pd.DatetimeIndex(dados.inicio_utc)
    if tempos.tz is None or (tempos[1:] - tempos[:-1] != pd.Timedelta(minutes=1)).any():
        raise ValueError('Grade de minutos ausente, duplicada ou desordenada.')
    valores = dados[['open', 'high', 'low', 'close', 'volume', 'negocios']].to_numpy(float, copy=True)
    valores[~dados.completo.to_numpy()] = np.nan
    return valores, int(tempos[0].timestamp() // 60)
