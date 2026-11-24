"""Backtest independente de carteiras com previsões preservadas; zero treino."""
import argparse
from pathlib import Path

if __name__=='__main__':
    from backtest_carteira import ciclo
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='acao',required=True);s.add_parser('preparar');q=s.add_parser('executar');q.add_argument('--autorizacao',required=True,type=Path);a=p.parse_args()
    if a.acao=='preparar':print(ciclo.preparar())
    else:ciclo.executar(a.autorizacao)
