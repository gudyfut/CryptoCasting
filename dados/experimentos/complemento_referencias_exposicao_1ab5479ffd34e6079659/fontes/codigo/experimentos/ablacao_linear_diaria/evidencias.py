"""Confere herança qualificada e preserva também a ablação seletiva encerrada."""
from pathlib import Path
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,conferir_arquivos
from experimentos.penalizacao_seletiva_diaria.evidencias import inspecionar as inspecionar_anterior
from .contratos import conferir_configuracao


def inspecionar(c):
    ptr=ler_json(RAIZ/c['referencia_seletiva']);p=RAIZ/ptr['pasta']
    assert ptr['id']=='26cea089ba0faa9d64dc'
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    f=ler_json(p/'congelamento.json');conferir_configuracao(c,f['configuracao'])
    assert ler_json(p/'processo.json')['ativo'] is False
    fecho=ler_json(RAIZ/'registros/penalizacao_seletiva_diaria/fechamento.json')
    assert sha256(RAIZ/fecho['arquivo'])==fecho['sha256']
    assert ler_json(p/'fechamento.json')['situacao']=='concluido_conferido'
    conferir_arquivos(p,ler_json(p/'fechamento.json')['arquivos'])
    conferir_arquivos(p/'fontes',f['fontes'])
    r=inspecionar_anterior(f['configuracao'])
    for a in p.rglob('*'):
        if a.is_file():r['preservacao'][a.relative_to(RAIZ).as_posix()]=sha256(a)
    r.update(heranca_aprovada=['A'],novos_ajustes_principais=3,novos_controles=2,
             seletiva_preservada=ptr,
             limite='A seleção prefixo200 comprovada; L treinará do zero. Sem herdar pesos treinados para L.')
    return r


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('destino');args=parser.parse_args()
    destino=Path(args.destino);assert not destino.exists()
    salvar_json(destino,inspecionar(ler_json(RAIZ/'configuracoes/ablacao_linear_diaria_001.json')))
    print('REFERENCIAS_E_TENTATIVAS_PRESERVADAS',flush=True)
