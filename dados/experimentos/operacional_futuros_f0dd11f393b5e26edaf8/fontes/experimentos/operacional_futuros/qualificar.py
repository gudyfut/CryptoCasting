"""Integração sintética CUDA e teste de recarga, sem treinos de mercado."""
import time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from infraestrutura.artefatos import RAIZ,salvar_json,agora
from entradas_modelo.operacional_futuros import preparar
from treinamento.operacional_futuros import ajustar
from .receitas import iniciais


def executar(destino):
    d=Path(destino);d.mkdir(parents=True,exist_ok=False)
    if not torch.cuda.is_available(): raise RuntimeError('CUDA oficial obrigatório.')
    rng=np.random.default_rng(2026);n=100*24
    t=pd.date_range('2021-01-01',periods=n,freq='h',tz='UTC').as_unit('ms').asi8
    c=100*np.exp(np.cumsum(rng.normal(0,.002,n)));o=np.r_[c[0],c[:-1]]
    h=pd.DataFrame(dict(open_time=t,close_time=t+3599999,open=o,high=np.maximum(o,c)*1.003,
        low=np.minimum(o,c)*.997,close=c,volume=rng.uniform(1,100,n)))
    cal={'treino':['2021-01-01','2021-02-15'],'validacao':['2021-02-15','2021-03-01'],
         'calibracao':['2021-03-01','2021-03-20'],'comparacao':['2021-03-20','2021-04-10']}
    pares=[];inicio=time.monotonic()
    for nome,r in iniciais().items():
        payoff=np.column_stack([np.sin(np.arange(n)/30)*.01-.002,-np.sin(np.arange(n)/30)*.01-.002]) if nome=='P0' else None
        dados=preparar(h,r,cal,payoff)
        resultados=[]
        for rep in (1,2):
            p=d/f'{nome}_{rep}'
            resultados.append(ajustar(dados,r,42,p,{'tipo':'sintetico','receita':nome},epocas=2,paciencia=2))
        desvios={}
        for fase in ('validacao','calibracao','comparacao'):
            a=np.load(d/f'{nome}_1'/(fase+'.npz'));b=np.load(d/f'{nome}_2'/(fase+'.npz'))
            if not all(np.array_equal(a[k],b[k]) for k in a.files if k!='previsoes'):
                raise ValueError('Repetição sintética divergente: '+nome+'/'+fase)
            desvios[fase]=float(np.max(np.abs(a['previsoes']-b['previsoes'])))
            # CUDA selective scan admite redução não bitwise entre treinos independentes.
            # Checkpoint recarregado continua exigindo igualdade exata no mesmo ajuste.
            np.testing.assert_allclose(a['previsoes'],b['previsoes'],rtol=0,atol=1e-7)
        pares.append({'receita':nome,'repeticao_numerica':True,'tolerancia_absoluta':1e-7,
            'desvios_maximos':desvios,'segundos':resultados[0]['segundos'],
            'linhas_treino':len(dados.indices['treino']),'gpu_pico_bytes':resultados[0]['gpu_pico_bytes']})
    salvar_json(d/'conclusao.json',{'status':'aprovado','utc':agora(),'tipo':'sintetico_integrado',
        'gpu':torch.cuda.get_device_name(),'torch':torch.__version__,'pares':pares,
        'segundos':time.monotonic()-inicio,'treinos_mercado':0})


if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('destino');args=a.parse_args();executar(RAIZ/args.destino)
