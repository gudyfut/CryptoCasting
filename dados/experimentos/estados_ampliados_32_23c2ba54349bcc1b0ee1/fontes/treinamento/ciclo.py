"""Congelar, conferir e executar são ações distintas; preparar nunca ajusta mercado."""
from pathlib import Path
import contextlib
import shutil
import traceback
from uuid import uuid4
import numpy as np
import pandas as pd
from infraestrutura.artefatos import (RAIZ, agora, identidade, ler_json, salvar_json, sha256,
                                     conferir_arquivos, fontes as listar_fontes, abrir_artefato)
from modelos.consumo import carregar_consumo
from .configuracao import carregar, grade, CAMINHO
from .ambiente import conferir as ambiente
from .preservacao import publicar, conferir, exclusividade

REGISTROS = RAIZ / 'registros/treinamento'


class ControleReprovado(ValueError):
    """Repetir até passar seria selecionar uma tentativa favorável."""


def fontes():
    f = listar_fontes('treinamento', 'avaliacao', 'modelos', 'entradas_modelo', 'mercado_binance', 'infraestrutura',
                     'tests_treinamento', 'tests_modelos', 'tests_dados')
    for p in (CAMINHO, 'configuracoes/modelos_ohlcv24_001.json', 'configuracoes/ohlcv24_001.json', 'run_treinamento.py'):
        f[p] = sha256(RAIZ / p)
    return f


def preparar(qualificacao):
    c = carregar()
    qpath = Path(qualificacao).resolve()
    q = ler_json(qpath)
    if q['status'] != 'aprovado' or q['fontes'] != fontes() or q['ambiente'] != ambiente():
        raise ValueError('Qualificação ausente, desatualizada ou de outro ambiente.')
    conferir_arquivos(qpath.parent, q['artefatos'])
    consumo = carregar_consumo(RAIZ / c['entradas_pasta'])
    abrir_artefato(RAIZ / c['mercado_pasta'])
    contrato = {'configuracao': c, 'fontes': fontes(), 'ambiente': ambiente(),
                'identidade_consumo': consumo.especificacao.identidade,
                'dependencias': {c[k]: sha256(RAIZ / c[k] / 'manifesto.json') for k in ('entradas_pasta', 'mercado_pasta')},
                'qualificacao': {'arquivo': qpath.relative_to(RAIZ).as_posix(), 'sha256': sha256(qpath)},
                'protocolo_sha256': sha256(RAIZ / 'docs/desenho_ohlcv24.md')}
    codigo = identidade(contrato)[:20]
    pasta = RAIZ / f'dados/experimentos/ohlcv_modular_{codigo}'
    if not pasta.exists():
        pasta.mkdir(parents=True)
        for nome in contrato['fontes']:
            destino = pasta / 'fontes' / nome
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(RAIZ / nome, destino)
        shutil.copy2(RAIZ / 'docs/desenho_ohlcv24.md', pasta / 'protocolo.md')
        salvar_json(pasta / 'congelamento.json', {'id': codigo, 'utc': agora(), 'contrato': contrato})
        salvar_json(pasta / 'progresso.json', {'status': 'aguardando_ok', 'concluidos': [], 'treinamentos_mercado': 0})
    elif ler_json(pasta / 'congelamento.json')['contrato'] != contrato:
        raise ValueError('Identidade divergente.')
    ponteiro = {'id': codigo, 'pasta': pasta.relative_to(RAIZ).as_posix(),
                'congelamento_sha256': sha256(pasta / 'congelamento.json')}
    # Verificação antes de publicar o ponteiro; não aceita pasta parcialmente preparada.
    conferir_arquivos(pasta / 'fontes', contrato['fontes'])
    conferir_arquivos(pasta, {'protocolo.md': contrato['protocolo_sha256']})
    if not (pasta / 'progresso.json').is_file():
        raise ValueError('Preparação incompleta; preservar e investigar.')
    salvar_json(REGISTROS / 'execucao.json', ponteiro)
    return ponteiro


