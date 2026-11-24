"""Sonda artificial por operação; não atualiza pesos ou consulta teste de mercado."""
import os
os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
import json
import torch
from treinamento.otimizacao import fixar_seed
from infraestrutura.artefatos import RAIZ, salvar_json, agora
from causal_conv1d import causal_conv1d_fn
from mamba_ssm.ops.selective_scan_interface import selective_scan_fn, selective_scan_ref


def repetir(nome, funcao, entradas):
    saidas, gradientes = [], []
    for _ in range(20):
        for v in entradas:
            v.grad = None
        z = funcao(*entradas)
        z.square().mean().backward()
        saidas.append(z.detach().clone())
        gradientes.append([v.grad.detach().clone() for v in entradas])
    r = {'operacao': nome, 'forward_exato': all(torch.equal(saidas[0], v) for v in saidas),
         'gradientes_max_abs': [max(float((g[i]-gradientes[0][i]).abs().max()) for g in gradientes) for i in range(len(entradas))]}
    print(json.dumps(r), flush=True)
    return r


def executar():
    fixar_seed(42)
    torch.use_deterministic_algorithms(True, warn_only=False)
    resultados = []
    for lote in (1, 32):
        x = torch.randn(lote,6,32,device='cuda').transpose(1,2).detach().requires_grad_()
        w = torch.randn(32,4,device='cuda',requires_grad=True)
        b = torch.randn(32,device='cuda',requires_grad=True)
        resultados.append(repetir(f'conv_lote{lote}', lambda x,w,b: causal_conv1d_fn(x,w,b,activation='silu'), [x,w,b]))
        argumentos = [torch.randn(lote,32,6,device='cuda'), torch.randn(lote,32,6,device='cuda'),
                      -torch.rand(32,64,device='cuda'), torch.randn(lote,64,6,device='cuda'),
                      torch.randn(lote,64,6,device='cuda'), torch.randn(32,device='cuda')]
        argumentos = [v.requires_grad_() for v in argumentos]
        for nome, fn in [('scan_cuda', selective_scan_fn), ('scan_ref_cuda', selective_scan_ref)]:
            resultados.append(repetir(f'{nome}_lote{lote}', lambda *a: fn(*a,delta_softplus=True), argumentos))
    destino=RAIZ/'registros/cryptomamba_diario/conferencias'/agora().replace(':','').replace('+','_')
    salvar_json(destino/'isolamento.json',{'resultados':resultados,'novos_treinos':0,'repeticoes':20})


if __name__=='__main__':
    executar()
