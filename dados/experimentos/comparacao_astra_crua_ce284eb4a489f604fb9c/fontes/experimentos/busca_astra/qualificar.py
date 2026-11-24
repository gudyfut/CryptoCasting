"""Qualificacao CUDA/sintetica: nenhum dado de mercado e treinado."""
import tempfile
from pathlib import Path
import numpy as np
from infraestrutura.artefatos import RAIZ, salvar_json, agora, sha256

def executar():
    from .ciclo import fontes
    fontes_antes=fontes()
    import torch
    import pandas as pd
    from modelos.mamba import RedeMamba
    from modelos.contratos import EspecificacaoModelo
    from treinamento.otimizacao import fixar_seed
    from .rede import Rede, editar_cabeca
    from .treino import ajustar, conferir_controle, atualizar
    from .contrato import REFERENCIA, ambiente_cuda
    assert torch.cuda.is_available()
    d=RAIZ/'registros/busca_astra/qualificacoes'/agora().replace(':','').replace('+','_')
    d.mkdir(parents=True)
    r=dict(REFERENCIA,contexto=24)
    fixar_seed(42)
    nova=Rede(r,5).cuda()
    esp=EspecificacaoModelo('sintetico',tuple('ohlcv'),24,60,1440,.001,.02)
    velha=RedeMamba(esp,{'largura':32,'camadas':2,'estado':16,'convolucao':4,'expansao':2,'dropout':.1}).cuda()
    velha.load_state_dict(nova.state_dict(),strict=True);nova.eval();velha.eval()
    x=torch.randn(9,24,5,device='cuda')
    torch.testing.assert_close(nova(x),velha(x),rtol=0,atol=0)
    antes=nova(x).detach()*.02+.001
    editar_cabeca(nova,.5,.001,.02)
    torch.testing.assert_close(nova(x)*.02+.001,antes*.5,rtol=2e-5,atol=2e-8)
    # Acumulacao correta com lote incompleto e equivalencia quadratica Huber.
    a=torch.nn.Linear(4,1).cuda();b=torch.nn.Linear(4,1).cuda();b.load_state_dict(a.state_dict())
    class Linear(torch.nn.Module):
        def __init__(self,m):super().__init__();self.m=m
        def forward(self,z):return self.m(z).squeeze(-1)
    aa,bb=Linear(a),Linear(b);xx=torch.randn(45,4,device='cuda')*.01;yy=a(xx).detach().squeeze(-1)+.02
    oa=torch.optim.SGD(aa.parameters(),lr=.01);ob=torch.optim.SGD(bb.parameters(),lr=.01)
    atualizar(aa,oa,xx,yy,'huber');ob.zero_grad();torch.nn.functional.mse_loss(bb(xx),yy).backward();torch.nn.utils.clip_grad_norm_(bb.parameters(),1.);ob.step()
    for pa,pb in zip(aa.parameters(),bb.parameters()):torch.testing.assert_close(pa,pb,rtol=1e-6,atol=1e-8)
    # Extremos autorizados: kernels/VRAM/dimensoes, pooling medio e dez canais.
    extremo=dict(REFERENCIA,largura=64,camadas=3,estado=64,indicadores=True,pooling='media')
    grande=Rede(extremo,10).cuda()
    gx=torch.randn(32,168,10,device='cuda');gy=torch.randn(32,device='cuda')
    go=torch.optim.AdamW(grande.parameters(),lr=.0002)
    atualizar(grande,go,gx,gy,'huber')
    memoria_extremo=torch.cuda.max_memory_allocated()
    del grande,gx,gy,go
    torch.cuda.empty_cache()
    class Sintetico:
        def __init__(self):
            self.bloco='sintetico';self.ym=.001;self.ys=.02
            rng=np.random.default_rng(77);self.x=rng.normal(size=(160,24,5)).astype(np.float32)
            self.y=.001+.02*(.3*self.x[:,-1,0]+.1*self.x[:,:,1].mean(1))
            self.indices={'treino':np.arange(128),'validacao':np.arange(128,160)}
            self.matriz=np.zeros((160,5),np.float32);self.escalas={'sintetico':True}
            t=pd.date_range('2000-01-01',periods=160,freq='h',tz='UTC')
            self.tabela=pd.DataFrame(dict(indice_candle=np.arange(160),origem_utc=t,destino_utc=t+pd.Timedelta(hours=24),alvo=self.y))
        def janelas(self,ids):return self.x[ids]
    ds=Sintetico();vinculo={'qualificacao':True}
    for nome in ['a','b']:
        ajustar(ds,r,42,d/nome,vinculo,300,epocas=3,paciencia=3)
    ctrl=conferir_controle(d/'a',d/'b')
    assert fontes_antes==fontes(),'Fontes alteradas durante qualificacao; preservar ensaio e repetir antes de congelar.'
    recibo={'utc':agora(),'situacao':'aprovado','ambiente':ambiente_cuda(),
        'equivalencia_rede_referencia_exata':True,'edicao_cabeca_retorno_real':True,
        'acumulacao_huber_lote_incompleto':True,'dois_ajustes_sinteticos':True,'controle':ctrl,
        'extremo_espaco_forward_backward':True,'memoria_extremo_bytes':memoria_extremo,'fontes':fontes_antes}
    salvar_json(d/'qualificacao.json',recibo)
    print('QUALIFICACAO',d.relative_to(RAIZ).as_posix(),flush=True)

if __name__=='__main__':executar()
