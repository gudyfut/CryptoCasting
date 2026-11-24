import argparse
import json
from .contrato import conferir

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='Pesquisa operacional separada: conferir, congelar, executar ou publicar.')
    parser.add_argument('acao',choices=['conferir','preparar','executar','publicar'])
    parser.add_argument('--integridade',action='store_true')
    parser.add_argument('--qualificacao')
    args=parser.parse_args()
    if args.acao=='conferir': resultado=conferir(args.integridade)
    elif args.acao=='preparar':
        from infraestrutura.artefatos import RAIZ
        from .ciclo import preparar
        if not args.qualificacao: parser.error('--qualificacao obrigatório')
        resultado=preparar(RAIZ/args.qualificacao)
    elif args.acao=='executar':
        from .ciclo import executar
        executar();resultado={'executor_encerrado':True,'publicacao_posterior':'ação publicar, somente leitura'}
    else:
        from .publicacao import publicar
        resultado=publicar()
    print(json.dumps(resultado,ensure_ascii=False,indent=2))
