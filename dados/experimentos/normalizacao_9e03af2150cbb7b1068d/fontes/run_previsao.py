"""Entrada explícita para as etapas auditáveis do estudo de 24 horas."""
import argparse
from pathlib import Path
from previsao24.arquivos import RAIZ
from previsao24.configuracao import carregar

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('etapa',choices=['coletar','preparar','qualificar','executar','congelar'])
    parser.add_argument('--configuracao',type=Path,default=RAIZ/'configuracoes/retorno24_001.json')
    parser.add_argument('--fase',choices=['desenvolvimento','avaliacao'],default='desenvolvimento')
    parser.add_argument('--piloto',action='store_true')
    args=parser.parse_args()
    c=carregar(args.configuracao)
    if args.etapa=='coletar':
        from previsao24.coleta import coletar
        coletar(c['inicio'],c['fim'])
    elif args.etapa=='preparar':
        from previsao24.dados import preparar
        print(preparar(RAIZ/f"dados/brutos/binance_spot_1m/manifesto_{c['inicio']}_{c['fim']}.json"))
    elif args.etapa=='qualificar':
        from previsao24.qualificacao import qualificar
        qualificar(c)
    elif args.etapa=='executar':
        from previsao24.execucao import executar
        print(executar(c,args.fase,args.piloto))
    elif args.etapa=='congelar':
        from previsao24.execucao import congelar
        print(congelar(c))

if __name__=='__main__':
    main()