def conferir_execucao():
    p = ler_json(REGISTROS / 'execucao.json')
    pasta = RAIZ / p['pasta']
    conferir_arquivos(pasta, {'congelamento.json': p['congelamento_sha256']})
    f = ler_json(pasta / 'congelamento.json')
    c = f['contrato']
    if p['id'] != f['id'] or f['id'] != identidade(c)[:20]:
        raise ValueError('Identidade congelada inválida.')
    conferir_arquivos(RAIZ, c['fontes'])
    conferir_arquivos(pasta / 'fontes', c['fontes'])
    conferir_arquivos(pasta, {'protocolo.md': c['protocolo_sha256']})
    conferir_arquivos(RAIZ, {c['qualificacao']['arquivo']: c['qualificacao']['sha256']})
    qpath = RAIZ / c['qualificacao']['arquivo']
    q = ler_json(qpath)
    conferir_arquivos(qpath.parent, q['artefatos'])
    if q['status'] != 'aprovado' or q['fontes'] != c['fontes'] or c['ambiente'] != ambiente():
        raise ValueError('Qualificação/ambiente divergentes.')
    for nome, h in c['dependencias'].items():
        conferir_arquivos(RAIZ / nome, {'manifesto.json': h})
        abrir_artefato(RAIZ / nome)
    consumo = carregar_consumo(RAIZ / c['configuracao']['entradas_pasta'])
    if consumo.especificacao.identidade != c['identidade_consumo']:
        raise ValueError('Contrato de consumo divergente.')
    partes = {b: pd.read_parquet(RAIZ / c['configuracao']['entradas_pasta'] / f'{b}.parquet')
              for b in ('treino', 'validacao', 'teste', 'operacional')}
    return pasta, f, consumo, partes


def conferir_autorizacao(caminho, codigo, celulas):
    a = ler_json(caminho)
    if (a.get('execucao') != codigo or a.get('acao') != 'treinar_validar_testar'
            or a.get('celulas') != [c['chave'] for c in celulas]
            or not a.get('mensagem_usuario') or not a.get('utc')):
        raise ValueError('Exige autorização explícita do pesquisador vinculada à execução e orçamento.')
    return a


def reproducao(referencia, repeticao, cfg):
    a, b = [ler_json(p / 'resultado.json') for p in (referencia, repeticao)]
    deltas = {}
    for parte in ('validacao', 'teste', 'operacional'):
        x, y = [pd.read_parquet(p / f'previsoes_{parte}.parquet') for p in (referencia, repeticao)]
        pd.testing.assert_frame_equal(x.drop(columns='previsao'), y.drop(columns='previsao'), check_exact=True)
        delta = np.abs(x.previsao.to_numpy() - y.previsao.to_numpy())
        if not np.isfinite(delta).all():
            raise ValueError('Reprodução não finita.')
        deltas[parte] = float(delta.max())
    relativa = abs(a['metricas']['validacao']['mse'] - b['metricas']['validacao']['mse']) / max(a['metricas']['validacao']['mse'], 1e-15)
    mesma = a['epoca_selecionada'] == b['epoca_selecionada']
    r = {'maxima_diferenca_previsoes': deltas, 'diferenca_relativa_mse_validacao': relativa,
         'mesma_epoca': mesma, 'limites': cfg}
    if not mesma or max(deltas.values()) > cfg['diferenca_absoluta_previsao'] or relativa > cfg['diferenca_relativa_mse']:
        raise ControleReprovado(f'Controle reprovado; não selecionar outra tentativa: {r}')
    return r


