"""Grades fixas de filtros e deslocamentos; sem treino ou seleção de políticas."""
from copy import deepcopy
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import sys
import time
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, conferir_arquivos, ler_json, salvar_json, sha256
from experimentos.generalizacao_moedas.avaliacao import carregar_mercado
from .inventario import REG, relativo
from .comum import (configuracao, contexto, congelar, exclusividade, fontes,
                    registrar_estado, carregar_npz, fechar, pais)
from .contratos import decisoes, precos_decisoes, deslocamentos
from .fontes_operacionais import (casos_fixos, casos_walkforward, conferir_populacoes,
                                  entradas, carteira_referencia)
from .operacoes import executar_carteira


def qualificar():
    etapa = 'qualificacao_operacional'
    with exclusividade(etapa):
        c = configuracao()
        destino = REG / etapa / str(time.time_ns())
        destino.mkdir(parents=True)
        antes = fontes()
        salvar_json(destino / 'fontes_antes.json', antes)
        ensaios = subprocess.run([sys.executable, '-B', '-m', 'unittest',
                    'testes.complemento_diario.test_contratos',
                    'testes.simulacao_operacoes.test_auditoria_grade_continuidade.GradeInteira', '-v'],
                    cwd=RAIZ, capture_output=True, text=True)
        (destino / 'testes.log').write_text(ensaios.stdout + ensaios.stderr, encoding='utf-8')
        assert ensaios.returncode == 0, ensaios.stdout + ensaios.stderr
        casos = casos_fixos()
        conferidos = conferir_populacoes(casos)
        # Critério técnico pré-fixado: primeira população BTC/2025/A, não
        # escolher caso por desempenho ou trocar após falha.
        caso = casos[0]
        assert caso['id'] == 'fixa_2025/BTCUSDT/A'
        z = carregar_npz(RAIZ / caso['previsao'])
        tempo = time.monotonic()
        mercado = carregar_mercado(caso['mercado'])
        carga = time.monotonic()-tempo
        regras = deepcopy(caso['regras'])
        regras['slippage_por_lado'] = .0001
        base = carteira_referencia(caso, 1)
        r = executar_carteira(destino / 'controle_base', z, mercado, regras,
                              referencia=base, identidade='controle_base_BTC2025A')
        zz = dict(z, previsoes=precos_decisoes(decisoes(z['previsoes'], z['ultimo_close'], .002), z['ultimo_close'], .002))
        rz = executar_carteira(destino / 'controle_zero', zz, mercado, regras,
                               referencia=base, identidade='controle_zero_BTC2025A')
        assert r['situacao'] == rz['situacao'] == 'concluida_conferida'
        conferir_arquivos(RAIZ, antes)
        q = dict(utc=agora(), situacao='aprovada', fontes=antes, populacoes=conferidos,
                 controle_base=r, controle_zero=rz, segundos_carga_mercado=carga,
                 plataforma=sys.platform, python=sys.version, numpy=np.__version__, pandas=pd.__version__,
                 criterio_piloto='Primeiro caso fixo: BTC/2025/A; reprodução de resultado conhecido.')
        salvar_json(destino / 'qualificacao.json', q)
        salvar_json(REG / 'qualificacao_operacional.json', dict(arquivo=relativo(destino / 'qualificacao.json'),
                    sha256=sha256(destino / 'qualificacao.json')))
        registrar_estado(etapa, 'aprovada', segundos_carteira=r['segundos'],
                          segundos_zero=rz['segundos'], segundos_carga=carga)


def exigir_auditoria(etapa):
    q = ler_json(REG / etapa / 'conferencia_posterior.json')
    assert q['situacao'] == 'aprovada', f'Etapa {etapa} ainda não auditada.'


def preparar(etapa):
    assert etapa in ('sensibilidade_filtro', 'deslocamento_exposicao')
    exigir_auditoria('lstm_walkforward' if etapa == 'sensibilidade_filtro' else 'sensibilidade_filtro')
    qp = ler_json(REG / 'qualificacao_operacional.json')
    assert sha256(RAIZ / qp['arquivo']) == qp['sha256']
    q = ler_json(RAIZ / qp['arquivo'])
    conferir_arquivos(RAIZ, q['fontes'])
    casos = casos_fixos() + (casos_walkforward() if etapa == 'sensibilidade_filtro' else [])
    populacoes = conferir_populacoes(casos)
    deps = entradas(casos)
    extras = dict(casos=casos, populacoes=populacoes)
    if etapa == 'deslocamento_exposicao':
        extras['deslocamentos_por_n'] = {str(n): deslocamentos(n, configuracao()['deslocamentos']).tolist()
                                         for n in sorted({x['n'] for x in casos})}
    congelar(etapa, deps, RAIZ / qp['arquivo'], extras)


