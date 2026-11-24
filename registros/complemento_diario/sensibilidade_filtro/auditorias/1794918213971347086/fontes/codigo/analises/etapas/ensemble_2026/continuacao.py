"""Continuação técnica: recuperação de observações oficiais ausentes nos ZIPs."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil

import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, identidade
from . import ciclo

REG = ciclo.REG


def preparar():
    antigo, ap, f = ciclo.contexto()
    assert antigo['id'] == 'f9329190899ef937e46a'
    assert (ap/'incidente_coletando.json').exists() and not (ap/'execucao.lock').exists()
    assert not (ap/'inferencia.json').exists()
    diag = ler_json(REG/'complementacao.json')
    assert diag['api_contem_todos_os_minutos'] and diag['processo_coleta_encerrado']
    f = deepcopy(f)
    f['utc'] = agora()
    f['continuidade_tecnica'] = dict(antecessora=antigo, diagnostico=diag,
        mudanca='Somente coleta: consultar API oficial para lacunas de até7dias, com cobertura exata e proveniência; nenhuma interpolação, alteração de modelo, filtro, período ou política.')
    nomes = ['codigo/mercado_futuros/periodo_publico_verificado.py',
             'codigo/analises/etapas/ensemble_2026/continuacao.py', 'testes/ensemble_2026/test_complementacao.py']
    for nome in nomes:
        f['fontes'][nome] = sha256(RAIZ/nome)
    for arquivo in [REG/'complementacao.json', REG/'diagnostico_lacuna/mark_20260629.json',
                    ap/'congelamento.json', ap/'incidente_coletando.json', ap/'coleta.log']:
        f['pais'][arquivo.relative_to(RAIZ).as_posix()] = sha256(arquivo)
    antigos_dados = RAIZ/'dados/mercado/ensemble_2026'/antigo['id']
    for arquivo in antigos_dados.rglob('*'):
        if arquivo.is_file():
            f['pais'][arquivo.relative_to(RAIZ).as_posix()] = sha256(arquivo)
    codigo = identidade(f)[:20]
    p = RAIZ/'dados/reavaliacoes'/f'ensemble_2026_{codigo}'
    p.mkdir(exist_ok=False)
    for nome in f['fontes']:
        destino = p/'fontes'/nome
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(RAIZ/nome, destino)
    salvar_json(p/'congelamento.json', f)
    ptr = dict(id=codigo, pasta=p.relative_to(RAIZ).as_posix(), congelamento_sha256=sha256(p/'congelamento.json'))
    salvar_json(REG/'tentativa_inicial.json', antigo)
    salvar_json(REG/'execucao.json', ptr)
    ciclo.estado('preparado_continuacao', execucao=ptr, novos_treinamentos=0)
    print(json.dumps(ptr), flush=True)


def mercado():
    from mercado_futuros.periodo_publico_verificado import coletar
    with ciclo.etapa('coletando') as (ptr,p,f):
        cfg = f['configuracao']
        inicio = int(pd.Timestamp(cfg['inicio'],tz='UTC').timestamp()*1000)
        fim = int(pd.Timestamp(cfg['fim_exclusivo'],tz='UTC').timestamp()*1000)
        saida = {}
        for simbolo in cfg['moedas']:
            destino = RAIZ/'dados/mercado/ensemble_2026'/ptr['id']/simbolo
            mp = coletar(destino, simbolo, inicio, fim)
            mp['pasta'] = destino.relative_to(RAIZ).as_posix()
            saida[simbolo] = mp
            ciclo.estado('coletando', execucao=ptr, moedas_concluidas=len(saida), total_moedas=4)
        salvar_json(p/'mercados.json', saida)
        ciclo.estado('mercados_conferidos', execucao=ptr, moedas_concluidas=4)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('acao',choices=['preparar','mercado','inferencia','avaliar','conferir'])
    acao = parser.parse_args().acao
    if acao in ['preparar','mercado']:
        globals()[acao]()
    elif acao == 'conferir':
        print(ciclo.contexto()[0])
    else:
        getattr(ciclo,acao)()


if __name__ == '__main__':
    main()
