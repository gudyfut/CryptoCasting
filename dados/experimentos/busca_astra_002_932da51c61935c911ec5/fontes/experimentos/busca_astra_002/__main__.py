import argparse
p=argparse.ArgumentParser();p.add_argument('acao',choices=['qualificar','preparar','executar']);p.add_argument('--qualificacao');a=p.parse_args()
if a.acao=='qualificar':
    from .qualificar import executar
    executar()
elif a.acao=='preparar':
    from .ciclo import preparar
    preparar(a.qualificacao)
else:
    from .ciclo import executar
    executar()
