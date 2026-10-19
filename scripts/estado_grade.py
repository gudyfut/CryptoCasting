"""Inspeção leve da grade; não treina nem modifica artefatos científicos."""
import argparse
import json
from pathlib import Path
from collections import Counter


def ler(p):
    return json.loads(p.read_text(encoding='utf-8'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('diretorio',type=Path)
    args=parser.parse_args();raiz=args.diretorio
    ciclo=ler(raiz/'ciclo.json');c=ciclo['assinatura']['configuracao']
    total=1
    for k in ('pares','contextos','horizontes','folds','seeds'):
        total*=len(c[k])
    estados=[ler(p) for p in raiz.glob('*/estado.json')]
    contagens=Counter(e['status'] for e in estados)
    ativos=[]
    for e in estados:
        if e['status'] in ('concluida_auditada','falha','interrompido'):
            continue
        item={'id':e['id'],'celula':e['celula'],'estado':e['status'],'modelo':e.get('modelo')}
        epocas=raiz/e['id']/e.get('modelo','')/'epocas.json'
        if epocas.exists():
            historia=ler(epocas)
            item['epoca']=historia[-1]['epoca']
            item['ultima_epoca_registrada_utc']=historia[-1]['utc']
        parcial=raiz/'cache_ar1'/f"{e['celula']['par']}_{e['celula']['fold']}"/'parcial.json'
        if e['status']=='baseline' and parcial.exists():
            item['ar1']=ler(parcial)
        ativos.append(item)
    resultado={'id_ciclo':ciclo['id'],'celulas_planejadas':total,'estados':dict(contagens),'em_andamento':ativos}
    # O arquivo de estado sozinho não demonstra que o executor ainda está vivo.
    try:
        import fcntl
        with (raiz/'execucao.lock').open('r') as trava:
            try:
                fcntl.flock(trava.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                resultado['executor_mantem_lock']=False
                fcntl.flock(trava.fileno(),fcntl.LOCK_UN)
            except BlockingIOError:
                resultado['executor_mantem_lock']=True
    except (ImportError,FileNotFoundError):
        resultado['executor_mantem_lock']=None
    print(json.dumps(resultado,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
