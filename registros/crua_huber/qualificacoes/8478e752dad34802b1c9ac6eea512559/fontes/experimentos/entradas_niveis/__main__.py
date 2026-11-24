"""Entrada separada das fontes congeladas de Huber."""
import argparse


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('acao',choices=('planejar','fila','conferir','publicar'))
    a=p.parse_args()
    from . import ciclo
    if a.acao=='planejar':print(ciclo.planejar()['id'],flush=True)
    elif a.acao=='fila':ciclo.fila()
    elif a.acao=='conferir':print(ciclo.conferir_execucao()[1]['id'],flush=True)
    else:
        from .publicacao import publicar
        print(publicar(),flush=True)


if __name__=='__main__':main()
