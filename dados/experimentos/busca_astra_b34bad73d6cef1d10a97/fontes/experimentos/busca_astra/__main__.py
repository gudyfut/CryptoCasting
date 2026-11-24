import argparse
from .ciclo import preparar, executar

p=argparse.ArgumentParser()
p.add_argument('acao',choices=['preparar','executar','publicar'])
p.add_argument('--qualificacao')
a=p.parse_args()
if a.acao=='preparar':
    if not a.qualificacao:p.error('Qualificacao obrigatoria.')
    preparar(a.qualificacao)
elif a.acao=='executar':executar()
else:
    from .publicacao import publicar_posteriormente
    publicar_posteriormente()
