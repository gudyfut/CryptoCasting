"""Dataset sem scaler global, com índices temporais explícitos e lacunas preservadas."""
from __future__ import annotations

from pathlib import Path
import shutil

import numpy as np
import pandas as pd

from .arquivos import RAIZ, agora, identidade, ler_json, salvar_json, sha256
from .coleta import ler_mes
from .configuracao import PARES, COLUNAS, HORIZONTES, VERSAO
from .rotulagem import rotular


def construir_horas(minutos: np.ndarray, primeiro_minuto: int) -> pd.DataFrame:
    if primeiro_minuto % 60 or len(minutos) % 60:
        raise ValueError('Série deve começar e terminar em fronteira horária UTC.')
    blocos = minutos.reshape(-1, 60, 6)
    completas = np.isfinite(blocos).all(axis=(1, 2))
    o = blocos[:, 0, 0].copy()
    h = np.max(blocos[:, :, 1], axis=1)
    l = np.min(blocos[:, :, 2], axis=1)
    c = blocos[:, -1, 3].copy()
    v = np.sum(blocos[:, :, 4], axis=1)
    for a in (o, h, l, c, v):
        a[~completas] = np.nan
    anterior = np.r_[np.nan, c[:-1]]
    x = np.column_stack([np.log(o/anterior), np.log(h/anterior), np.log(l/anterior),
                         np.log(c/anterior), np.log1p(v)])
    tempos = primeiro_minuto + (np.arange(len(blocos))+1)*60
    q = pd.DataFrame(x, columns=COLUNAS)
    q['origem_utc'] = pd.to_datetime(tempos, unit='m', utc=True)
    q['indice_hora'] = np.arange(len(q))
    q['entrada_indice'] = (np.arange(len(q))+1)*60+1
    q['sigma'] = q['retorno'].rolling(168, min_periods=168).std(ddof=1)
    validas = pd.Series(np.isfinite(x).all(axis=1)).rolling(168, min_periods=168).sum().eq(168)
    q['elegivel_passado'] = validas & np.isfinite(q['sigma']) & q['sigma'].gt(0)
    entradas = q['entrada_indice'].to_numpy()
    fins = entradas + 168*60
    prefixo = np.r_[0, np.cumsum(~np.isfinite(minutos).all(axis=1))]
    dentro = fins < len(minutos)
    completo = np.zeros(len(q), bool)
    completo[dentro] = prefixo[fins[dentro]+1] == prefixo[entradas[dentro]]
    q['futuro_completo'] = completo
    return q


