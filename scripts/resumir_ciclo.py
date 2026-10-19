"""Resumo descritivo da grade completa, sem ajustar modelos ou escolher políticas."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from barreiras.arquivos import agora, identidade, ler_json, salvar_json, sha256
from scripts.descrever_amostras import descrever


def registros(quadro):
    return json.loads(quadro.to_json(orient='records', double_precision=15))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('diretorio', type=Path)
    parser.add_argument('--destino', type=Path, required=True)
    args = parser.parse_args()
    raiz = args.diretorio.resolve()
    fontes = {}

    def fonte(caminho, hashes=None, relativo=None):
        digest = sha256(caminho)
        if hashes is not None and hashes.get(relativo) != digest:
            raise ValueError(f'Hash divergente: {caminho}')
        fontes[str(caminho.relative_to(RAIZ)).replace('\\', '/')] = digest
        return caminho

    def ler(caminho, hashes=None, relativo=None):
        return ler_json(fonte(caminho, hashes, relativo))

    ciclo = ler(raiz / 'ciclo.json')
    if identidade(ciclo['assinatura'])[:20] != ciclo['id']:
        raise ValueError('Identidade do ciclo divergente.')
    config = ciclo['assinatura']['configuracao']
    if config['seeds'] != [42] or set(config['folds']) != {'DB1', 'DB2', 'DB3', 'DB4'}:
        raise ValueError('Resumo especificado para o ciclo inicial de desenvolvimento.')
    resumo = ler(raiz / 'consolidacao/resumo.json')
    auditoria = ler(raiz / 'consolidacao/auditoria_suplementar.json')
    if (resumo['status'] != 'completo' or resumo['celulas_auditadas'] != 96
            or auditoria['status'] != 'aprovado' or auditoria['auditadas'] != 96
            or auditoria['id_ciclo'] != ciclo['id'] or resumo['id_ciclo'] != ciclo['id']):
        raise ValueError('Exige grade inicial completa e auditoria suplementar aprovada.')
    auditadas = {a['id']: a for a in auditoria['verificacoes']}
    metricas, treinos, financas, classes = [], [], [], []
    amostras, cortes, vistas = {}, {}, set()
    for arquivo in sorted(raiz.glob('*/estado.json')):
        estado = ler(arquivo)
        if estado['status'] != 'concluida_auditada' or estado['id'] not in auditadas:
            raise ValueError('Tentativa não auditada incluída no resumo.')
        celula = estado['celula']
        chave = tuple(celula[k] for k in ('par', 'contexto', 'horizonte', 'fold', 'seed'))
        if chave in vistas or estado['id_ciclo'] != ciclo['id']:
            raise ValueError('Célula duplicada ou de outro ciclo.')
        vistas.add(chave)
        pasta = arquivo.parent
        hashes = ler(pasta / 'integridade.json')
        referencia = ler(pasta / 'referencia_constante.json', hashes, 'referencia_constante.json')
        if referencia != estado['referencia_constante']:
            raise ValueError('Referência constante alterada no registro.')
        for modelo in ('mamba', 'lstm', 'ar1', 'frequencia_treino'):
            if modelo == 'frequencia_treino':
                met = referencia['metricas_teste']
            else:
                resultado = ler(pasta / modelo / 'resultado_modelo.json', hashes, f'{modelo}/resultado_modelo.json')
                if resultado != estado['resultados'][modelo]:
                    raise ValueError('Métricas do registro divergentes do artefato.')
                met = resultado['metricas']['teste']
                aval = auditadas[estado['id']]['modelos'][modelo]
                if not np.isclose(met['log_loss'], aval['log_loss_recalculada'], atol=1e-12, rtol=0):
                    raise ValueError('Métrica divergente da auditoria suplementar.')
                q = pd.read_parquet(fonte(pasta / modelo / 'previsoes_teste.parquet', hashes, f'{modelo}/previsoes_teste.parquet'))
                p = q[['p0', 'p1', 'p2']].to_numpy()
                y = q.classe.to_numpy()
                for k in range(3):
                    classes.append({**celula, 'modelo': modelo, 'classe': k,
                        'probabilidade_media': float(p[:, k].mean()),
                        'frequencia_observada': float((y == k).mean()),
                        'brier_classe': float(np.square(p[:, k] - (y == k)).mean())})
                if modelo == 'mamba' and celula['contexto'] == 24:
                    amostras.setdefault((celula['par'], celula['horizonte']), []).append(q)
                    origens = tuple(q.origem_utc.astype(str))
                    anterior = cortes.setdefault(celula['fold'], origens)
                    if anterior != origens:
                        raise ValueError('Origens não comuns entre moedas e prazos.')
                fin = ler(pasta / modelo / 'financeiro.json', hashes, f'{modelo}/financeiro.json')
                if fin != estado['financeiro'][modelo]:
                    raise ValueError('Financeiro divergente do artefato.')
                for variante in ('base', 'custos_agravados', 'ambiguidade_superior', 'sem_filtro'):
                    v = fin[variante]
                    financas.append({**celula, 'modelo': modelo, 'variante': variante,
                        **{k: v.get(k) for k in ('status', 'operacoes', 'retorno_liquido', 'drawdown_maximo', 'tempo_exposto')}})
                if modelo != 'ar1':
                    epocas = ler(pasta / modelo / 'epocas.json', hashes, f'{modelo}/epocas.json')
                    selecionada = next(e for e in epocas if e['epoca'] == resultado['epoca_selecionada'])
                    treinos.append({**celula, 'modelo': modelo,
                        **{k: resultado[k] for k in ('epoca_selecionada', 'epocas_executadas', 'parametros', 'segundos', 'memoria_cuda_maxima_bytes')},
                        'treino_log_loss_epoca_selecionada': selecionada['treino_log_loss'],
                        'validacao_log_loss_epoca_selecionada': selecionada['validacao_log_loss'],
                        'diferenca_validacao_treino': selecionada['validacao_log_loss'] - selecionada['treino_log_loss']})
            metricas.append({**celula, 'modelo': modelo, 'id': estado['id'],
                **{k: met[k] for k in ('n', 'log_loss', 'brier', 'balanced_accuracy', 'macro_f1')},
                'ambiguos': met['ambiguidade']['n'],
                'log_loss_ambiguidade_inferior': met['ambiguidade']['limite_inferior_log_loss'],
                'log_loss_ambiguidade_superior': met['ambiguidade']['limite_superior_log_loss']})
    if len(vistas) != 96:
        raise ValueError('Contagem de células divergente.')
    m = pd.DataFrame(metricas)
    medidas = ['log_loss', 'brier', 'balanced_accuracy', 'macro_f1']
    medias = m.groupby('modelo')[medidas].mean().reset_index()
    for modelo, valores in resumo['medias_das_celulas_disponiveis'].items():
        for medida, valor in valores.items():
            atual = medias.loc[medias.modelo.eq(modelo), medida].item()
            if not np.isclose(atual, valor, rtol=0, atol=1e-12):
                raise ValueError('Média não reproduz a consolidação.')
    contrastes = ler(raiz / 'consolidacao/efeito_contexto.json')
    contexto = pd.DataFrame([
        {k: v for k, v in c.items() if k != 'intervalos'} |
        {f'ic{bloco}_{lado}': limites[i] for bloco, limites in c['intervalos'].items()
         for i, lado in enumerate(('inferior', 'superior'))}
        for c in contrastes])
    contexto['favorece_168'] = contexto.diferenca_log_loss.gt(0).astype(int)
    contexto_resumo = contexto.groupby(['modelo', 'horizonte']).agg(
        diferenca_log_loss=('diferenca_log_loss', 'mean'),
        pares=('diferenca_log_loss', 'size'), favorece_168=('favorece_168', 'sum')).reset_index()
    fin = pd.DataFrame(financas)
    anual = ler(raiz / 'consolidacao/financeiro_concatenado.json')
    anual_linhas = []
    for a in anual:
        filtro = np.ones(len(fin), dtype=bool)
        for k in ('par', 'contexto', 'horizonte', 'seed', 'modelo', 'variante'):
            filtro &= fin[k].eq(a[k])
        partes = fin.loc[filtro]
        if len(partes) != 4:
            raise ValueError('Estratégia anual sem quatro folds.')
        valido = a['status'] == 'auditavel'
        if valido:
            composto = float(np.prod(1 + partes.retorno_liquido) - 1)
            if not np.isclose(composto, a['retorno_liquido'], rtol=0, atol=1e-10):
                raise ValueError('Retorno anual não reproduz os folds.')
        limites = a.get('intervalos', {}).get('14', {}).get('retorno_liquido', [None, None])
        anual_linhas.append({k: v for k, v in a.items() if k != 'intervalos'} | {
            'operacoes': int(partes.operacoes.sum()) if valido else None,
            'retorno_ic14_inferior': limites[0], 'retorno_ic14_superior': limites[1]})
    descricoes = []
    for (par, horizonte), partes in sorted(amostras.items()):
        q = pd.concat(partes).sort_values('origem_utc').reset_index(drop=True)
        if q.origem_utc.duplicated().any():
            raise ValueError('Origem duplicada na descrição anual.')
        descricoes.append({'par': par, 'horizonte': horizonte, **descrever(q)})
    t = pd.DataFrame(treinos)
    treino_resumo = t.groupby('modelo').agg(
        ajustes=('epoca_selecionada', 'size'), parametros=('parametros', 'first'),
        epoca_selecionada_mediana=('epoca_selecionada', 'median'),
        epoca_selecionada_minima=('epoca_selecionada', 'min'),
        epoca_selecionada_maxima=('epoca_selecionada', 'max'),
        epocas_executadas_mediana=('epocas_executadas', 'median'),
        diferenca_validacao_treino_mediana=('diferenca_validacao_treino', 'median'),
        segundos_totais_observados=('segundos', 'sum'),
        memoria_cuda_maxima_bytes=('memoria_cuda_maxima_bytes', 'max')).reset_index()
    treino_resumo['selecionou_primeira_epoca'] = treino_resumo.modelo.map(t.groupby('modelo').epoca_selecionada.apply(lambda x: int(x.eq(1).sum())))
    pares_modelos = m.pivot(index=['par', 'contexto', 'horizonte', 'fold', 'seed'], columns='modelo', values='log_loss')
    diferencas = (pares_modelos.mamba - pares_modelos.lstm).rename('mamba_menos_lstm').reset_index()
    controles = ler(raiz / 'consolidacao/controles/auditoria.json')
    fonte(raiz / 'consolidacao/diagnostico_sinais.csv')
    fonte(raiz / 'consolidacao/descricao_amostras.json')
    fonte(raiz / 'consolidacao/populacoes_operacionais.csv')
    saida = args.destino.resolve()
    saida.mkdir(parents=True, exist_ok=True)
    quadros = {
        'metricas_por_celula': m, 'treinamentos': t,
        'financeiro_anual': pd.DataFrame(anual_linhas),
        'barreiras_observadas': pd.DataFrame(descricoes),
        'efeito_contexto': contexto,
        'classes_probabilidades': pd.DataFrame(classes),
    }
    for nome, quadro in quadros.items():
        quadro.to_csv(saida / f'{nome}.csv', index=False)
    relatorio = {'id_ciclo': ciclo['id'], 'dataset': ciclo['assinatura']['dataset'],
        'criado_utc': agora(), 'script_sha256': sha256(Path(__file__)),
        'descricao_script_sha256': sha256(RAIZ / 'scripts/descrever_amostras.py'),
        'celulas': len(vistas), 'origens_teste_por_fold': {k: len(v) for k, v in sorted(cortes.items())},
        'ponderacao': 'Médias com peso igual por célula e fold, seed 42; quantis de barreiras calculados sobre origens concatenadas, sem repetir W/modelo.',
        'medias': registros(medias), 'contrastes_globais': resumo['contrastes_globais'],
        'por_horizonte': registros(m.groupby(['horizonte', 'modelo'])[medidas].mean().reset_index()),
        'por_moeda': registros(m.groupby(['par', 'modelo'])[medidas].mean().reset_index()),
        'por_fold': registros(m.groupby(['fold', 'modelo'])[medidas].mean().reset_index()),
        'contexto': registros(contexto_resumo),
        'nota_contexto': 'W24 menos W168: positivo favorece sequência longa. Resumo descritivo; não calcular média dos limites dos intervalos individuais.',
        'treinamentos': registros(treino_resumo),
        'mamba_menor_log_loss_que_lstm': int(diferencas.mamba_menos_lstm.lt(0).sum()),
        'classes_por_horizonte': registros(pd.DataFrame(classes).groupby(['horizonte', 'modelo', 'classe'])[['probabilidade_media', 'frequencia_observada', 'brier_classe']].mean().reset_index()),
        'comprar_manter_pontas': controles['complemento_pontas_concatenadas'],
        'arquivos_saida': {p.name: sha256(p) for p in sorted(saida.glob('*.csv'))},
        'fontes': fontes}
    salvar_json(saida / 'resumo.json', relatorio)
    print(json.dumps({k: relatorio[k] for k in ('id_ciclo', 'celulas', 'origens_teste_por_fold', 'medias', 'contexto', 'treinamentos')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
