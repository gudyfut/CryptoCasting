"""Comandos explícitos; importação não inicia tarefas."""
import argparse
import os
os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('acao', choices=['qualificar', 'preparar', 'conferir', 'executar'])
    args = parser.parse_args()
    if args.acao == 'qualificar':
        from .qualificacao import executar
    else:
        from . import ciclo
        executar = {'preparar': ciclo.preparar, 'conferir': ciclo.conferir,
                    'executar': ciclo.executar}[args.acao]
    executar()


if __name__ == '__main__':
    main()
