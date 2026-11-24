"""Uma abordagem CryptoMamba adaptada, seis seeds; sem editar ciclos anteriores."""
import argparse
from pathlib import Path

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='acao',required=True)
    for n in ('qualificar','conferir','posprocessar'):s.add_parser(n)
    q=s.add_parser('preparar');q.add_argument('--qualificacao',type=Path,required=True)
    q=s.add_parser('executar');q.add_argument('--autorizacao',type=Path,required=True);q.add_argument('--retomar',action='store_true')
    a=p.parse_args();from experimento_cryptomamba import ciclo
    if a.acao=='qualificar':print(ciclo.qualificar())
    elif a.acao=='preparar':print(ciclo.preparar(a.qualificacao))
    elif a.acao=='conferir':print(ciclo.conferir_execucao()[1]['id'])
    elif a.acao=='posprocessar':
        from experimento_cryptomamba.finalizacao import posprocessar
        print(posprocessar())
    else:
        ciclo.executar(a.autorizacao,a.retomar)
        from experimento_cryptomamba.finalizacao import posprocessar
        print(posprocessar())
