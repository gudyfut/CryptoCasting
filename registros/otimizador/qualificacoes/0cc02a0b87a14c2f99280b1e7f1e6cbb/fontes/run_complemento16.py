"""Completar as seis seeds do estado16 com somente três novos ajustes."""
import argparse
from pathlib import Path

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='acao',required=True)
    s.add_parser('qualificar')
    q=s.add_parser('preparar');q.add_argument('--qualificacao',type=Path,required=True)
    s.add_parser('conferir');s.add_parser('auditar')
    q=s.add_parser('executar');q.add_argument('--autorizacao',type=Path,required=True);q.add_argument('--retomar',action='store_true')
    a=p.parse_args();from experimento_complemento16 import ciclo
    if a.acao=='qualificar':print(ciclo.qualificar())
    elif a.acao=='preparar':print(ciclo.preparar(a.qualificacao))
    elif a.acao=='conferir':print(ciclo.conferir_execucao()[1]['id'])
    elif a.acao=='auditar':print(ciclo.conferir_conclusao())
    else:ciclo.executar(a.autorizacao,a.retomar)
