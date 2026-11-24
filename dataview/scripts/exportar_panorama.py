"""Exportação de leitura para a apresentação. Não importa nem executa treinadores.

Os JSONs publicados e as previsões são conferidos contra seus manifestos.
As séries diárias são exemplos; as métricas mantêm toda a população horária.
"""
from pathlib import Path
import hashlib
import json
import math
from datetime import datetime, timezone
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / 'dados/portal_panorama'
FONTES = {}


def hash_bytes(b):
    return hashlib.sha256(b).hexdigest()


def ler(p, esperado=None):
    p = Path(p)
    if not p.is_absolute():
        p = RAIZ / p
    b = p.read_bytes()
    h = hash_bytes(b)
    if esperado and h != esperado:
        raise ValueError(f'Fonte divergente: {p}')
    FONTES[p.relative_to(RAIZ).as_posix()] = h
    return json.loads(b)


def publicar_json(p, j):
    p.parent.mkdir(parents=True, exist_ok=True)
    b = json.dumps(j, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()
    p.write_bytes(b)
    return hash_bytes(b)


PASTAS = {
    'r0': 'ohlcv_modular_ab5baf3eab3a2e66d8b2',
    'estado8': 'estado_mamba_dcf4b0ed9012f7247bce',
    'estado32': 'estados_ampliados_32_23c2ba54349bcc1b0ee1',
    'estado64': 'estados_ampliados_64_42cb667ea43df563e3ac',
    'complemento': 'complemento_estado16_cc0b166fe42a3ed1678d',
    'taxa': 'taxa_aprendizado_1af0a64e83d472ac533e',
    'crypto': 'cryptomamba_adaptado_35dd98141ee20d9b8885',
    'adamw': 'cryptomamba_adamw_6829c5fa076dc8c0e0ac',
    'dinamica': 'mamba16_taxa_dinamica_99884456ac71fedfd9b0',
    'huber': 'mamba16_perda_huber_ed8e55ff978b2742c200',
    'blocos': 'huber_blocos_10dac17ea9df2c540c57',
    'entradas': 'entradas_niveis_76f6c437e70eaaa605ad',
}


def exportar():
    publicacoes, series = {}, []
    for chave, pasta in PASTAS.items():
        raiz_ciclo = RAIZ / 'dados/experimentos' / pasta
        pub = raiz_ciclo / 'publicacoes/tentativa_001'
        manifesto = ler(pub / 'manifesto.json')
        j = ler(pub / 'resultados.json', manifesto['arquivos']['resultados.json'])
        # Somente campos necessários à apresentação; não expor logs/ambiente.
        publicacoes[chave] = {k: j[k] for k in ['medias', 'medias_globais', 'medias_por_bloco', 'contrastes', 'criterio_primario', 'medias_operacionais_por_bloco', 'utc'] if k in j}
        publicacoes[chave]['fonte'] = (pub / 'resultados.json').relative_to(RAIZ).as_posix()
        publicacoes[chave]['execucao'] = pasta.rsplit('_', 1)[-1]
        if chave in ['blocos', 'entradas']:
            publicacoes[chave]['benchmarks_blocos'] = {k: v for k, v in j['carteiras'].items() if '/benchmark/' in k}
        for conclusao in sorted(raiz_ciclo.glob('celulas/*/tentativa_001/conclusao.json')):
            celula = conclusao.parent.parent.name
            if 'controle' in celula:
                continue
            c = ler(conclusao)
            if c.get('status') != 'concluido':
                raise ValueError(f'Célula não concluída: {celula}')
            arq = conclusao.parent / 'previsoes_teste.parquet'
            esperado = c['arquivos'].get(arq.name)
            if esperado is None:
                continue
            b = arq.read_bytes()
            if hash_bytes(b) != esperado:
                raise ValueError(f'Previsões divergentes: {arq}')
            FONTES[arq.relative_to(RAIZ).as_posix()] = esperado
            resultado = ler(conclusao.parent / 'resultado.json', c['arquivos']['resultado.json'])
            df = pd.read_parquet(arq)
            assert np.isfinite(df[['close', 'preco_destino', 'alvo', 'previsao']]).all().all()
            assert (df.destino_utc - df.origem_utc == pd.Timedelta(hours=24)).all()
            assert df.origem_utc.is_unique and df.origem_utc.is_monotonic_increasing
            assert np.allclose(np.log(df.preco_destino / df.close), df.alvo, atol=1e-12, rtol=1e-10)
            m = resultado['metricas']['teste']
            mse = float(np.mean((df.previsao - df.alvo) ** 2))
            assert math.isclose(mse, m['mse'], rel_tol=1e-10, abs_tol=1e-14)
            diario = df[df.origem_utc.dt.hour == 0]
            pontos = [[int(x.origem_utc.timestamp()), float(x.close), float(x.preco_destino), float(x.alvo), float(x.previsao)] for x in diario.itertuples()]
            aprendizagem = []
            if 'epocas.json' in c['arquivos']:
                epocas = ler(conclusao.parent / 'epocas.json', c['arquivos']['epocas.json'])
                aprendizagem = [{'epoca': e['epoca'], 'mse_validacao': e['mse_validacao']} for e in epocas]
            registro = {'ciclo': chave, 'celula': celula, 'metricas': m, 'pontos': pontos,
                        'aprendizagem': aprendizagem, 'epoca_selecionada': resultado.get('epoca_selecionada'),
                        'colunas': ['origem_segundos_utc', 'preco_origem', 'preco_24h', 'alvo_log', 'previsao_log'],
                        'fonte': arq.relative_to(RAIZ).as_posix(), 'fonte_sha256': esperado}
            bruto = json.dumps(registro, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()
            identidade = hash_bytes(bruto)
            destino = SAIDA / 'series' / f'{identidade}.json'
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(bruto)
            partes = celula.split('_')
            bloco = partes[0] if partes[0] in ['B1', 'B2', 'B3', 'B4'] else '2025'
            seed = resultado.get('seed')
            modelo = '_'.join(partes[1:-1]) if bloco != '2025' else '_'.join(partes[:-1]) if seed is not None else celula
            series.append({'id': identidade, 'ciclo': chave, 'celula': celula, 'modelo': modelo, 'bloco': bloco, 'seed': seed, 'n': len(pontos), 'n_horario': len(df), 'epoca': resultado.get('epoca_selecionada'), 'mse': mse})
    for chave, pasta in [('retornos', 'registros/analises/1e7c5ed662fba55ddd25/avaliacao'), ('penalizacao', 'dados/experimentos/penalizacao_7868a4d847c1410fc681/analises/avaliacao'), ('prenorm', 'dados/experimentos/normalizacao_9e03af2150cbb7b1068d/analises/avaliacao')]:
        # Publicações históricas: manifesto de publicação original, sem reexecutar.
        manifesto = ler(f'{pasta}/publicacao.json')
        j = ler(f'{pasta}/resumo.json', manifesto['arquivos']['resumo.json'])
        publicacoes[chave] = {k: j[k] for k in ['modelos', 'contrastes', 'contextos', 'utc', 'gerado_utc'] if k in j}
        publicacoes[chave]['fonte'] = f'{pasta}/resumo.json'
    manifesto_back = ler('dados/experimentos/backtest_carteira_8ec8a66648313caa48e3/resultados/manifesto.json')
    back = ler('dados/experimentos/backtest_carteira_8ec8a66648313caa48e3/resultados/comparacao.json', manifesto_back['arquivos']['comparacao.json'])
    publicacoes['carteira'] = {'medias': back['medias'], 'fonte': 'dados/experimentos/backtest_carteira_8ec8a66648313caa48e3/resultados/comparacao.json'}
    manifesto_custos = ler('registros/diagnosticos_previsoes/cryptomamba_custos_20261103/manifesto_final.json')
    custos = ler('registros/diagnosticos_previsoes/cryptomamba_custos_20261103/custos_resultados.json', manifesto_custos['custos_resultados.json'])
    publicacoes['custos_publicos'] = {'series': custos['series'], 'fonte': 'registros/diagnosticos_previsoes/cryptomamba_custos_20261103/custos_resultados.json'}
    # Textos são fontes editoriais, explicitamente distintos das publicações conferidas.
    docs = list((RAIZ / 'docs').glob('resultados_*.md'))
    docs += [RAIZ / 'docs/desenho_ohlcv24.md', RAIZ / 'arquivo/estudo_barreiras_2026-10-20/README.md', RAIZ / 'arquivo/estudo_barreiras_2026-10-20/projeto/historico/analises/ciclo_001_resultados.md']
    docs += list((RAIZ / 'arquivo/estudos_preliminares_2026-10-28/documentacao').glob('resultados_*.md'))
    docs += list((RAIZ / 'docs/adr').glob('00*.md'))
    docs += [RAIZ / 'registros/entradas_niveis/entrega/20261103/conferencia.json']
    for p in docs:
        FONTES[p.relative_to(RAIZ).as_posix()] = hash_bytes(p.read_bytes())
    dados = {'gerado_utc': datetime.now(timezone.utc).isoformat(), 'publicacoes': publicacoes, 'series': series, 'fontes': FONTES,
             'natureza': 'Exportação de leitura; zero novos treinamentos, inferências ou simulações.'}
    destino = RAIZ / 'dataview/src/data/panorama.json'
    h = publicar_json(destino, dados)
    publicar_json(RAIZ / 'registros/interface/panorama_20261103/exportacao.json', {'utc': dados['gerado_utc'], 'arquivo': destino.relative_to(RAIZ).as_posix(), 'sha256': h, 'fontes': len(FONTES), 'series': len(series), 'pontos_diarios': sum(s['n'] for s in series), 'series_horizonte_alvo_mse_conferidos': True, 'novos_treinamentos': 0})
    print(json.dumps({'series': len(series), 'fontes': len(FONTES), 'sha256': h}))


if __name__ == '__main__':
    exportar()
