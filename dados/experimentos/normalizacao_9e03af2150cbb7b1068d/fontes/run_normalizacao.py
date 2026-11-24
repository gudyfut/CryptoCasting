"""Entrada exclusiva da extensão; nunca atualiza os ponteiros do ciclo original."""
import argparse
import fcntl
from previsao24.arquivos import RAIZ
from experimento_normalizacao.ciclo import preparar,executar

if __name__=='__main__':
    argumentos=argparse.ArgumentParser()
    argumentos.add_argument('acao',choices=['preparar','executar'])
    acao=argumentos.parse_args().acao
    pasta=RAIZ/'registros/normalizacao'
    pasta.mkdir(parents=True,exist_ok=True)
    with (pasta/'executor.lock').open('a') as bloqueio:
        try: fcntl.flock(bloqueio,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise RuntimeError('Preparação/execução já ativa; não duplicar.')
        print(preparar() if acao=='preparar' else executar(),flush=True)
