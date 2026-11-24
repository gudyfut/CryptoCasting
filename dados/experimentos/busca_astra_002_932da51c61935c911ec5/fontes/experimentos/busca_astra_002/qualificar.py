"""Qualificação CUDA sintética; não consome ajustes de mercado."""
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,salvar_json,sha256
from .contrato import REG,ancoras,ambiente_cuda

def executar():
    import torch
    from treinamento.otimizacao import fixar_seed
    from experimentos.busca_astra.rede import Rede
    from experimentos.busca_astra.treino import ajustar,atualizar,conferir_controle
    from .ciclo import fontes
    fs=fontes();dest=REG/'qualificacoes'/agora().replace(':','').replace('+','_');dest.mkdir(parents=True)
    r=dict(ancoras()['A0_C05'],contexto=24)
    class Sintetico:
        def __init__(self):
            self.bloco='sintetico';self.ym=.001;self.ys=.02
            rng=np.random.default_rng(77);self.x=rng.normal(size=(192,24,5)).astype(np.float32)
            self.y=.001+.02*(.3*self.x[:,-1,0]+.1*self.x[:,:,1].mean(1))
            self.indices={'treino':np.arange(128),'validacao':np.arange(128,160),'comparacao':np.arange(160,192)}
            self.matriz=np.zeros((192,5),np.float32);self.escalas={'sintetico':True}
            t=pd.date_range('2000-01-01',periods=192,freq='h',tz='UTC')
            self.tabela=pd.DataFrame(dict(indice_candle=np.arange(192),origem_utc=t,destino_utc=t+pd.Timedelta(hours=24),alvo=self.y))
        def janelas(self,ids):return self.x[ids]
    ds=Sintetico()
    for n in ['a','b']:
        ajustar(ds,r,42,dest/n,{'qualificacao':True},300,epocas=3,paciencia=3)
    ctrl=conferir_controle(dest/'a',dest/'b')
    pa=pd.read_parquet(dest/'a/previsoes_comparacao.parquet');pb=pd.read_parquet(dest/'b/previsoes_comparacao.parquet')
    np.testing.assert_allclose(pa.previsao,pb.previsao,rtol=0,atol=1e-5)
    # S é avaliado apenas após seleção. Alterar seus alvos não pode mudar pesos/época/predições.
    ds.y[160:]+=5.;ds.tabela.loc[160:,'alvo']=ds.y[160:]
    ajustar(ds,r,42,dest/'s_alterado',{'qualificacao':True},300,epocas=3,paciencia=3)
    conferir_controle(dest/'a',dest/'s_alterado')
    pc=pd.read_parquet(dest/'s_alterado/previsoes_comparacao.parquet')
    np.testing.assert_allclose(pa.previsao,pc.previsao,rtol=0,atol=1e-5)
    fixar_seed(42);extremo=dict(r,contexto=168,largura=64,pooling='media',momentum=True,volatilidade=True,volume_relativo=True)
    rede=Rede(extremo,10).cuda();x=torch.randn(64,168,10,device='cuda');y=torch.randn(64,device='cuda')
    grupos=[{'params':[p for p in rede.parameters() if not getattr(p,'_no_weight_decay',False)],'weight_decay':.001},
            {'params':[p for p in rede.parameters() if getattr(p,'_no_weight_decay',False)],'weight_decay':0.}]
    assert grupos[1]['params'];opt=torch.optim.AdamW(grupos,lr=.0002)
    antes=rede.projecao.weight.detach().clone();atualizar(rede,opt,x,y,'huber');assert not torch.equal(antes,rede.projecao.weight)
    assert rede(x).shape==(64,)
    memoria=torch.cuda.max_memory_allocated();assert fs==fontes()
    recibo={'utc':agora(),'situacao':'aprovado','fontes':fs,'ambiente':ambiente_cuda(),'controle_sintetico':ctrl,
        'S_nao_seleciona_checkpoint':True,'dimensoes_extremas_64x168x10':True,'atualizacao_confirmada':True,
        'decay_marcados_isento':True,'recarga_exata':True,'memoria_pico_bytes':memoria,'treinos_mercado':0}
    salvar_json(dest/'qualificacao.json',recibo);print('QUALIFICACAO',str((dest/'qualificacao.json').relative_to(RAIZ)),flush=True)

if __name__=='__main__':executar()
