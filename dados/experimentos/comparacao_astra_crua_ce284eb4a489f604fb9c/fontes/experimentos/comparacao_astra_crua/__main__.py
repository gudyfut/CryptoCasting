import argparse
from .ciclo import preparar, executar
p=argparse.ArgumentParser();p.add_argument('acao',choices=['qualificar','preparar','executar','publicar'])
a=p.parse_args()
if a.acao=='qualificar':
    from .qualificar import executar as qualificar
    qualificar()
elif a.acao=='preparar':preparar()
else:executar(publicacao_apenas=a.acao=='publicar')
