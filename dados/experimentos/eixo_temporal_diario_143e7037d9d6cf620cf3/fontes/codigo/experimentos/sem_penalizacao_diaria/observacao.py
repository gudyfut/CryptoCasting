"""Observação do treino, sem seleção, sorteio ou atualização adicional de pesos."""
import numpy as np
import torch
from mamba_ssm import Mamba
from infraestrutura.artefatos import salvar_json

EPOCAS=(1,5,10,25,50,100,250,500,1000)


def grupo(nome):
    if nome.endswith('A_log'):return 'A_log'
    if nome.endswith('.D'):return 'D'
    if '.norm.' in nome:return 'layernorm'
    if '.op.' in nome:return 'outros_mamba'
    return 'lineares'


def gradientes(rede,penalizacao):
    somas={}
    for n,p in rede.named_parameters():
        g=somas.setdefault(grupo(n),{'grad2':0.,'l2_2':0.})
        assert p.grad is not None and torch.isfinite(p.grad).all(),n
        g['grad2']+=float(p.grad.detach().double().square().sum())
        g['l2_2']+=float((penalizacao*p.detach().double()).square().sum())
    return {k:{'norma_gradiente_tarefa':v['grad2']**.5,'norma_l2':v['l2_2']**.5} for k,v in somas.items()}


def observar(rede,x,destino,epoca,gradiente=None):
    modo=rede.training;cpu_rng=torch.get_rng_state().clone();gpu_rng=torch.cuda.get_rng_state().clone()
    pesos={k:v.detach().clone() for k,v in rede.state_dict().items()}
    ix=np.linspace(0,len(x)-1,min(32,len(x)),dtype=int)
    lote=torch.as_tensor(x[ix],device='cuda');normas={};ativacoes={};hooks=[]
    try:
        rede.eval()
        for n,p in rede.named_parameters():
            g=normas.setdefault(grupo(n),{'soma_quadrados':0.,'elementos':0,'menores_1e6':0})
            v=p.detach().double();g['soma_quadrados']+=float(v.square().sum());g['elementos']+=v.numel();g['menores_1e6']+=int((v.abs()<1e-6).sum())
        for n,m in rede.named_modules():
            if isinstance(m,Mamba):
                def guardar(m,a,o,n=n):
                    ativacoes[n]={'forma':list(a[0].shape),'rms_saida':float(o.double().square().mean().sqrt()),'max_saida':float(o.abs().max())}
                hooks.append(m.register_forward_hook(guardar))
        with torch.inference_mode():completo=rede(lote).clone()
        for h in hooks:h.remove()
        hooks=[m.register_forward_hook(lambda m,a,o:torch.zeros_like(o)) for m in rede.modules() if isinstance(m,Mamba)]
        with torch.inference_mode():residual=rede(lote)
        delta=(completo.double()-residual.double())
        assert torch.isfinite(completo).all() and torch.isfinite(residual).all()
        for k,v in rede.state_dict().items():assert torch.equal(pesos[k],v),k
        assert torch.equal(cpu_rng,torch.get_rng_state()) and torch.equal(gpu_rng,torch.cuda.get_rng_state())
        salvar_json(destino,{'epoca':epoca,'populacao':'janelas de treino fixas e espaçadas; sem alvos na sonda','indices':ix.tolist(),
            'normas':{k:{'norma':v['soma_quadrados']**.5,'elementos':v['elementos'],'fracao_menor_1e6':v['menores_1e6']/v['elementos']} for k,v in normas.items()},
            'ativacoes':ativacoes,'contribuicao_ramos':{'max_abs':float(delta.abs().max()),'rms':float(delta.square().mean().sqrt()),'previsao_media':float(completo.double().mean()),'previsao_desvio':float(completo.double().std(unbiased=False))},
            'gradiente_ultimo_lote_antes_atualizacao':gradiente,'pesos_e_rng_preservados':True,
            'limites':'Somente observação; não seleciona épocas nem interrompe por desempenho. Gradiente de um lote não é trajetória do Adam; contribuição funcional não é lucro.'})
    finally:
        for h in hooks:h.remove()
        rede.train(modo)
