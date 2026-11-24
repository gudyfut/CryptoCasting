import argparse
import os
# Precisa existir antes da primeira inicialização CUDA, inclusive na qualificação.
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
from . import ciclo

parser=argparse.ArgumentParser()
parser.add_argument('acao',choices=['preparar','executar','conferir-preservacao'])
args=parser.parse_args()
{'preparar':ciclo.preparar,'executar':ciclo.executar,'conferir-preservacao':ciclo.conferir_preservacao}[args.acao]()