def linha_carteira(caso, recibo, **atributos):
    r = dict(populacao=caso['populacao'], moeda=caso['moeda'], variante=caso['variante'],
             situacao=recibo['situacao'], **atributos)
    if recibo['metricas'] is not None:
        r.update(recibo['metricas'])
        r['dias_caixa'] = recibo['descricao']['exposicao_executada']['0']
        r['reversoes_diretas'] = recibo['descricao']['reversoes_diretas']
        r['concentracao_tres_maiores'] = recibo['descricao']['concentracao']['fracao_tres_maiores_ganhos_movimento']
    return r


def sensibilidade():
    etapa = 'sensibilidade_filtro'
    with exclusividade(etapa):
        ptr, p, f = contexto(etapa)
        assert not (p / 'fechamento.json').exists()
        c, casos = f['configuracao'], f['extras']['casos']
        chave_mercado, mercado = None, None
        linhas, recibos = [], []
        filtros = [c['filtro_referencia']] + [x for x in c['filtros'] if x != c['filtro_referencia']]
        for caso in casos:
            if caso['mercado']['pasta'] != chave_mercado:
                del mercado
                mercado = carregar_mercado(caso['mercado'])
                chave_mercado = caso['mercado']['pasta']
            z = carregar_npz(RAIZ / caso['previsao'])
            referencia_lados = decisoes(z['previsoes'], z['ultimo_close'], c['filtro_referencia'])
            for filtro in filtros:
                for custo, slip in enumerate(c['slippage_cenarios'], 1):
                    ident = f"{caso['id']}/filtro_{round(filtro*100000):03d}/custo_{custo}"
                    regras = deepcopy(caso['regras'])
                    regras.update(filtro_retorno_absoluto=filtro, slippage_por_lado=slip)
                    referencia = carteira_referencia(caso, custo) if filtro == c['filtro_referencia'] else None
                    r = executar_carteira(p / 'carteiras' / ident, z, mercado, regras,
                                           referencia=referencia, identidade=ident)
                    alteracoes = float(np.mean(decisoes(z['previsoes'], z['ultimo_close'], filtro) != referencia_lados))
                    linha = linha_carteira(caso, r, filtro=filtro, custo=custo, slippage=slip,
                            fracao_decisoes_alteradas=alteracoes, membro=ident)
                    linhas.append(linha)
                    recibos.append(dict(identidade=ident, recibo=relativo(p / 'carteiras' / ident / 'recibo.json'),
                                        sha256=sha256(p / 'carteiras' / ident / 'recibo.json')))
                    registrar_estado(etapa, 'simulando', concluidas=len(linhas), previstas=324,
                                      identidade=ident)
        assert len(linhas) == 324
        pub = p / 'publicacao'
        pub.mkdir(exist_ok=False)
        pd.DataFrame(linhas).to_csv(pub / 'carteiras.csv', index=False)
        salvar_json(pub / 'resultados.json', dict(carteiras=linhas, recibos=recibos,
                    controles_originais=108, configuracoes_alternativas=216,
                    limite='Grade descritiva completa; nenhum filtro/custo promovido.'))
        fechar(etapa, dict(combinacoes=324, controles_originais=108,
                          falhas_prudenciais=sum(x['situacao'] == 'falha_prudencial' for x in linhas)))


def resumo_deslocamentos(original, linhas):
    validas = [x for x in linhas if x['situacao'] == 'concluida_conferida']
    saida = dict(configuracoes=len(linhas), validas=len(validas),
                 falhas_prudenciais=len(linhas)-len(validas), metricas={})
    for campo in ('retorno_liquido', 'crescimento_log_diario', 'drawdown_maximo'):
        v = np.asarray([x[campo] for x in validas], dtype=float)
        valor = original['metricas'][campo]
        saida['metricas'][campo] = dict(original=valor,
            quantis_condicionais_validas=np.quantile(v, [0, .05, .25, .5, .75, .95, 1]).tolist() if len(v) else None,
            percentil_descritivo=100*float((np.sum(v < valor)+.5*np.sum(v == valor))/len(v)) if len(validas) == len(linhas) else None,
            melhores_valores='menores' if campo == 'drawdown_maximo' else 'maiores',
            limite='Sem percentil quando há falhas; não é p-valor ou confirmação de habilidade.')
    return saida


