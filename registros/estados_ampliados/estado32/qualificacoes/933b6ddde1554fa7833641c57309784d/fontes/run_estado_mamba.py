"""Rodada delimitada: Mamba estado8 com seis seeds; R0 somente herdada."""
import argparse
from pathlib import Path


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='acao',required=True)
    s.add_parser('qualificar')
    q=s.add_parser('preparar');q.add_argument('--qualificacao',type=Path,required=True)
    s.add_parser('conferir')
    e=s.add_parser('executar');e.add_argument('--autorizacao',type=Path,required=True);e.add_argument('--retomar',action='store_true')
    a=p.parse_args();from experimento_estado_mamba import ciclo
    if a.acao=='qualificar':print(ciclo.qualificar())
    elif a.acao=='preparar':print(ciclo.preparar(a.qualificacao))
    elif a.acao=='conferir':print(ciclo.conferir_execucao()[1]['id'])
    else:ciclo.executar(a.autorizacao,a.retomar)
