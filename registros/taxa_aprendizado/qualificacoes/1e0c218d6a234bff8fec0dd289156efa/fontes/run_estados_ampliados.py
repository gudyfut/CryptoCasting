"""Sequência previamente delimitada: seis Mamba32, depois seis Mamba64."""
import argparse
from pathlib import Path


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='acao',required=True)
    q=s.add_parser('qualificar');q.add_argument('--estado',type=int,choices=[32,64],required=True)
    q=s.add_parser('preparar');q.add_argument('--estado',type=int,choices=[32,64],required=True);q.add_argument('--qualificacao',type=Path,required=True)
    q=s.add_parser('conferir');q.add_argument('--estado',type=int,choices=[32,64],required=True)
    q=s.add_parser('fila');q.add_argument('--autorizacao',type=Path,required=True);q.add_argument('--retomar',action='store_true')
    a=p.parse_args();from experimento_estados_ampliados import ciclo
    from infraestrutura.artefatos import ler_json
    if a.acao=='qualificar':print(ciclo.qualificar(a.estado))
    elif a.acao=='preparar':
        dep=ler_json(ciclo.registro(32)/'execucao.json') if a.estado==64 else None
        print(ciclo.preparar(a.estado,a.qualificacao,dep))
    elif a.acao=='conferir':print(ciclo.conferir_execucao(a.estado)[1]['id'])
    else:ciclo.executar_fila(a.autorizacao,a.retomar)