def executar(autorizacao, retomar=False):
    from .neural import ajustar as ajustar_neural
    from .arima import ajustar as ajustar_arima
    from .avaliar import avaliar
    from avaliacao.publicacao import concluir
    pasta, congelado, consumo, partes = conferir_execucao()
    c = congelado['contrato']['configuracao']
    celulas = grade(c)
    a = conferir_autorizacao(autorizacao, congelado['id'], celulas)
    with exclusividade(pasta, retomar):
        estado = ler_json(pasta / 'progresso.json')
        if estado['status'] == 'concluido':
            raise ValueError('Execução concluída não pode ser reexecutada.')
        if estado['status'] != 'aguardando_ok' and not retomar:
            raise ValueError('Retomada exige investigação explícita.')
        registro = pasta / 'autorizacao.json'
        if registro.exists() and ler_json(registro) != a:
            raise ValueError('Autorização já registrada não pode ser substituída.')
        if not registro.exists():
            salvar_json(registro, a)
        concluidos = {}
        try:
            for celula in celulas:
                chave = celula['chave']
                raiz = pasta / 'celulas' / chave
                anteriores = sorted(raiz.glob('tentativa_*'))
                for anterior in anteriores:
                    if (anterior / 'falha.json').exists() and ler_json(anterior / 'falha.json').get('bloqueia_repeticao'):
                        raise ControleReprovado('Controle anterior reprovado; retomada não pode buscar resultado favorável.')
                prontas = [p for p in anteriores if (p / 'conclusao.json').exists()]
                if len(prontas) > 1:
                    raise ValueError('Múltiplos resultados concluídos; seleção indevida de tentativa.')
                if prontas:
                    tentativa = prontas[0]
                    conferir(tentativa)
                else:
                    tentativa = raiz / f'tentativa_{len(anteriores) + 1:03d}'
                    tentativa.mkdir(parents=True)
                    vinculo = {'execucao': congelado['id'], 'celula': celula,
                               'configuracao_treino': c['treino'], 'identidade_consumo': consumo.especificacao.identidade}
                    salvar_json(tentativa / 'inicio.json', {'utc': agora(), 'vinculo': vinculo,
                                'anteriores_preservadas': [p.name for p in anteriores]})
                    salvar_json(pasta / 'progresso.json', {'status': 'executando', 'atual': chave,
                                'concluidos': list(concluidos), 'utc': agora()})
                    try:
                        with (tentativa / 'treinamento.log').open('w', encoding='utf-8', buffering=1) as log:
                            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                                rede, ajuste = None, None
                                if celula['modelo'] in ('mamba', 'lstm'):
                                    rede, ajuste = ajustar_neural(consumo, celula['modelo'], celula['seed'], c['treino'],
                                                                 RAIZ / c['configuracao_modelos'], tentativa, vinculo)
                                elif celula['modelo'] == 'arima':
                                    ajustar_arima(consumo, c['arima'], tentativa)
                                avaliar(consumo, partes, celula['modelo'], c, tentativa, vinculo, rede, ajuste)
                                del rede
                        if celula.get('controle'):
                            r = reproducao(concluidos[f"{celula['modelo']}_{celula['seed']}"], tentativa, c['reproducao'])
                            salvar_json(tentativa / 'reproducao.json', r)
                        publicar(tentativa)
                    except BaseException as erro:
                        salvar_json(tentativa / 'falha.json', {'utc': agora(), 'erro': traceback.format_exc(),
                                    'bloqueia_repeticao': isinstance(erro, ControleReprovado)})
                        raise
                if celula.get('controle'):
                    reproducao(concluidos[f"{celula['modelo']}_{celula['seed']}"], tentativa, c['reproducao'])
                concluidos[chave] = tentativa
            if set(concluidos) != {q['chave'] for q in celulas}:
                raise ValueError('Cobertura incompleta.')
            # Conferência final de fontes/artefatos antes de publicar resultados.
            conferir_arquivos(RAIZ, congelado['contrato']['fontes'])
            for tentativa in concluidos.values():
                conferir(tentativa)
            concluir(pasta, c, {'mercado': c['mercado_pasta']}, partes, concluidos)
            salvar_json(pasta / 'progresso.json', {'status': 'concluido', 'utc': agora(), 'concluidos': list(concluidos)})
        except BaseException:
            salvar_json(pasta / 'progresso.json', {'status': 'interrompido', 'utc': agora(),
                        'concluidos': list(concluidos), 'erro': traceback.format_exc()})
            raise
