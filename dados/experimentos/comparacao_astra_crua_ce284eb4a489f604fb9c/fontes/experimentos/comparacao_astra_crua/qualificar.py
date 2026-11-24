"""Dados reais sem treino; reproducao sintetica CUDA na receita crua."""
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, sha256, agora
from .contrato import REG, ORIGEM, ASTRA, CRUA, FINAIS, SEEDS, fontes

def conferir_populacoes():
    from experimentos.busca_astra.dados import Dados, carregar_candles
    candles=carregar_candles();evidencias={}
    for b in FINAIS:
        a=Dados(candles,ASTRA,b);c=Dados(candles,CRUA,b)
        assert (a.ym,a.ys)==(c.ym,c.ys)
        antigo=ler_json(ORIGEM/'final/candidata'/f'{b}_42'/'escalas.json')
        assert a.escalas==antigo
        for parte in a.indices:
            np.testing.assert_array_equal(a.indices[parte],c.indices[parte])
            ids=a.indices[parte]
            amostra=ids[np.linspace(0,len(ids)-1,min(2048,len(ids))).astype(int)] if parte=='treino' else ids
            esperado=a.tabela.iloc[amostra].reset_index(drop=True)
            for s in SEEDS:
                q=pd.read_parquet(ORIGEM/'final/candidata'/f'{b}_{s}'/f'previsoes_{parte}.parquet')
                pd.testing.assert_frame_equal(esperado,q.drop(columns='previsao').reset_index(drop=True))
            ix=ids[np.linspace(0,len(ids)-1,min(64,len(ids))).astype(int)]
            x=c.janelas(ix)
            for j,i in enumerate(ix):np.testing.assert_array_equal(x[j],candles[['open','high','low','close','volume']].iloc[i-167:i+1].to_numpy(np.float32))
        evidencias[b]={'contagens':a.escalas['contagens'],'media_alvo':a.ym,'escala_alvo':a.ys,
                       'iguais_heranca_8_seeds':True,'entrada_crua_exata':True}
    return evidencias

def executar():
    antes=fontes()
    from experimentos.busca_astra.contrato import ambiente_cuda
    from experimentos.busca_astra.treino import ajustar, conferir_controle
    import torch
    assert ambiente_cuda()==ler_json(ORIGEM/'congelamento.json')['ambiente_cuda']
    d=REG/'qualificacoes'/agora().replace(':','').replace('+','_');d.mkdir(parents=True)
    pop=conferir_populacoes()
    class Sintetico:
        def __init__(self):
            rng=np.random.default_rng(1123);self.bloco='sintetico';self.ym=.001;self.ys=.02
            self.x=np.empty((96,168,5),np.float32)
            precos=50000*np.exp(rng.normal(0,.002,(96,168)))
            for k in range(4): self.x[:,:,k]=precos*(1+(k-1.5)*.0001)
            self.x[:,:,4]=rng.lognormal(4,1,(96,168))
            self.y=self.ym+self.ys*rng.normal(size=96)
            self.indices={'treino':np.arange(64),'validacao':np.arange(64,80),'teste':np.arange(80,96)}
            self.matriz=np.zeros((96,5),np.float32);self.escalas={'sintetico':True}
            t=pd.date_range('2000-01-01',periods=96,freq='h',tz='UTC')
            self.tabela=pd.DataFrame(dict(indice_candle=np.arange(96),origem_utc=t,destino_utc=t+pd.Timedelta(hours=24),alvo=self.y))
        def janelas(self,ids):return self.x[ids]
    for nome in ['a','b']:
        ajustar(Sintetico(),CRUA,42,d/nome,{'sintetico':True},300,epocas=3,paciencia=3)
    ctrl=conferir_controle(d/'a',d/'b')
    assert antes==fontes()
    recibo={'situacao':'aprovado','utc':agora(),'fontes':antes,'ambiente':ambiente_cuda(),
        'populacoes':pop,'controle_sintetico':ctrl,'ajustes_sinteticos':2,
        'memoria_cuda_maxima_bytes':torch.cuda.max_memory_allocated(),'pasta':d.relative_to(RAIZ).as_posix()}
    salvar_json(d/'qualificacao.json',recibo)
    salvar_json(REG/'qualificacao.json',recibo)
    print('QUALIFICACAO_APROVADA',d,flush=True)

if __name__=='__main__':executar()
