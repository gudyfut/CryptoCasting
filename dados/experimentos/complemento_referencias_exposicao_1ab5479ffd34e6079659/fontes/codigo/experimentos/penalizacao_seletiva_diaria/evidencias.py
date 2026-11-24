"""Herança A no prefixo200 e preservação do fatorial encerrado."""
from pathlib import Path
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, sha256, conferir_arquivos
from experimentos.eixo_temporal_diario.evidencias import inspecionar as inspecionar_fatorial
from experimentos.eixo_temporal_diario.evidencias import conferir_pesos_controle
from .contratos import conferir_configuracao


def inspecionar(c):
    ptr=ler_json(RAIZ/c['referencia_fatorial']);p=RAIZ/ptr['pasta']
    assert ptr['id']=='143e7037d9d6cf620cf3'
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    f=ler_json(p/'congelamento.json');conferir_configuracao(c,f['configuracao'])
    assert ler_json(p/'processo.json')['ativo'] is False
    fecho=ler_json(RAIZ/'registros/eixo_temporal_diario/fechamento.json')
    assert sha256(RAIZ/fecho['arquivo'])==fecho['sha256']
    assert ler_json(p/'fechamento.json')['situacao']=='concluido_conferido'
    conferir_arquivos(p,ler_json(p/'fechamento.json')['arquivos'])
    conferir_arquivos(p/'fontes',f['fontes'])
    r=inspecionar_fatorial(f['configuracao'])
    r['referencias']={'A':r['referencias']['A']}
    r['fatorial']=ptr
    for a in p.rglob('*'):
        if a.is_file():r['preservacao'][a.relative_to(RAIZ).as_posix()]=sha256(a)
    r['dados_preparados']={fase:(p/'dados'/f'{fase}.npz').relative_to(RAIZ).as_posix()
                           for fase in ('treino','validacao','teste')}
    return r


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('destino');args=parser.parse_args()
    destino=Path(args.destino);assert not destino.exists()
    salvar_json(destino,inspecionar(ler_json(RAIZ/'configuracoes/penalizacao_seletiva_diaria_001.json')))
    print('REFERENCIA_A_E_FATORIAL_PRESERVADOS',flush=True)
