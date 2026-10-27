"""Entrada exclusiva da extensão; nunca atualiza os ponteiros do ciclo original."""
import argparse
from experimento_penalizacao.ciclo import preparar,executar

if __name__=='__main__':
    argumentos=argparse.ArgumentParser()
    argumentos.add_argument('acao',choices=['preparar','executar'])
    acao=argumentos.parse_args().acao
    print(preparar() if acao=='preparar' else executar(),flush=True)
