"""Verificação sintética independente da discretização AR(1); sem preços de mercado."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import numpy as np
import torch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from barreiras.ar1 import probabilidades

def executar():
    destino=RAIZ/'historico/analises/diagnostico_2026-10-19/simulacao_sintetica.json'
    registro={'tipo':'teste_sintetico_sem_dados_de_mercado','inicio_utc':datetime.now(timezone.utc).isoformat(),
              'configuracao':{'horizonte':1,'sigma_barreira':.01,'razoes_sigma':[.5,1.,2.],
                              'trajetorias_rotina':16384,'trajetorias_referencia':65536,
                              'intercepto':0,'phi':0,'semente':20261019,'tolerancia_absoluta':.03},
              'status':'em_execucao','casos':[]}
    destino.write_text(json.dumps(registro,indent=2)+'\n',encoding='utf-8')
    torch.set_num_threads(2)
    try:
        for razao in registro['configuracao']['razoes_sigma']:
            ajuste={'intercepto':0.,'phi':0.,'sigma_residual':.01*razao}
            p=probabilidades(ajuste,0.,.01,[1],20261019,trajetorias=16384,dispositivo='cpu')[0]
            # Caminhada de 60 incrementos após a entrada; latência irrelevante para phi=0.
            g=np.random.default_rng(20261019)
            nivel=np.zeros(65536); classes=np.ones(65536,dtype=int)
            for _ in range(60):
                nivel += g.normal(0,.01*razao/np.sqrt(60),len(nivel))
                livres=classes==1
                classes[livres & (nivel>=.01)]=2
                classes[livres & (nivel<=-.01)]=0
            referencia=(np.bincount(classes,minlength=3)+.5)/(65536+1.5)
            diferenca=float(np.max(np.abs(p-referencia)))
            registro['casos'].append({'razao_sigma':razao,'rotina':p.tolist(),'referencia_independente':referencia.tolist(),'diferenca_maxima':diferenca})
            assert diferenca<=.03, registro['casos'][-1]
        assert all(registro['casos'][i]['rotina'][1]>registro['casos'][i+1]['rotina'][1] for i in range(2))
        registro['status']='aprovado'
    except Exception as e:
        registro['status']='falha'; registro['erro']=repr(e)
        raise
    finally:
        registro['fim_utc']=datetime.now(timezone.utc).isoformat()
        registro['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        registro['fonte_ar1_sha256']=hashlib.sha256((RAIZ/'barreiras/ar1.py').read_bytes()).hexdigest()
        registro['versoes']={'numpy':np.__version__,'torch':torch.__version__}
        destino.write_text(json.dumps(registro,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(registro['casos'],indent=2))

if __name__=='__main__':
    executar()
