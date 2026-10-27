"""Qualificação numérica e de ambiente; não substitui avaliação de mercado."""
from __future__ import annotations

import importlib.metadata
import inspect
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch

from .arquivos import RAIZ, agora, salvar_json, sha256
from .treino import fixar_seed
from .ar1 import probabilidades, semente_origem


def ambiente():
    pacotes={nome:importlib.metadata.version(nome) for nome in
              ('torch','mamba-ssm','causal-conv1d','numpy','pandas','pyarrow','numba','transformers','triton')}
    from mamba_ssm.modules import mamba_simple
    fonte=Path(inspect.getsourcefile(mamba_simple))
    return {'python':sys.version,'executavel':sys.executable,'plataforma':platform.platform(),
            'pacotes':pacotes,'cuda_disponivel':torch.cuda.is_available(),'cuda_runtime':torch.version.cuda,
            'gpu':torch.cuda.get_device_name() if torch.cuda.is_available() else None,
            'fonte_mamba_sha256':sha256(fonte),'precisao':'float32','tf32':False,
            'determinismo':'algoritmos determinísticos solicitados; kernels externos auditados por recarga',
            'freeze':subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True).splitlines()}


def qualificar():
    inicio=agora()
    destino=RAIZ/'historico/qualificacoes'/f'ambiente_{inicio.replace(":","").replace(".","_")}.json'
    registro={'inicio_utc':inicio,'natureza':'teste_sintetico_sem_resultado_de_mercado','status':'em_execucao'}
    salvar_json(destino,registro)
    try:
        fixar_seed(42)
        if not torch.cuda.is_available():
            raise RuntimeError('CUDA indisponível.')
        subprocess.run([sys.executable,'-m','pip','check'],check=True,capture_output=True,text=True)
        from mamba_ssm import Mamba
        from mamba_ssm.ops.selective_scan_interface import selective_scan_fn,selective_scan_ref
        verificacoes=[]
        for comprimento in (24,168):
            base=[torch.randn(2,8,comprimento,device='cuda'),torch.randn(2,8,comprimento,device='cuda')*.1,
                  -torch.rand(8,4,device='cuda'),torch.randn(2,4,comprimento,device='cuda'),
                  torch.randn(2,4,comprimento,device='cuda'),torch.randn(8,device='cuda'),
                  torch.randn(2,8,comprimento,device='cuda'),torch.randn(8,device='cuda')]
            a=[x.detach().clone().requires_grad_(True) for x in base]
            b=[x.detach().clone().requires_grad_(True) for x in base]
            real=selective_scan_fn(*a[:6],z=a[6],delta_bias=a[7],delta_softplus=True)
            ref=selective_scan_ref(*b[:6],z=b[6],delta_bias=b[7],delta_softplus=True)
            ga=torch.autograd.grad(real.square().mean(),a)
            gb=torch.autograd.grad(ref.square().mean(),b)
            torch.testing.assert_close(real,ref,rtol=1e-3,atol=1e-3)
            for g,r in zip(ga,gb):
                torch.testing.assert_close(g,r,rtol=1e-3,atol=1e-3)
            rede=Mamba(d_model=32,d_state=16,d_conv=4,expand=2).cuda()
            x=torch.randn(2,comprimento,32,device='cuda',requires_grad=True)
            y=rede(x)
            y.square().mean().backward()
            if not torch.isfinite(y).all() or not torch.isfinite(x.grad).all():
                raise ValueError('Forward/backward não finitos.')
            alterado=x.detach().clone();alterado[:,comprimento//2:]+=10
            rede.eval()
            with torch.no_grad():
                antes=rede(x.detach())[:,:comprimento//2]
                depois=rede(alterado)[:,:comprimento//2]
            torch.testing.assert_close(antes,depois,rtol=0,atol=0)
            dt=torch.nn.functional.softplus(rede.dt_proj.bias.detach())
            if dt.min()<.001-1e-6 or dt.max()>.1+1e-6:
                raise ValueError('Inicialização de delta fora da referência.')
            verificacoes.append({'contexto':comprimento,'erro_saida_scan':float((real-ref).abs().max()),
                'erro_gradiente_scan':max(float((g-r).abs().max()) for g,r in zip(ga,gb)),
                'causalidade_prefixo_exata':True,'dt_min':float(dt.min()),'dt_max':float(dt.max())})
        registro.update(status='aprovado',ambiente=ambiente(),verificacoes=verificacoes,fim_utc=agora())
        salvar_json(destino,registro)
        return registro
    except Exception as erro:
        registro.update(status='falha',erro=f'{type(erro).__name__}: {erro}',fim_utc=agora())
        salvar_json(destino,registro)
        raise


def qualificar_ar1(ajuste,horas,amostras,par,fold,destino):
    # Datas determinadas por índice, não por volatilidade, classe ou desempenho.
    indices=np.unique(np.linspace(0,len(amostras)-1,32,dtype=int))
    diferencas=[]
    exemplos=[]
    inicio=time.perf_counter()
    for i in indices:
        r=amostras.iloc[i]
        seed=semente_origem(par,fold,r.origem_utc.isoformat())
        anterior=float(horas.loc[int(r.indice_hora),'retorno'])
        p=probabilidades(ajuste,anterior,float(r.sigma),[1,24,168],seed)
        grande=probabilidades(ajuste,anterior,float(r.sigma),[1,24,168],seed,trajetorias=16384)
        diff=np.abs(p-grande)
        diferencas.extend(diff.ravel())
        exemplos.append({'origem':r.origem_utc.isoformat(),'p4096':p.tolist(),'p16384':grande.tolist()})
    proporcao=float((np.asarray(diferencas)<=.03).mean())
    resultado={'status':'aprovado' if proporcao>=.95 else 'falha','proporcao_diferenca_ate_003':proporcao,
               'maxima_diferenca':float(max(diferencas)),'segundos':time.perf_counter()-inicio,'exemplos':exemplos}
    salvar_json(destino,resultado)
    if proporcao<.95:
        raise ValueError('Convergência Monte Carlo não aprovada.')
    return resultado
