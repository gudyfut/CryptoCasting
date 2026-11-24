import argparse
from .ciclo import preparar, executar

a=argparse.ArgumentParser();a.add_argument('acao',choices=['preparar','executar'])
args=a.parse_args()
if args.acao=='preparar':preparar()
else:executar()
