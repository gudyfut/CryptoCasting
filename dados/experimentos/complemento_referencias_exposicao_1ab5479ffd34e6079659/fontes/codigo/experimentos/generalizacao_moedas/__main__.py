import os
os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
import argparse
from . import ciclo

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('acao', choices=('preparar','executar','conferir'))
    getattr(ciclo, parser.parse_args().acao)()
