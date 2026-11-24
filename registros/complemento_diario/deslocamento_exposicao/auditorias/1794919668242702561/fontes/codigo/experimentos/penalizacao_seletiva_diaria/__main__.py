import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('acao', choices=['qualificar', 'preparar', 'conferir', 'executar'])
    acao = parser.parse_args().acao
    if acao == 'qualificar':
        from .qualificacao import executar
        executar()
    else:
        from . import ciclo
        getattr(ciclo, acao)()


if __name__ == '__main__':
    main()
