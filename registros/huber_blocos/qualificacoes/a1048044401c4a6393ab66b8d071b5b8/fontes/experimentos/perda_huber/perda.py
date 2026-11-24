"""Única intervenção: 2*Huber(delta=1) no alvo padronizado de treino."""
POLITICA = {'nome': 'HuberLoss', 'delta': 1.0, 'multiplicador': 2.0,
            'reducao': 'sum_por_lote_real', 'alvo': 'padronizado_treino'}


def atualizar_lote(rede, otimizador, x, y, microbatch, clipping, politica):
    import math
    import torch
    if (len(x) == 0 or y.shape != (len(x),) or microbatch < 1
            or set(politica) != set(POLITICA)
            or any(politica[k] != POLITICA[k] for k in POLITICA if k != 'delta')
            or not math.isfinite(politica['delta']) or politica['delta'] <= 0):
        raise ValueError('Lote/alvo inválido.')
    otimizador.zero_grad(set_to_none=True)
    soma = 0.
    for inicio in range(0, len(x), microbatch):
        p = rede(x[inicio:inicio + microbatch])
        real = y[inicio:inicio + microbatch]
        if p.shape != real.shape:
            raise ValueError('Saída e alvo não podem usar broadcasting.')
        perda = politica['multiplicador'] * torch.nn.functional.huber_loss(
            p, real, reduction='sum', delta=politica['delta'])
        if not torch.isfinite(perda):
            raise ValueError('Perda não finita.')
        (perda / len(x)).backward()
        soma += float(perda.detach().cpu())
    torch.nn.utils.clip_grad_norm_(rede.parameters(), clipping, error_if_nonfinite=True)
    otimizador.step()
    return soma
