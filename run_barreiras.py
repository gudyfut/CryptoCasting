"""Entrada única do estudo de barreiras; avaliação final permanece bloqueada."""
import argparse
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='acao',required=True)
    coleta=sub.add_parser('coletar');coleta.add_argument('--inicio',default='2021-01-01');coleta.add_argument('--fim',default='2024-01-01')
    processamento=sub.add_parser('preparar');processamento.add_argument('--manifesto',type=Path,default=Path('dados/brutos/barreiras_1m/manifesto_2021-01-01_2024-01-01.json'))
    sub.add_parser('qualificar')
    sub.add_parser('auditar-dados')
    consolidacao=sub.add_parser('consolidar');consolidacao.add_argument('diretorio',type=Path)
    plano=sub.add_parser('planejar');plano.add_argument('--configuracao',type=Path,default=Path('configuracoes/ciclo_001.json'))
    treino=sub.add_parser('treinar');treino.add_argument('--configuracao',type=Path,default=Path('configuracoes/ciclo_001.json'))
    treino.add_argument('--dataset',type=Path);treino.add_argument('--somente-pilotos',action='store_true')
    args=p.parse_args()
    if args.acao=='coletar':
        from barreiras.coleta import coletar
        coletar(args.inicio,args.fim)
    elif args.acao=='preparar':
        from barreiras.dados import preparar
        print(preparar(args.manifesto))
    elif args.acao=='qualificar':
        from barreiras.qualificacao import qualificar
        print(qualificar()['status'])
    elif args.acao=='auditar-dados':
        from barreiras.arquivos import RAIZ,ler_json
        from barreiras.preparacao import auditar_preparacao
        pasta=RAIZ/ler_json(RAIZ/'dados/processados/dataset_barreiras_atual.json')['caminho']
        print(auditar_preparacao(pasta)['status'])
    elif args.acao=='consolidar':
        from barreiras.consolidacao import consolidar
        r=consolidar(args.diretorio)
        print({k:r[k] for k in ('status','celulas_esperadas','celulas_auditadas')})
    elif args.acao=='planejar':
        from barreiras.configuracao import carregar,celulas
        from barreiras.arquivos import identidade
        c=carregar(args.configuracao);grade=celulas(c)
        print({'ciclo':c['ciclo'],'hash_configuracao':identidade(c),'celulas':len(grade),'ajustes_neurais':2*len(grade)})
        for x in grade:
            print(x)
    elif args.acao=='treinar':
        from barreiras.arquivos import RAIZ,ler_json
        from barreiras.execucao import executar
        dataset=args.dataset or RAIZ/ler_json(RAIZ/'dados/processados/dataset_barreiras_atual.json')['caminho']
        print(executar(args.configuracao,dataset,somente_pilotos=args.somente_pilotos))


if __name__=='__main__':
    main()
