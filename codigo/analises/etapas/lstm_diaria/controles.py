"""Verifica independentemente a trajetória e os checkpoints dos controles."""
import argparse
import json
import numpy as np
import torch
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256


def conferir(moeda):
    reg=RAIZ/'registros/lstm_diaria';ptr=ler_json(reg/'execucao.json');p=RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    a=p/moeda/'ajustes/seed_42';b=p/moeda/'ajustes/controle_42'
    assert ler_json(a/'conclusao.json')['situacao']==ler_json(b/'conclusao.json')['situacao']=='concluido'
    def historia(d):
        return [{k:v for k,v in json.loads(l).items() if k!='segundos'}
                for l in (d/'epocas.jsonl').read_text(encoding='utf-8').splitlines()]
    h1,h2=historia(a),historia(b)
    assert len(h1)==len(h2)==200 and h1==h2
    sa,sb=ler_json(a/'selecao.json'),ler_json(b/'selecao.json')
    assert (sa['epoca'],sa['rmse_validacao'])==(sb['epoca'],sb['rmse_validacao'])
    with np.load(a/'validacao.npz',allow_pickle=False) as x,np.load(b/'validacao.npz',allow_pickle=False) as y:
        np.testing.assert_array_equal(x['previsoes'],y['previsoes'])
    nomes=sorted(p.name for p in (a/'checkpoints').glob('*.pt'))
    assert nomes==sorted(p.name for p in (b/'checkpoints').glob('*.pt')) and nomes
    for nome in nomes:
        x=torch.load(a/'checkpoints'/nome,map_location='cpu',weights_only=True)['pesos']
        y=torch.load(b/'checkpoints'/nome,map_location='cpu',weights_only=True)['pesos']
        assert x.keys()==y.keys() and all(torch.equal(x[k],y[k]) for k in x)
    arquivo=reg/'controles_independentes.json'
    recibo=ler_json(arquivo) if arquivo.exists() else {'execucao':ptr,'moedas':{}}
    assert recibo['execucao']==ptr
    recibo['moedas'][moeda]=dict(utc=agora(),aprovado=True,epocas=200,checkpoints=len(nomes),
                                 epoca_selecionada=sa['epoca'],trajetoria_e_pesos_exatos=True)
    salvar_json(arquivo,recibo)
    print('CONTROLE_INDEPENDENTE_APROVADO',moeda,len(nomes),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('moeda');conferir(parser.parse_args().moeda)
