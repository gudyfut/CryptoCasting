"""Adam → AdamW: seis ajustes delimitados; sem mudar os estudos anteriores."""
import argparse
from pathlib import Path

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='acao',required=True)
    for nome in ('qualificar','conferir','posprocessar'):s.add_parser(nome)
    q=s.add_parser('preparar');q.add_argument('--qualificacao',type=Path,required=True)
    q=s.add_parser('executar');q.add_argument('--autorizacao',type=Path,required=True);q.add_argument('--retomar',action='store_true')
    a=p.parse_args();from experimento_otimizador import ciclo
    if a.acao=='qualificar':print(ciclo.qualificar(),flush=True)
    elif a.acao=='preparar':print(ciclo.preparar(a.qualificacao),flush=True)
    elif a.acao=='conferir':print(ciclo.conferir_execucao()[1]['id'],flush=True)
    else:
        if a.acao=='executar':ciclo.executar(a.autorizacao,a.retomar)
        from experimento_otimizador.publicacao import posprocessar
        print(posprocessar(),flush=True)
