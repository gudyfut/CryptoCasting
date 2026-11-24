"""Entrada própria; não altera lançadores congelados de outras rodadas."""
import argparse
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='acao',required=True)
    for nome in ('entradas','qualificar','conferir','publicar'):s.add_parser(nome)
    q=s.add_parser('preparar');q.add_argument('--qualificacao',type=Path,required=True)
    q=s.add_parser('executar');q.add_argument('--autorizacao',type=Path,required=True);q.add_argument('--retomar',action='store_true')
    a=p.parse_args()
    if a.acao=='entradas':
        from .dados import preparar_dados
        print(preparar_dados(),flush=True);return
    from . import ciclo
    if a.acao=='qualificar':print(ciclo.qualificar(),flush=True)
    elif a.acao=='preparar':print(ciclo.preparar(a.qualificacao),flush=True)
    elif a.acao=='conferir':print(ciclo.conferir_execucao()[1]['id'],flush=True)
    else:
        if a.acao=='executar':ciclo.executar(a.autorizacao,a.retomar)
        from .publicacao import posprocessar
        print(posprocessar(),flush=True)


if __name__=='__main__':main()
