"""Carteiras atômicas, auditoria independente e descrição da exposição."""
from copy import deepcopy
from pathlib import Path
import io
import json
import time
import zipfile
import numpy as np
import pandas as pd
from infraestrutura.artefatos import agora, ler_json, salvar_json, sha256
from simulacao_operacoes.continuidade_diaria.simulador import simular
from simulacao_operacoes.continuidade_diaria.auditoria_grade import conferir
from .fontes_operacionais import comparar_carteiras


def descrever(resultado, curva):
    dias = resultado['dias']
    sinais = np.array([d['lado_sinal'] for d in dias], dtype=np.int8)
    lados = np.sign([d['quantidade'] for d in dias]).astype(np.int8)
    episodios = []
    for i, lado in enumerate(lados):
        if lado == 0:
            continue
        if i == 0 or lado != lados[i-1]:
            episodios.append(dict(inicio_indice=i, fim_indice=i, lado=int(lado), dias=0,
                                 movimento_contrato_usdt=0.))
        episodios[-1]['fim_indice'] = i
        episodios[-1]['dias'] += 1
        episodios[-1]['movimento_contrato_usdt'] += dias[i]['pnl_movimento_contrato']
    positivos = sorted([e['movimento_contrato_usdt'] for e in episodios
                        if e['movimento_contrato_usdt'] > 0], reverse=True)
    total_positivo = sum(positivos)
    t = pd.to_datetime([d['origem_ms'] for d in dias], unit='ms', utc=True)
    etiquetas = [f'{x.year}S{1 if x.month <= 6 else 2}' for x in t]
    eq = curva['saldos_diarios']
    semestres = []
    for etiqueta in dict.fromkeys(etiquetas):
        ids = [i for i, x in enumerate(etiquetas) if x == etiqueta]
        a, b = ids[0], ids[-1]+1
        recorte = eq[a:b+1]
        semestres.append(dict(periodo_origens=etiqueta, dias=b-a,
            retorno_liquido=float(eq[b]/eq[a]-1),
            crescimento_log_diario=float(np.diff(np.log(recorte)).mean()),
            drawdown_fechamentos_diarios=float(np.max(1-recorte/np.maximum.accumulate(recorte))),
            patrimonio_inicio=float(eq[a]), patrimonio_fim=float(eq[b]), capital_reiniciado=False))
    return dict(decisoes={str(l): int(np.sum(sinais == l)) for l in (-1, 0, 1)},
                exposicao_executada={str(l): int(np.sum(lados == l)) for l in (-1, 0, 1)},
                reversoes_diretas=int(np.sum(lados[1:]*lados[:-1] < 0)),
                quantidade_episodios=len(episodios), episodios=episodios,
                concentracao=dict(ganhos_positivos_movimento_usdt=total_positivo,
                    fracao_tres_maiores_ganhos_movimento=sum(positivos[:3])/total_positivo if total_positivo else None,
                    limite='Concentração de movimentos positivos por episódio, não participação no lucro líquido.'),
                semestres=semestres,
                limite_drawdown='Principal: envelope intraminuto; recortes semestrais: fechamentos diários.')


def executar_carteira(destino, z, mercado, regras, referencia=None, identidade=None):
    destino = Path(destino)
    recibo = destino / 'recibo.json'
    if recibo.exists():
        anterior = ler_json(recibo)
        assert sha256(destino / anterior['artefato']) == anterior['sha256']
        assert anterior['identidade'] == identidade
        return anterior
    assert not destino.exists(), 'Tentativa incompleta preservada; investigar antes de continuar.'
    destino.mkdir(parents=True)
    inicio = time.monotonic()
    try:
        r, cv = simular(z['origens_ms'], z['previsoes'], z['ultimo_close'], mercado, regras, 'liquida')
    except ValueError as erro:
        if 'Violação prudencial' not in str(erro):
            raise
        salvar_json(destino / 'falha.json', dict(utc=agora(), erro=str(erro), identidade=identidade,
                    natureza='falha_prudencial_preservada', regras=regras))
        saida = dict(utc=agora(), identidade=identidade, situacao='falha_prudencial',
                     artefato='falha.json', sha256=sha256(destino / 'falha.json'),
                     segundos=time.monotonic()-inicio, metricas=None)
        salvar_json(recibo, saida)
        return saida
    auditoria = conferir(r, cv, mercado, regras, 'liquida', z['origens_ms'], z['previsoes'], z['ultimo_close'], None)
    controle = comparar_carteiras(r, cv, *referencia) if referencia is not None else None
    descricao = descrever(r, cv)
    with zipfile.ZipFile(destino / 'carteira.zip', 'x', compression=zipfile.ZIP_DEFLATED) as arquivo:
        arquivo.writestr('resultado.json', json.dumps(dict(regras=regras, **r), ensure_ascii=False, allow_nan=False))
        buf = io.BytesIO()
        np.savez_compressed(buf, origens_ms=z['origens_ms'], **cv)
        arquivo.writestr('curva.npz', buf.getvalue())
    saida = dict(utc=agora(), identidade=identidade, situacao='concluida_conferida',
                 artefato='carteira.zip', sha256=sha256(destino / 'carteira.zip'),
                 segundos=time.monotonic()-inicio, metricas=r['metricas'],
                 auditoria=auditoria, controle=controle, descricao=descricao)
    salvar_json(recibo, saida)
    return saida


def ler_carteira(destino):
    destino = Path(destino)
    recibo = ler_json(destino / 'recibo.json')
    assert recibo['situacao'] == 'concluida_conferida'
    assert sha256(destino / 'carteira.zip') == recibo['sha256']
    with zipfile.ZipFile(destino / 'carteira.zip') as arquivo:
        resultado = json.loads(arquivo.read('resultado.json'))
        with np.load(io.BytesIO(arquivo.read('curva.npz')), allow_pickle=False) as q:
            curva = {k: q[k].copy() for k in q.files}
    return resultado, curva


def agregar_pacotes(destino, unidades):
    destino = Path(destino)
    assert not destino.exists()
    with zipfile.ZipFile(destino, 'x', compression=zipfile.ZIP_DEFLATED) as arquivo:
        for membro, pasta in unidades:
            recibo = ler_json(Path(pasta) / 'recibo.json')
            assert sha256(Path(pasta) / recibo['artefato']) == recibo['sha256']
            if recibo['situacao'] == 'falha_prudencial':
                arquivo.writestr(membro + '/falha.json', (Path(pasta) / 'falha.json').read_bytes())
            else:
                with zipfile.ZipFile(Path(pasta) / 'carteira.zip') as origem:
                    for nome in ('resultado.json', 'curva.npz'):
                        arquivo.writestr(membro + '/' + nome, origem.read(nome))
    with zipfile.ZipFile(destino) as arquivo:
        assert arquivo.testzip() is None