def preparar(manifesto: Path) -> Path:
    m = ler_json(manifesto)
    if m['intervalo'] != '1m' or tuple(m['pares']) != PARES:
        raise ValueError('Fonte não corresponde ao contrato.')
    meses = pd.date_range(m['inicio'], m['fim'], freq='MS', tz='UTC')
    esperado = {(par, f'{a:%Y-%m}') for par in PARES for a in meses[:-1]}
    registros = {(r['par'], r['mes']): r for r in m['registros']}
    if len(registros) != len(m['registros']) or set(registros) != esperado:
        raise ValueError('Inventário mensal incompleto/duplicado.')
    if any(r['status'] != 'auditado' for r in registros.values()):
        raise ValueError('Coleta tem falhas não resolvidas.')
    assinatura = {'versao': VERSAO, 'inicio': m['inicio'], 'fim': m['fim'],
                  'fontes': {f'{p}/{mes}': registros[p,mes]['sha256'] for p,mes in sorted(registros)},
                  'codigo': {p.name: sha256(p) for p in [Path(__file__), RAIZ/'barreiras/rotulagem.py',
                              RAIZ/'barreiras/coleta.py',RAIZ/'barreiras/configuracao.py']}}
    id_dados = identidade(assinatura)[:20]
    destino = RAIZ/'dados/processados'/f'barreiras_{id_dados}'
    if (destino/'dataset.json').exists():
        verificar_dataset(destino)
        return destino
    destino.mkdir(parents=True, exist_ok=True)
    (destino/'fontes').mkdir(exist_ok=True)
    for nome in assinatura['codigo']:
        shutil.copyfile(RAIZ/'barreiras'/nome,destino/'fontes'/nome)
    a = int(meses[0].timestamp()//60)
    b = int(meses[-1].timestamp()//60)
    comuns = None
    resumo = {}
    for par in PARES:
        pasta = destino/par
        pasta.mkdir(exist_ok=True)
        dados = np.full((b-a, 6), np.nan, dtype=np.float64)
        auditorias = []
        for inicio, fim in zip(meses[:-1], meses[1:]):
            mes = f'{inicio:%Y-%m}'
            bruto = RAIZ/'dados/brutos/barreiras_1m'/par/f'{par}-1m-{mes}.zip'
            if sha256(bruto) != registros[par,mes]['sha256']:
                raise ValueError(f'Dado mudou desde a coleta: {bruto}')
            q, auditoria = ler_mes(bruto, inicio, fim)
            for chave in ('observados','esperados','lacunas','minutos_interrompidos','sem_negocios','unidade'):
                if auditoria[chave] != registros[par,mes].get(chave):
                    raise ValueError(f'Auditoria divergente: {par}/{mes}/{chave}')
            dados[q.index.to_numpy()-a] = q.to_numpy()
            auditorias.append(auditoria)
        np.save(pasta/'minutos.npy', dados, allow_pickle=False)
        horas = construir_horas(dados, a)
        horas.to_parquet(pasta/'horas.parquet', index=False)
        origens = horas.loc[horas['elegivel_passado']].copy()
        mascara = horas['elegivel_passado'].to_numpy() & horas['futuro_completo'].to_numpy()
        for h in HORIZONTES:
            q = origens[['origem_utc', 'indice_hora', 'entrada_indice', 'sigma', 'futuro_completo']].copy()
            q['distancia'] = q['sigma'] * np.sqrt(h)
            e = q['entrada_indice'].to_numpy(np.int64)
            y, saida, conhecido, preco, ambiguo, motivo = rotular(dados, e, q['distancia'].to_numpy(), h*60)
            q['classe'], q['saida_indice'], q['saida_conhecida_indice'] = y, saida, conhecido
            q['preco_saida'], q['ambiguo'], q['motivo_nao_observado'] = preco, ambiguo, motivo
            q['entrada_utc'] = q['origem_utc']+pd.Timedelta(minutes=1)
            q['expiracao_utc'] = q['entrada_utc']+pd.Timedelta(hours=h)
            q['expiracao_maxima_utc'] = q['entrada_utc']+pd.Timedelta(hours=168)
            q['preco_entrada'] = np.where(e < len(dados), dados[np.minimum(e,len(dados)-1),0], np.nan)
            q['saida_utc'] = pd.to_datetime(np.where(saida >= 0, (a+saida)*60, np.nan), unit='s', utc=True)
            q['par'], q['horizonte'] = par, h
            q.to_parquet(pasta/f'amostras_H{h}.parquet', index=False)
            sem_rotulo = q.loc[q['classe'] < 0, 'indice_hora'].to_numpy(np.int64)
            mascara[sem_rotulo] = False
        comuns = mascara.copy() if comuns is None else comuns & mascara
        resumo[par] = {'minutos_esperados': b-a, 'minutos_ausentes': int((~np.isfinite(dados[:,0])).sum()),
                       'horas': len(horas), 'origens_causais': len(origens),
                       'minutos_interrompidos': sum(r['minutos_interrompidos'] for r in auditorias)}
        print(f'{par}: {len(origens)} origens causais; qualidade auditada.', flush=True)
    np.save(destino/'origens_comuns.npy', comuns, allow_pickle=False)
    for nome,h in assinatura['codigo'].items():
        if sha256(RAIZ/'barreiras'/nome)!=h or sha256(destino/'fontes'/nome)!=h:
            raise ValueError('Código de transformação mudou durante a pipeline.')
    arquivos = {p.relative_to(destino).as_posix(): sha256(p) for p in sorted(destino.rglob('*')) if p.is_file()}
    salvar_json(destino/'dataset.json', {'id': id_dados, 'assinatura': assinatura, 'criado_utc': agora(),
               'primeiro_minuto': a, 'fim_minuto': b, 'resumo': resumo,
               'origens_comuns': int(comuns.sum()), 'arquivos': arquivos})
    verificar_dataset(destino)
    salvar_json(RAIZ/'dados/processados/dataset_barreiras_atual.json', {'caminho': destino.relative_to(RAIZ).as_posix(), 'id': id_dados})
    return destino


def verificar_dataset(pasta: Path) -> dict:
    m = ler_json(pasta/'dataset.json')
    if identidade(m['assinatura'])[:20] != m['id']:
        raise ValueError('Identidade do dataset não corresponde ao conteúdo.')
    for relativo, esperado in m['arquivos'].items():
        p = (pasta/relativo).resolve()
        if not p.is_relative_to(pasta.resolve()) or sha256(p) != esperado:
            raise ValueError(f'Artefato do dataset ausente/alterado: {relativo}')
    return m
