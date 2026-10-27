"""Explica filtros de entrada sem alterar previsões, operações ou treinamento."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('diretorio',type=Path)
    args=parser.parse_args();raiz=args.diretorio
    ciclo=json.loads((raiz/'ciclo.json').read_text(encoding='utf-8'))
    linhas=[]
    for estado in sorted(raiz.glob('*/estado.json')):
        r=json.loads(estado.read_text(encoding='utf-8'))
        if r['status']!='concluida_auditada' or r['id_ciclo']!=ciclo['id']:
            continue
        integridade=json.loads((estado.parent/'integridade.json').read_text(encoding='utf-8'))
        for nome in ('mamba','lstm','ar1'):
            rel=f'{nome}/previsoes_operacional.parquet';p=estado.parent/rel
            if hashlib.sha256(p.read_bytes()).hexdigest()!=integridade[rel]:
                raise ValueError('Previsões operacionais foram alteradas.')
            q=pd.read_parquet(p,columns=['p2','distancia'])
            d=q.distancia.to_numpy();p2=q.p2.to_numpy()
            fator=.9995*.999/(1.0005*1.001)
            ru=np.exp(d)*fator-1;rl=np.exp(-d)*fator-1
            confianca=p2>=.6;viabilidade=p2*ru+(1-p2)*rl>0
            ambos=confianca&viabilidade
            financeiro=r['financeiro'][nome]['base']
            if financeiro['status']=='auditavel' and financeiro['operacoes']>int(ambos.sum()):
                raise ValueError('Mais operações do que sinais elegíveis: verificar contabilidade.')
            linhas.append({**r['celula'],'modelo':nome,'id':r['id'],'origens_causais':len(q),
                'p_superior_maxima':float(p2.max()),'p_superior_percentil95':float(np.quantile(p2,.95)),
                'origens_p_superior_ge_060':int(confianca.sum()),
                'origens_confianca_aprovada_custo_reprovado':int((confianca&~viabilidade).sum()),
                'sinais_antes_controle_posicao':int(ambos.sum()),
                'limiar_nominal_mediano':float(np.median(-rl/(ru-rl))),
                'proporcao_alvos_com_lucro_nominal':float((ru>0).mean()),
                'status_financeiro':financeiro['status'],'operacoes':financeiro.get('operacoes')})
    destino=raiz/'consolidacao';destino.mkdir(exist_ok=True)
    pd.DataFrame(linhas).to_csv(destino/'diagnostico_sinais.csv',index=False)
    resumo={'id_ciclo':ciclo['id'],'celulas_auditadas':len(linhas)//3,
        'natureza':'Diagnóstico posterior; não altera o sinal nem usa qualidade futura para escolher entradas.',
        'interpretacao':'Sinais podem ser ignorados enquanto há posição. Falta de operação não prova nem rentabilidade nem inutilidade da previsão.',
        'linhas':linhas}
    (destino/'diagnostico_sinais.json').write_text(json.dumps(resumo,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print(f'Diagnóstico salvo para {len(linhas)//3} células auditadas.')


if __name__=='__main__':
    main()
