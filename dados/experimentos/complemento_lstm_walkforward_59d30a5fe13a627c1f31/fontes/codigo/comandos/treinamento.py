"""Entrada explícita: qualificar/preparar/conferir nunca iniciam estudo de mercado."""
import argparse
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='acao', required=True)
    sub.add_parser('qualificar')
    preparar = sub.add_parser('preparar')
    preparar.add_argument('--qualificacao', type=Path, required=True)
    sub.add_parser('conferir')
    executar = sub.add_parser('executar')
    executar.add_argument('--autorizacao', type=Path, required=True)
    executar.add_argument('--retomar', action='store_true')
    a = p.parse_args()
    from treinamento import ciclo
    if a.acao == 'qualificar':
        from treinamento.qualificacao import qualificar
        print(qualificar())
    elif a.acao == 'preparar':
        print(ciclo.preparar(a.qualificacao))
    elif a.acao == 'conferir':
        pasta, f, consumo, partes = ciclo.conferir_execucao()
        print({'id': f['id'], 'pasta': str(pasta), 'integridade': 'conferida', 'treinamento_iniciado': False})
    else:
        ciclo.executar(a.autorizacao, a.retomar)


if __name__ == '__main__':
    main()
