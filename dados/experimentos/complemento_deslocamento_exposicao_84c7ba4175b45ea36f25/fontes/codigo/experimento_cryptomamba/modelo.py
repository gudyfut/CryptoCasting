"""Estrutura CMBlock/CMamba de Sepehri et al., MIT; núcleo SSM oficial instalado.

Origem: MShahabSepehri/CryptoMamba@fef42727861a9c3a32241283ab981ef21a49e291.
LICENSE e fonte original preservadas em registros/cryptomamba/fontes_externas/.
Adaptação: contexto168→14 aprendido, cinco canais vigentes e saída de retorno normalizado.
"""
from copy import deepcopy
import torch
from torch import nn
from infraestrutura.artefatos import RAIZ,ler_json
from modelos.neurais import conferir_tensor


class Permutar(nn.Module):
    def forward(self,x):return x.permute(0,2,1)


class CMBlock(nn.Module):
    def __init__(self,largura,estado=64,convolucao=4,expansao=2,eps=1e-5):
        super().__init__()
        import selective_scan_cuda
        import causal_conv1d_cuda
        from mamba_ssm import Mamba
        if Mamba.__module__!='mamba_ssm.modules.mamba_simple':raise RuntimeError('Mamba-1 oficial obrigatório.')
        self.norm=nn.LayerNorm(largura,eps=eps)
        self.op=Mamba(d_model=largura,d_state=estado,d_conv=convolucao,expand=expansao)

    def forward(self,x):return self.op(self.norm(x))+x


class NucleoCMamba(nn.Module):
    def __init__(self,canais,larguras=(14,16,32,1),densidade=4,estado=64,convolucao=4,expansao=2,eps=1e-5):
        super().__init__()
        self.post_process=nn.Sequential(Permutar(),nn.Linear(canais,1))
        self.blocks=nn.ModuleList([nn.Sequential(*[CMBlock(a,estado,convolucao,expansao,eps) for _ in range(densidade)],nn.Linear(a,b)) for a,b in zip(larguras[:-1],larguras[1:])])

    def forward(self,x):
        for bloco in self.blocks:x=bloco(x)
        return self.post_process(x)


class RedeCryptoMambaAdaptada(nn.Module):
    def __init__(self,especificacao,cfg):
        super().__init__();self.especificacao=especificacao;self.familia='cryptomamba_adaptado';self.configuracao_modelo=deepcopy(cfg)
        a=cfg['arquitetura']
        if especificacao.dimensao_entrada!=a['canais'] or a['larguras'][0]!=a['contexto_projetado']:raise ValueError('Contrato da adaptação divergente.')
        self.adaptacao_temporal=nn.Linear(especificacao.contexto,a['contexto_projetado'])
        self.nucleo=NucleoCMamba(a['canais'],a['larguras'],a['densidade'],a['estado'],a['convolucao'],a['expansao'],a['eps_layernorm'])

    def forward(self,x):
        conferir_tensor(x,self.especificacao)
        z=self.adaptacao_temporal(x.transpose(1,2))
        return self.nucleo(z).reshape(len(x))


def criar_rede(especificacao,cfg=None):
    if not torch.cuda.is_available():raise RuntimeError('Adaptação exige CUDA oficial; sem fallback.')
    c=ler_json(RAIZ/'configuracoes/cryptomamba_adaptado_001.json') if cfg is None else cfg
    return RedeCryptoMambaAdaptada(especificacao,c).to(device='cuda',dtype=torch.float32).eval()
