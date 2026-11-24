"""Seed, AdamW e acumulação com peso correto para o último lote incompleto."""
import os
import random
import numpy as np


def fixar_seed(seed):
    os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.use_deterministic_algorithms(True, warn_only=True)
    torch.set_num_threads(2)


def criar_otimizador(rede, cfg):
    import torch
    grupos, recibo = [], []
    for nome, p in rede.named_parameters():
        decay = 0. if getattr(p, '_no_weight_decay', False) else cfg['weight_decay']
        if not grupos or grupos[-1]['weight_decay'] != decay:
            grupos.append({'params': [], 'weight_decay': decay})
            recibo.append({'nomes': [], 'weight_decay': decay, 'elementos': 0})
        grupos[-1]['params'].append(p)
        recibo[-1]['nomes'].append(nome)
        recibo[-1]['elementos'] += p.numel()
    if not grupos or sum(len(g['params']) for g in grupos) != len(list(rede.parameters())):
        raise ValueError('Cobertura incorreta do otimizador.')
    return torch.optim.AdamW(grupos, lr=cfg['taxa_aprendizado'], weight_decay=cfg['weight_decay'],
                             betas=(.9, .999), eps=1e-8), recibo


def atualizar_lote(rede, otimizador, x, y, microbatch, clipping):
    import torch
    if len(x) == 0 or y.shape != (len(x),) or microbatch < 1:
        raise ValueError('Lote/alvo inválido.')
    otimizador.zero_grad(set_to_none=True)
    soma = 0.
    for inicio in range(0, len(x), microbatch):
        p = rede(x[inicio:inicio + microbatch])
        real = y[inicio:inicio + microbatch]
        if p.shape != real.shape:
            raise ValueError('Saída e alvo não podem usar broadcasting.')
        perda = torch.nn.functional.mse_loss(p, real, reduction='sum')
        if not torch.isfinite(perda):
            raise ValueError('Perda não finita.')
        (perda / len(x)).backward()
        soma += float(perda.detach().cpu())
    torch.nn.utils.clip_grad_norm_(rede.parameters(), clipping, error_if_nonfinite=True)
    otimizador.step()
    return soma
