"""Resolve cada previsão e carteira de referência sem confundir populações."""
from functools import lru_cache
from pathlib import Path
import io
import json
import zipfile
import numpy as np
from infraestrutura.artefatos import RAIZ, ler_json, sha256, conferir_arquivos
from .comum import configuracao, pais, carregar_npz, contexto
from .inventario import relativo


@lru_cache(maxsize=32)
def indice(caminho):
    return ler_json(Path(caminho))


def selecionar_membros(pasta, filtros):
    linhas = indice(str(pasta / 'operacoes.json'))['carteiras']
    encontrados = [x for x in linhas if all(x.get(k) == v for k, v in filtros.items())]
    assert len(encontrados) == 3, (pasta, filtros, len(encontrados))
    assert {x['custo'] for x in encontrados} == {1, 2, 3}
    return {str(x['custo']): x['membro'] for x in encontrados}


def casos_fixos():
    c, refs = configuracao(), pais()
    f25 = ler_json(refs['fixa'] / 'congelamento.json')
    f26 = ler_json(refs['extensao'] / 'congelamento.json')
    periodo = RAIZ / f26['referencia_periodo']['pasta']
    mercados26 = ler_json(periodo / 'mercados.json')
    casos = []
    for ano in (2025, 2026):
        for moeda in c['moedas']:
            cfg = ler_json(refs['fixa'] / moeda / 'configuracao.json')
            mercado = f25['referencias']['moedas'][moeda]['mercado_minuto'] if ano == 2025 else mercados26[moeda]
            for variante in c['variantes']:
                unidade = f'{variante}_ensemble'
                if variante == 'LSTM':
                    pub = refs['lstm'] / 'publicacao'
                    previsao = pub / moeda / str(ano) / f'{unidade}.npz'
                    membros = selecionar_membros(pub, dict(moeda=moeda, ano=ano, unidade=unidade))
                elif ano == 2025:
                    pub = refs['fixa'] / moeda / 'publicacao'
                    previsao = pub / 'previsoes' / f'teste_{unidade}.npz'
                    membros = selecionar_membros(pub, dict(fase='teste', unidade=unidade))
                else:
                    pub = refs['extensao']
                    previsao = pub / moeda / f'{unidade}.npz'
                    membros = selecionar_membros(pub, dict(moeda=moeda, unidade=unidade))
                casos.append(dict(id=f'fixa_{ano}/{moeda}/{variante}', populacao=f'fixa_{ano}',
                         moeda=moeda, variante=variante, previsao=relativo(previsao),
                         mercado=mercado, regras=cfg['operacoes'],
                         zip_referencia=relativo(pub / 'carteiras.zip'), membros=membros,
                         n=350 if ano == 2025 else 314))
    assert len(casos) == 24
    return casos


def casos_walkforward():
    c, refs = configuracao(), pais()
    wf = ler_json(refs['walkforward'] / 'congelamento.json')
    _, nova, _ = contexto('lstm_walkforward', conferir=False)
    casos = []
    for bloco in c['blocos']:
        b = bloco['id']
        for variante in c['variantes']:
            pub = (nova if variante == 'LSTM' else refs['walkforward']) / 'publicacao'
            unidade = f'{variante}_ensemble'
            membros = selecionar_membros(pub, dict(bloco=b, unidade=unidade))
            casos.append(dict(id=f'{b}/BTCUSDT/{variante}', populacao=b, moeda='BTCUSDT',
                    variante=variante, previsao=relativo(pub / b / 'previsoes' / f'{unidade}.npz'),
                    mercado=wf['referencias']['mercado'], regras=wf['configs_blocos'][b]['operacoes'],
                    zip_referencia=relativo(pub / 'carteiras.zip'), membros=membros, n=bloco['n_teste']))
    assert len(casos) == 12
    return casos


def conferir_populacoes(casos):
    grupos = {}
    for caso in casos:
        z = carregar_npz(RAIZ / caso['previsao'])
        assert len(z['origens_ms']) == caso['n']
        assert np.all(np.diff(z['origens_ms']) == 86400000)
        assert z['previsoes'].shape == z['ultimo_close'].shape == z['alvo_retorno'].shape
        assert np.isfinite(z['previsoes']).all()
        assert np.isfinite(z['alvo_retorno']).all() and np.all(z['ultimo_close'] > 0)
        chave = (caso['populacao'], caso['moeda'])
        if chave in grupos:
            for k in ('origens_ms', 'ultimo_close', 'alvo_retorno'):
                np.testing.assert_array_equal(z[k], grupos[chave][k], err_msg=str(chave) + k)
        else:
            grupos[chave] = z
    return dict(casos=len(casos), populacoes=len(grupos), comparabilidade_exata=True)


def entradas(casos):
    arquivos = set()
    for caso in casos:
        arquivos.add(RAIZ / caso['previsao'])
        arquivos.add(RAIZ / caso['zip_referencia'])
        p = RAIZ / caso['mercado']['pasta']
        assert sha256(p / 'manifesto.json') == caso['mercado']['manifesto_sha256']
        manifesto = ler_json(p / 'manifesto.json')
        conferir_arquivos(p, manifesto['arquivos'])
        arquivos.add(p / 'manifesto.json')
        arquivos.update(p / n for n in manifesto['arquivos'])
    return sorted(arquivos)


def carteira_referencia(caso, custo):
    membro = caso['membros'][str(custo)]
    with zipfile.ZipFile(RAIZ / caso['zip_referencia']) as z:
        resultado = json.loads(z.read(membro + '/resultado.json'))
        with np.load(io.BytesIO(z.read(membro + '/curva.npz')), allow_pickle=False) as q:
            curva = {k: q[k].copy() for k in q.files}
    return resultado, curva


def comparar_carteiras(resultado, curva, antigo, anterior):
    """Ledger e saldos devem reproduzir exatamente; metadados podem diferir."""
    for campo in ('ordens', 'dias', 'funding', 'rejeicoes', 'metricas'):
        assert resultado[campo] == antigo[campo], f'Reprodução diverge: {campo}'
    for k in ('saldos_diarios', 'drawdown_acumulado'):
        np.testing.assert_array_equal(curva[k], anterior[k], err_msg=k)
    return dict(aprovado=True, ledger_exato=True, curva_exata=True, metricas_exatas=True)
