import argparse
from . import ciclo

parser=argparse.ArgumentParser()
parser.add_argument('acao',choices=['qualificar','preparar','conferir','executar'])
args=parser.parse_args()
if args.acao=='qualificar':
    from .qualificacao import executar
    executar()
else:getattr(ciclo,args.acao)()
