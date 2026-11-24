"""Conferência global de cobertura, preservação, publicação e orçamento."""
import argparse
import csv
import json
import platform
from pathlib import Path
from infraestrutura.artefatos import RAIZ, agora, conferir_arquivos, ler_json, salvar_json, sha256
from .comum import contexto, configuracao
from .inventario import REG, relativo


def conferir():
    c = configuracao()
    inv = ler_json(REG / 'inventario.json')
    conferir_arquivos(RAIZ, {k: v['sha256'] for k, v in inv['arquivos'].items()})
    conferir_arquivos(RAIZ, ler_json(REG / 'artigo_preservado.json'))
    conferir_arquivos(REG / 'documentos_anteriores', ler_json(REG / 'documentos_anteriores/manifesto.json'))
    decisao = ler_json(REG / 'ablacao_timestamp/decisao.json')
    etapas = ['lstm_walkforward', 'sensibilidade_filtro', 'deslocamento_exposicao', 'referencias_exposicao']
    if decisao['executar']:
        etapas.append('ablacao_timestamp')
    auditorias, pastas, arquivos = {}, {}, {}
    for etapa in etapas:
        q = ler_json(REG / etapa / 'conferencia_posterior.json')
        assert q['situacao'] == 'aprovada' and sha256(RAIZ / q['arquivo']) == q['sha256']
        ptr, p, f = contexto(etapa)
        pastas[etapa] = p
        fecho = ler_json(REG / etapa / 'fechamento.json')
        assert sha256(RAIZ / fecho['arquivo']) == fecho['sha256']
        conferir_arquivos(p, ler_json(p / 'fechamento.json')['arquivos'])
        auditorias[etapa] = dict(arquivo=relativo(REG / etapa / 'conferencia_posterior.json'), sha256=sha256(REG / etapa / 'conferencia_posterior.json'), execucao=ptr)
        arquivos[relativo(p / 'fechamento.json')] = sha256(p / 'fechamento.json')
        print('PRESERVACAO_CONFERIDA', etapa, flush=True)
    lstm = pastas['lstm_walkforward']
    lc = ler_json(lstm / 'treinamentos_concluidos.json')
    assert lc['cientificos'] == 12 and lc['controles'] == 2
    lo = ler_json(lstm / 'publicacao/operacoes.json')
    grade_lstm = {(x['bloco'], x['unidade'], x['custo']) for x in lo['carteiras']+lo['falhas']}
    assert grade_lstm == {(b['id'], f'LSTM_{s}', custo) for b in c['blocos'] for s in (*c['seeds'], 'ensemble') for custo in (1, 2, 3)}
    with (pastas['sensibilidade_filtro'] / 'publicacao/carteiras.csv').open(encoding='utf-8', newline='') as arq:
        linhas = list(csv.DictReader(arq))
    assert len(linhas) == 324
    observado = {(x['populacao'], x['moeda'], x['variante'], float(x['filtro']), int(x['custo'])) for x in linhas}
    from .contratos import grade_sensibilidade
    esperado = {(x['populacao'], x['moeda'], x['variante'], x['filtro'], x['custo']) for x in grade_sensibilidade(c)}
    assert observado == esperado
    with (pastas['deslocamento_exposicao'] / 'publicacao/carteiras.csv').open(encoding='utf-8', newline='') as arq:
        deslocamentos = list(csv.DictReader(arq))
    assert len(deslocamentos) == 2376
    dr = ler_json(pastas['deslocamento_exposicao'] / 'publicacao/resultados.json')
    assert len(dr['resumos']) == len(dr['controles']) == 24
    cientificos, controles = 12, 2
    if decisao['executar']:
        tp = pastas['ablacao_timestamp']
        t = ler_json(tp / 'treinamentos_concluidos.json')
        assert t['cientificos'] == 24 and t['controles'] == 4
        op = ler_json(tp / 'publicacao/operacoes.json')
        observado = {(x['bloco'], x['unidade'], x['custo']) for x in op['carteiras']+op['falhas']}
        esperado = {(b['id'], f'{v}_sem_timestamp_{s}', custo) for b in c['blocos'] for v in ('A', 'L') for s in (*c['seeds'], 'ensemble') for custo in (1, 2, 3)}
        assert len(observado) == 96 and observado == esperado
        assert len(ler_json(tp / 'publicacao/ramos.json')['populacoes']) == 36
        cientificos, controles = 36, 6
    assert cientificos <= 36 and controles <= 6
    _, pub_raiz, _ = contexto('sintese_complemento')
    pub = pub_raiz / 'publicacao'
    conferir_arquivos(pub_raiz, ler_json(pub_raiz / 'fechamento.json')['arquivos'])
    visual = ler_json(REG / 'sintese_complemento/inspecao_visual.json')
    assert visual['situacao'] == 'aprovada'
    assert set(visual['arquivos']) == {relativo(q) for q in pub.glob('*.png')}
    conferir_arquivos(RAIZ, visual['arquivos'])
    obrigatorias = dict(lstm_walkforward_previsoes=64, lstm_walkforward_operacoes=60,
        sensibilidade_carteiras=324, deslocamentos_carteiras=2376, deslocamentos_percentis=72, referencias_exposicao=32)
    if decisao['executar']:
        obrigatorias.update(timestamp_previsoes=84, timestamp_operacoes=120, timestamp_ramos=36)
    for nome, n in obrigatorias.items():
        with (pub / (nome+'.csv')).open(encoding='utf-8', newline='') as arq:
            assert len(list(csv.DictReader(arq))) == n, (nome, n)
    catalogo = ler_json(RAIZ / 'registros/catalogo_estudos.json')
    entrada = next(x for x in catalogo['estudos'] if x['chave'] == 'complemento_diario_001')
    assert entrada['situacao_historica'] == 'concluido_auditado'
    assert set(entrada['ciclos']) >= set(etapas)
    docs = ler_json(REG / 'documentacao_final.json')
    assert docs['situacao'] == 'concluida'
    conferir_arquivos(RAIZ, docs['arquivos'])
    assert 'escrita_tcc' not in ' '.join(docs['arquivos'])
    return dict(utc=agora(), situacao='aprovada', host=platform.node(),
        arquivos_pais_preservados=len(inv['arquivos']), arquivos_editoriais_preservados=len(ler_json(REG / 'artigo_preservado.json')),
        ajustes_cientificos=cientificos, controles_de_mercado=controles, qualificacoes_sinteticas_separadas=True,
        auditorias=auditorias, publicacao=relativo(pub), tabelas_integralmente_cobertas=obrigatorias,
        decisao_timestamp=decisao, documentos=docs, artefatos_de_fechamento=arquivos,
        resultado_positivo_nao_exigido=True, pendencias_obrigatorias=[])


