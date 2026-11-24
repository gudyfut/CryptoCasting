"""Comandos explícitos para a nova referência. Executar no WSL qualificado."""
import argparse
from estudo_ohlcv.ciclo import REGISTROS, preparar, congelar, executar

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('acao', choices=['preparar', 'qualificar', 'congelar', 'executar'])
    p.add_argument('--retomar', action='store_true')
    a = p.parse_args()
    if a.retomar and a.acao != 'executar':
        p.error('--retomar só se aplica a executar.')
    import fcntl
    REGISTROS.mkdir(parents=True, exist_ok=True)
    with (REGISTROS / 'executor.lock').open('a+') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('Outro processo OHLCV está ativo; não duplicar.')
        if a.acao == 'qualificar':
            from estudo_ohlcv.qualificacao import qualificar
            print(qualificar())
        elif a.acao == 'preparar':
            print(preparar()[0])
        elif a.acao == 'congelar':
            print(congelar())
        else:
            executar(a.retomar)
