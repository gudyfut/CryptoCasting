"""Qualificar, congelar e executar somente a combinação que ainda não existe."""
import argparse


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('acao', choices=('qualificar', 'preparar', 'conferir', 'executar', 'publicar'))
    p.add_argument('--qualificacao')
    p.add_argument('--autorizacao')
    a = p.parse_args()
    from . import ciclo
    if a.acao == 'qualificar':
        print(ciclo.qualificar(), flush=True)
    elif a.acao == 'preparar':
        print(ciclo.preparar(a.qualificacao), flush=True)
    elif a.acao == 'conferir':
        print(ciclo.conferir_execucao()[1]['id'], flush=True)
    elif a.acao == 'executar':
        ciclo.executar(a.autorizacao)
        from .publicacao import publicar
        print(publicar(), flush=True)
    else:
        from .publicacao import publicar
        print(publicar(), flush=True)


if __name__ == '__main__':
    main()