def encerrar():
    assert not (REG / 'fechamento.json').exists(), 'Fechamento já existe; usar conferir, que é somente leitura.'
    resultado = conferir()
    salvar_json(REG / 'conferencia_encerramento.json', resultado)
    matriz = ler_json(REG / 'requisitos.json')
    for x in matriz['requisitos']:
        if x['id'].startswith(('22_', '23_', '24_', '25_')) and not resultado['decisao_timestamp']['executar']:
            x.update(situacao='dispensado_pelos_criterios_previos', evidencia='registros/complemento_diario/ablacao_timestamp/decisao.json')
        else:
            x.update(situacao='concluido', evidencia=x.get('evidencia', 'registros/complemento_diario/conferencia_encerramento.json'))
    salvar_json(REG / 'requisitos.json', matriz)
    salvar_json(REG / 'fechamento.json', dict(utc=agora(), situacao='concluido_auditado',
        conferencia_sha256=sha256(REG / 'conferencia_encerramento.json'), requisitos_sha256=sha256(REG / 'requisitos.json'),
        ajustes_cientificos=resultado['ajustes_cientificos'], controles=resultado['controles_de_mercado'], publicacao=resultado['publicacao']))
    salvar_json(REG / 'estado.json', dict(utc=agora(), situacao='concluido_auditado', artigo='preservado',
        fechamento='registros/complemento_diario/fechamento.json', pendencias_obrigatorias=[]))
    print('COMPLEMENTO_ENCERRADO', json.dumps({k: resultado[k] for k in ('ajustes_cientificos', 'controles_de_mercado', 'publicacao')}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('acao', choices=['conferir', 'encerrar'])
    acao = parser.parse_args().acao
    if acao == 'conferir':
        print(json.dumps(conferir(), ensure_ascii=False, indent=2))
    else:
        encerrar()
