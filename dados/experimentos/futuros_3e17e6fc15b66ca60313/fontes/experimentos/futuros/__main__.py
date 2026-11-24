import sys
from .ciclo import preparar,executar
if __name__=='__main__':
    if sys.argv[1:] == ['preparar']:preparar()
    elif sys.argv[1:] == ['executar']:executar()
    else:raise SystemExit('Use preparar ou executar. Ciclo concluido nao se repete.')
