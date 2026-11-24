"""Inspeção do consumo de dados; deliberadamente sem comandos de treinamento."""
import argparse
from pathlib import Path
import traceback
from uuid import uuid4
from infraestrutura.artefatos import RAIZ, salvar_json, relativo, agora
from modelos.conferencia import conferir_consumo


def principal():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='acao', required=True)
    s = sub.add_parser('conferir')
    s.add_argument('--entradas', type=Path, required=True)
    a = p.parse_args()
    destino = RAIZ / 'registros/modelos/conferencias' / uuid4().hex
    destino.mkdir(parents=True)
    salvar_json(destino / 'solicitacao.json', {'utc': agora(), 'entradas': relativo(a.entradas), 'treinamento': False})
    try:
        resumo = conferir_consumo(a.entradas)
        salvar_json(destino / 'resumo.json', resumo)
        print(relativo(destino / 'resumo.json'))
    except BaseException:
        salvar_json(destino / 'falha.json', {'utc': agora(), 'erro': traceback.format_exc()})
        raise


if __name__ == '__main__': principal()
