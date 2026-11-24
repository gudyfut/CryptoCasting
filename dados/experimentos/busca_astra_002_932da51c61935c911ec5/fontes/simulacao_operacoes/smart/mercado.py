import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json, sha256, conferir_arquivos
from mercado_futuros.contexto import carregar_contexto
from simulacao_operacoes.futuros.mercado import Mercado


def contrato_spot():
    p=RAIZ/'dados/mercado/binance_spot/449aab6c79dbf88aa625'
    m=ler_json(p/'manifesto.json')
    arquivos={n:h for n,h in m['arquivos'].items() if n.startswith('minutos/BTCUSDT/') and n.endswith('.parquet') and '2023-12' <= n.rsplit('/',1)[-1][:7] <= '2025-12'}
    assert len(arquivos)==25
    return {'pasta':p.relative_to(RAIZ).as_posix(),'manifesto_sha256':sha256(p/'manifesto.json'),'arquivos':arquivos}


def carregar(spot, futuros):
    p=RAIZ/spot['pasta']
    assert sha256(p/'manifesto.json')==spot['manifesto_sha256']
    conferir_arquivos(p,spot['arquivos'])
    partes=[pd.read_parquet(p/n) for n in sorted(spot['arquivos'])]
    q=pd.concat(partes,ignore_index=True)
    q=q[q.inicio_utc >= pd.Timestamp('2023-12-31T23:59:00Z')].reset_index(drop=True)
    assert q.completo.all(), 'Minutos incompletos: nao interpolar.'
    negocio=pd.DataFrame({'open_time':pd.DatetimeIndex(q.inicio_utc).as_unit('ms').asi8})
    for campo in ['open','high','low','close']:
        negocio[campo]=q[campo]
    negocio['count']=q.negocios
    vazio=pd.DataFrame(columns=['fundingTime','fundingRate','markPrice'],dtype=float)
    s=Mercado(negocio,negocio,vazio)
    f=Mercado(*carregar_contexto(futuros))
    assert s.inicio==f.inicio and s.fim==f.fim
    return {'spot':s, 'futuro':f}