def deslocar():
    etapa = 'deslocamento_exposicao'
    with exclusividade(etapa):
        ptr, p, f = contexto(etapa)
        assert not (p / 'fechamento.json').exists()
        c, casos = f['configuracao'], f['extras']['casos']
        chave_mercado, mercado = None, None
        linhas, resumos, controles = [], {}, []
        for caso in casos:
            if caso['mercado']['pasta'] != chave_mercado:
                del mercado
                mercado = carregar_mercado(caso['mercado'])
                chave_mercado = caso['mercado']['pasta']
            z = carregar_npz(RAIZ / caso['previsao'])
            lados = decisoes(z['previsoes'], z['ultimo_close'], c['filtro_referencia'])
            regras = deepcopy(caso['regras'])
            regras.update(filtro_retorno_absoluto=c['filtro_referencia'], slippage_por_lado=.0001)
            zero = dict(z, previsoes=precos_decisoes(lados, z['ultimo_close'], c['filtro_referencia']))
            id_zero = caso['id'] + '/controle_zero'
            base = executar_carteira(p / 'carteiras' / id_zero, zero, mercado, regras,
                                    referencia=carteira_referencia(caso, 1), identidade=id_zero)
            assert base['situacao'] == 'concluida_conferida'
            controles.append(dict(identidade=id_zero, controle=base['controle']))
            locais, sequencias = [], set()
            for k in f['extras']['deslocamentos_por_n'][str(caso['n'])]:
                novos_lados = np.roll(lados, k)
                np.testing.assert_array_equal(np.sort(novos_lados), np.sort(lados))
                sequencias.add(novos_lados.tobytes())
                artificial = dict(z, previsoes=precos_decisoes(novos_lados, z['ultimo_close'], c['filtro_referencia']))
                ident = caso['id'] + f'/deslocamento_{k:03d}'
                r = executar_carteira(p / 'carteiras' / ident, artificial, mercado, regras, identidade=ident)
                linha = linha_carteira(caso, r, deslocamento=k, membro=ident,
                    sequencia_igual_original=bool(np.array_equal(novos_lados, lados)),
                    contagens_decisoes_preservadas=True)
                if r['situacao'] == 'concluida_conferida':
                    for chave in ('dias_comprado', 'dias_vendido', 'dias_posicionado', 'blocos_posicao',
                                  'ordens', 'volume_negociado_usdt', 'comissoes', 'custo_slippage_ticks'):
                        linha['diferenca_' + chave] = r['metricas'][chave]-base['metricas'][chave]
                linhas.append(linha)
                locais.append(linha)
                if len(linhas) % 20 == 0:
                    registrar_estado(etapa, 'simulando', concluidas=len(linhas), previstas=2376, identidade=ident)
                else:
                    salvar_json(REG / etapa / 'estado.json', dict(utc=agora(), etapa=etapa,
                                situacao='simulando', concluidas=len(linhas), previstas=2376, identidade=ident))
            resumo = resumo_deslocamentos(base, locais)
            resumo.update(sequencias_distintas=len(sequencias), sequencia_original_constante=bool(np.all(lados == lados[0])),
                          multiplicidades_preservadas=True, original_descricao=base['descricao'])
            resumos[caso['id']] = resumo
            salvar_json(p / 'resumos_parciais' / (caso['id'].replace('/', '_') + '.json'), resumo)
        assert len(linhas) == 2376 and len(controles) == 24
        pub = p / 'publicacao'
        pub.mkdir(exist_ok=False)
        pd.DataFrame(linhas).to_csv(pub / 'carteiras.csv', index=False)
        salvar_json(pub / 'resultados.json', dict(resumos=resumos, controles=controles,
                    deslocamentos=f['extras']['deslocamentos_por_n'],
                    limite='Diagnóstico condicional retrospectivo, com bordas circulares e possível mistura de regimes.'))
        fechar(etapa, dict(carteiras_deslocadas=2376, controles_zero=24,
                    falhas_prudenciais=sum(x['situacao'] == 'falha_prudencial' for x in linhas)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('acao', choices=['qualificar', 'preparar_sensibilidade', 'sensibilidade', 'preparar_deslocamentos', 'deslocar'])
    acao = parser.parse_args().acao
    if acao == 'preparar_sensibilidade':
        preparar('sensibilidade_filtro')
    elif acao == 'preparar_deslocamentos':
        preparar('deslocamento_exposicao')
    else:
        globals()[acao]()
